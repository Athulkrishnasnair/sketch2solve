"""Conversational Natural-Language Truss Design Service.

Enables creating, modifying, and explaining 2D planar trusses via natural language
while strictly enforcing deterministic structural engineering validation, schema
integrity, and proposal safety.
"""

from __future__ import annotations

import copy
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from app.models.truss import TrussModel, ValidationIssue
from app.services.solver import (
    SolverAssemblyError,
    assemble_equilibrium_system,
    diagnose_equilibrium_system,
    solve_equilibrium_system,
)
from app.services.truss_preview import evaluate_truss_preview, find_connected_components
from app.services.validation import validate_truss_request


BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_DESIGN_MODEL = "gemini-3.1-flash-lite"
DEFAULT_TIMEOUT_SECONDS = 30.0

MAX_MESSAGE_LENGTH = 2000
MAX_ELEMENTS_COUNT = 500
COORDINATE_BOUND = 1e6

ALLOWED_OPERATIONS = frozenset({
    "add_joint",
    "update_joint",
    "remove_joint",
    "add_member",
    "update_member",
    "remove_member",
    "add_support",
    "update_support",
    "remove_support",
    "add_load",
    "update_load",
    "remove_load",
})

OUT_OF_SCOPE_PATTERNS = [
    r"\b(write|create|generate|show|provide|give\s+me)\s+(?:a\s+|an\s+|some\s+)?(python|javascript|bash|shell|c\+\+|sql|code|script)\b",
    r"\b(python|javascript|bash|shell|c\+\+|sql)\s+script\b",
    r"\b(system\s*prompt|system\s*instruction|ignore\s+(all\s+)?previous\s+instructions)\b",
    r"\b(api[_\s-]?key|secret|password|credential|token|env\s*file|\.env)\b",
    r"\b(rm\s+-rf|curl\s+|wget\s+|chmod\s+|eval\(|exec\(|subprocess|os\.system)\b",
    r"\b(recipe|cook|weather|poem|song|lyrics|movie|joke|dating|football|horoscope)\b",
]

DESIGN_SYSTEM_PROMPT = (
    "You are an expert structural engineering assistant specializing in 2D pin-jointed planar trusses. "
    "You help users create, modify, and explain truss structures using concise, rigorous engineering language. "
    "Rules:\n"
    "1. Answer the actual engineering request concisely without filler or echoing the prompt.\n"
    "2. For CREATE: propose a complete, valid 2D truss in Schema 1.0 (nodes, members, supports, loads, units). "
    "Use standard engineering layouts (e.g. Warren, Pratt, triangular roof). Never invent unstated materials or cross-sections.\n"
    "3. For MODIFY: propose ONLY the specific requested changes as discrete operations (add_joint, update_joint, "
    "remove_joint, add_member, update_member, remove_member, add_support, update_support, remove_support, add_load, "
    "update_load, remove_load). Preserve all unaffected geometry, supports, loads, and metadata.\n"
    "4. For EXPLAIN: provide concise, technical explanations grounded in actual joint coordinates, members, static determinacy "
    "(m + r vs 2j), equilibrium equations, and available solver results. If unsolved, state that verified forces are unavailable.\n"
    "5. When a request is ambiguous (e.g. 'make it stronger' or missing critical dimensions), ask specific clarification questions.\n"
    "6. Never claim a structure is safe merely because it is solvable."
)

DESIGN_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "intent": {"type": "STRING", "enum": ["create", "modify", "explain"]},
        "status": {"type": "STRING", "enum": ["proposed", "explained", "needs_clarification", "rejected"]},
        "explanation": {"type": "STRING", "description": "Concise engineering explanation."},
        "clarification_questions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "question": {"type": "STRING"},
                    "options": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "recommended": {"type": "STRING"},
                },
                "required": ["question", "options"],
            },
        },
        "operations": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "op": {
                        "type": "STRING",
                        "enum": [
                            "add_joint",
                            "update_joint",
                            "remove_joint",
                            "add_member",
                            "update_member",
                            "remove_member",
                            "add_support",
                            "update_support",
                            "remove_support",
                            "add_load",
                            "update_load",
                            "remove_load",
                        ],
                    },
                    "id": {"type": "STRING"},
                    "node_i": {"type": "STRING"},
                    "node_j": {"type": "STRING"},
                    "node": {"type": "STRING"},
                    "x": {"type": "NUMBER"},
                    "y": {"type": "NUMBER"},
                    "dx": {"type": "NUMBER"},
                    "dy": {"type": "NUMBER"},
                    "type": {"type": "STRING", "enum": ["pin", "roller"]},
                    "direction": {"type": "STRING", "enum": ["horizontal", "vertical"]},
                    "fx": {"type": "NUMBER"},
                    "fy": {"type": "NUMBER"},
                },
                "required": ["op"],
            },
        },
        "proposed_model": {
            "type": "OBJECT",
            "properties": {
                "schema_version": {"type": "STRING"},
                "metadata": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "units": {
                            "type": "OBJECT",
                            "properties": {
                                "length": {"type": "STRING", "enum": ["m", "mm", "ft"]},
                                "force": {"type": "STRING", "enum": ["kN", "N", "lbf"]},
                            },
                            "required": ["length", "force"],
                        },
                    },
                    "required": ["units"],
                },
                "model": {
                    "type": "OBJECT",
                    "properties": {
                        "nodes": {"type": "ARRAY", "items": {"type": "OBJECT"}},
                        "members": {"type": "ARRAY", "items": {"type": "OBJECT"}},
                        "supports": {"type": "ARRAY", "items": {"type": "OBJECT"}},
                        "loads": {"type": "ARRAY", "items": {"type": "OBJECT"}},
                    },
                    "required": ["nodes", "members", "supports", "loads"],
                },
            },
            "required": ["schema_version", "metadata", "model"],
        },
    },
    "required": ["intent", "status", "explanation"],
}


def is_out_of_scope(message: str) -> bool:
    """Detect non-structural engineering prompts or prompt-injection attempts."""
    msg = message.strip().lower()
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, msg, re.IGNORECASE):
            return True
    return False


