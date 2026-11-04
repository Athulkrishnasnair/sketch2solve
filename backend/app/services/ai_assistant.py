"""AI-powered Issue Resolution Assistant for 2D truss geometry and diagnostics."""

from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.models.truss import TrussModel
from app.services.solver import (
    assemble_equilibrium_system,
    diagnose_equilibrium_system,
    SolverAssemblyError,
)
from app.services.validation import validate_truss_request


BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_ASSISTANT_MODEL = "muse-spark-1.3"
DEFAULT_TIMEOUT_SECONDS = 75.0

ASSISTANT_SYSTEM_PROMPT = (
    "You are an expert structural engineer specializing in 2D pin-jointed truss analysis. "
    "You analyze geometry validation errors, stability deficiencies, support constraints, and kinematic mechanisms. "
    "Provide clear root-cause explanations in rigorous engineering terminology, followed by specific, "
    "minimal, structured geometric and support corrections. Never invent arbitrary unrequested loads, supports, "
    "or dimensions. For a stable 2D planar truss, static determinacy requires m + r = 2j (with r >= 3 non-parallel "
    "reaction components) and non-collinear triangulated bays."
)

ASSISTANT_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "root_cause_explanation": {
            "type": "STRING",
            "description": "Clear 1-2 sentence engineering explanation of why this error or instability occurred.",
        },
        "engineering_rationale": {
            "type": "STRING",
            "description": "Detailed structural mechanics rationale explaining the physical behavior.",
        },
        "proposed_fixes": {
            "type": "ARRAY",
            "description": "List of structured proposed corrections.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "title": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "affected_elements": {
                        "type": "OBJECT",
                        "properties": {
                            "nodes": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "members": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "supports": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "loads": {"type": "ARRAY", "items": {"type": "STRING"}},
                        },
                        "required": ["nodes", "members", "supports", "loads"],
                    },
                    "modifications": {
                        "type": "OBJECT",
                        "properties": {
                            "nodes_to_add": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "id": {"type": "STRING"},
                                        "x": {"type": "NUMBER"},
                                        "y": {"type": "NUMBER"},
                                    },
                                    "required": ["id", "x", "y"],
                                },
                            },
                            "nodes_to_remove": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "members_to_add": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "id": {"type": "STRING"},
                                        "node_i": {"type": "STRING"},
                                        "node_j": {"type": "STRING"},
                                    },
                                    "required": ["id", "node_i", "node_j"],
                                },
                            },
                            "members_to_remove": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "supports_to_add": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "id": {"type": "STRING"},
                                        "node": {"type": "STRING"},
                                        "type": {"type": "STRING"},
                                        "direction": {"type": "STRING"},
                                    },
                                    "required": ["id", "node", "type"],
                                },
                            },
                            "supports_to_remove": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "loads_to_add": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "id": {"type": "STRING"},
                                        "node": {"type": "STRING"},
                                        "fx": {"type": "NUMBER"},
                                        "fy": {"type": "NUMBER"},
                                    },
                                    "required": ["id", "node", "fx", "fy"],
                                },
                            },
                            "loads_to_remove": {"type": "ARRAY", "items": {"type": "STRING"}},
                        },
                    },
                },
                "required": ["id", "title", "description", "affected_elements", "modifications"],
            },
        },
        "alternatives": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Alternative valid engineering solutions if multiple options exist.",
        },
        "missing_information": {
            "type": "STRING",
            "description": "Specific missing engineering details if information is insufficient.",
        },
    },
    "required": ["root_cause_explanation", "engineering_rationale", "proposed_fixes"],
}


