"""Isolated Muse Spark adapter for proposing visual truss interpretations.

All coordinates returned by this module are image pixels. They remain
untrusted visual proposals and are never passed to the deterministic solver.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
import json
import math
import os
from pathlib import Path
from typing import Any

import cv2
from dotenv import load_dotenv
import numpy as np
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, OpenAIError
from app.services.perception import PerceptionInputError, inspect_image_header


BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=BACKEND_ENV_PATH, override=False)
META_BASE_URL = "https://api.meta.ai/v1"
MUSE_MODEL = "muse-spark-1.3"
DEFAULT_TIMEOUT_SECONDS = 60.0
MAX_INLINE_IMAGE_BYTES = 50_000_000

_SYSTEM_INSTRUCTIONS = """You interpret truss sketches as a visual proposal only. You do not calculate forces or perform engineering analysis. Do not invent hidden geometry, dimensions, loads, force magnitudes, units, or support types. Omit unseen items. Return uncertain items with uncertainty flags and explain ambiguity or missing information. For every location, use integer coordinates on the normalized 0–1000 image grid: (0,0) is the original image top-left, x increases right, y increases down. The application will convert those coordinates to pixels using the exact original image dimensions. A visual crossing is not automatically a connected joint; mark uncertain connections explicitly."""

_USER_PROMPT = """Interpret the visible truss-like drawing in the attached image. Return:
1. Candidate joints at visible connection points.
2. Candidate members connecting candidate joint IDs; flag connections uncertain when a crossing or overlap is ambiguous.
3. Visible support locations with a possible type only when the symbol supports it; otherwise use unknown and flag uncertainty.
4. Explicitly visible loads and their directions. Give a magnitude and unit only when both are legible; otherwise use null for both.
5. A concise list of uncertain interpretations and missing information.