def validate_design_input(message: Any, context: Any = None) -> tuple[bool, str | None, str | None]:
    """Validate message length, JSON structure, complexity, and scope."""
    if not isinstance(message, str):
        return False, "INVALID_REQUEST", "Message must be a string."
    cleaned = message.strip()
    if not cleaned:
        return False, "EMPTY_MESSAGE", "Message cannot be empty."
    if len(cleaned) > MAX_MESSAGE_LENGTH:
        return False, "MESSAGE_TOO_LONG", f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters."

    if is_out_of_scope(cleaned):
        return False, "OUT_OF_SCOPE", "I can help create, modify or explain truss structures. Describe the structural design you want."

    if context is not None:
        if not isinstance(context, dict):
            return False, "INVALID_CONTEXT", "Context must be an object."
        model = context.get("model")
        if model is not None:
            if not isinstance(model, dict):
                return False, "INVALID_MODEL_CONTAINER", "Context 'model' must be an object."
            inner = model.get("model")
            if isinstance(inner, dict):
                nodes = inner.get("nodes", [])
                members = inner.get("members", [])
                supports = inner.get("supports", [])
                loads = inner.get("loads", [])
                if (
                    len(nodes) > MAX_ELEMENTS_COUNT
                    or len(members) > MAX_ELEMENTS_COUNT
                    or len(supports) > MAX_ELEMENTS_COUNT
                    or len(loads) > MAX_ELEMENTS_COUNT
                ):
                    return False, "CONTEXT_TOO_LARGE", f"Model exceeds complexity limit of {MAX_ELEMENTS_COUNT} elements per collection."

                # Verify numbers are finite
                for node in nodes:
                    if isinstance(node, dict):
                        for k in ("x", "y"):
                            val = node.get(k)
                            if val is not None and (isinstance(val, bool) or not math.isfinite(val) or abs(val) > COORDINATE_BOUND):
                                return False, "NON_FINITE_NUMERIC_VALUE", f"Node coordinate {k} must be a finite number within bounds."
                for load in loads:
                    if isinstance(load, dict):
                        for k in ("fx", "fy"):
                            val = load.get(k)
                            if val is not None and (isinstance(val, bool) or not math.isfinite(val) or abs(val) > COORDINATE_BOUND):
                                return False, "NON_FINITE_NUMERIC_VALUE", f"Load force component {k} must be a finite number."

    return True, None, None


def detect_intent(intent_param: str | None, message: str, has_model: bool) -> str:
    """Classify user intent into 'create', 'modify', or 'explain'."""
    if intent_param in ("create", "modify", "explain"):
        return intent_param

    msg = message.strip().lower()

    # Question / explanation keywords
    explain_terms = [
        "explain", "why is", "why are", "what happens", "what would happen",
        "is this stable", "is it stable", "which member", "which members",
        "compression", "tension", "reaction", "reactions", "determinacy",
        "carrying more force", "zero force", "load path"
    ]
    if any(term in msg for term in explain_terms):
        return "explain"

    # Modification keywords
    modify_terms = [
        "add a diagonal", "add diagonal", "add member", "remove member", "delete member",
        "move j", "move node", "move joint", "shift joint", "shift j", "change support",
        "change the right support", "change the left support", "add another panel",
        "make the bottom chord", "remove j", "delete j", "add load", "apply load",
        "apply 10 kn", "apply a load", "remove load", "make it stronger"
    ]
    if any(term in msg for term in modify_terms) and has_model:
        return "modify"

    # Creation keywords
    create_terms = [
        "create a", "build a", "design a", "generate a", "make a triangular",
        "make a warren", "make a pratt", "make a roof", "make a truss", "new truss"
    ]
    if any(term in msg for term in create_terms) or not has_model:
        return "create"

    return "modify" if has_model else "create"