def resolve_geometry_issue(
    geometry: dict[str, Any],
    issue: dict[str, Any],
    diagnostics: dict[str, Any] | None = None,
    *,
    provider: str | None = None,
    client: Any | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Resolve an identified structural issue using AI with deterministic safety validation.

    1. Checks issue context and diagnostics.
    2. Attempts AI provider call if credentials are configured or mock client is passed.
    3. Gracefully falls back to deterministic structural mechanics guidance if AI is unavailable.
    4. Deterministically validates all proposed modifications against the TrussModel schema.
    5. Returns verified explanations, affected elements, and safe structured fix operations.
    """
    if not isinstance(geometry, dict) or "model" not in geometry:
        raise ValueError("Invalid geometry payload: missing 'model' container.")

    load_dotenv(dotenv_path=BACKEND_ENV_PATH, override=False)
    api_key = os.environ.get("MODEL_API_KEY", "").strip()

    ai_response = None
    if client is not None or api_key:
        try:
            ai_response = _call_ai_provider(
                geometry=geometry,
                issue=issue,
                diagnostics=diagnostics or {},
                provider="meta",
                client=client,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
            )
        except Exception:
            # Fall back to deterministic engineering rules on provider failure, timeout, or rate-limit
            ai_response = None

    if ai_response is None:
        ai_response = _generate_heuristic_resolution(geometry, issue, diagnostics or {})
    elif not ai_response.get("proposed_fixes"):
        # Augment with deterministic structural repair if the model provided explanations without explicit edits
        heuristic = _generate_heuristic_resolution(geometry, issue, diagnostics or {})
        ai_response["proposed_fixes"] = heuristic.get("proposed_fixes", [])
        if not ai_response.get("root_cause_explanation"):
            ai_response["root_cause_explanation"] = heuristic.get("root_cause_explanation")

    # Safety Validation Gate: verify every proposed fix against schema
    validated_fixes = []
    for fix in ai_response.get("proposed_fixes", []):
        is_valid, validation_errors, modified_geometry = _test_apply_modifications(geometry, fix.get("modifications", {}))
        fix_copy = copy.deepcopy(fix)
        fix_copy["is_valid"] = is_valid
        fix_copy["validation_errors"] = validation_errors
        if is_valid:
            # Check solvability impact
            preview_val = validate_truss_request(modified_geometry)
            if preview_val.is_valid and preview_val.model:
                try:
                    sys = assemble_equilibrium_system(preview_val.model)
                    diag = diagnose_equilibrium_system(sys)
                    fix_copy["predicted_status"] = "solvable" if diag.category == "SQUARE_FULL_RANK" else "unsolvable"
                    fix_copy["predicted_category"] = diag.category
                except SolverAssemblyError as err:
                    fix_copy["predicted_status"] = "assembly_error"
                    fix_copy["predicted_category"] = err.code
            validated_fixes.append(fix_copy)
        else:
            # If invalid, still report why it failed validation rather than silently applying it
            fix_copy["predicted_status"] = "invalid_geometry"
            validated_fixes.append(fix_copy)

    ai_response["proposed_fixes"] = validated_fixes
    ai_response["issue_code"] = issue.get("code", "UNKNOWN_ISSUE")
    ai_response["status"] = "success"
    return ai_response


def _normalize_assistant_response(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None

    root_cause = data.get("root_cause_explanation")
    if not root_cause:
        rc_raw = data.get("root_cause")
        if isinstance(rc_raw, dict):
            root_cause = rc_raw.get("description") or rc_raw.get("stability") or rc_raw.get("effect")
        elif isinstance(rc_raw, str):
            root_cause = rc_raw
        elif data.get("analysis"):
            root_cause = str(data.get("analysis"))

    rationale = data.get("engineering_rationale")
    if not rationale and isinstance(data.get("root_cause"), dict):
        rationale = data["root_cause"].get("stability") or data["root_cause"].get("effect")

    proposed_fixes = data.get("proposed_fixes")
    if not proposed_fixes and "corrections_minimal" in data and isinstance(data["corrections_minimal"], list):
        proposed_fixes = []
        for idx, corr in enumerate(data["corrections_minimal"], start=1):
            title = corr.get("option") or f"Fix option {idx}"
            desc = corr.get("result") or corr.get("note") or corr.get("constraints_used") or title
            mods = {
                "nodes_to_add": [],
                "nodes_to_remove": [],
                "members_to_add": [],
                "members_to_remove": [],
                "supports_to_add": [],
                "supports_to_remove": [],
                "loads_to_add": [],
                "loads_to_remove": [],
            }
            affected = {"nodes": [], "members": [], "supports": [], "loads": []}
            for op in corr.get("operations", []):
                action = op.get("op", "")
                if action in ("delete_node", "remove_node"):
                    node_id = op.get("node") or op.get("id")
                    if node_id:
                        mods["nodes_to_remove"].append(node_id)
                        affected["nodes"].append(node_id)
                elif action in ("add_member", "connect"):
                    count = len(mods["members_to_add"]) + 1
                    m_id = op.get("id") or f"M_add_{count}"
                    ni = op.get("node_i") or op.get("start")
                    nj = op.get("node_j") or op.get("end")
                    if ni and nj:
                        mods["members_to_add"].append({"id": m_id, "node_i": ni, "node_j": nj})
                        affected["members"].append(m_id)
                        affected["nodes"].extend([ni, nj])
                elif action in ("delete_member", "remove_member"):
                    m_id = op.get("member") or op.get("id")
                    if m_id:
                        mods["members_to_remove"].append(m_id)
                        affected["members"].append(m_id)
                elif action in ("add_support",):
                    count = len(mods["supports_to_add"]) + 1
                    s_id = op.get("id") or f"S_add_{count}"
                    s_node = op.get("node")
                    s_type = op.get("type", "pin")
                    if s_node:
                        mods["supports_to_add"].append({"id": s_id, "node": s_node, "type": s_type})
                        affected["supports"].append(s_id)
                        affected["nodes"].append(s_node)
                elif action in ("delete_support", "remove_support"):
                    s_id = op.get("support") or op.get("id")
                    if s_id:
                        mods["supports_to_remove"].append(s_id)
                        affected["supports"].append(s_id)

            proposed_fixes.append({
                "id": f"fix_{idx}",
                "title": title,
                "description": desc,
                "affected_elements": {k: list(dict.fromkeys(v)) for k, v in affected.items()},
                "modifications": mods,
            })

    return {
        "root_cause_explanation": root_cause or "Structural issue identified.",
        "engineering_rationale": rationale or "",
        "proposed_fixes": proposed_fixes or [],
    }


def _call_ai_provider(
    geometry: dict[str, Any],
    issue: dict[str, Any],
    diagnostics: dict[str, Any],
    provider: str,
    client: Any | None,
    api_key: str,
    timeout_seconds: float,
) -> dict[str, Any] | None:
    """Call Meta Model API with structured JSON output schema."""
    user_prompt = (
        f"Truss Geometry:\n{json.dumps(geometry, indent=2)}\n\n"
        f"Detected Issue:\n{json.dumps(issue, indent=2)}\n\n"
        f"Solver Diagnostics:\n{json.dumps(diagnostics, indent=2)}\n\n"
        "Explain the engineering root cause and propose minimal, structured corrections."
    )

    base_url = os.environ.get("MODEL_BASE_URL", "https://api.meta.ai/v1").strip() or "https://api.meta.ai/v1"
    model_name = os.environ.get("MODEL_NAME", DEFAULT_ASSISTANT_MODEL).strip() or DEFAULT_ASSISTANT_MODEL

    use_sdk = client is None
    if use_sdk:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout_seconds,
                max_retries=0,
            )
        except ImportError:
            return None

    try:
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                timeout=timeout_seconds,
            )
            content = response.choices[0].message.content if getattr(response, "choices", None) else None
            if not content:
                return None
            return _normalize_assistant_response(json.loads(content))
        elif hasattr(client, "responses") and hasattr(client.responses, "create"):
            response = client.responses.create(
                model=model_name,
                instructions=ASSISTANT_SYSTEM_PROMPT,
                input=[{
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                }],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "issue_resolution",
                        "strict": True,
                        "schema": ASSISTANT_RESPONSE_SCHEMA,
                    },
                },
                timeout=timeout_seconds,
                store=False,
            )
            output_text = getattr(response, "output_text", None)
            if not output_text:
                return None
            return _normalize_assistant_response(json.loads(output_text))
    except Exception:
        return None

    return None


def _generate_heuristic_resolution(
    geometry: dict[str, Any],
    issue: dict[str, Any],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    """Deterministic engineering issue resolution based on structural mechanics."""
    code = (issue.get("code") or "").upper()
    element_id = issue.get("element_id") or ""
    message = issue.get("message") or ""
    model = geometry.get("model", {})
    nodes = model.get("nodes", [])
    members = model.get("members", [])
    supports = model.get("supports", [])
    loads = model.get("loads", [])

    node_ids = [n["id"] for n in nodes if "id" in n]

    # 1. Missing or Insufficient Supports
    if code in ("INSUFFICIENT_SUPPORTS", "MISSING_SUPPORTS") or "support" in message.lower():
        reaction_count = sum(2 if s.get("type") == "pin" else 1 for s in supports)
        needed = max(0, 3 - reaction_count)
        
        # Sort nodes by X coordinate to find left and right boundary joints
        sorted_nodes = sorted(nodes, key=lambda n: (n.get("x", 0), n.get("y", 0)))
        left_node = sorted_nodes[0]["id"] if sorted_nodes else (node_ids[0] if node_ids else "N1")
        right_node = sorted_nodes[-1]["id"] if len(sorted_nodes) > 1 else (node_ids[1] if len(node_ids) > 1 else "N2")

        fixes = []
        if reaction_count == 0:
            fixes.append({
                "id": "fix_standard_pin_roller",
                "title": f"Apply standard support layout: Pin at {left_node}, Roller at {right_node}",
                "description": (
                    f"Assigns a Pin Support (restraining X & Y) at Joint {left_node} and a Roller Support "
                    f"(restraining Y) at Joint {right_node}, providing the 3 non-parallel reaction components required for stable equilibrium."
                ),
                "affected_elements": {
                    "nodes": [left_node, right_node],
                    "members": [],
                    "supports": ["S_pin", "S_roller"],
                    "loads": [],
                },
                "modifications": {
                    "supports_to_add": [
                        {"id": "S_pin", "node": left_node, "type": "pin"},
                        {"id": "S_roller", "node": right_node, "type": "roller", "direction": "vertical"},
                    ],
                    "supports_to_remove": [],
                    "members_to_add": [],
                    "members_to_remove": [],
                    "nodes_to_add": [],
                    "nodes_to_remove": [],
                    "loads_to_add": [],
                    "loads_to_remove": [],
                },
            })
        elif reaction_count < 3:
            # Find an unconstrained node
            supported_nodes = {s.get("node") for s in supports}
            target_node = right_node if right_node not in supported_nodes else (left_node if left_node not in supported_nodes else None)
            if not target_node:
                for n in node_ids:
                    if n not in supported_nodes:
                        target_node = n
                        break
            target_node = target_node or (node_ids[-1] if node_ids else "N1")
            existing_pin = any(s.get("type") == "pin" for s in supports)
            s_type = "roller" if existing_pin else "pin"
            
            s_id = f"S_{target_node}"
            while any(s.get("id") == s_id for s in supports):
                s_id = f"{s_id}_new"

            fixes.append({
                "id": "fix_add_constraint",
                "title": f"Add {s_type.capitalize()} support at Joint {target_node}",
                "description": (
                    f"Provides additional boundary restraint at Joint {target_node} to satisfy the global 3-reaction equilibrium criterion."
                ),
                "affected_elements": {
                    "nodes": [target_node],
                    "members": [],
                    "supports": [s_id],
                    "loads": [],
                },
                "modifications": {
                    "supports_to_add": (
                        [{"id": s_id, "node": target_node, "type": "roller", "direction": "vertical"}]
                        if s_type == "roller"
                        else [{"id": s_id, "node": target_node, "type": "pin"}]
                    ),
                    "supports_to_remove": [],
                    "members_to_add": [],
                    "members_to_remove": [],
                    "nodes_to_add": [],
                    "nodes_to_remove": [],
                    "loads_to_add": [],
                    "loads_to_remove": [],
                },
            })

        return {
            "root_cause_explanation": (
                f"The structure has only {reaction_count} support constraint(s). Planar 2D static equilibrium "
                "requires at least 3 non-parallel reaction components to prevent rigid-body translation and rotation."
            ),
            "engineering_rationale": (
                "Under static equilibrium equations (ΣFx = 0, ΣFy = 0, ΣM = 0), a 2D planar body possesses "
                "3 rigid-body degrees of freedom. Without 3 non-concurrent, non-parallel constraints, the equilibrium "
                "coefficient matrix is rank-deficient and cannot resist arbitrary loads."
            ),
            "proposed_fixes": fixes,
            "alternatives": [
                "Alternative: Replace a roller support with a fixed pin support if horizontal thrust restraint is available at both abutments.",
                "Alternative: If an inclined roller is intended, specify the normal constraint direction explicitly.",
            ],
            "missing_information": None,
        }

    # 2. Disconnected Joint
    if code == "DISCONNECTED_JOINT":
        disc_id = element_id or (node_ids[0] if node_ids else "N1")
        # Find nearest connected joint to connect to
        disc_node = next((n for n in nodes if n.get("id") == disc_id), None)
        other_nodes = [n for n in nodes if n.get("id") != disc_id]
        
        fixes = []
        if disc_node and other_nodes:
            # Sort other nodes by Euclidean distance
            def dist_sq(n: dict[str, Any]) -> float:
                return (n.get("x", 0) - disc_node.get("x", 0)) ** 2 + (n.get("y", 0) - disc_node.get("y", 0)) ** 2
            sorted_others = sorted(other_nodes, key=dist_sq)
            nearest = sorted_others[0]["id"]
            
            m_id = f"M_{disc_id}_{nearest}"
            while any(m.get("id") == m_id for m in members):
                m_id = f"{m_id}_new"

            fixes.append({
                "id": "fix_connect_joint",
                "title": f"Connect Joint {disc_id} to nearest Joint {nearest}",
                "description": f"Creates a structural member ({m_id}) bridging Joint {disc_id} to Joint {nearest}.",
                "affected_elements": {
                    "nodes": [disc_id, nearest],
                    "members": [m_id],
                    "supports": [],
                    "loads": [],
                },
                "modifications": {
                    "members_to_add": [{"id": m_id, "node_i": disc_id, "node_j": nearest}],
                    "members_to_remove": [],
                    "nodes_to_add": [],
                    "nodes_to_remove": [],
                    "supports_to_add": [],
                    "supports_to_remove": [],
                    "loads_to_add": [],
                    "loads_to_remove": [],
                },
            })

        fixes.append({
            "id": "fix_delete_disconnected_joint",
            "title": f"Delete unused floating Joint {disc_id}",
            "description": f"Removes isolated Joint {disc_id} from the geometry model because it carries no structural load path.",
            "affected_elements": {
                "nodes": [disc_id],
                "members": [],
                "supports": [],
                "loads": [],
            },
            "modifications": {
                "nodes_to_remove": [disc_id],
                "nodes_to_add": [],
                "members_to_add": [],
                "members_to_remove": [],
                "supports_to_add": [],
                "supports_to_remove": [],
                "loads_to_add": [],
                "loads_to_remove": [],
            },
        })

        return {
            "root_cause_explanation": f"Joint {disc_id} is isolated from the structural network with zero incident members.",
            "engineering_rationale": (
                "In pin-jointed truss analysis, equilibrium equations are formulated node-by-node (2 equations per joint). "
                f"An isolated joint adds 2 trivial zero-force equations (0 = 0) that cause matrix singularity unless connected."
            ),
            "proposed_fixes": fixes,
            "alternatives": [
                "Option A: Add members connecting this joint to adjacent truss chords.",
                "Option B: If the joint was a visual sketch artifact, remove it from the model.",
            ],
            "missing_information": None,
        }

    # 3. Duplicate Member Connection
    if code == "DUPLICATE_MEMBER_CONNECTION":
        dup_member_id = element_id or (members[0]["id"] if members else "M1")
        return {
            "root_cause_explanation": f"Member {dup_member_id} connects the same two joints as another existing member.",
            "engineering_rationale": (
                "Parallel collinear members sharing both endpoints represent redundant structural paths that cause "
                "static indeterminacy under direct pin-joint equilibrium formulation."
            ),
            "proposed_fixes": [
                {
                    "id": "fix_remove_duplicate_member",
                    "title": f"Remove duplicate member {dup_member_id}",
                    "description": f"Deletes redundant member {dup_member_id} to retain a single axial load path between the joints.",
                    "affected_elements": {
                        "nodes": [],
                        "members": [dup_member_id],
                        "supports": [],
                        "loads": [],
                    },
                    "modifications": {
                        "members_to_remove": [dup_member_id],
                        "members_to_add": [],
                        "nodes_to_add": [],
                        "nodes_to_remove": [],
                        "supports_to_add": [],
                        "supports_to_remove": [],
                        "loads_to_add": [],
                        "loads_to_remove": [],
                    },
                }
            ],
            "alternatives": ["Combine the cross-sectional area of both members into one single member."],
            "missing_information": None,
        }

    # 4. Zero Length Member
    if code in ("ZERO_LENGTH_MEMBER", "INVALID_GEOMETRY") or "zero length" in message.lower():
        zero_member_id = element_id or (members[0]["id"] if members else "M1")
        return {
            "root_cause_explanation": f"Member {zero_member_id} has zero length because its endpoints coincide at the same spatial coordinates.",
            "engineering_rationale": (
                "Zero-length members have undefined directional cosines (Δx/L, Δy/L = 0/0), preventing the assembly of "
                "equilibrium equations."
            ),
            "proposed_fixes": [
                {
                    "id": "fix_remove_zero_member",
                    "title": f"Remove zero-length member {zero_member_id}",
                    "description": f"Deletes invalid degenerate member {zero_member_id}.",
                    "affected_elements": {
                        "nodes": [],
                        "members": [zero_member_id],
                        "supports": [],
                        "loads": [],
                    },
                    "modifications": {
                        "members_to_remove": [zero_member_id],
                        "members_to_add": [],
                        "nodes_to_add": [],
                        "nodes_to_remove": [],
                        "supports_to_add": [],
                        "supports_to_remove": [],
                        "loads_to_add": [],
                        "loads_to_remove": [],
                    },
                }
            ],
            "alternatives": ["Adjust the coordinates of one of the incident joints so the member has finite span."],
            "missing_information": None,
        }

    # 5. Kinematic Mechanism / Underdetermined / Singular Square
    category = (diagnostics.get("category") or "").upper()
    if code in ("UNDERDETERMINED", "SINGULAR_SQUARE") or category in ("UNDERDETERMINED", "SINGULAR_SQUARE"):
        eq_count = diagnostics.get("equation_count", len(nodes) * 2)
        un_count = diagnostics.get("unknown_count", len(members) + len(supports))
        rank = diagnostics.get("rank", 0)

        fixes = []
        # If members are missing to form rigid triangles, propose a diagonal brace if at least 4 nodes exist
        if len(nodes) >= 4:
            # Check for potential diagonal connection between node 0 and node 2 or 1 and 3
            existing_pairs = {(min(m["node_i"], m["node_j"]), max(m["node_i"], m["node_j"])) for m in members}
            cand_pair = None
            for i in range(len(node_ids)):
                for j in range(i + 1, len(node_ids)):
                    p = (min(node_ids[i], node_ids[j]), max(node_ids[i], node_ids[j]))
                    if p not in existing_pairs:
                        cand_pair = p
                        break
                if cand_pair:
                    break

            if cand_pair:
                brace_id = f"M_brace_{cand_pair[0]}_{cand_pair[1]}"
                fixes.append({
                    "id": "fix_add_diagonal_brace",
                    "title": f"Add diagonal bracing member between {cand_pair[0]} and {cand_pair[1]}",
                    "description": f"Triangulates open quadrilateral bay to eliminate kinematic mechanism degree of freedom.",
                    "affected_elements": {
                        "nodes": list(cand_pair),
                        "members": [brace_id],
                        "supports": [],
                        "loads": [],
                    },
                    "modifications": {
                        "members_to_add": [{"id": brace_id, "node_i": cand_pair[0], "node_j": cand_pair[1]}],
                        "members_to_remove": [],
                        "nodes_to_add": [],
                        "nodes_to_remove": [],
                        "supports_to_add": [],
                        "supports_to_remove": [],
                        "loads_to_add": [],
                        "loads_to_remove": [],
                    },
                })

        return {
            "root_cause_explanation": (
                f"Kinematic mechanism detected ({eq_count} equations vs {un_count} unknowns, numerical rank {rank}). "
                "The truss geometry allows internal unconstrained movement or lacks triangulation."
            ),
            "engineering_rationale": (
                "For planar pin-jointed trusses, non-triangulated panels (e.g. rectangular bays without diagonals) "
                "behave as four-bar linkages with internal degrees of freedom. All bays must be triangulated to be rigid."
            ),
            "proposed_fixes": fixes,
            "alternatives": [
                "Alternative: Inspect quadrilateral bays and add cross-bracing or diagonal web members.",
                "Alternative: Verify that support constraints prevent global rigid-body translation or rotation.",
            ],
            "missing_information": None,
        }

    # 6. Generic / Fallback
    return {
        "root_cause_explanation": f"Diagnostic check flagged {code or 'validation issue'}: {message or 'Geometry needs adjustment.'}",
        "engineering_rationale": (
            "Static determinacy and solver stability require a schema-compliant model with valid connectivity, "
            "rigid triangulation, and at least 3 non-parallel support reaction components."
        ),
        "proposed_fixes": [],
        "alternatives": [
            "Check that all member end references point to valid existing joints.",
            "Confirm that units and physical dimensions are declared.",
        ],
        "missing_information": "Inspect the geometry editor properties panel to correct invalid parameters.",
    }


def _test_apply_modifications(
    geometry: dict[str, Any],
    modifications: dict[str, Any],
) -> tuple[bool, list[str], dict[str, Any]]:
    """Simulate applying proposed modifications and validate against TrussModel schema."""
    geom_copy = copy.deepcopy(geometry)
    model = geom_copy.get("model", {})
    nodes = list(model.get("nodes", []))
    members = list(model.get("members", []))
    supports = list(model.get("supports", []))
    loads = list(model.get("loads", []))

    # 1. Removals
    nodes_to_remove = set(modifications.get("nodes_to_remove", []))
    members_to_remove = set(modifications.get("members_to_remove", []))
    supports_to_remove = set(modifications.get("supports_to_remove", []))
    loads_to_remove = set(modifications.get("loads_to_remove", []))

    nodes = [n for n in nodes if n.get("id") not in nodes_to_remove]
    members = [m for m in members if m.get("id") not in members_to_remove]
    supports = [s for s in supports if s.get("id") not in supports_to_remove]
    loads = [l for l in loads if l.get("id") not in loads_to_remove]

    # 2. Additions
    for n in modifications.get("nodes_to_add", []):
        if not any(existing.get("id") == n.get("id") for existing in nodes):
            nodes.append(n)

    for m in modifications.get("members_to_add", []):
        if not any(existing.get("id") == m.get("id") for existing in members):
            members.append(m)

    for s in modifications.get("supports_to_add", []):
        if not any(existing.get("id") == s.get("id") for existing in supports):
            cleaned_s = copy.deepcopy(s)
            if cleaned_s.get("type") == "pin" and "direction" in cleaned_s:
                del cleaned_s["direction"]
            supports.append(cleaned_s)

    for l in modifications.get("loads_to_add", []):
        if not any(existing.get("id") == l.get("id") for existing in loads):
            loads.append(l)

    model["nodes"] = nodes
    model["members"] = members
    model["supports"] = supports
    model["loads"] = loads
    geom_copy["model"] = model

    val_res = validate_truss_request(geom_copy)
    errors = [issue.message for issue in val_res.errors]
    return val_res.is_valid, errors, geom_copy
