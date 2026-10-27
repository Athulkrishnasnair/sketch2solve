"""Pure validation and normalization for version 1.0 truss request objects.

Member endpoints are considered coincident when their Euclidean distance is
at most ``max(ZERO_LENGTH_ABS_TOL, ZERO_LENGTH_REL_TOL * model_scale)``.
``model_scale`` is the diagonal of the axis-aligned bounding box of all valid
nodes. This makes the relative term independent of the coordinate origin.
The absolute floor is ``1e-12`` in the model's declared length unit; no unit
conversion is performed. The tolerance is a practical floating-point guard,
not a statement about fabrication precision. At extreme coordinate magnitudes,
floating-point representation can itself lose small geometric differences.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from app.models.truss import (
    Load,
    Member,
    Node,
    Support,
    TrussModel,
    Units,
    ValidationIssue,
    ValidationResult,
)


SUPPORTED_LENGTH_UNITS = frozenset({"m", "mm", "ft"})
SUPPORTED_FORCE_UNITS = frozenset({"N", "kN", "lbf"})
ZERO_LENGTH_REL_TOL = 1e-12
ZERO_LENGTH_ABS_TOL = 1e-12


def validate_truss_request(data: Any) -> ValidationResult:
    """Validate a Python object parsed from the truss request JSON.

    Returns a normalized ``TrussModel`` when valid, or field-addressed issues
    when expected input errors are present. Unexpected implementation errors
    are allowed to propagate.
    """
    errors: list[ValidationIssue] = []

    if not isinstance(data, dict):
        return _failure("INVALID_TYPE", "", "Request body must be a JSON object.")

    _check_keys(data, {"schema_version", "metadata", "model"}, "", errors)
    version = data.get("schema_version")
    if "schema_version" not in data:
        _issue(errors, "MISSING_FIELD", "/schema_version", "Field is required.")
    elif not isinstance(version, str):
        _issue(errors, "INVALID_TYPE", "/schema_version", "Must be a string.")
    elif version != "1.0":
        _issue(errors, "UNSUPPORTED_SCHEMA_VERSION", "/schema_version", "Supported schema version is '1.0'.")

    metadata = data.get("metadata")
    name: str | None = None
    source: str | None = None
    units: Units | None = None
    if "metadata" not in data:
        _issue(errors, "MISSING_FIELD", "/metadata", "Field is required.")
    elif not isinstance(metadata, dict):
        _issue(errors, "INVALID_TYPE", "/metadata", "Must be an object.")
    else:
        _check_keys(metadata, {"name", "source", "units"}, "/metadata", errors)
        name = _optional_nonempty_string(metadata, "name", "/metadata", errors)
        source = _optional_nonempty_string(metadata, "source", "/metadata", errors)
        units_value = metadata.get("units")
        if "units" not in metadata:
            _issue(errors, "MISSING_FIELD", "/metadata/units", "Field is required.")
        elif not isinstance(units_value, dict):
            _issue(errors, "INVALID_TYPE", "/metadata/units", "Must be an object.")
        else:
            _check_keys(units_value, {"length", "force"}, "/metadata/units", errors)
            length = _enum_value(units_value, "length", "/metadata/units", SUPPORTED_LENGTH_UNITS, errors)
            force = _enum_value(units_value, "force", "/metadata/units", SUPPORTED_FORCE_UNITS, errors)
            if length is not None and force is not None:
                units = Units(length=length, force=force)  # type: ignore[arg-type]

    model_value = data.get("model")
    if "model" not in data:
        _issue(errors, "MISSING_FIELD", "/model", "Field is required.")
        return ValidationResult(None, tuple(errors))
    if not isinstance(model_value, dict):
        _issue(errors, "INVALID_TYPE", "/model", "Must be an object.")
        return ValidationResult(None, tuple(errors))

    collections = {"nodes", "members", "supports", "loads"}
    _check_keys(model_value, collections, "/model", errors)
    raw_collections: dict[str, list[Any]] = {}
    for collection in ("nodes", "members", "supports", "loads"):
        value = model_value.get(collection)
        if collection not in model_value:
            _issue(errors, "MISSING_FIELD", f"/model/{collection}", "Field is required.")
            raw_collections[collection] = []
        elif not isinstance(value, list):
            _issue(errors, "INVALID_TYPE", f"/model/{collection}", "Must be an array.")
            raw_collections[collection] = []
        else:
            raw_collections[collection] = value

    raw_nodes = raw_collections["nodes"]
    raw_members = raw_collections["members"]
    raw_supports = raw_collections["supports"]
    raw_loads = raw_collections["loads"]
    if not raw_nodes:
        _issue(errors, "EMPTY_MODEL", "/model/nodes", "A truss model must contain at least one node.")

    nodes = _parse_nodes(raw_nodes, errors)
    node_by_id = {node.id: node for node in nodes}
    member_tolerance = _zero_length_tolerance(nodes)
    members = _parse_members(raw_members, node_by_id, member_tolerance, errors)
    supports = _parse_supports(raw_supports, node_by_id, errors)
    loads = _parse_loads(raw_loads, node_by_id, errors)

    if errors or units is None or not isinstance(version, str):
        return ValidationResult(None, tuple(errors))

    return ValidationResult(
        TrussModel(
            schema_version=version,
            name=name,
            source=source,
            units=units,
            nodes=tuple(nodes),
            members=tuple(members),
            supports=tuple(supports),
            loads=tuple(loads),
        ),
        (),
    )


def _parse_nodes(values: list[Any], errors: list[ValidationIssue]) -> list[Node]:
    result: list[Node] = []
    seen: set[str] = set()
    keys = {"id", "x", "y"}
    for index, value in enumerate(values):
        path = f"/model/nodes/{index}"
        if not isinstance(value, dict):
            _issue(errors, "INVALID_TYPE", path, "Node must be an object.")
            continue
        _check_keys(value, keys, path, errors)
        node_id = _identifier(value, "id", path, errors)
        x = _number(value, "x", path, errors)
        y = _number(value, "y", path, errors)
        if node_id is not None:
            if node_id in seen:
                _issue(errors, "DUPLICATE_NODE_ID", f"{path}/id", f"Node ID '{node_id}' is duplicated.")
            else:
                seen.add(node_id)
        if node_id is not None and x is not None and y is not None and node_id not in {n.id for n in result}:
            result.append(Node(node_id, x, y))
    return result


def _parse_members(
    values: list[Any],
    nodes: dict[str, Node],
    zero_length_tolerance: float,
    errors: list[ValidationIssue],
) -> list[Member]:
    result: list[Member] = []
    seen: set[str] = set()
    keys = {"id", "node_i", "node_j"}
    for index, value in enumerate(values):
        path = f"/model/members/{index}"
        if not isinstance(value, dict):
            _issue(errors, "INVALID_TYPE", path, "Member must be an object.")
            continue
        _check_keys(value, keys, path, errors)
        member_id = _identifier(value, "id", path, errors)
        node_i = _identifier(value, "node_i", path, errors)
        node_j = _identifier(value, "node_j", path, errors)
        if member_id is not None:
            if member_id in seen:
                _issue(errors, "DUPLICATE_MEMBER_ID", f"{path}/id", f"Member ID '{member_id}' is duplicated.")
            else:
                seen.add(member_id)
        valid_i = node_i in nodes if node_i is not None else False
        valid_j = node_j in nodes if node_j is not None else False
        if node_i is not None and not valid_i:
            _issue(errors, "UNKNOWN_NODE_REFERENCE", f"{path}/node_i", f"Member references unknown node '{node_i}'.")
        if node_j is not None and not valid_j:
            _issue(errors, "UNKNOWN_NODE_REFERENCE", f"{path}/node_j", f"Member references unknown node '{node_j}'.")
        if node_i is not None and node_j is not None and node_i == node_j:
            _issue(errors, "SELF_CONNECTED_MEMBER", f"{path}/node_j", "Member endpoints must reference distinct nodes.")
        if valid_i and valid_j and node_i != node_j:
            left, right = nodes[node_i], nodes[node_j]  # type: ignore[index]
            if math.hypot(right.x - left.x, right.y - left.y) <= zero_length_tolerance:
                _issue(errors, "ZERO_LENGTH_MEMBER", path, "Member endpoints have coincident coordinates within the configured tolerance.")
        if member_id is not None and node_i is not None and node_j is not None and member_id not in {m.id for m in result}:
            result.append(Member(member_id, node_i, node_j))
    return result


def _zero_length_tolerance(nodes: list[Node]) -> float:
    """Return an origin-independent tolerance using the complete node bounds."""
    if not nodes:
        return ZERO_LENGTH_ABS_TOL
    min_x = min(node.x for node in nodes)
    max_x = max(node.x for node in nodes)
    min_y = min(node.y for node in nodes)
    max_y = max(node.y for node in nodes)
    model_scale = math.hypot(max_x - min_x, max_y - min_y)
    return max(ZERO_LENGTH_ABS_TOL, ZERO_LENGTH_REL_TOL * model_scale)


def _parse_supports(values: list[Any], nodes: dict[str, Node], errors: list[ValidationIssue]) -> list[Support]:
    result: list[Support] = []
    seen_ids: set[str] = set()
    seen_nodes: set[str] = set()
    for index, value in enumerate(values):
        path = f"/model/supports/{index}"
        if not isinstance(value, dict):
            _issue(errors, "INVALID_TYPE", path, "Support must be an object.")
            continue
        if value.get("type") == "roller":
            keys = {"id", "node", "type", "direction"}
        else:
            keys = {"id", "node", "type"}
        _check_keys(value, keys, path, errors)
        support_id = _identifier(value, "id", path, errors)
        node_id = _identifier(value, "node", path, errors)
        support_type = value.get("type")
        if "type" not in value:
            _issue(errors, "MISSING_FIELD", f"{path}/type", "Field is required.")
        elif support_type not in ("pin", "roller"):
            _issue(errors, "INVALID_SUPPORT_TYPE", f"{path}/type", "Support type must be 'pin' or 'roller'.")
        direction: str | None = None
        if support_type == "roller":
            direction = _enum_value(value, "direction", path, frozenset({"horizontal", "vertical"}), errors)
        elif support_type == "pin" and "direction" in value:
            _issue(errors, "UNEXPECTED_FIELD", f"{path}/direction", "Pin supports must not specify a direction.")
        if support_id is not None:
            if support_id in seen_ids:
                _issue(errors, "DUPLICATE_SUPPORT_ID", f"{path}/id", f"Support ID '{support_id}' is duplicated.")
            else:
                seen_ids.add(support_id)
        if node_id is not None and node_id not in nodes:
            _issue(errors, "UNKNOWN_NODE_REFERENCE", f"{path}/node", f"Support references unknown node '{node_id}'.")
        if node_id is not None:
            if node_id in seen_nodes:
                _issue(errors, "DUPLICATE_SUPPORT_NODE", f"{path}/node", f"Node '{node_id}' has more than one support record.")
            else:
                seen_nodes.add(node_id)
        if support_id is not None and node_id is not None and support_type in ("pin", "roller") and (support_type == "pin" or direction in ("horizontal", "vertical")):
            if support_id not in {s.id for s in result}:
                result.append(Support(support_id, node_id, support_type, direction))  # type: ignore[arg-type]
    return result


def _parse_loads(values: list[Any], nodes: dict[str, Node], errors: list[ValidationIssue]) -> list[Load]:
    result: list[Load] = []
    seen_ids: set[str] = set()
    seen_nodes: set[str] = set()
    keys = {"id", "node", "fx", "fy"}
    for index, value in enumerate(values):
        path = f"/model/loads/{index}"
        if not isinstance(value, dict):
            _issue(errors, "INVALID_TYPE", path, "Load must be an object.")
            continue
        _check_keys(value, keys, path, errors)
        load_id = _identifier(value, "id", path, errors)
        node_id = _identifier(value, "node", path, errors)
        fx = _number(value, "fx", path, errors)
        fy = _number(value, "fy", path, errors)
        if load_id is not None:
            if load_id in seen_ids:
                _issue(errors, "DUPLICATE_LOAD_ID", f"{path}/id", f"Load ID '{load_id}' is duplicated.")
            else:
                seen_ids.add(load_id)
        if node_id is not None and node_id not in nodes:
            _issue(errors, "UNKNOWN_NODE_REFERENCE", f"{path}/node", f"Load references unknown node '{node_id}'.")
        if node_id is not None:
            if node_id in seen_nodes:
                _issue(errors, "DUPLICATE_LOAD_NODE", f"{path}/node", f"Node '{node_id}' has more than one load record.")
            else:
                seen_nodes.add(node_id)
        if load_id is not None and node_id is not None and fx is not None and fy is not None and load_id not in {load.id for load in result}:
            result.append(Load(load_id, node_id, fx, fy))
    return result


def _identifier(value: dict[str, Any], key: str, path: str, errors: list[ValidationIssue]) -> str | None:
    field_path = f"{path}/{key}"
    if key not in value:
        _issue(errors, "MISSING_FIELD", field_path, "Field is required.")
        return None
    item = value[key]
    if not isinstance(item, str):
        _issue(errors, "INVALID_TYPE", field_path, "Must be a string.")
        return None
    if not item or not item.strip():
        _issue(errors, "EMPTY_ID", field_path, "Must be a nonempty string.")
        return None
    if item != item.strip():
        _issue(errors, "INVALID_ID", field_path, "Must not have leading or trailing whitespace.")
        return None
    return item


def _number(value: dict[str, Any], key: str, path: str, errors: list[ValidationIssue]) -> float | None:
    field_path = f"{path}/{key}"
    if key not in value:
        _issue(errors, "MISSING_FIELD", field_path, "Field is required.")
        return None
    item = value[key]
    if isinstance(item, bool) or not isinstance(item, (int, float)):
        _issue(errors, "INVALID_TYPE", field_path, "Must be a finite JSON number; booleans are not accepted.")
        return None
    try:
        number = float(item)
    except (OverflowError, ValueError):
        _issue(errors, "NON_FINITE_NUMBER", field_path, "Must be finite.")
        return None
    if not math.isfinite(number):
        _issue(errors, "NON_FINITE_NUMBER", field_path, "Must be finite.")
        return None
    return number


def _optional_nonempty_string(value: dict[str, Any], key: str, path: str, errors: list[ValidationIssue]) -> str | None:
    if key not in value:
        return None
    item = value[key]
    field_path = f"{path}/{key}"
    if not isinstance(item, str):
        _issue(errors, "INVALID_TYPE", field_path, "Must be a string.")
        return None
    if not item.strip():
        _issue(errors, "EMPTY_STRING", field_path, "Must be a nonempty string.")
        return None
    if item != item.strip():
        _issue(errors, "INVALID_STRING", field_path, "Must not have leading or trailing whitespace.")
        return None
    return item


def _enum_value(value: dict[str, Any], key: str, path: str, allowed: frozenset[str], errors: list[ValidationIssue]) -> str | None:
    field_path = f"{path}/{key}"
    if key not in value:
        _issue(errors, "MISSING_FIELD", field_path, "Field is required.")
        return None
    item = value[key]
    if not isinstance(item, str):
        _issue(errors, "INVALID_TYPE", field_path, "Must be a string.")
        return None
    if item not in allowed:
        choices = ", ".join(sorted(allowed))
        _issue(errors, "INVALID_VALUE", field_path, f"Must be one of: {choices}.")
        return None
    return item


def _check_keys(value: Mapping[str, Any], allowed: set[str], path: str, errors: list[ValidationIssue]) -> None:
    for key in value:
        if key not in allowed:
            _issue(errors, "UNKNOWN_FIELD", f"{path}/{_escape_pointer(str(key))}", f"Unknown field '{key}'.")


def _escape_pointer(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _issue(errors: list[ValidationIssue], code: str, path: str, message: str) -> None:
    errors.append(ValidationIssue(code, path, message))


def _failure(code: str, path: str, message: str) -> ValidationResult:
    return ValidationResult(None, (ValidationIssue(code, path, message),))