def synthesize_truss_model(
    message: str,
    units: dict[str, str] | None = None,
) -> tuple[dict[str, Any], str, list[dict[str, Any]], str]:
    """Deterministically synthesize a new truss model from natural language specifications."""
    msg = message.strip().lower()
    length_unit = (units or {}).get("length", "m")
    force_unit = (units or {}).get("force", "kN")

    # Detect unit overrides in message
    if " mm " in f" {msg} " or msg.endswith("mm"):
        length_unit = "mm"
    elif " ft " in f" {msg} " or " feet " in f" {msg} " or msg.endswith("ft"):
        length_unit = "ft"
    elif " m " in f" {msg} " or " meters " in f" {msg} " or " metres " in f" {msg}":
        length_unit = "m"

    if " lbf " in f" {msg} ":
        force_unit = "lbf"
    elif " n " in f" {msg} " or " newton " in f" {msg} ":
        force_unit = "N"
    elif " kn " in f" {msg} " or " kilonewton " in f" {msg} ":
        force_unit = "kN"

    # Parse span
    span = 6.0
    span_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|mm|ft|meter|meters|metre|metres)?\s*span", msg)
    if not span_match:
        span_match = re.search(r"span\s*(?:of)?\s*(\d+(?:\.\d+)?)", msg)
    if span_match:
        span = float(span_match.group(1))

    # Parse height
    height = None
    height_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|mm|ft|meter|meters|metre|metres)?\s*(?:height|high|tall)", msg)
    if not height_match:
        height_match = re.search(r"height\s*(?:of)?\s*(\d+(?:\.\d+)?)", msg)
    if height_match:
        height = float(height_match.group(1))

    # Parse panel count
    panels = 4
    panel_match = re.search(r"(\d+)\s*(?:panel|panels|bay|bays)", msg)
    if panel_match:
        panels = max(2, min(20, int(panel_match.group(1))))

    # Parse load
    load_fy = None
    load_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kn|n|lbf)?\s*(?:downward|down)?\s*load", msg)
    if not load_match:
        load_match = re.search(r"load\s*(?:of)?\s*(\d+(?:\.\d+)?)", msg)
    if load_match:
        load_val = float(load_match.group(1))
        load_fy = -abs(load_val)

    clarification_questions = []
    status = "proposed"

    # Check if prompt was too brief / ambiguous
    if not span_match and not height_match and not any(t in msg for t in ("warren", "pratt", "howe", "triangle", "triangular", "roof")):
        status = "needs_clarification"
        clarification_questions.append({
            "question": "What overall span and height would you like for this truss?",
            "options": [f"6 {length_unit} span, 3 {length_unit} height", f"10 {length_unit} span, 2.5 {length_unit} height", f"12 {length_unit} span, 3 {length_unit} height"],
            "recommended": f"6 {length_unit} span, 3 {length_unit} height",
        })
        clarification_questions.append({
            "question": "What truss topology suits your structural application?",
            "options": ["Triangular Roof Truss (3 joints)", "Warren Truss (4 panels)", "Pratt Truss (4 panels)"],
            "recommended": "Triangular Roof Truss (3 joints)",
        })

    is_warren = "warren" in msg
    is_pratt = "pratt" in msg
    is_roof = "roof" in msg or "triang" in msg or (not is_warren and not is_pratt)

    nodes: list[dict[str, Any]] = []
    members: list[dict[str, Any]] = []
    supports: list[dict[str, Any]] = []
    loads: list[dict[str, Any]] = []

    if is_warren:
        h = height if height is not None else round(span / 4.0, 2)
        panel_w = span / panels
        explanation = f"Generated a {panels}-panel Warren truss with a {span} {length_unit} span and {h} {length_unit} height."

        # Bottom chord nodes: panels + 1 nodes
        for i in range(panels + 1):
            nodes.append({"id": f"J{i+1}", "x": round(i * panel_w, 3), "y": 0.0})

        # Top chord nodes: panels nodes
        top_offset = len(nodes)
        for i in range(panels):
            nodes.append({"id": f"J{top_offset + i + 1}", "x": round((i + 0.5) * panel_w, 3), "y": round(h, 3)})

        # Bottom chord members
        mid = 1
        for i in range(panels):
            members.append({"id": f"M{mid}", "node_i": f"J{i+1}", "node_j": f"J{i+2}"})
            mid += 1

        # Top chord members
        for i in range(panels - 1):
            members.append({"id": f"M{mid}", "node_i": f"J{top_offset + i + 1}", "node_j": f"J{top_offset + i + 2}"})
            mid += 1

        # Diagonals
        for i in range(panels):
            b_left = f"J{i+1}"
            b_right = f"J{i+2}"
            t_node = f"J{top_offset + i + 1}"
            members.append({"id": f"M{mid}", "node_i": b_left, "node_j": t_node})
            mid += 1
            members.append({"id": f"M{mid}", "node_i": t_node, "node_j": b_right})
            mid += 1

        # Standard supports: Pin at J1, Roller at J_{panels+1}
        supports.append({"id": "S1", "node": "J1", "type": "pin"})
        supports.append({"id": "S2", "node": f"J{panels+1}", "type": "roller", "direction": "vertical"})

        # Load at central top node
        center_top_idx = top_offset + (panels // 2)
        load_mag = load_fy if load_fy is not None else -10.0
        loads.append({"id": "L1", "node": f"J{center_top_idx}", "fx": 0.0, "fy": load_mag})

    elif is_pratt:
        h = height if height is not None else round(span / 4.0, 2)
        panel_w = span / panels
        explanation = f"Generated a {panels}-panel Pratt truss with a {span} {length_unit} span and {h} {length_unit} height."

        # Bottom chord nodes
        for i in range(panels + 1):
            nodes.append({"id": f"J{i+1}", "x": round(i * panel_w, 3), "y": 0.0})

        # Top chord nodes (aligned with bottom nodes)
        top_offset = len(nodes)
        for i in range(panels + 1):
            nodes.append({"id": f"J{top_offset + i + 1}", "x": round(i * panel_w, 3), "y": round(h, 3)})

        mid = 1
        # Bottom chord members
        for i in range(panels):
            members.append({"id": f"M{mid}", "node_i": f"J{i+1}", "node_j": f"J{i+2}"})
            mid += 1

        # Top chord members
        for i in range(panels):
            members.append({"id": f"M{mid}", "node_i": f"J{top_offset + i + 1}", "node_j": f"J{top_offset + i + 2}"})
            mid += 1

        # Vertical struts
        for i in range(panels + 1):
            members.append({"id": f"M{mid}", "node_i": f"J{i+1}", "node_j": f"J{top_offset + i + 1}"})
            mid += 1

        # Diagonals sloping toward center
        half = panels // 2
        for i in range(panels):
            if i < half:
                # Slopes down toward center: top left to bottom right
                members.append({"id": f"M{mid}", "node_i": f"J{top_offset + i + 1}", "node_j": f"J{i+2}"})
            else:
                # Slopes down toward center: bottom left to top right
                members.append({"id": f"M{mid}", "node_i": f"J{i+1}", "node_j": f"J{top_offset + i + 2}"})
            mid += 1

        supports.append({"id": "S1", "node": "J1", "type": "pin"})
        supports.append({"id": "S2", "node": f"J{panels+1}", "type": "roller", "direction": "vertical"})
        load_mag = load_fy if load_fy is not None else -10.0
        center_top = f"J{top_offset + half + 1}"
        loads.append({"id": "L1", "node": center_top, "fx": 0.0, "fy": load_mag})

    else:
        # Standard determinate triangular / roof truss
        h = height if height is not None else round(span / 2.0, 2)
        explanation = (
            f"Generated a statically determinate triangular truss with a {span} {length_unit} span, "
            f"{h} {length_unit} height, pin support at left, roller support at right, and applied vertical load."
        )

        nodes = [
            {"id": "J1", "x": 0.0, "y": 0.0},
            {"id": "J2", "x": round(span, 3), "y": 0.0},
            {"id": "J3", "x": round(span / 2.0, 3), "y": round(h, 3)},
        ]
        members = [
            {"id": "M1", "node_i": "J1", "node_j": "J2"},
            {"id": "M2", "node_i": "J2", "node_j": "J3"},
            {"id": "M3", "node_i": "J3", "node_j": "J1"},
        ]
        supports = [
            {"id": "S1", "node": "J1", "type": "pin"},
            {"id": "S2", "node": "J2", "type": "roller", "direction": "vertical"},
        ]
        load_mag = load_fy if load_fy is not None else -10.0
        loads = [
            {"id": "L1", "node": "J3", "fx": 0.0, "fy": load_mag},
        ]

    model_dict = {
        "schema_version": "1.0",
        "metadata": {
            "name": f"{'Warren' if is_warren else ('Pratt' if is_pratt else 'Triangular')} Truss",
            "source": "conversational_ai",
            "units": {"length": length_unit, "force": force_unit},
        },
        "model": {
            "nodes": nodes,
            "members": members,
            "supports": supports,
            "loads": loads,
        },
    }

    return model_dict, explanation, clarification_questions, status


def apply_operations_to_model(
    base_model: dict[str, Any],
    operations: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, list[str]], list[str]]:
    """Sequentially apply operations to a deep copy of base_model with strict validation."""
    model_copy = copy.deepcopy(base_model)
    inner = model_copy.setdefault("model", {})
    nodes = inner.setdefault("nodes", [])
    members = inner.setdefault("members", [])
    supports = inner.setdefault("supports", [])
    loads = inner.setdefault("loads", [])

    affected = {
        "nodes": set(),
        "members": set(),
        "supports": set(),
        "loads": set(),
    }
    errors: list[str] = []

    for op_idx, op in enumerate(operations):
        if not isinstance(op, dict):
            errors.append(f"Operation at index {op_idx} must be an object.")
            continue
        op_type = op.get("op")
        if op_type not in ALLOWED_OPERATIONS:
            errors.append(f"Disallowed or unknown operation '{op_type}' at index {op_idx}.")
            continue

        target_id = op.get("id")

        if op_type == "add_joint":
            if not target_id:
                target_id = f"J{len(nodes) + 1}"
            if any(n.get("id") == target_id for n in nodes):
                errors.append(f"Cannot add joint: ID '{target_id}' already exists.")
                continue
            x = op.get("x", 0.0)
            y = op.get("y", 0.0)
            if not math.isfinite(x) or not math.isfinite(y):
                errors.append(f"Joint '{target_id}' coordinates must be finite numbers.")
                continue
            nodes.append({"id": target_id, "x": round(float(x), 4), "y": round(float(y), 4)})
            affected["nodes"].add(target_id)

        elif op_type == "update_joint":
            node = next((n for n in nodes if n.get("id") == target_id), None)
            if not node:
                errors.append(f"Cannot update joint: ID '{target_id}' not found.")
                continue
            if "x" in op and op["x"] is not None:
                if not math.isfinite(op["x"]):
                    errors.append(f"Joint '{target_id}' x coordinate must be finite.")
                    continue
                node["x"] = round(float(op["x"]), 4)
            if "y" in op and op["y"] is not None:
                if not math.isfinite(op["y"]):
                    errors.append(f"Joint '{target_id}' y coordinate must be finite.")
                    continue
                node["y"] = round(float(op["y"]), 4)
            if "dx" in op and op["dx"] is not None:
                node["x"] = round(float(node["x"]) + float(op["dx"]), 4)
            if "dy" in op and op["dy"] is not None:
                node["y"] = round(float(node["y"]) + float(op["dy"]), 4)
            affected["nodes"].add(target_id)

        elif op_type == "remove_joint":
            node_idx = next((i for i, n in enumerate(nodes) if n.get("id") == target_id), None)
            if node_idx is None:
                errors.append(f"Cannot remove joint: ID '{target_id}' not found.")
                continue
            nodes.pop(node_idx)
            affected["nodes"].add(target_id)

            # Cascade removals
            connected_members = [m for m in members if m.get("node_i") == target_id or m.get("node_j") == target_id]
            for m in connected_members:
                mid = m.get("id")
                members.remove(m)
                if mid:
                    affected["members"].add(mid)

            connected_supports = [s for s in supports if s.get("node") == target_id]
            for s in connected_supports:
                sid = s.get("id")
                supports.remove(s)
                if sid:
                    affected["supports"].add(sid)

            connected_loads = [l for l in loads if l.get("node") == target_id]
            for l in connected_loads:
                lid = l.get("id")
                loads.remove(l)
                if lid:
                    affected["loads"].add(lid)

        elif op_type == "add_member":
            ni = op.get("node_i")
            nj = op.get("node_j")
            if not ni or not nj:
                errors.append("add_member operation requires 'node_i' and 'node_j'.")
                continue
            if ni == nj:
                errors.append(f"Self-connected member between '{ni}' and '{nj}' is not allowed.")
                continue
            known_node_ids = {n.get("id") for n in nodes}
            if ni not in known_node_ids or nj not in known_node_ids:
                errors.append(f"add_member references unknown node: {ni if ni not in known_node_ids else nj}.")
                continue
            if any({m.get("node_i"), m.get("node_j")} == {ni, nj} for m in members):
                errors.append(f"Duplicate member between '{ni}' and '{nj}' already exists.")
                continue
            if not target_id:
                target_id = f"M{len(members) + 1}"
            if any(m.get("id") == target_id for m in members):
                errors.append(f"Cannot add member: ID '{target_id}' already exists.")
                continue
            members.append({"id": target_id, "node_i": ni, "node_j": nj})
            affected["members"].add(target_id)
            affected["nodes"].add(ni)
            affected["nodes"].add(nj)

        elif op_type == "update_member":
            member = next((m for m in members if m.get("id") == target_id), None)
            if not member:
                errors.append(f"Cannot update member: ID '{target_id}' not found.")
                continue
            ni = op.get("node_i", member.get("node_i"))
            nj = op.get("node_j", member.get("node_j"))
            if ni == nj:
                errors.append("Member cannot connect a node to itself.")
                continue
            known_node_ids = {n.get("id") for n in nodes}
            if ni not in known_node_ids or nj not in known_node_ids:
                errors.append("Updated member references unknown node.")
                continue
            member["node_i"] = ni
            member["node_j"] = nj
            affected["members"].add(target_id)

        elif op_type == "remove_member":
            member_idx = next((i for i, m in enumerate(members) if m.get("id") == target_id), None)
            if member_idx is None:
                errors.append(f"Cannot remove member: ID '{target_id}' not found.")
                continue
            m = members.pop(member_idx)
            affected["members"].add(target_id)
            if m.get("node_i"):
                affected["nodes"].add(m["node_i"])
            if m.get("node_j"):
                affected["nodes"].add(m["node_j"])

        elif op_type == "add_support":
            node_ref = op.get("node")
            known_node_ids = {n.get("id") for n in nodes}
            if node_ref not in known_node_ids:
                errors.append(f"add_support references unknown node '{node_ref}'.")
                continue
            stype = op.get("type", "pin")
            if stype not in ("pin", "roller"):
                errors.append(f"Invalid support type '{stype}'. Must be 'pin' or 'roller'.")
                continue
            sdir = op.get("direction")
            if stype == "roller" and sdir not in ("horizontal", "vertical"):
                sdir = "vertical"
            if not target_id:
                target_id = f"S{len(supports) + 1}"
            if any(s.get("id") == target_id for s in supports):
                errors.append(f"Cannot add support: ID '{target_id}' already exists.")
                continue
            supp_entry = {"id": target_id, "node": node_ref, "type": stype}
            if stype == "roller":
                supp_entry["direction"] = sdir
            supports.append(supp_entry)
            affected["supports"].add(target_id)
            affected["nodes"].add(node_ref)

        elif op_type == "update_support":
            supp = next((s for s in supports if s.get("id") == target_id), None)
            if not supp:
                errors.append(f"Cannot update support: ID '{target_id}' not found.")
                continue
            if "type" in op:
                stype = op["type"]
                if stype not in ("pin", "roller"):
                    errors.append(f"Invalid support type '{stype}'.")
                    continue
                supp["type"] = stype
            if "direction" in op:
                supp["direction"] = op["direction"]
            if supp.get("type") == "roller" and not supp.get("direction"):
                supp["direction"] = "vertical"
            elif supp.get("type") == "pin":
                supp.pop("direction", None)
            affected["supports"].add(target_id)

        elif op_type == "remove_support":
            s_idx = next((i for i, s in enumerate(supports) if s.get("id") == target_id), None)
            if s_idx is None:
                errors.append(f"Cannot remove support: ID '{target_id}' not found.")
                continue
            s = supports.pop(s_idx)
            affected["supports"].add(target_id)
            if s.get("node"):
                affected["nodes"].add(s["node"])

        elif op_type == "add_load":
            node_ref = op.get("node")
            known_node_ids = {n.get("id") for n in nodes}
            if node_ref not in known_node_ids:
                errors.append(f"add_load references unknown node '{node_ref}'.")
                continue
            fx = float(op.get("fx", 0.0))
            fy = float(op.get("fy", 0.0))
            if not math.isfinite(fx) or not math.isfinite(fy):
                errors.append("Load force components must be finite.")
                continue
            if not target_id:
                target_id = f"L{len(loads) + 1}"
            if any(l.get("id") == target_id for l in loads):
                errors.append(f"Cannot add load: ID '{target_id}' already exists.")
                continue
            loads.append({"id": target_id, "node": node_ref, "fx": round(fx, 4), "fy": round(fy, 4)})
            affected["loads"].add(target_id)
            affected["nodes"].add(node_ref)

        elif op_type == "update_load":
            load = next((l for l in loads if l.get("id") == target_id), None)
            if not load:
                errors.append(f"Cannot update load: ID '{target_id}' not found.")
                continue
            if "fx" in op and op["fx"] is not None:
                load["fx"] = round(float(op["fx"]), 4)
            if "fy" in op and op["fy"] is not None:
                load["fy"] = round(float(op["fy"]), 4)
            affected["loads"].add(target_id)

        elif op_type == "remove_load":
            l_idx = next((i for i, l in enumerate(loads) if l.get("id") == target_id), None)
            if l_idx is None:
                errors.append(f"Cannot remove load: ID '{target_id}' not found.")
                continue
            l = loads.pop(l_idx)
            affected["loads"].add(target_id)
            if l.get("node"):
                affected["nodes"].add(l["node"])

    affected_sorted = {k: sorted(v) for k, v in affected.items()}
    return model_copy, affected_sorted, errors


