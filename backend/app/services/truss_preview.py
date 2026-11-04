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


def find_connected_components(nodes: list[Any], members: list[Any]) -> list[dict[str, list[str]]]:
    """Partition nodes and members into connected graph components."""
    node_ids = {n.id for n in nodes if hasattr(n, "id")}
    adj: dict[str, set[str]] = {nid: set() for nid in node_ids}
    member_map: dict[str, list[str]] = {nid: [] for nid in node_ids}

    for m in members:
        ni = getattr(m, "node_i", None)
        nj = getattr(m, "node_j", None)
        mid = getattr(m, "id", None)
        if ni in adj and nj in adj:
            adj[ni].add(nj)
            adj[nj].add(ni)
            if mid:
                member_map[ni].append(mid)
                member_map[nj].append(mid)

    visited: set[str] = set()
    components: list[dict[str, list[str]]] = []

    for nid in sorted(node_ids):
        if nid in visited:
            continue
        comp_nodes: list[str] = []
        comp_members: set[str] = set()
        queue = [nid]
        visited.add(nid)

        while queue:
            curr = queue.pop(0)
            comp_nodes.append(curr)
            for mid in member_map.get(curr, []):
                comp_members.add(mid)
            for neighbor in adj.get(curr, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        components.append({
            "nodes": sorted(comp_nodes),
            "members": sorted(comp_members),
        })

    return components


def _enrich_validation_errors(errors: list[Any], raw_model: Any) -> list[dict[str, Any]]:
    enriched = []
    model_dict = raw_model.get("model", {}) if isinstance(raw_model, dict) else {}
    nodes_list = model_dict.get("nodes", []) if isinstance(model_dict, dict) else []
    members_list = model_dict.get("members", []) if isinstance(model_dict, dict) else []
    supports_list = model_dict.get("supports", []) if isinstance(model_dict, dict) else []

    for issue in errors:
        d = asdict(issue)
        d["classification"] = "invalid_geometry"
        d["localization_precision"] = "exact"
        path = d.get("path") or ""
        element_id = ""
        affected = {"nodes": [], "members": [], "supports": []}

        parts = path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "model":
            category = parts[1]
            try:
                idx = int(parts[2])
            except ValueError:
                idx = -1

            if category == "members" and 0 <= idx < len(members_list):
                m = members_list[idx]
                if isinstance(m, dict):
                    element_id = m.get("id", "")
                    affected["members"] = [element_id] if element_id else []
                    affected["nodes"] = [n for n in (m.get("node_i"), m.get("node_j")) if n]
            elif category == "nodes" and 0 <= idx < len(nodes_list):
                n = nodes_list[idx]
                if isinstance(n, dict):
                    element_id = n.get("id", "")
                    affected["nodes"] = [element_id] if element_id else []
            elif category == "supports" and 0 <= idx < len(supports_list):
                s = supports_list[idx]
                if isinstance(s, dict):
                    element_id = s.get("id", "")
                    affected["supports"] = [element_id] if element_id else []
                    if s.get("node"):
                        affected["nodes"] = [s.get("node")]

        d["element_id"] = element_id
        d["affected_elements"] = affected
        enriched.append(d)
    return enriched


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
                "errors": _enrich_validation_errors(validation.errors, raw_model),
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
                "classification": "disconnected_geometry",
                "localization_precision": "exact",
                "message": f"Joint {node.id} has no connected members.",
                "element_id": node.id,
                "affected_elements": {"nodes": [node.id], "members": [], "supports": []},
                "path": f"/model/nodes/{node.id}",
            })

    # 2. Duplicate member connections
    seen_pairs: dict[tuple[str, str], str] = {}
    for member in model.members:
        pair = (min(member.node_i, member.node_j), max(member.node_i, member.node_j))
        if pair in seen_pairs:
            warnings.append({
                "code": "DUPLICATE_MEMBER_CONNECTION",
                "classification": "invalid_geometry",
                "localization_precision": "exact",
                "message": f"Member {member.id} connects the same joints ({member.node_i} ↔ {member.node_j}) as member {seen_pairs[pair]}.",
                "element_id": member.id,
                "affected_elements": {"nodes": [member.node_i, member.node_j], "members": [member.id, seen_pairs[pair]], "supports": []},
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
        supp_nodes = [s.node for s in model.supports] if model.supports else [n.id for n in model.nodes]
        warnings.append({
            "code": "INSUFFICIENT_SUPPORTS",
            "classification": "underconstrained_system",
            "localization_precision": "exact" if model.supports else "component_level",
            "message": f"The structure has {reaction_count} support constraint{'s' if reaction_count != 1 else ''} (at least 3 non-parallel constraints are required for stable planar equilibrium).",
            "element_id": model.supports[0].id if model.supports else (model.nodes[0].id if model.nodes else ""),
            "affected_elements": {
                "nodes": supp_nodes,
                "members": [],
                "supports": [s.id for s in model.supports],
            },
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
                "classification": "invalid_geometry",
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

        components = find_connected_components(model.nodes, model.members)
        primary_comp = components[0] if components else {"nodes": [n.id for n in model.nodes], "members": [m.id for m in model.members]}
        classification = "mechanism" if diagnostics.category in ("UNDERDETERMINED", "SINGULAR_SQUARE") else ("statically_indeterminate" if diagnostics.category == "OVERDETERMINED" else "solver_diagnostic")

        uncertainty_msg = None
        if diagnostics.category in ("UNDERDETERMINED", "SINGULAR_SQUARE"):
            uncertainty_msg = (
                f"Numerical rank deficiency detected (rank {diagnostics.numerical_rank} vs {diagnostics.unknown_count} unknowns). "
                "The kinematic mechanism is distributed across this connected component. Because the deficiency is a property of the global "
                "equilibrium matrix, the exact affected member cannot be uniquely isolated without adding panel bracing."
            )
        elif diagnostics.category == "OVERDETERMINED":
            uncertainty_msg = (
                f"Statically indeterminate system: {diagnostics.equation_count} equations vs {diagnostics.unknown_count} unknowns. "
                "Redundant members or constraints are distributed across this component."
            )

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
                "classification": classification,
                "message": msg,
                "equation_count": diagnostics.equation_count,
                "unknown_count": diagnostics.unknown_count,
                "rank": diagnostics.numerical_rank,
                "condition_number": diagnostics.condition_number,
                "affected_elements": {
                    "nodes": primary_comp["nodes"],
                    "members": primary_comp["members"],
                    "supports": [s.id for s in model.supports],
                },
                "localization_precision": "component_level",
                "uncertainty_explanation": uncertainty_msg,
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