Do not infer dimensions from scale, hidden geometry, engineering constraints, or numerical forces. These are candidates for human review, not confirmed structural entities."""

_INTERPRETATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "joints": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "x_1000": {"type": "integer"},
                    "y_1000": {"type": "integer"},
                },
                "required": ["id", "x_1000", "y_1000"],
                "additionalProperties": False,
            },
        },
        "members": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "joint_i": {"type": "string"},
                    "joint_j": {"type": "string"},
                    "connection_uncertain": {"type": "boolean"},
                    "notes": {"type": "string"},
                },
                "required": ["id", "joint_i", "joint_j", "connection_uncertain", "notes"],
                "additionalProperties": False,
            },
        },
        "supports": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "x_1000": {"type": "integer"},
                    "y_1000": {"type": "integer"},
                    "possible_type": {"type": "string", "enum": ["pin", "roller", "other", "unknown"]},
                    "uncertain": {"type": "boolean"},
                    "notes": {"type": "string"},
                },
                "required": ["id", "x_1000", "y_1000", "possible_type", "uncertain", "notes"],
                "additionalProperties": False,
            },
        },
        "loads": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "x_1000": {"type": "integer"},
                    "y_1000": {"type": "integer"},
                    "direction": {"type": "string"},
                    "magnitude": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "unit": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "uncertain": {"type": "boolean"},
                    "notes": {"type": "string"},
                },
                "required": ["id", "x_1000", "y_1000", "direction", "magnitude", "unit", "uncertain", "notes"],
                "additionalProperties": False,
            },
        },
        "ambiguities": {"type": "array", "items": {"type": "string"}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["joints", "members", "supports", "loads", "ambiguities", "missing_information"],
    "additionalProperties": False,
}


class MuseInterpretationError(RuntimeError):
    """Base class for safe, client-facing adapter failures."""

    code = "MUSE_INTERPRETATION_FAILED"


class MissingModelAPIKeyError(MuseInterpretationError):
    code = "MISSING_MODEL_API_KEY"

    def __init__(self) -> None:
        super().__init__("MODEL_API_KEY is not configured.")


class InvalidSketchImageError(MuseInterpretationError):
    code = "INVALID_SKETCH_IMAGE"


class MuseTimeoutError(MuseInterpretationError):
    code = "MUSE_TIMEOUT"

    def __init__(self) -> None:
        super().__init__("Muse Model API request timed out.")


class MuseNetworkError(MuseInterpretationError):
    code = "MUSE_NETWORK_ERROR"

    def __init__(self) -> None:
        super().__init__("Muse Model API could not be reached.")


class MuseAPIError(MuseInterpretationError):
    code = "MUSE_API_ERROR"

    def __init__(self, status_code: int | None = None) -> None:
        self.status_code = status_code
        self.code = {
            401: "MUSE_AUTHENTICATION_FAILED",
            403: "MUSE_AUTHENTICATION_FAILED",
            404: "MUSE_INVALID_MODEL",
            429: "MUSE_RATE_LIMITED",
        }.get(status_code, self.code)
        message = "Muse Model API request failed."
        if self.code == "MUSE_AUTHENTICATION_FAILED":
            message = "Muse authentication failed. Check the server-side credential and account access."
        elif self.code == "MUSE_INVALID_MODEL":
            message = "Muse rejected the configured model. Check the model setting."
        elif self.code == "MUSE_RATE_LIMITED":
            message = "Muse rate limit or quota was reached. Try again later."
        super().__init__(message)


class InvalidMuseResponseError(MuseInterpretationError):
    code = "INVALID_MUSE_RESPONSE"


@dataclass(frozen=True)
class CandidateJointProposal:
    id: str
    x: int
    y: int


@dataclass(frozen=True)
class CandidateMemberProposal:
    id: str
    joint_i: str
    joint_j: str
    connection_uncertain: bool
    notes: str


@dataclass(frozen=True)
class CandidateSupportProposal:
    id: str
    x: int
    y: int
    possible_type: str
    uncertain: bool
    notes: str


@dataclass(frozen=True)
class CandidateLoadProposal:
    id: str
    x: int
    y: int
    direction: str
    magnitude: float | None
    unit: str | None
    uncertain: bool
    notes: str


@dataclass(frozen=True)
class TrussInterpretationProposal:
    image_width: int
    image_height: int
    coordinate_space: str
    coordinate_convention: str
    joints: tuple[CandidateJointProposal, ...]
    members: tuple[CandidateMemberProposal, ...]
    supports: tuple[CandidateSupportProposal, ...]
    loads: tuple[CandidateLoadProposal, ...]
    ambiguities: tuple[str, ...]
    missing_information: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_width": self.image_width,
            "image_height": self.image_height,
            "coordinate_space": self.coordinate_space,
            "coordinate_convention": self.coordinate_convention,
            "joints": [asdict(item) for item in self.joints],
            "members": [asdict(item) for item in self.members],
            "supports": [asdict(item) for item in self.supports],
            "loads": [asdict(item) for item in self.loads],
            "ambiguities": list(self.ambiguities),
            "missing_information": list(self.missing_information),
            "proposal_only": True,
        }


def interpret_truss_sketch(
    image_bytes: bytes,
    *,
    mime_type: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    client: Any | None = None,
) -> TrussInterpretationProposal:
    """Ask Muse Spark for an untrusted visual proposal from an encoded image.

    Local JPEG, PNG, and WebP bytes are sent inline as a base64 data URL; no
    public upload URL is needed. Model coordinates use Meta's documented
    normalized 0–1000 grid and are converted to the original pixel dimensions.
    Pass a client implementing ``responses.create`` to test without network I/O.
    """
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a positive finite number.")
    if not isinstance(image_bytes, (bytes, bytearray, memoryview)) or not image_bytes:
        raise InvalidSketchImageError("Image data must be non-empty encoded bytes.")
    image_bytes = bytes(image_bytes)
    width, height, detected_mime = _inspect_image(image_bytes, mime_type)
    api_key = os.environ.get("MODEL_API_KEY", "").strip()
    base_url = os.environ.get("MODEL_BASE_URL", META_BASE_URL).strip() or META_BASE_URL
    model_name = os.environ.get("MODEL_NAME", MUSE_MODEL).strip() or MUSE_MODEL

    if client is None:
        if not api_key:
            raise MissingModelAPIKeyError()
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=0,
        )

    data_url = f"data:{detected_mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    request_input = [{
        "type": "message",
        "role": "user",
        "content": [
            {"type": "input_text", "text": _USER_PROMPT},
            {"type": "input_image", "image_url": data_url},
        ],
    }]
    try:
        if hasattr(client, "responses") and hasattr(client.responses, "create"):
            response = client.responses.create(
                model=model_name,
                instructions=_SYSTEM_INSTRUCTIONS,
                input=request_input,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "truss_visual_interpretation",
                        "strict": True,
                        "schema": _INTERPRETATION_SCHEMA,
                    },
                },
                timeout=timeout_seconds,
                store=False,
            )
            output_text = getattr(response, "output_text", None)
        else:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": _SYSTEM_INSTRUCTIONS},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _USER_PROMPT},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0,
                timeout=timeout_seconds,
            )
            output_text = response.choices[0].message.content if getattr(response, "choices", None) else None
    except APITimeoutError as error:
        raise MuseTimeoutError() from error
    except APIConnectionError as error:
        raise MuseNetworkError() from error
    except APIStatusError as error:
        raise MuseAPIError(error.status_code) from error
    except OpenAIError as error:
        raise MuseAPIError() from error
    if not isinstance(output_text, str) or not output_text.strip():
        raise InvalidMuseResponseError("Muse Model API returned no structured text.")
    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError as error:
        raise InvalidMuseResponseError("Muse Model API returned malformed JSON.") from error
    return _parse_proposal(payload, width=width, height=height)


def _inspect_image(image_bytes: bytes, mime_type: str | None) -> tuple[int, int, str]:
    if not isinstance(image_bytes, (bytes, bytearray, memoryview)) or not image_bytes:
        raise InvalidSketchImageError("Image data must be non-empty encoded bytes.")
    image_bytes = bytes(image_bytes)
    if len(image_bytes) > MAX_INLINE_IMAGE_BYTES:
        raise InvalidSketchImageError("Image exceeds Meta Model API's 50 MB inline image limit.")
    try:
        header_width, header_height, detected_mime = inspect_image_header(
            image_bytes,
            max_bytes=MAX_INLINE_IMAGE_BYTES,
        )
    except PerceptionInputError as error:
        raise InvalidSketchImageError(str(error)) from error
    if mime_type is not None:
        if not isinstance(mime_type, str):
            raise InvalidSketchImageError("Image MIME type must be a string.")
        # Treat a declared MIME as advisory only. The encoded format is checked
        # below and is the value used in provider requests.
    try:
        decoded = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    except cv2.error as error:
        raise InvalidSketchImageError("Image data could not be decoded.") from error
    if decoded is None or decoded.size == 0:
        raise InvalidSketchImageError("Image data could not be decoded.")
    height, width = decoded.shape[:2]
    if (width, height) != (header_width, header_height):
        raise InvalidSketchImageError("Image header dimensions do not match the decoded image.")
    return width, height, detected_mime


def _parse_proposal(payload: Any, *, width: int, height: int) -> TrussInterpretationProposal:
    required = {"joints", "members", "supports", "loads", "ambiguities", "missing_information"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise InvalidMuseResponseError("Structured interpretation has an unexpected top-level shape.")

    joints_raw = _list(payload, "joints")
    joint_ids: set[str] = set()
    joints = []
    for item in joints_raw:
        record = _object(item, {"id", "x_1000", "y_1000"})
        point_id = _identifier(record["id"], "joint")
        if point_id in joint_ids:
            raise InvalidMuseResponseError("Joint identifiers must be unique.")
        joint_ids.add(point_id)
        x = _to_pixel(record["x_1000"], width, "joint x")
        y = _to_pixel(record["y_1000"], height, "joint y")
        joints.append(CandidateJointProposal(point_id, x, y))

    members_raw = _list(payload, "members")
    member_ids: set[str] = set()
    members = []
    for item in members_raw:
        record = _object(item, {"id", "joint_i", "joint_j", "connection_uncertain", "notes"})
        member_id = _identifier(record["id"], "member")
        joint_i = _identifier(record["joint_i"], "member endpoint")
        joint_j = _identifier(record["joint_j"], "member endpoint")
        if member_id in member_ids or joint_i not in joint_ids or joint_j not in joint_ids or joint_i == joint_j:
            raise InvalidMuseResponseError("Member IDs and joint references must be unique and valid.")
        member_ids.add(member_id)
        members.append(CandidateMemberProposal(
            member_id,
            joint_i,
            joint_j,
            _boolean(record["connection_uncertain"], "connection_uncertain"),
            _string(record["notes"], "member notes"),
        ))

    supports_raw = _list(payload, "supports")
    support_ids: set[str] = set()
    supports = []
    for item in supports_raw:
        record = _object(item, {"id", "x_1000", "y_1000", "possible_type", "uncertain", "notes"})
        support_id = _identifier(record["id"], "support")
        possible_type = record["possible_type"]
        if support_id in support_ids or not isinstance(possible_type, str) or possible_type not in {"pin", "roller", "other", "unknown"}:
            raise InvalidMuseResponseError("Support IDs or possible types are invalid.")
        support_ids.add(support_id)
        supports.append(CandidateSupportProposal(
            support_id,
            _to_pixel(record["x_1000"], width, "support x"),
            _to_pixel(record["y_1000"], height, "support y"),
            possible_type,
            _boolean(record["uncertain"], "support uncertain"),
            _string(record["notes"], "support notes"),
        ))

    loads_raw = _list(payload, "loads")
    load_ids: set[str] = set()
    loads = []
    for item in loads_raw:
        record = _object(item, {"id", "x_1000", "y_1000", "direction", "magnitude", "unit", "uncertain", "notes"})
        load_id = _identifier(record["id"], "load")
        magnitude = record["magnitude"]
        unit = record["unit"]
        if load_id in load_ids:
            raise InvalidMuseResponseError("Load identifiers must be unique.")
        if magnitude is not None and (isinstance(magnitude, bool) or not isinstance(magnitude, (int, float)) or not math.isfinite(magnitude)):
            raise InvalidMuseResponseError("Load magnitude must be a finite number or null.")
        if unit is not None and (not isinstance(unit, str) or not unit.strip()):
            raise InvalidMuseResponseError("Load unit must be a non-empty string or null.")
        if (magnitude is None) != (unit is None):
            raise InvalidMuseResponseError("Load magnitude and unit must both be present or both be null.")
        load_ids.add(load_id)
        loads.append(CandidateLoadProposal(
            load_id,
            _to_pixel(record["x_1000"], width, "load x"),
            _to_pixel(record["y_1000"], height, "load y"),
            _string(record["direction"], "load direction"),
            None if magnitude is None else float(magnitude),
            unit,
            _boolean(record["uncertain"], "load uncertain"),
            _string(record["notes"], "load notes"),
        ))

    ambiguities = _string_list(payload["ambiguities"], "ambiguities")
    missing_information = _string_list(payload["missing_information"], "missing_information")
    return TrussInterpretationProposal(
        image_width=width,
        image_height=height,
        coordinate_space="original_image_pixels",
        coordinate_convention="origin_top_left_x_right_y_down",
        joints=tuple(joints),
        members=tuple(members),
        supports=tuple(supports),
        loads=tuple(loads),
        ambiguities=ambiguities,
        missing_information=missing_information,
    )


def _to_pixel(value: Any, dimension: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1000:
        raise InvalidMuseResponseError(f"{field} must be an integer between 0 and 1000.")
    return round(value * (dimension - 1) / 1000)


def _list(payload: dict, key: str) -> list:
    value = payload[key]
    if not isinstance(value, list):
        raise InvalidMuseResponseError(f"{key} must be an array.")
    return value


def _object(value: Any, expected_keys: set[str]) -> dict:
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise InvalidMuseResponseError("Interpretation item has missing or unexpected fields.")
    return value


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidMuseResponseError(f"{field} identifier must be a non-empty string.")
    return value


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidMuseResponseError(f"{field} must be a boolean.")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidMuseResponseError(f"{field} must be a string.")
    return value


def _string_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise InvalidMuseResponseError(f"{field} must be an array of strings.")
    return tuple(value)