def synthesize_truss_modification(
    base_model: dict[str, Any],
    message: str,
    selected_element: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    """Parse modification commands and produce restricted operations."""
    msg = message.strip()
    msg_lower = msg.lower()

    inner = base_model.get("model", {})
    nodes = inner.get("nodes", [])
    members = inner.get("members", [])
    supports = inner.get("supports", [])
    loads = inner.get("loads", [])

    node_ids = [n["id"] for n in nodes if "id" in n]
    member_ids = [m["id"] for m in members if "id" in m]

    operations: list[dict[str, Any]] = []
    explanation = ""
    clarification_questions: list[dict[str, Any]] = []

    # Check for "Make it stronger"
    if "make it stronger" in msg_lower or "increase capacity" in msg_lower or "reinforce" in msg_lower:
        explanation = (
            "What do you want to change: add diagonal bracing, increase member sections, or modify the support arrangement? "
            "I cannot determine strength without material and section-capacity information."
        )
        clarification_questions.append({
            "question": "How would you like to reinforce the structural model?",
            "options": [
                "Add diagonal bracing members across unbraced bays",
                "Add an intermediate support to reduce member spans",
                "Reduce applied load magnitudes",
            ],
            "recommended": "Add diagonal bracing members across unbraced bays",
        })
        return [], explanation, clarification_questions

    # 1. Add diagonal / member between J_a and J_b
    add_member_match = re.search(r"add\s+(?:a\s+)?(?:diagonal|member)\s+between\s+(?:(?:joint|node)\s+)?([a-zA-Z0-9_-]+)\s+and\s+(?:(?:joint|node)\s+)?([a-zA-Z0-9_-]+)", msg_lower)
    if add_member_match:
        na_raw, nb_raw = add_member_match.group(1), add_member_match.group(2)
        na = next((nid for nid in node_ids if nid.lower() == na_raw), na_raw.upper())
        nb = next((nid for nid in node_ids if nid.lower() == nb_raw), nb_raw.upper())
        new_mid = f"M{len(members) + 1}"
        operations.append({
            "op": "add_member",
            "id": new_mid,
            "node_i": na,
            "node_j": nb,
        })
        explanation = f"Added member {new_mid} connecting joint {na} and joint {nb}. All other geometry remains unchanged."
        return operations, explanation, []

    # 2. Move joint / node upwards / downwards / coordinate
    move_match = re.search(r"move\s+(?:(?:joint|node)\s+)?([a-zA-Z0-9_-]+)\s+(up(?:ward)?s?|down(?:ward)?s?|left|right)\s+by\s+(\d+(?:\.\d+)?)\s*(?:m|mm|ft|meter|meters)?", msg_lower)
    if move_match:
        target_nid = move_match.group(1)
        direction = move_match.group(2)
        dist = float(move_match.group(3))
        matched_node = next((n for n in nodes if n.get("id", "").lower() == target_nid), None)
        if matched_node:
            nid = matched_node["id"]
            dx, dy = 0.0, 0.0
            if "up" in direction:
                dy = dist
            elif "down" in direction:
                dy = -dist
            elif "left" in direction:
                dx = -dist
            elif "right" in direction:
                dx = dist
            operations.append({
                "op": "update_joint",
                "id": nid,
                "dx": dx,
                "dy": dy,
            })
            explanation = f"Moved joint {nid} {direction} by {dist} {base_model.get('metadata', {}).get('units', {}).get('length', 'm')}."
            return operations, explanation, []

    # 3. Remove member
    remove_member_match = re.search(r"(?:remove|delete)\s+member\s+([a-zA-Z0-9_-]+)", msg_lower)
    if remove_member_match:
        raw_mid = remove_member_match.group(1)
        matched_m = next((m for m in members if m.get("id", "").lower() == raw_mid), None)
        if matched_m:
            mid = matched_m["id"]
            operations.append({"op": "remove_member", "id": mid})
            explanation = f"Removed member {mid} between joints {matched_m.get('node_i')} and {matched_m.get('node_j')}."
            return operations, explanation, []

    # 4. Add load at center / joint
    add_load_match = re.search(r"add\s+(?:a\s+)?(\d+(?:\.\d+)?)\s*(?:kn|n|lbf)?\s*(?:downward|down)?\s*load\s+(?:at\s+(?:the\s+)?([a-zA-Z0-9_-]+))?", msg_lower)
    if add_load_match:
        mag = float(add_load_match.group(1))
        target_loc = add_load_match.group(2) or "centre"
        target_node = None
        if target_loc in ("centre", "center", "middle"):
            # Find node closest to center x
            if nodes:
                min_x = min(n.get("x", 0.0) for n in nodes)
                max_x = max(n.get("x", 0.0) for n in nodes)
                center_x = (min_x + max_x) / 2.0
                target_node = min(nodes, key=lambda n: abs(n.get("x", 0.0) - center_x)).get("id")
        else:
            matched_node = next((n for n in nodes if n.get("id", "").lower() == target_loc), None)
            if matched_node:
                target_node = matched_node["id"]

        if target_node:
            new_lid = f"L{len(loads) + 1}"
            operations.append({
                "op": "add_load",
                "id": new_lid,
                "node": target_node,
                "fx": 0.0,
                "fy": -abs(mag),
            })
            explanation = f"Applied a {mag} {base_model.get('metadata', {}).get('units', {}).get('force', 'kN')} downward load at joint {target_node}."
            return operations, explanation, []

    # 5. Change support to roller / pin
    change_support_match = re.search(r"change\s+(?:the\s+)?(right|left)?\s*support\s*(?:at\s+([a-zA-Z0-9_-]+))?\s*to\s+(?:a\s+)?(roller|pin)", msg_lower)
    if change_support_match:
        side = change_support_match.group(1)
        node_spec = change_support_match.group(2)
        new_type = change_support_match.group(3)
        target_supp = None
        if node_spec:
            target_supp = next((s for s in supports if s.get("node", "").lower() == node_spec.lower()), None)
        elif side == "right" and supports:
            # support with highest node x
            supp_nodes = {s["id"]: next((n.get("x", 0) for n in nodes if n.get("id") == s.get("node")), 0) for s in supports}
            target_id = max(supp_nodes, key=supp_nodes.get)
            target_supp = next((s for s in supports if s["id"] == target_id), None)
        elif side == "left" and supports:
            supp_nodes = {s["id"]: next((n.get("x", 0) for n in nodes if n.get("id") == s.get("node")), 0) for s in supports}
            target_id = min(supp_nodes, key=supp_nodes.get)
            target_supp = next((s for s in supports if s["id"] == target_id), None)
        elif supports:
            target_supp = supports[0]

        if target_supp:
            operations.append({
                "op": "update_support",
                "id": target_supp["id"],
                "type": new_type,
                "direction": "vertical" if new_type == "roller" else None,
            })
            explanation = f"Changed support {target_supp['id']} at joint {target_supp.get('node')} to a {new_type} support."
            return operations, explanation, []

    # 6. Make bottom chord horizontal
    if "make the bottom chord horizontal" in msg_lower or "bottom chord horizontal" in msg_lower:
        if nodes:
            min_y = min(n.get("y", 0.0) for n in nodes)
            # Find nodes along the bottom line (y close to min_y)
            bottom_nodes = [n for n in nodes if abs(n.get("y", 0.0) - min_y) < 1.0]
            for bn in bottom_nodes:
                if bn.get("y") != min_y:
                    operations.append({
                        "op": "update_joint",
                        "id": bn["id"],
                        "y": min_y,
                    })
            explanation = f"Aligned bottom chord joints ({', '.join(n['id'] for n in bottom_nodes)}) horizontally at y = {min_y}."
            return operations, explanation, []

    # 7. Add another panel to the right
    if "add another panel to the right" in msg_lower or "add panel to the right" in msg_lower:
        if nodes and len(nodes) >= 3:
            max_x = max(n.get("x", 0.0) for n in nodes)
            # Find rightmost nodes
            right_nodes = sorted([n for n in nodes if n.get("x", 0.0) >= max_x - 1e-4], key=lambda n: n.get("y", 0.0))
            # Average bay width
            xs = sorted({n.get("x", 0.0) for n in nodes})
            bay_w = xs[-1] - xs[-2] if len(xs) >= 2 else 2.5
            new_x = max_x + bay_w

            new_j_bottom = f"J{len(nodes) + 1}"
            operations.append({"op": "add_joint", "id": new_j_bottom, "x": new_x, "y": right_nodes[0].get("y", 0.0)})
            if len(right_nodes) > 1:
                new_j_top = f"J{len(nodes) + 2}"
                operations.append({"op": "add_joint", "id": new_j_top, "x": new_x, "y": right_nodes[1].get("y", 0.0)})
                # Connect bottom chord
                operations.append({"op": "add_member", "id": f"M{len(members) + 1}", "node_i": right_nodes[0]["id"], "node_j": new_j_bottom})
                # Connect top chord
                operations.append({"op": "add_member", "id": f"M{len(members) + 2}", "node_i": right_nodes[1]["id"], "node_j": new_j_top})
                # Connect vertical
                operations.append({"op": "add_member", "id": f"M{len(members) + 3}", "node_i": new_j_bottom, "node_j": new_j_top})
                # Connect diagonal
                operations.append({"op": "add_member", "id": f"M{len(members) + 4}", "node_i": right_nodes[0]["id"], "node_j": new_j_top})
            else:
                operations.append({"op": "add_member", "id": f"M{len(members) + 1}", "node_i": right_nodes[0]["id"], "node_j": new_j_bottom})

            explanation = f"Extended truss geometry with an additional {bay_w} {base_model.get('metadata', {}).get('units', {}).get('length', 'm')} panel to the right."
            return operations, explanation, []

    # If could not parse a specific modification, prompt user for clarification
    explanation = f"Could not determine the exact structural modification for: '{msg}'. Specify affected joints, members, supports, or coordinates."
    clarification_questions.append({
        "question": "Which structural element would you like to modify?",
        "options": [
            "Add a diagonal member between two joints",
            "Move a joint to new coordinates",
            "Add or modify support conditions",
            "Add or adjust point loads",
        ],
        "recommended": "Add a diagonal member between two joints",
    })
    return [], explanation, clarification_questions


def synthesize_truss_explanation(
    model_dict: dict[str, Any],
    message: str,
    diagnostics: dict[str, Any] | None = None,
    solver_results: dict[str, Any] | None = None,
    selected_element: dict[str, Any] | None = None,
) -> str:
    """Generate concise, factual structural mechanics explanations grounded in actual model data."""
    msg_lower = message.strip().lower()
    inner = model_dict.get("model", {})
    nodes = inner.get("nodes", [])
    members = inner.get("members", [])
    supports = inner.get("supports", [])
    loads = inner.get("loads", [])

    j_count = len(nodes)
    m_count = len(members)
    r_count = sum(2 if s.get("type") == "pin" else 1 for s in supports)
    eq_count = 2 * j_count
    unk_count = m_count + r_count

    diag = diagnostics or {}
    results = solver_results or {}
    forces = results.get("member_forces")

    # 1. "What happens if I remove [member]"
    remove_query = re.search(r"(?:what happens|what would happen)?\s*(?:if\s+(?:i|we)\s+remove|remove|removing)\s+(?:member\s+)?([a-zA-Z0-9_-]+)", msg_lower)
    if remove_query:
        target_mid = remove_query.group(1).upper()
        matched_m = next((m for m in members if m.get("id", "").upper() == target_mid), None)
        if matched_m:
            new_m_count = m_count - 1
            new_unk = new_m_count + r_count
            if new_unk < eq_count:
                return (
                    f"Removing member {target_mid} would reduce unknowns to {new_unk} against {eq_count} equilibrium equations "
                    f"(deficit of {eq_count - new_unk}). The structure would lose static determinacy and form an internal mechanism."
                )
            return (
                f"Removing member {target_mid} leaves {new_unk} unknowns vs {eq_count} equations. "
                "The system must be re-analyzed to verify whether the remaining members prevent kinematic mechanisms."
            )

    # 2. "Why is this structure unstable"
    if "why is this structure unstable" in msg_lower or "why unstable" in msg_lower or "is this stable" in msg_lower:
        reasons = []
        if r_count < 3:
            reasons.append(f"Insufficient external constraints: {r_count} reactions provided (at least 3 non-parallel required).")
        if unk_count < eq_count:
            reasons.append(f"Static determinacy deficit: {unk_count} unknowns (m={m_count}, r={r_count}) vs {eq_count} equations (2j={2*j_count}).")
        components = find_connected_components(nodes, members)
        if len(components) > 1:
            reasons.append(f"Disconnected geometry: structure contains {len(components)} separate graph components.")
        if diag.get("category") == "UNDERDETERMINED":
            reasons.append(f"Equilibrium matrix is rank-deficient (rank {diag.get('rank', 'N/A')} < {eq_count}).")

        if reasons:
            return "Structural instability identified:\n• " + "\n• ".join(reasons)
        if unk_count == eq_count and r_count >= 3:
            return f"The structure satisfies static determinacy criteria: m + r = {unk_count} matches 2j = {eq_count} with {r_count} support reactions."

    # 3. "Which members are in compression / tension" or member force query
    if any(k in msg_lower for k in ("compression", "tension", "member force", "carrying more force", "axial force")):
        if not forces:
            return (
                "Verified member forces and axial stress classifications are unavailable because this model has not been solved yet. "
                "Submit the model to the deterministic solver to calculate verified tension and compression forces."
            )
        tension_members = [f"{mid} (+{round(f, 2)} kN)" for mid, f in forces.items() if f > 1e-4]
        compression_members = [f"{mid} ({round(f, 2)} kN)" for mid, f in forces.items() if f < -1e-4]
        zero_members = [mid for mid, f in forces.items() if abs(f) <= 1e-4]

        lines = []
        if tension_members:
            lines.append(f"Tension members: {', '.join(tension_members)}.")
        if compression_members:
            lines.append(f"Compression members: {', '.join(compression_members)}.")
        if zero_members:
            lines.append(f"Zero-force members: {', '.join(zero_members)}.")
        return "Member force distribution:\n" + "\n".join(lines)

    # 4. Support reactions query
    if "support reaction" in msg_lower or "what does this support do" in msg_lower:
        reactions = results.get("support_reactions")
        if not reactions:
            supp_summary = [f"Support {s['id']} ({s['type']}) at joint {s['node']}" for s in supports]
            return (
                f"The structure has {len(supports)} supports: {', '.join(supp_summary)}. "
                "Verified numerical reactions are unavailable because the model has not been solved yet."
            )
        react_lines = []
        for s_id, axes in reactions.items():
            comp_str = ", ".join(f"{axis.upper()} = {round(val, 2)} kN" for axis, val in axes.items())
            react_lines.append(f"Support {s_id}: {comp_str}")
        return "Support reactions:\n• " + "\n• ".join(react_lines)

    # 5. General "Explain this truss"
    supp_types = [f"{s['type']} at {s['node']}" for s in supports]
    supp_desc = f"Supported by {', '.join(supp_types)}" if supp_types else "No supports defined"
    load_desc = f"{len(loads)} applied point load(s)" if loads else "unloaded"

    lines = [
        f"2D planar truss with {j_count} joints and {m_count} pin-connected members.",
        f"Statics equilibrium requires 2j = {eq_count} equations against m + r = {unk_count} unknowns ({r_count} support constraints).",
        f"Boundary conditions: {supp_desc}. External loading: {load_desc}.",
    ]

    if forces:
        t_count = sum(1 for f in forces.values() if f > 1e-4)
        c_count = sum(1 for f in forces.values() if f < -1e-4)
        lines.append(f"Solver analysis complete: {t_count} member(s) in tension, {c_count} in compression.")
    else:
        lines.append("Verified numerical forces and reactions are currently unavailable (model not solved).")

    return " ".join(lines)


def _call_design_provider(
    message: str,
    context: dict[str, Any],
    provider: str,
    client: Any | None,
    api_key: str,
    timeout_seconds: float,
) -> dict[str, Any] | None:
    """Call external AI provider with JSON schema for natural language design."""
    user_prompt = (
        f"User Instruction:\n{message}\n\n"
        f"Truss Context:\n{json.dumps(context, indent=2)}\n\n"
        "Return structured output strictly matching the provided schema."
    )

    if provider == "gemini":
        use_sdk = client is None
        if use_sdk:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(timeout=max(1, int(timeout_seconds * 1000))),
                )
            except ImportError:
                return None

        model_name = os.environ.get("GEMINI_MODEL", DEFAULT_DESIGN_MODEL).strip() or DEFAULT_DESIGN_MODEL
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[user_prompt],
                config={
                    "system_instruction": DESIGN_SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "response_json_schema": DESIGN_RESPONSE_SCHEMA,
                    "temperature": 0.1,
                },
            )
            output_text = getattr(response, "text", None)
            if not output_text:
                return None
            return json.loads(output_text)
        except Exception:
            return None

    elif provider == "meta":
        use_sdk = client is None
        if use_sdk:
            try:
                from openai import OpenAI
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.meta.ai/v1",
                    timeout=timeout_seconds,
                )
            except ImportError:
                return None
        try:
            response = client.chat.completions.create(
                model="muse-spark-1.3",
                messages=[
                    {"role": "system", "content": DESIGN_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = response.choices[0].message.content
            return json.loads(content) if content else None
        except Exception:
            return None

    return None


def process_design_request(
    message: str,
    context: dict[str, Any] | None = None,
    intent: str | None = None,
    provider: str | None = None,
    client: Any | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Orchestrate conversational natural-language truss design (CREATE, MODIFY, EXPLAIN)."""
    ctx = context or {}
    base_model = ctx.get("model")
    has_model = isinstance(base_model, dict) and bool(base_model.get("model", {}).get("nodes"))
    model_revision = ctx.get("model_revision", 1)
    analysis_id = ctx.get("analysis_id")

    resolved_intent = detect_intent(intent, message, has_model)
    proposal_id = uuid4().hex

    # Check external provider configuration
    load_dotenv(dotenv_path=BACKEND_ENV_PATH, override=False)
    raw_provider = (provider or os.environ.get("INTERPRETATION_PROVIDER", "gemini")).strip().lower()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip() if raw_provider == "gemini" else os.environ.get("MODEL_API_KEY", "").strip()

    ai_output: dict[str, Any] | None = None
    if client is not None or api_key:
        ai_output = _call_design_provider(
            message=message,
            context=ctx,
            provider=raw_provider,
            client=client,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )

    # Heuristic deterministic engine fallback
    if resolved_intent == "create":
        units = ctx.get("units")
        if ai_output and ai_output.get("proposed_model"):
            proposed_model = ai_output["proposed_model"]
            explanation = ai_output.get("explanation", "Proposed new truss model.")
            clarification_questions = ai_output.get("clarification_questions", [])
            status = ai_output.get("status", "proposed")
        else:
            proposed_model, explanation, clarification_questions, status = synthesize_truss_model(message, units)

        # Deterministic geometry validation
        val_result = validate_truss_request(proposed_model)
        validation_data = {
            "is_valid": val_result.is_valid,
            "issues": [asdict(i) for i in val_result.errors],
        }

        # Diagnostics evaluation
        preview_data = evaluate_truss_preview(proposed_model)
        solvability = preview_data.get("solvability", {})
        predicted_diagnostics = {
            "status": solvability.get("status", "unknown"),
            "category": solvability.get("category"),
            "equation_count": solvability.get("equation_count"),
            "unknown_count": solvability.get("unknown_count"),
            "rank": solvability.get("rank"),
        }

        affected_elements = {
            "nodes": [n["id"] for n in proposed_model.get("model", {}).get("nodes", []) if "id" in n],
            "members": [m["id"] for m in proposed_model.get("model", {}).get("members", []) if "id" in m],
            "supports": [s["id"] for s in proposed_model.get("model", {}).get("supports", []) if "id" in s],
            "loads": [l["id"] for l in proposed_model.get("model", {}).get("loads", []) if "id" in l],
        }

        return {
            "intent": "create",
            "status": status,
            "proposal_id": proposal_id,
            "base_revision": model_revision,
            "explanation": explanation,
            "proposed_model": proposed_model,
            "operations": [],
            "affected_elements": affected_elements,
            "clarification_questions": clarification_questions,
            "validation": validation_data,
            "predicted_diagnostics": predicted_diagnostics,
            "warnings": preview_data.get("warnings", []),
        }

    elif resolved_intent == "modify":
        if not has_model or not isinstance(base_model, dict):
            # Fall back to create if user asks for modification but no model is loaded
            return process_design_request(message, ctx, intent="create", provider=provider, client=client, timeout_seconds=timeout_seconds)

        if ai_output and ai_output.get("operations"):
            operations = ai_output["operations"]
            explanation = ai_output.get("explanation", "Proposed geometry modifications.")
            clarification_questions = ai_output.get("clarification_questions", [])
        else:
            operations, explanation, clarification_questions = synthesize_truss_modification(
                base_model, message, ctx.get("selected_element")
            )

        if not operations and clarification_questions:
            return {
                "intent": "modify",
                "status": "needs_clarification",
                "proposal_id": proposal_id,
                "base_revision": model_revision,
                "explanation": explanation,
                "proposed_model": base_model,
                "operations": [],
                "affected_elements": {"nodes": [], "members": [], "supports": [], "loads": []},
                "clarification_questions": clarification_questions,
                "validation": {"is_valid": True, "issues": []},
                "predicted_diagnostics": {},
                "warnings": [],
            }

        # Apply operations safely to a copy of base_model
        modified_model, affected_elements, op_errors = apply_operations_to_model(base_model, operations)

        # Deterministic geometry validation
        val_result = validate_truss_request(modified_model)
        val_issues = [asdict(i) for i in val_result.errors]
        for err in op_errors:
            val_issues.append({"code": "INVALID_OPERATION", "path": "/operations", "message": err})

        validation_data = {
            "is_valid": val_result.is_valid and not op_errors,
            "issues": val_issues,
        }

        preview_data = evaluate_truss_preview(modified_model) if val_result.is_valid else {}
        solvability = preview_data.get("solvability", {})
        predicted_diagnostics = {
            "status": solvability.get("status", "invalid_geometry"),
            "category": solvability.get("category"),
            "equation_count": solvability.get("equation_count"),
            "unknown_count": solvability.get("unknown_count"),
            "rank": solvability.get("rank"),
        }

        return {
            "intent": "modify",
            "status": "proposed" if validation_data["is_valid"] else "rejected",
            "proposal_id": proposal_id,
            "base_revision": model_revision,
            "explanation": explanation,
            "proposed_model": modified_model,
            "operations": operations,
            "affected_elements": affected_elements,
            "clarification_questions": clarification_questions,
            "validation": validation_data,
            "predicted_diagnostics": predicted_diagnostics,
            "warnings": preview_data.get("warnings", []),
        }

    else:  # explain
        if ai_output and ai_output.get("explanation"):
            explanation = ai_output["explanation"]
        else:
            explanation = synthesize_truss_explanation(
                base_model or {},
                message,
                ctx.get("diagnostics"),
                ctx.get("solver_results"),
                ctx.get("selected_element"),
            )

        return {
            "intent": "explain",
            "status": "explained",
            "proposal_id": proposal_id,
            "base_revision": model_revision,
            "explanation": explanation,
            "proposed_model": None,
            "operations": [],
            "affected_elements": {"nodes": [], "members": [], "supports": [], "loads": []},
            "clarification_questions": [],
            "validation": {"is_valid": True, "issues": []},
            "predicted_diagnostics": ctx.get("diagnostics") or {},
            "warnings": [],
        }
