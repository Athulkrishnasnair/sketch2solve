"""Compare fixed overlapping ROI tile layouts using the unchanged detector."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "evaluation/results/phase-a-2026-10-30/overlapping-tile-experiment-2026-10-30/tile_config.json"
BASELINE_PATH = ROOT / "evaluation/results/phase-a-2026-10-30/detector-baseline/baseline.json"
ROI_RESULTS_PATH = ROOT / "evaluation/results/phase-a-2026-10-30/roi-crop-experiment/results.json"
ANNOTATION_PATH = ROOT / "evaluation/results/phase-a-2026-10-30/annotations/test5.json"


def map_segment_to_original(segment: dict, origin_x: int, origin_y: int) -> dict:
    """Map a tile-local segment to source-image pixels, preserving provenance."""
    if type(origin_x) is not int or type(origin_y) is not int:
        raise ValueError("tile origins must be integers")
    mapped = dict(segment)
    mapped["start"] = [segment["start"][0] + origin_x, segment["start"][1] + origin_y]
    mapped["end"] = [segment["end"][0] + origin_x, segment["end"][1] + origin_y]
    return mapped


def _length(segment: dict) -> float:
    return math.dist(segment["start"], segment["end"])


def _canonical_endpoints(segment: dict):
    return tuple(sorted((tuple(segment["start"]), tuple(segment["end"]))))


def _point_segment_distance(point, start, end) -> float:
    vx, vy = end[0] - start[0], end[1] - start[1]
    denominator = vx * vx + vy * vy
    if denominator == 0:
        return math.dist(point, start)
    t = max(0.0, min(1.0, ((point[0] - start[0]) * vx + (point[1] - start[1]) * vy) / denominator))
    projection = (start[0] + t * vx, start[1] + t * vy)
    return math.dist(point, projection)


def _projected_overlap_ratio(a: dict, b: dict) -> float:
    ax, ay = a["end"][0] - a["start"][0], a["end"][1] - a["start"][1]
    length_a, length_b = _length(a), _length(b)
    if min(length_a, length_b) == 0:
        return 0.0
    bx, by = b["end"][0] - b["start"][0], b["end"][1] - b["start"][1]
    theta_a, theta_b = math.atan2(ay, ax), math.atan2(by, bx)
    angle = 0.5 * math.atan2(math.sin(2 * theta_a) + math.sin(2 * theta_b), math.cos(2 * theta_a) + math.cos(2 * theta_b))
    ux, uy = math.cos(angle), math.sin(angle)
    proj_a = sorted((a["start"][0] * ux + a["start"][1] * uy, a["end"][0] * ux + a["end"][1] * uy))
    proj_b = sorted((b["start"][0] * ux + b["start"][1] * uy, b["end"][0] * ux + b["end"][1] * uy))
    overlap = max(0.0, min(proj_a[1], proj_b[1]) - max(proj_a[0], proj_b[0]))
    return overlap / min(length_a, length_b)


def lines_are_duplicate(a: dict, b: dict, *, perpendicular_tolerance_px: float,
                        angle_tolerance_degrees: float = 4.0,
                        minimum_overlap_ratio: float = 0.35) -> bool:
    """Whether cross-tile segments are compatible duplicate observations."""
    if a.get("tile_id") == b.get("tile_id"):
        return False
    length_a, length_b = _length(a), _length(b)
    if length_a == 0 or length_b == 0:
        return False
    ax, ay = a["end"][0] - a["start"][0], a["end"][1] - a["start"][1]
    bx, by = b["end"][0] - b["start"][0], b["end"][1] - b["start"][1]
    cosine = min(1.0, max(-1.0, abs((ax * bx + ay * by) / (length_a * length_b))))
    if math.degrees(math.acos(cosine)) > angle_tolerance_degrees:
        return False
    # Symmetric line-to-line distances reject parallel neighboring members.
    def line_distance(point, segment):
        vx = segment["end"][0] - segment["start"][0]
        vy = segment["end"][1] - segment["start"][1]
        return abs(vx * (point[1] - segment["start"][1]) - vy * (point[0] - segment["start"][0])) / _length(segment)

    endpoint_distances = (
        line_distance(a["start"], b), line_distance(a["end"], b),
        line_distance(b["start"], a), line_distance(b["end"], a),
    )
    if max(endpoint_distances) > perpendicular_tolerance_px:
        return False
    if _projected_overlap_ratio(a, b) < minimum_overlap_ratio:
        return False
    # An endpoint must touch the other finite segment, which supports partial
    # duplicates but rejects nearby non-overlapping collinear detections.
    endpoint_support = min(
        _point_segment_distance(a["start"], b["start"], b["end"]),
        _point_segment_distance(a["end"], b["start"], b["end"]),
        _point_segment_distance(b["start"], a["start"], a["end"]),
        _point_segment_distance(b["end"], a["start"], a["end"]),
    )
    return endpoint_support <= perpendicular_tolerance_px


def _merge_group(group: list[dict], group_id: str) -> dict:
    # Orientation is an axial quantity, so average doubled angles to handle
    # reversed endpoint ordering. Union projected intervals without bridging gaps.
    weighted_cos = weighted_sin = 0.0
    all_points = []
    for line in group:
        dx = line["end"][0] - line["start"][0]
        dy = line["end"][1] - line["start"][1]
        theta = math.atan2(dy, dx)
        length = math.hypot(dx, dy)
        weighted_cos += length * math.cos(2 * theta)
        weighted_sin += length * math.sin(2 * theta)
        all_points.extend((line["start"], line["end"]))
    theta = 0.5 * math.atan2(weighted_sin, weighted_cos)
    ux, uy = math.cos(theta), math.sin(theta)
    if ux < 0 or (abs(ux) < 1e-12 and uy < 0):
        ux, uy = -ux, -uy
    nx, ny = -uy, ux
    along = [point[0] * ux + point[1] * uy for point in all_points]
    offsets = [point[0] * nx + point[1] * ny for point in all_points]
    offset = statistics.median(offsets)
    lo, hi = min(along), max(along)
    start = [round(lo * ux + offset * nx), round(lo * uy + offset * ny)]
    end = [round(hi * ux + offset * nx), round(hi * uy + offset * ny)]
    ordered = sorted(group, key=lambda line: (line["tile_id"], line["line_id"], _canonical_endpoints(line)))
    return {
        "id": group_id,
        "start": start,
        "end": end,
        "length_px": math.dist(start, end),
        "evidence": "cross_tile_candidate_union",
        "source_tile_ids": sorted({line["tile_id"] for line in group}),
        "source_detections": [
            {
                "tile_id": line["tile_id"],
                "line_id": line["line_id"],
                "tile_origin": line["tile_origin"],
                "mapped_start": line["start"],
                "mapped_end": line["end"],
            }
            for line in ordered
        ],
    }


def deduplicate_segments(segments: list[dict], *, perpendicular_tolerance_px: float,
                         angle_tolerance_degrees: float = 4.0,
                         minimum_overlap_ratio: float = 0.35) -> list[dict]:
    """Deterministic complete-link deduplication with cross-tile provenance."""
    ordered = sorted(segments, key=lambda line: (*_canonical_endpoints(line), line.get("tile_id", ""), line.get("line_id", "")))
    groups: list[list[dict]] = []
    for candidate in ordered:
        target = None
        for group in groups:
            if candidate.get("tile_id") in {member.get("tile_id") for member in group}:
                continue
            if all(lines_are_duplicate(candidate, member,
                                       perpendicular_tolerance_px=perpendicular_tolerance_px,
                                       angle_tolerance_degrees=angle_tolerance_degrees,
                                       minimum_overlap_ratio=minimum_overlap_ratio) for member in group):
                target = group
                break
        if target is None:
            groups.append([candidate])
        else:
            target.append(candidate)
    return [_merge_group(group, f"D{index:04d}") for index, group in enumerate(groups, start=1)]


def _validate_tile_config(roi: dict, configurations: dict) -> None:
    rx, ry, rw, rh = (roi[key] for key in ("x", "y", "width", "height"))
    for name, config in configurations.items():
        tw, th = config["tile_width"], config["tile_height"]
        if th != rh or tw <= 0 or tw > rw:
            raise ValueError(f"{name}: configured tiles must span the full ROI height and fit its width")
        origins = config["origins_original_pixels"]
        if not origins or any(y != ry or x < rx or x + tw > rx + rw for x, y in origins):
            raise ValueError(f"{name}: tile origins must be in-bounds and aligned to the ROI top")
        intervals = sorted((x, x + tw) for x, _y in origins)
        covered = intervals[0][0] == rx and intervals[-1][1] == rx + rw
        covered = covered and all(current[0] <= previous[1] for previous, current in zip(intervals, intervals[1:]))
        if not covered:
            raise ValueError(f"{name}: tiles must cover the complete ROI without gaps")


def _build_combined_result(lines: list[dict], image_width: int, image_height: int,
                           endpoint_tolerance: float) -> tuple[dict, object]:
    from app.services.perception import CandidateLine, PerceptionResult, _cluster_endpoints

    candidates = tuple(CandidateLine(
        id=line["id"], start=tuple(line["start"]), end=tuple(line["end"]),
        length_px=line["length_px"], evidence=line["evidence"],
    ) for line in lines)
    joints = _cluster_endpoints(candidates, endpoint_tolerance)
    result_object = PerceptionResult(
        image_width=image_width,
        image_height=image_height,
        coordinate_space="image_pixels",
        lines=candidates,
        joints=joints,
        settings={"source": "cross-tile deduplicated candidates", "endpoint_tolerance": endpoint_tolerance},
        warnings=(),
        diagnostics={"candidate_line_count": len(candidates)},
    )
    return result_object.to_dict(), result_object


def _overlay(source, lines: list[dict], joints: list[dict], ambiguous_points: list[dict], path: Path) -> None:
    image = source.copy()
    for line in lines:
        cv2.line(image, tuple(line["start"]), tuple(line["end"]), (0, 0, 235), 2, cv2.LINE_AA)
    for joint in joints:
        point = tuple(round(value) for value in joint["point"])
        cv2.circle(image, point, 4, (30, 190, 40), -1, cv2.LINE_AA)
    for point in ambiguous_points:
        center = (point["x"], point["y"])
        cv2.circle(image, center, 9, (0, 140, 255), 2, cv2.LINE_AA)
    if not cv2.imwrite(str(path), image):
        raise OSError(f"Could not write overlay {path}")


def run(config_path: Path, output_dir: Path, repeats: int) -> dict:
    backend_dir = ROOT / "backend"
    sys.path.insert(0, str(backend_dir))
    sys.path.insert(0, str(ROOT / "evaluation"))
    from app.services.perception import detect_candidate_geometry, inspect_image_header, _cluster_endpoints
    from perception_evaluation import evaluate_image, validate_annotation, _member_coverage

    config = json.loads(config_path.read_text())
    roi = config["roi"]
    configurations = config["configurations"]
    _validate_tile_config(roi, configurations)
    source_path = ROOT / config["source"]["path"]
    source_bytes = source_path.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    if source_hash != config["source"]["sha256"]:
        raise ValueError("Source image hash does not match frozen tile config")
    width, height, mime = inspect_image_header(source_bytes)
    if (width, height) != (config["source"]["width"], config["source"]["height"]):
        raise ValueError("Source image dimensions do not match tile config")
    source = cv2.imdecode(np.frombuffer(source_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if source is None:
        raise ValueError("Source image could not be decoded")
    annotation = json.loads(ANNOTATION_PATH.read_text())
    validate_annotation(annotation)
    annotated_crossings = [
        {"x": int(point["point"][0]), "y": int(point["point"][1]), "status": point["status"]}
        for point in annotation["ambiguous_regions"]
    ]
    if annotated_crossings != config["test5_ambiguous_crossings_original_pixels"]:
        raise ValueError("Frozen ambiguous crossing markers do not match the existing annotation")

    x0, y0, rw, rh = roi["x"], roi["y"], roi["width"], roi["height"]
    roi_crop = source[y0:y0 + rh, x0:x0 + rw]
    ok, roi_encoded = cv2.imencode(".png", roi_crop)
    if not ok:
        raise RuntimeError("Could not encode the fixed ROI")
    roi_detector_result = detect_candidate_geometry(roi_encoded.tobytes()).to_dict()
    roi_fullspace = json.loads(json.dumps(roi_detector_result))
    for line in roi_fullspace["lines"]:
        line["start"] = [line["start"][0] + x0, line["start"][1] + y0]
        line["end"] = [line["end"][0] + x0, line["end"][1] + y0]
    for joint in roi_fullspace["joints"]:
        joint["point"] = [joint["point"][0] + x0, joint["point"][1] + y0]
    roi_fullspace["image_width"], roi_fullspace["image_height"] = width, height

    baseline = json.loads(BASELINE_PATH.read_text())
    original = next(image for image in baseline["images"] if image["input"]["filename"] == "test5.png")
    prior_roi = json.loads(ROI_RESULTS_PATH.read_text())
    roi_record = next(image for image in prior_roi["images"] if image["filename"] == "test5.png")
    original_metrics = evaluate_image(original, annotation)
    roi_metrics = evaluate_image(roi_record["cropped"]["detector_result_original_coordinates"], annotation)

    def member_coverage_detail(result_dict):
        confirmed = {joint["id"]: (joint["x"], joint["y"]) for joint in annotation["joints"] if joint["status"] == "confirmed"}
        diagonal = math.hypot(width, height)
        corridor = max(12.0, 0.0075 * diagonal)
        lines = [(line["start"], line["end"]) for line in result_dict["lines"]]
        detail = {}
        for member in annotation["members"]:
            if member["status"] != "confirmed":
                continue
            coverage = _member_coverage(
                (confirmed[member["node_i"]], confirmed[member["node_j"]]),
                lines,
                corridor,
                8.0,
            )
            detail[member["id"]] = {"coverage_fraction": coverage, "recovered_at_80_percent": coverage >= 0.8}
        return detail

    def rightmost_bay_summary(detail):
        member_ids = config["rightmost_bay_reference_member_ids"]
        recovered = [member_id for member_id in member_ids if detail[member_id]["recovered_at_80_percent"]]
        return {"reference_member_ids": member_ids, "recovered_member_ids": recovered,
                "recovered_count": len(recovered), "reference_count": len(member_ids)}

    original_detail = member_coverage_detail(original)
    roi_fullspace = roi_record["cropped"]["detector_result_original_coordinates"]
    roi_detail = member_coverage_detail(roi_fullspace)

    output_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir = output_dir / "overlays"
    overlay_dir.mkdir(exist_ok=True)
    result_by_config = {}
    tolerance_values = config["deduplication"]["sensitivity_perpendicular_tolerances_px"]
    for config_name, tile_config in configurations.items():
        tile_width, tile_height = tile_config["tile_width"], tile_config["tile_height"]
        tile_payloads = []
        tile_metadata = []
        for index, (tile_x, tile_y) in enumerate(tile_config["origins_original_pixels"], start=1):
            tile_image = source[tile_y:tile_y + tile_height, tile_x:tile_x + tile_width]
            ok, encoded = cv2.imencode(".png", tile_image)
            if not ok:
                raise RuntimeError(f"{config_name}: tile {index} PNG encoding failed")
            tile_payloads.append(encoded.tobytes())
            tile_metadata.append({"tile_id": f"{config_name}-T{index:02d}", "origin": [tile_x, tile_y],
                                  "width": tile_width, "height": tile_height})

        tile_runs = [[] for _ in tile_payloads]
        repeat_total_ms = []
        for _repeat in range(repeats):
            total = 0.0
            for tile_index, payload in enumerate(tile_payloads):
                started = time.perf_counter()
                detection = detect_candidate_geometry(payload)
                elapsed_ms = (time.perf_counter() - started) * 1000
                total += elapsed_ms
                tile_runs[tile_index].append((elapsed_ms, detection.to_dict()))
            repeat_total_ms.append(total)

        raw_segments = []
        tile_records = []
        for tile_index, runs in enumerate(tile_runs):
            if any(run[1] != runs[0][1] for run in runs[1:]):
                raise RuntimeError(f"{tile_metadata[tile_index]['tile_id']}: non-deterministic detector output")
            metadata = tile_metadata[tile_index]
            local_result = runs[0][1]
            local_lines = local_result["lines"]
            for line in local_lines:
                mapped = map_segment_to_original(line, *metadata["origin"])
                raw_segments.append({
                    "tile_id": metadata["tile_id"],
                    "line_id": line["id"],
                    "tile_origin": metadata["origin"],
                    "start": mapped["start"],
                    "end": mapped["end"],
                })
            tile_dir = output_dir / "tiles" / config_name
            tile_dir.mkdir(parents=True, exist_ok=True)
            tile_overlay = runs[0][1]
            from app.services.perception import CandidateJoint, CandidateLine, PerceptionResult, render_detections
            local_object = PerceptionResult(
                image_width=tile_overlay["image_width"], image_height=tile_overlay["image_height"],
                coordinate_space=tile_overlay["coordinate_space"],
                lines=tuple(CandidateLine(id=l["id"], start=tuple(l["start"]), end=tuple(l["end"]),
                                          length_px=l["length_px"], evidence=l["evidence"]) for l in local_lines),
                joints=tuple(CandidateJoint(id=j["id"], point=tuple(j["point"]), evidence=j["evidence"],
                                            line_ids=tuple(j["line_ids"]), endpoint_count=j["endpoint_count"])
                             for j in tile_overlay["joints"]),
                settings=tile_overlay["settings"], warnings=tuple(tile_overlay["warnings"]), diagnostics=tile_overlay["diagnostics"],
            )
            (tile_dir / f"{metadata['tile_id']}.png").write_bytes(render_detections(tile_payloads[tile_index], local_object))
            tile_records.append({
                **metadata,
                "candidate_line_count": len(local_lines),
                "endpoint_cluster_count": len(tile_overlay["joints"]),
                "candidate_cap_reached": len(local_lines) == 300,
                "runtime_ms_median": statistics.median(run[0] for run in runs),
                "runtime_ms_min": min(run[0] for run in runs),
                "runtime_ms_max": max(run[0] for run in runs),
                "deterministic_across_runs": True,
                "mapped_line_detections": [
                    {"tile_id": metadata["tile_id"], "line_id": line["id"], "tile_origin": metadata["origin"],
                     "start": map_segment_to_original(line, *metadata["origin"])["start"],
                     "end": map_segment_to_original(line, *metadata["origin"])["end"]}
                    for line in local_lines
                ],
            })

        sensitivity = {}
        primary_fullspace = None
        primary_lines = None
        raw_as_lines = [
            {"id": f"R{index:05d}", "start": line["start"], "end": line["end"],
             "length_px": _length(line), "evidence": "tile_candidate"}
            for index, line in enumerate(raw_segments, start=1)
        ]
        raw_fullspace, _raw_object = _build_combined_result(raw_as_lines, width, height, endpoint_tolerance=12.0)
        raw_metrics = evaluate_image(raw_fullspace, annotation)
        for tolerance in tolerance_values:
            deduplicated = deduplicate_segments(
                raw_segments,
                perpendicular_tolerance_px=tolerance,
                angle_tolerance_degrees=config["deduplication"]["orientation_tolerance_degrees"],
                minimum_overlap_ratio=config["deduplication"]["minimum_projected_overlap_ratio_of_shorter_segment"],
            )
            combined_dict, combined_object = _build_combined_result(
                deduplicated, width, height, endpoint_tolerance=12.0,
            )
            metrics = evaluate_image(combined_dict, annotation)
            sensitivity[str(tolerance)] = {
                "deduplicated_candidate_line_count": len(deduplicated),
                "removed_detection_count": len(raw_segments) - len(deduplicated),
                "removed_fraction": (len(raw_segments) - len(deduplicated)) / len(raw_segments) if raw_segments else 0.0,
                "endpoint_cluster_count": len(combined_dict["joints"]),
                "metrics": metrics,
                "member_coverage_by_reference_member": member_coverage_detail(combined_dict),
                "rightmost_bay_coverage": rightmost_bay_summary(member_coverage_detail(combined_dict)),
            }
            if tolerance == config["deduplication"]["primary_perpendicular_tolerance_px"]:
                primary_fullspace, primary_lines = combined_dict, deduplicated

        if primary_fullspace is None:
            raise ValueError("Primary deduplication tolerance must be listed in sensitivity tolerances")
        overlay_stem = f"{config_name}_deduplicated.png"
        _overlay(source, primary_lines, primary_fullspace["joints"], annotated_crossings, overlay_dir / overlay_stem)
        raw_overlay_lines = [
            {"start": line["start"], "end": line["end"]} for line in raw_segments
        ]
        _overlay(source, raw_overlay_lines, [], annotated_crossings, overlay_dir / f"{config_name}_raw.png")
        result_by_config[config_name] = {
            "configuration": tile_config,
            "tiles": tile_records,
            "total_raw_candidate_count_before_deduplication": len(raw_segments),
            "raw_reconstructed_endpoint_cluster_count_before_deduplication": len(raw_fullspace["joints"]),
            "raw_reconstructed_metrics_before_deduplication": raw_metrics,
            "primary_deduplication_tolerance_px": config["deduplication"]["primary_perpendicular_tolerance_px"],
            "sensitivity": sensitivity,
            "primary_deduplicated_lines_with_provenance": primary_lines,
            "primary_reconstructed_candidate_result_original_coordinates": primary_fullspace,
            "runtime": {
                "repeat_count": repeats,
                "total_detector_runtime_ms_median": statistics.median(repeat_total_ms),
                "total_detector_runtime_ms_min": min(repeat_total_ms),
                "total_detector_runtime_ms_max": max(repeat_total_ms),
                "per_repeat_detector_runtime_ms": repeat_total_ms,
                "deduplication_runtime_included": False,
                "tile_creation_and_encoding_included": False,
            },
            "overlay_paths": {
                "raw": f"overlays/{config_name}_raw.png",
                "deduplicated": f"overlays/{overlay_stem}",
            },
        }

    original_lines = original["lines"]
    _overlay(source, original_lines, original["joints"], annotated_crossings, overlay_dir / "original_full_image.png")
    _overlay(source, roi_record["cropped"]["detector_result_original_coordinates"]["lines"],
             roi_record["cropped"]["detector_result_original_coordinates"]["joints"], annotated_crossings,
             overlay_dir / "previous_full_roi.png")
    return {
        "experiment": config["experiment"],
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {"path": config["source"]["path"], "sha256": source_hash, "mime_type": mime,
                   "width": width, "height": height},
        "repeats_per_tile": repeats,
        "detector": "unchanged default detect_candidate_geometry(image_bytes)",
        "opencv_version": cv2.__version__,
        "reference_and_metrics": "Existing Phase A test5 main-truss annotation; original-image coordinates; same Phase A matching and coverage tolerances.",
        "comparison_conditions": {
            "original": {"candidate_line_count": len(original["lines"]),
                         "candidate_cap_reached": original["measurement"]["candidate_cap_reached"],
                         "endpoint_cluster_count": len(original["joints"]),
                         "runtime_ms_median": original["measurement"]["runtime_ms_median"],
                         "metrics": original_metrics,
                         "member_coverage_by_reference_member": original_detail,
                         "rightmost_bay_coverage": rightmost_bay_summary(original_detail)},
            "previous_full_roi": {"candidate_line_count": roi_record["cropped"]["candidate_line_count"],
                                  "candidate_cap_reached": roi_record["cropped"]["measurement"]["candidate_cap_reached"],
                                  "endpoint_cluster_count": roi_record["cropped"]["endpoint_cluster_count"],
                                  "runtime_ms_median": roi_record["cropped"]["measurement"]["runtime_ms_median"],
                                  "metrics": roi_metrics,
                                  "member_coverage_by_reference_member": roi_detail,
                                  "rightmost_bay_coverage": rightmost_bay_summary(roi_detail)},
        },
        "deduplication": config["deduplication"],
        "configurations": result_by_config,
        "ambiguous_crossings": annotated_crossings,
        "interpretation_note": "All accuracy metrics are exploratory candidate geometry scores, not structural semantics. Tiled predictions are reconstructed in source coordinates before evaluation. No metrics are averaged across tiles.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    output_dir = args.output_dir.resolve()
    result = run(args.config.resolve(), output_dir, args.repeats)
    (output_dir / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Original full image: {result['comparison_conditions']['original']['candidate_line_count']} lines; "
          f"P/R={result['comparison_conditions']['original']['metrics']['joint_precision']:.4f}/"
          f"{result['comparison_conditions']['original']['metrics']['joint_recall']:.4f}")
    print(f"Previous full ROI: {result['comparison_conditions']['previous_full_roi']['candidate_line_count']} lines; "
          f"P/R={result['comparison_conditions']['previous_full_roi']['metrics']['joint_precision']:.4f}/"
          f"{result['comparison_conditions']['previous_full_roi']['metrics']['joint_recall']:.4f}")
    for name, configuration in result["configurations"].items():
        print(f"{name}: tiles=" + ", ".join(f"{tile['candidate_line_count']} (cap={tile['candidate_cap_reached']})" for tile in configuration["tiles"]))
        for tolerance, measurement in configuration["sensitivity"].items():
            metrics = measurement["metrics"]
            print(f"  dedup tol={tolerance}px: {measurement['total_raw_candidate_count_before_deduplication'] if 'total_raw_candidate_count_before_deduplication' in measurement else configuration['total_raw_candidate_count_before_deduplication']} -> {measurement['deduplicated_candidate_line_count']} lines; "
                  f"P/R={metrics['joint_precision']:.4f}/{metrics['joint_recall']:.4f}; "
                  f"coverage={metrics['members_with_at_least_80_percent_candidate_line_coverage']}/16")
    print(f"Results: {output_dir / 'results.json'}")


if __name__ == "__main__":
    main()
