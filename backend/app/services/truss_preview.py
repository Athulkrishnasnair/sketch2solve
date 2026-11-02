"""Non-persistent preview validation and equilibrium calculations for interactive editing."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.services.solver import (
    SolverAssemblyError,
    assemble_equilibrium_system,
    diagnose_equilibrium_system,
    solve_equilibrium_system,
)
from app.services.validation import validate_truss_request


def evaluate_truss_preview(payload: Any) -> dict[str, Any]:
    """Evaluate a draft truss model without persisting or approving it.

    Performs schema validation, geometric connectivity checks, equilibrium assembly,
    rank/condition diagnostics, and direct solution when determinate.
    """
    if isinstance(payload, dict) and "geometry" in payload and isinstance(payload["geometry"], dict):
        raw_model = payload["geometry"]
    else:
        raw_model = payload

    validation = validate_truss_request(raw_model)
    if not validation.is_valid:
        return {
            "is_valid": False,
            "validation": {
                "status": "invalid",
                "is_valid": False,
                "errors": [asdict(issue) for issue in validation.errors],
                "warnings": [],
            },
            "solvability": {
                "status": "invalid_geometry",
                "category": "INVALID_SYSTEM",
                "message": "Draft geometry has validation errors.",
            },
            "solver_results": None,
        }

    model = validation.model
    if model is None:
        return {
            "is_valid": False,
            "validation": {
                "status": "invalid",
                "is_valid": False,
                "errors": [{"code": "NO_MODEL", "message": "Model could not be parsed.", "path": ""}],
                "warnings": [],
            },
            "solvability": {
                "status": "invalid_geometry",
                "category": "INVALID_SYSTEM",
                "message": "Model could not be parsed.",
            },
            "solver_results": None,
        }

    # Semantic engineering warnings
    warnings: list[dict[str, Any]] = []

    # 1. Disconnected joints (nodes with zero members attached)
    connected_nodes: set[str] = set()
    for member in model.members:
        connected_nodes.add(member.node_i)
        connected_nodes.add(member.node_j)

    for node in model.nodes:
        if node.id not in connected_nodes:
            warnings.append({
                "code": "DISCONNECTED_JOINT",
                "message": f"Joint {node.id} has no connected members.",
                "element_id": node.id,
                "path": f"/model/nodes/{node.id}",
            })

    # 2. Duplicate member connections
    seen_pairs: dict[tuple[str, str], str] = {}
    for member in model.members:
        pair = (min(member.node_i, member.node_j), max(member.node_i, member.node_j))
        if pair in seen_pairs:
            warnings.append({
                "code": "DUPLICATE_MEMBER_CONNECTION",
                "message": f"Member {member.id} connects the same joints ({member.node_i} ↔ {member.node_j}) as member {seen_pairs[pair]}.",
                "element_id": member.id,
                "path": f"/model/members/{member.id}",
            })
        else:
            seen_pairs[pair] = member.id

    # 3. Support constraints count
    reaction_count = 0
    for support in model.supports:
        if support.type == "pin":
            reaction_count += 2
        elif support.type == "roller":
            reaction_count += 1

    equation_count = 2 * len(model.nodes)
    unknown_count = len(model.members) + reaction_count

    # Check for incomplete draft
    if len(model.nodes) < 2 or len(model.members) < 1:
        return {
            "is_valid": True,
            "validation": {
                "status": "incomplete",
                "is_valid": True,
                "errors": [],
                "warnings": warnings,
            },
            "solvability": {
                "status": "incomplete",
                "category": "INCOMPLETE_MODEL",
                "message": "Add at least two connected joints and one member to evaluate equilibrium.",
                "equation_count": equation_count,
                "unknown_count": unknown_count,
            },
            "solver_results": None,
        }

    if reaction_count < 3:
        warnings.append({
            "code": "INSUFFICIENT_SUPPORTS",
            "message": f"The structure has {reaction_count} support constraint{'s' if reaction_count != 1 else ''} (at least 3 non-parallel constraints are required for stable planar equilibrium).",
            "element_id": model.supports[0].id if model.supports else "",
            "path": "/model/supports",
        })

    # Equilibrium matrix assembly
    try:
        system = assemble_equilibrium_system(model)
    except SolverAssemblyError as err:
        return {
            "is_valid": True,
            "validation": {
                "status": "valid",
                "is_valid": True,
                "errors": [],
                "warnings": warnings,
            },
            "solvability": {
                "status": "unsolvable",
                "category": "ASSEMBLY_ERROR",
                "code": err.code,
                "message": err.message,
                "equation_count": equation_count,
                "unknown_count": unknown_count,
            },
            "solver_results": None,
        }

    # System diagnostics
    diagnostics = diagnose_equilibrium_system(system)

    if diagnostics.category != "SQUARE_FULL_RANK":
        if diagnostics.category == "UNDERDETERMINED":
            msg = (
                f"Mechanism or under-constrained system detected: {diagnostics.equation_count} equations vs "
                f"{diagnostics.unknown_count} unknowns (numerical rank {diagnostics.numerical_rank})."
            )
        elif diagnostics.category == "OVERDETERMINED":
            msg = (
                f"Statically indeterminate system: {diagnostics.equation_count} equations vs "
                f"{diagnostics.unknown_count} unknowns. Direct equilibrium requires a square determinate system."
            )
        elif diagnostics.category == "SINGULAR_SQUARE":
            msg = (
                f"Kinematic mechanism detected: square system ({diagnostics.equation_count}×{diagnostics.unknown_count}) "
                f"is rank-deficient (rank {diagnostics.numerical_rank}). Joints may form an unbraced or collinear mechanism."
            )
        elif diagnostics.category == "NUMERICALLY_ILL_CONDITIONED":
            msg = f"Equilibrium matrix is ill-conditioned (condition number {diagnostics.condition_number:.2e} exceeds safe numerical limit)."
        else:
            msg = diagnostics.message or "Structure cannot be solved in static equilibrium."

        return {
            "is_valid": True,
            "validation": {
                "status": "valid",
                "is_valid": True,
                "errors": [],
                "warnings": warnings,
            },
            "solvability": {
                "status": "unsolvable",
                "category": diagnostics.category,
                "message": msg,
                "equation_count": diagnostics.equation_count,
                "unknown_count": diagnostics.unknown_count,
                "rank": diagnostics.numerical_rank,
                "condition_number": diagnostics.condition_number,
            },
            "solver_results": None,
        }

    # Attempt direct solve
    solution = solve_equilibrium_system(system)
    if solution.status == "SOLVED" and solution.member_forces is not None:
        member_states: dict[str, str] = {}
        for m_id, force in solution.member_forces.items():
            if force > 1e-7:
                member_states[m_id] = "tension"
            elif force < -1e-7:
                member_states[m_id] = "compression"
            else:
                member_states[m_id] = "zero"

        formatted_reactions: dict[str, dict[str, float]] = {}
        for (s_id, axis), val in (solution.support_reactions or {}).items():
            if s_id not in formatted_reactions:
                formatted_reactions[s_id] = {}
            formatted_reactions[s_id][axis] = float(val)

        return {
            "is_valid": True,
            "validation": {
                "status": "valid",
                "is_valid": True,
                "errors": [],
                "warnings": warnings,
            },
            "solvability": {
                "status": "solvable",
                "category": "SQUARE_FULL_RANK",
                "message": "Truss is statically determinate and in static equilibrium.",
                "equation_count": diagnostics.equation_count,
                "unknown_count": diagnostics.unknown_count,
                "rank": diagnostics.numerical_rank,
                "condition_number": diagnostics.condition_number,
            },
            "solver_results": {
                "status": "SOLVED",
                "member_forces": solution.member_forces,
                "member_states": member_states,
                "support_reactions": formatted_reactions,
                "max_equilibrium_residual": solution.max_residual,
                "residual_tolerance": solution.residual_tolerance,
                "condition_number": solution.condition_number,
                "force_unit": system.force_unit,
                "length_unit": model.units.length,
            },
        }

    return {
        "is_valid": True,
        "validation": {
            "status": "valid",
            "is_valid": True,
            "errors": [],
            "warnings": warnings,
        },
        "solvability": {
            "status": "unsolvable",
            "category": diagnostics.category,
            "message": solution.message or "Numerical solution failed.",
            "equation_count": diagnostics.equation_count,
            "unknown_count": diagnostics.unknown_count,
            "rank": diagnostics.numerical_rank,
            "condition_number": solution.condition_number,
        },
        "solver_results": None,
    }

