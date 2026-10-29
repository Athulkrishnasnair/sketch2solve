"""OpenCV prototype for extracting candidate image lines and endpoint joints.

This service reports visual evidence in image pixels. It does not assign
structural meaning to any detected geometry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import struct

import cv2
import numpy as np


MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_DIMENSION = 6000
MAX_IMAGE_PIXELS = 24_000_000
MAX_RAW_HOUGH_SEGMENTS = 5_000
MAX_CANDIDATE_LINES = 300


class PerceptionInputError(ValueError):
    """Raised when image data is empty, unsupported, malformed, or too large."""


def inspect_image_header(image_bytes: bytes, *, max_bytes: int = MAX_IMAGE_BYTES) -> tuple[int, int, str]:
    """Identify and bound a JPEG, PNG, or WebP from its encoded header.

    Header dimensions are checked before OpenCV allocates decoded pixels. The
    decoder still verifies that the complete image is readable afterwards.
    """
    if not isinstance(image_bytes, (bytes, bytearray, memoryview)) or not image_bytes:
        raise PerceptionInputError("Image data must be non-empty encoded bytes.")
    if len(image_bytes) > max_bytes:
        raise PerceptionInputError(f"Encoded image exceeds the {max_bytes}-byte limit.")
    content = bytes(image_bytes)
    mime_type = _mime_from_signature(content)
    if mime_type is None:
        raise PerceptionInputError("Only JPEG, PNG, and WebP image bytes are supported.")
    dimensions = _header_dimensions(content, mime_type)
    if dimensions is None:
        raise PerceptionInputError("Image header is incomplete or corrupted.")
    width, height = dimensions
    if width < 8 or height < 8:
        raise PerceptionInputError("Image dimensions must be at least 8 by 8 pixels.")
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION or width * height > MAX_IMAGE_PIXELS:
        raise PerceptionInputError("Decoded image dimensions exceed configured safety limits.")
    return width, height, mime_type


def _mime_from_signature(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def _header_dimensions(content: bytes, mime_type: str) -> tuple[int, int] | None:
    if mime_type == "image/png":
        if len(content) < 24 or content[12:16] != b"IHDR":
            return None
        return struct.unpack(">II", content[16:24])

    if mime_type == "image/jpeg":
        offset = 2
        sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
        while offset < len(content):
            if content[offset] != 0xFF:
                return None
            while offset < len(content) and content[offset] == 0xFF:
                offset += 1
            if offset >= len(content):
                return None
            marker = content[offset]
            offset += 1
            if marker in {0xD8, 0xD9, 0x01, *range(0xD0, 0xD8)}:
                continue
            if offset + 2 > len(content):
                return None
            segment_length = int.from_bytes(content[offset:offset + 2], "big")
            if segment_length < 2 or offset + segment_length > len(content):
                return None
            if marker in sof_markers:
                if segment_length < 7:
                    return None
                height = int.from_bytes(content[offset + 3:offset + 5], "big")
                width = int.from_bytes(content[offset + 5:offset + 7], "big")
                return width, height
            offset += segment_length
        return None

    if len(content) < 21:
        return None
    riff_size = int.from_bytes(content[4:8], "little")
    if riff_size + 8 > len(content):
        return None
    chunk_type = content[12:16]
    if chunk_type == b"VP8X" and len(content) >= 30:
        return 1 + int.from_bytes(content[24:27], "little"), 1 + int.from_bytes(content[27:30], "little")
    if chunk_type == b"VP8 " and len(content) >= 30 and content[23:26] == b"\x9d\x01\x2a":
        width = int.from_bytes(content[26:28], "little") & 0x3FFF
        height = int.from_bytes(content[28:30], "little") & 0x3FFF
        return width, height
    if chunk_type == b"VP8L" and len(content) >= 25 and content[20] == 0x2F:
        bits = content[21:25]
        width = 1 + bits[0] + ((bits[1] & 0x3F) << 8)
        height = 1 + ((bits[1] & 0xC0) >> 6) + (bits[2] << 2) + ((bits[3] & 0x0F) << 10)
        return width, height
    return None


@dataclass(frozen=True)
class PerceptionConfig:
    """Typed tuning settings for preprocessing, Hough detection, and clustering."""

    canny_sigma: float = 0.8
    canny_min_threshold: int = 40
    canny_max_threshold: int = 160
    hough_rho: float = 1.0
    hough_theta_degrees: float = 1.0
    hough_threshold: int = 25
    min_line_length: float = 20.0
    max_line_gap: float = 8.0
    endpoint_tolerance: float = 12.0
    duplicate_angle_degrees: float = 4.0
    duplicate_distance: float = 4.0
    duplicate_overlap_ratio: float = 0.65


@dataclass(frozen=True)
class CandidateLine:
    id: str
    start: tuple[int, int]
    end: tuple[int, int]
    length_px: float
    evidence: str = "probabilistic_hough"


@dataclass(frozen=True)
class CandidateJoint:
    id: str
    point: tuple[float, float]
    evidence: str
    line_ids: tuple[str, ...]
    endpoint_count: int


@dataclass(frozen=True)
class PerceptionResult:
    image_width: int
    image_height: int
    coordinate_space: str
    lines: tuple[CandidateLine, ...]
    joints: tuple[CandidateJoint, ...]
    settings: dict
    warnings: tuple[str, ...]
    diagnostics: dict

    def to_dict(self) -> dict:
        """Return a JSON-serializable result with arrays represented as lists."""
        return {
            "image_width": self.image_width,
            "image_height": self.image_height,
            "coordinate_space": self.coordinate_space,
            "lines": [
                {**asdict(line), "start": list(line.start), "end": list(line.end)}
                for line in self.lines
            ],
            "joints": [
                {**asdict(joint), "point": list(joint.point), "line_ids": list(joint.line_ids)}
                for joint in self.joints
            ],
            "settings": self.settings,
            "warnings": list(self.warnings),
            "diagnostics": self.diagnostics,
        }


def detect_candidate_geometry(
    image_bytes: bytes,
    config: PerceptionConfig | None = None,
) -> PerceptionResult:
    """Decode an encoded image and return candidate line segments and endpoint clusters.

    Endpoint clusters are merged when all points connect transitively by no more
    than ``endpoint_tolerance`` pixels. Intersections inside line segments are
    deliberately not inferred in this phase.
    """
    config = config or PerceptionConfig()
    _validate_config(config)
    header_width, header_height, _mime_type = inspect_image_header(image_bytes)
    encoded = np.frombuffer(bytes(image_bytes), dtype=np.uint8)
    try:
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    except cv2.error as error:
        raise PerceptionInputError("Image data could not be decoded.") from error
    if image is None or image.size == 0:
        raise PerceptionInputError("Image data could not be decoded.")
    height, width = image.shape[:2]
    if (width, height) != (header_width, header_height):
        raise PerceptionInputError("Image header dimensions do not match the decoded image.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    median = float(np.median(blurred))
    lower = int(min(config.canny_max_threshold - 1, max(config.canny_min_threshold, (1.0 - config.canny_sigma) * median)))
    upper = int(max(lower + 1, min(config.canny_max_threshold, (1.0 + config.canny_sigma) * median)))
    edges = cv2.Canny(blurred, lower, upper, L2gradient=True)
    segments = cv2.HoughLinesP(
        edges,
        rho=config.hough_rho,
        theta=math.radians(config.hough_theta_degrees),
        threshold=config.hough_threshold,
        minLineLength=config.min_line_length,
        maxLineGap=config.max_line_gap,
    )
    raw_detection_count = 0 if segments is None else len(segments)
    candidates = _canonical_segments(segments, config)
    lines = tuple(
        CandidateLine(
            id=f"L{index:03d}",
            start=(x1, y1),
            end=(x2, y2),
            length_px=math.hypot(x2 - x1, y2 - y1),
        )
        for index, (x1, y1, x2, y2) in enumerate(candidates, start=1)
    )
    joints = _cluster_endpoints(lines, config.endpoint_tolerance)
    warning_list = []
    if not lines:
        warning_list.append("No candidate line segments were detected.")
    if raw_detection_count > MAX_RAW_HOUGH_SEGMENTS or len(candidates) == MAX_CANDIDATE_LINES:
        warning_list.append("Candidate line output was capped to keep processing bounded.")
    return PerceptionResult(
        image_width=width,
        image_height=height,
        coordinate_space="image_pixels",
        lines=lines,
        joints=joints,
        settings={**asdict(config), "canny_lower_used": lower, "canny_upper_used": upper},
        warnings=tuple(warning_list),
        diagnostics={
            "edge_pixel_count": int(np.count_nonzero(edges)),
            "raw_hough_segment_count": raw_detection_count,
            "candidate_line_count": len(lines),
        },
    )


def render_detections(image_bytes: bytes, result: PerceptionResult, *, show_ids: bool = False) -> bytes:
    """Return an annotated PNG as bytes; does not open a GUI window."""
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.shape[1] != result.image_width or image.shape[0] != result.image_height:
        raise PerceptionInputError("Image bytes do not match the supplied perception result.")
    overlay = image.copy()
    for line in result.lines:
        cv2.line(overlay, line.start, line.end, (30, 70, 235), 2, cv2.LINE_AA)
        if show_ids:
            midpoint = ((line.start[0] + line.end[0]) // 2, (line.start[1] + line.end[1]) // 2)
            cv2.putText(overlay, line.id, midpoint, cv2.FONT_HERSHEY_SIMPLEX, 0.42, (15, 45, 180), 1, cv2.LINE_AA)
    for joint in result.joints:
        point = (round(joint.point[0]), round(joint.point[1]))
        cv2.circle(overlay, point, 4, (20, 190, 40), -1, cv2.LINE_AA)
    ok, png = cv2.imencode(".png", overlay)
    if not ok:
        raise PerceptionInputError("Could not encode annotated image.")
    return png.tobytes()


def _validate_config(config: PerceptionConfig) -> None:
    if not 0 < config.canny_sigma < 1:
        raise ValueError("canny_sigma must be between zero and one.")
    if not 0 <= config.canny_min_threshold < config.canny_max_threshold <= 255:
        raise ValueError("Canny thresholds must satisfy 0 <= minimum < maximum <= 255.")
    if config.endpoint_tolerance < 0 or config.min_line_length < 0:
        raise ValueError("Endpoint tolerance and minimum line length must be non-negative.")
    if config.hough_rho <= 0 or config.hough_theta_degrees <= 0:
        raise ValueError("Hough rho and theta increments must be positive.")


def _canonical_segments(raw_segments, config: PerceptionConfig) -> list[tuple[int, int, int, int]]:
    if raw_segments is None:
        return []
    segments = []
    for raw in raw_segments.reshape(-1, 4):
        x1, y1, x2, y2 = (int(value) for value in raw)
        if (x2, y2) < (x1, y1):
            x1, y1, x2, y2 = x2, y2, x1, y1
        if math.hypot(x2 - x1, y2 - y1) >= config.min_line_length:
            segments.append((x1, y1, x2, y2))
    segments.sort()
    segments = segments[:MAX_RAW_HOUGH_SEGMENTS]
    kept: list[tuple[int, int, int, int]] = []
    for candidate in segments:
        if not any(_is_duplicate(candidate, existing, config) for existing in kept):
            kept.append(candidate)
            if len(kept) >= MAX_CANDIDATE_LINES:
                break
    return kept


def _is_duplicate(a, b, config: PerceptionConfig) -> bool:
    ax, ay = a[2] - a[0], a[3] - a[1]
    bx, by = b[2] - b[0], b[3] - b[1]
    length_a, length_b = math.hypot(ax, ay), math.hypot(bx, by)
    cosine = min(1.0, abs((ax * bx + ay * by) / (length_a * length_b)))
    angle = math.degrees(math.acos(cosine))
    if angle > config.duplicate_angle_degrees:
        return False
    distance = max(
        _point_line_distance((a[0], a[1]), b),
        _point_line_distance((a[2], a[3]), b),
        _point_line_distance((b[0], b[1]), a),
        _point_line_distance((b[2], b[3]), a),
    )
    if distance > config.duplicate_distance:
        return False
    ux, uy = ax / length_a, ay / length_a
    a_proj = sorted((a[0] * ux + a[1] * uy, a[2] * ux + a[3] * uy))
    b_proj = sorted((b[0] * ux + b[1] * uy, b[2] * ux + b[3] * uy))
    overlap = max(0.0, min(a_proj[1], b_proj[1]) - max(a_proj[0], b_proj[0]))
    return overlap / min(length_a, length_b) >= config.duplicate_overlap_ratio


def _point_line_distance(point, segment) -> float:
    x1, y1, x2, y2 = segment
    length = math.hypot(x2 - x1, y2 - y1)
    return abs((y2 - y1) * point[0] - (x2 - x1) * point[1] + x2 * y1 - y2 * x1) / length


def _cluster_endpoints(lines: tuple[CandidateLine, ...], tolerance: float) -> tuple[CandidateJoint, ...]:
    endpoints = [(line.id, line.start) for line in lines] + [(line.id, line.end) for line in lines]
    parent = list(range(len(endpoints)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for left in range(len(endpoints)):
        for right in range(left + 1, len(endpoints)):
            if math.dist(endpoints[left][1], endpoints[right][1]) <= tolerance:
                root_left, root_right = find(left), find(right)
                if root_left != root_right:
                    parent[max(root_left, root_right)] = min(root_left, root_right)
    groups: dict[int, list] = {}
    for index, endpoint in enumerate(endpoints):
        groups.setdefault(find(index), []).append(endpoint)
    clusters = sorted(groups.values(), key=lambda group: (min(p[1][1] for p in group), min(p[1][0] for p in group), tuple(sorted(p[0] for p in group))))
    return tuple(
        CandidateJoint(
            id=f"J{index:03d}",
            point=(sum(item[1][0] for item in group) / len(group), sum(item[1][1] for item in group) / len(group)),
            evidence="endpoint_cluster",
            line_ids=tuple(sorted({item[0] for item in group})),
            endpoint_count=len(group),
        )
        for index, group in enumerate(clusters, start=1)
    )
