"""Test one fixed, annotation-selected tile around test5's rightmost bay."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "evaluation/results/phase-a-2026-10-30/rightmost-bay-targeted-tile-2026-10-30/tile_config.json"
BASELINE_PATH = ROOT / "evaluation/results/phase-a-2026-10-30/detector-baseline/baseline.json"
ROI_RESULTS_PATH = ROOT / "evaluation/results/phase-a-2026-10-30/roi-crop-experiment/results.json"
TILE_RESULTS_PATH = ROOT / "evaluation/results/phase-a-2026-10-30/overlapping-tile-experiment-2026-10-30/results.json"
ANNOTATION_PATH = ROOT / "evaluation/results/phase-a-2026-10-30/annotations/test5.json"
TARGET_IDS = ("M09", "M10", "M16")


def _load_shared_helpers():
    evaluation_dir = ROOT / "evaluation"
    sys.path.insert(0, str(ROOT / "backend"))
    sys.path.insert(0, str(evaluation_dir))
    spec = importlib.util.spec_from_file_location("overlapping_tile_helpers", evaluation_dir / "run_overlapping_tile_experiment.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from app.services.perception import detect_candidate_geometry, inspect_image_header
    from perception_evaluation import evaluate_image, validate_annotation, _member_coverage, _maximum_cardinality_matches, _inside_roi
    return module, detect_candidate_geometry, inspect_image_header, evaluate_image, validate_annotation, _member_coverage, _maximum_cardinality_matches, _inside_roi


def _map_result(local_result: dict, tile: dict, width: int, height: int) -> dict:
    mapped = json.loads(json.dumps(local_result))
    ox, oy = tile["x"], tile["y"]
    for line in mapped["lines"]:
        line["start"] = [line["start"][0] + ox, line["start"][1] + oy]
        line["end"] = [line["end"][0] + ox, line["end"][1] + oy]
    for joint in mapped["joints"]:
        joint["point"] = [joint["point"][0] + ox, joint["point"][1] + oy]
    mapped["image_width"], mapped["image_height"] = width, height
    mapped["coordinate_space"] = "image_pixels"
    return mapped


def _member_detail(result: dict, annotation: dict, member_ids: list[str], member_coverage,
                   maximum_cardinality_matches, inside_roi) -> dict:
    joints = {joint["id"]: joint for joint in annotation["joints"] if joint["status"] == "confirmed"}
    member_by_id = {member["id"]: member for member in annotation["members"] if member["status"] == "confirmed"}
    references = list(joints.values())
    roi = annotation["evaluation_roi"]
    predictions = [joint for joint in result["joints"] if inside_roi(joint["point"], roi)]
    tolerance = max(12.0, 0.0075 * (result["image_width"] ** 2 + result["image_height"] ** 2) ** 0.5)
    matches = maximum_cardinality_matches(
        [joint["point"] for joint in predictions],
        [(joint["x"], joint["y"]) for joint in references],
        tolerance,
    )
    errors_by_node = {}
    for predicted_index, reference_index, distance in matches:
        errors_by_node[references[reference_index]["id"]] = distance
    lines = [(line["start"], line["end"]) for line in result["lines"]]
    corridor = tolerance
    detail = {}
    for member_id in member_ids:
        member = member_by_id[member_id]
        start_id, end_id = member["node_i"], member["node_j"]
        coverage = member_coverage(
            ((joints[start_id]["x"], joints[start_id]["y"]), (joints[end_id]["x"], joints[end_id]["y"])),
            lines,
            corridor,
            8.0,
        )
        detail[member_id] = {
            "start_joint": start_id,
            "end_joint": end_id,
            "coverage_fraction": coverage,
            "recovered_at_80_percent": coverage >= 0.8,
            "matched_endpoint_localization_error_px": {
                start_id: errors_by_node.get(start_id),
                end_id: errors_by_node.get(end_id),
            },
        }
    return detail


def _save_overlay(source, result: dict, ambiguous: list[dict], path: Path) -> None:
    overlay = source.copy()
    for line in result["lines"]:
        cv2.line(overlay, tuple(line["start"]), tuple(line["end"]), (0, 0, 235), 2, cv2.LINE_AA)
    for joint in result["joints"]:
        cv2.circle(overlay, tuple(round(value) for value in joint["point"]), 4, (30, 190, 40), -1, cv2.LINE_AA)
    for point in ambiguous:
        cv2.circle(overlay, (point["x"], point["y"]), 9, (0, 140, 255), 2, cv2.LINE_AA)
    if not cv2.imwrite(str(path), overlay):
        raise OSError(f"Could not write overlay {path}")


def run(config_path: Path, output_dir: Path, repeats: int) -> dict:
    (tile_tools, detect, inspect_header, evaluate_image, validate_annotation,
     member_coverage, maximum_cardinality_matches, inside_roi) = _load_shared_helpers()
    config = json.loads(config_path.read_text())
    source_config, tile = config["source"], config["tile"]
    source_bytes = (ROOT / source_config["path"]).read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    if source_sha != source_config["sha256"]:
        raise ValueError("Source image hash differs from frozen config")
    source_width, source_height, mime = inspect_header(source_bytes)
    if (source_width, source_height) != (source_config["width"], source_config["height"]):
        raise ValueError("Source dimensions differ from frozen config")
    decode_started = time.perf_counter()
    source = cv2.imdecode(np.frombuffer(source_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    source_decode_ms = (time.perf_counter() - decode_started) * 1000
    if source is None:
        raise ValueError("Source image could not be decoded")
    roi = config["reference_roi"]
    if not (roi["x"] <= tile["x"] and roi["y"] <= tile["y"] and
            tile["x"] + tile["width"] <= roi["x"] + roi["width"] and
            tile["y"] + tile["height"] <= roi["y"] + roi["height"]):
        raise ValueError("Target tile must be contained in the fixed reference ROI")

    annotation = json.loads(ANNOTATION_PATH.read_text())
    validate_annotation(annotation)
    annotation_members = {m["id"]: m for m in annotation["members"]}
    for member_id in TARGET_IDS:
        member = annotation_members[member_id]
        nodes = {j["id"]: j for j in annotation["joints"]}
        endpoints = (nodes[member["node_i"]], nodes[member["node_j"]])
        for endpoint in endpoints:
            if not (tile["x"] <= endpoint["x"] < tile["right_exclusive"] and tile["y"] <= endpoint["y"] < tile["bottom_exclusive"]):
                raise ValueError(f"Tile does not contain both endpoints for {member_id}")
    ambiguous = [
        {"x": int(region["point"][0]), "y": int(region["point"][1]), "status": region["status"]}
        for region in annotation["ambiguous_regions"]
    ]
    if ambiguous != config["ambiguous_crossings_original_pixels"]:
        raise ValueError("Ambiguous crossing config does not match unchanged annotation")

    # Repeated end-to-end tile passes separately capture preparation, detector,
    # and mapping/dedup/clustering costs. Source file read and decode are reported once.
    tile_runs = []
    stage_timings = []
    for _ in range(repeats):
        pipeline_started = time.perf_counter()
        prep_started = time.perf_counter()
        tile_pixels = source[tile["y"]:tile["bottom_exclusive"], tile["x"]:tile["right_exclusive"]]
        ok, encoded = cv2.imencode(".png", tile_pixels)
        prep_ms = (time.perf_counter() - prep_started) * 1000
        if not ok:
            raise RuntimeError("Target tile PNG encoding failed")
        detector_started = time.perf_counter()
        local_obj = detect(encoded.tobytes())
        detector_ms = (time.perf_counter() - detector_started) * 1000
        local_dict = local_obj.to_dict()
        post_started = time.perf_counter()
        mapped = _map_result(local_dict, tile, source_width, source_height)
        raw_segments = []
        for line in local_dict["lines"]:
            shifted = tile_tools.map_segment_to_original(line, tile["x"], tile["y"])
            raw_segments.append({
                "tile_id": tile["tile_id"], "line_id": line["id"],
                "tile_origin": [tile["x"], tile["y"]],
                "start": shifted["start"], "end": shifted["end"],
            })
        deduplicated = tile_tools.deduplicate_segments(
            raw_segments,
            perpendicular_tolerance_px=config["deduplication"]["primary_perpendicular_tolerance_px"],
            angle_tolerance_degrees=config["deduplication"]["orientation_tolerance_degrees"],
            minimum_overlap_ratio=config["deduplication"]["minimum_projected_overlap_ratio_of_shorter_segment"],
        )
        combined, _combined_obj = tile_tools._build_combined_result(
            deduplicated, source_width, source_height,
            endpoint_tolerance=config["deduplication"]["endpoint_clustering_tolerance_px"],
        )
        post_ms = (time.perf_counter() - post_started) * 1000
        pipeline_ms = (time.perf_counter() - pipeline_started) * 1000
        tile_runs.append({"local_result": local_dict, "mapped_result": mapped,
                          "raw_segments": raw_segments, "deduplicated": deduplicated,
                          "combined": combined})
        stage_timings.append({"tile_extract_png_encode_ms": prep_ms,
                              "detector_call_ms": detector_ms,
                              "coordinate_map_dedup_cluster_ms": post_ms,
                              "tile_pipeline_total_ms": pipeline_ms})
    if any(run["local_result"] != tile_runs[0]["local_result"] for run in tile_runs[1:]):
        raise RuntimeError("Target tile detector output was not deterministic across repeats")

    baseline = json.loads(BASELINE_PATH.read_text())
    original = next(item for item in baseline["images"] if item["input"]["filename"] == "test5.png")
    roi_results = json.loads(ROI_RESULTS_PATH.read_text())
    roi_image = next(item for item in roi_results["images"] if item["filename"] == "test5.png")
    previous_tiles = json.loads(TILE_RESULTS_PATH.read_text())
    prior_conditions = {
        "original": (original, original["measurement"]["runtime_ms_median"]),
        "full_roi": (roi_image["cropped"]["detector_result_original_coordinates"], roi_image["cropped"]["measurement"]["runtime_ms_median"]),
        "three_wide": (previous_tiles["configurations"]["three_wide"]["sensitivity"]["4"]["metrics_result"]
                       if "metrics_result" in previous_tiles["configurations"]["three_wide"]["sensitivity"]["4"] else
                       previous_tiles["configurations"]["three_wide"]["primary_reconstructed_candidate_result_original_coordinates"],
                       previous_tiles["configurations"]["three_wide"]["runtime"]["total_detector_runtime_ms_median"]),
        "four_narrow": (previous_tiles["configurations"]["four_narrow"]["primary_reconstructed_candidate_result_original_coordinates"],
                        previous_tiles["configurations"]["four_narrow"]["runtime"]["total_detector_runtime_ms_median"]),
    }
    # Existing tile results store metrics separately; use the preserved metric
    # objects for comparison rather than re-evaluating a different reference.
    prior_metric_objects = {
        "three_wide": previous_tiles["configurations"]["three_wide"]["sensitivity"]["4"]["metrics"],
        "four_narrow": previous_tiles["configurations"]["four_narrow"]["sensitivity"]["4"]["metrics"],
    }
    metrics = {}
    member_details = {}
    for name, (result, runtime) in prior_conditions.items():
        if name == "three_wide" or name == "four_narrow":
            metrics[name] = prior_metric_objects[name]
            result_dict = result
        else:
            result_dict = result
            metrics[name] = evaluate_image(result_dict, annotation)
        member_details[name] = _member_detail(result_dict, annotation, list(TARGET_IDS),
                                              member_coverage, maximum_cardinality_matches, inside_roi)

    target_run = tile_runs[0]
    target_metrics = evaluate_image(target_run["combined"], annotation)
    metrics["targeted"] = target_metrics
    member_details["targeted"] = _member_detail(target_run["combined"], annotation, list(TARGET_IDS),
                                                member_coverage, maximum_cardinality_matches, inside_roi)

    sensitivity = {}
    for tolerance in config["deduplication"]["sensitivity_tolerances_px"]:
        dedup = tile_tools.deduplicate_segments(
            target_run["raw_segments"],
            perpendicular_tolerance_px=tolerance,
            angle_tolerance_degrees=config["deduplication"]["orientation_tolerance_degrees"],
            minimum_overlap_ratio=config["deduplication"]["minimum_projected_overlap_ratio_of_shorter_segment"],
        )
        combined, _ = tile_tools._build_combined_result(dedup, source_width, source_height,
                                                        config["deduplication"]["endpoint_clustering_tolerance_px"])
        sensitivity[str(tolerance)] = {
            "candidate_line_count_after_deduplication": len(dedup),
            "removed_detection_count": len(target_run["raw_segments"]) - len(dedup),
            "metrics": evaluate_image(combined, annotation),
            "target_member_coverage": _member_detail(combined, annotation, list(TARGET_IDS),
                                                      member_coverage, maximum_cardinality_matches, inside_roi),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    tile_ok, tile_png = cv2.imencode(".png", source[tile["y"]:tile["bottom_exclusive"], tile["x"]:tile["right_exclusive"]])
    if not tile_ok:
        raise OSError("Could not encode the selected tile artifact")
    (output_dir / "tile.png").write_bytes(tile_png.tobytes())
    tile_overlay = json.loads(json.dumps(target_run["local_result"]))
    (output_dir / "tile_candidate_overlay.png").write_bytes(
        _render_local_overlay(source[tile["y"]:tile["bottom_exclusive"], tile["x"]:tile["right_exclusive"]],
                              tile_overlay, tile, ROOT / "backend"))
    _save_overlay(source, target_run["combined"], ambiguous, output_dir / "targeted_on_original.png")

    mapped_lines_with_provenance = []
    for merged in target_run["deduplicated"]:
        line = dict(merged)
        line["source_detections"] = merged["source_detections"]
        mapped_lines_with_provenance.append(line)
    summary = {
        "experiment": config["experiment"],
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {"path": source_config["path"], "sha256": source_sha, "mime_type": mime,
                   "width": source_width, "height": source_height},
        "reference_roi": roi,
        "tile": tile,
        "target_members": config["target_members"],
        "repeats": repeats,
        "detector": "unchanged default detect_candidate_geometry(image_bytes)",
        "opencv_version": cv2.__version__,
        "tile_detection": {
            "candidate_line_count_before_deduplication": len(target_run["raw_segments"]),
            "endpoint_cluster_count_before_deduplication": len(target_run["local_result"]["joints"]),
            "candidate_cap_reached": len(target_run["local_result"]["lines"]) == 300,
            "deterministic_across_repeats": True,
            "runtime_ms_median": statistics.median(stage["detector_call_ms"] for stage in stage_timings),
            "mapped_line_detections": target_run["raw_segments"],
            "mapped_joint_detections": [
                {"tile_id": tile["tile_id"], "joint_id": joint["id"],
                 "point": [joint["point"][0] + tile["x"], joint["point"][1] + tile["y"]],
                 "line_ids": joint["line_ids"], "endpoint_count": joint["endpoint_count"]}
                for joint in target_run["local_result"]["joints"]
            ],
        },
        "primary_deduplication": {
            "tolerance_px": config["deduplication"]["primary_perpendicular_tolerance_px"],
            "candidate_line_count_after_deduplication": len(target_run["deduplicated"]),
            "removed_detection_count": len(target_run["raw_segments"]) - len(target_run["deduplicated"]),
            "deduplicated_lines_with_provenance": mapped_lines_with_provenance,
        },
        "runtime_breakdown_ms_median": {
            "source_decode_once": source_decode_ms,
            "tile_extract_and_png_encode": statistics.median(stage["tile_extract_png_encode_ms"] for stage in stage_timings),
            "detector_call_only": statistics.median(stage["detector_call_ms"] for stage in stage_timings),
            "coordinate_map_dedup_cluster": statistics.median(stage["coordinate_map_dedup_cluster_ms"] for stage in stage_timings),
            "tile_pipeline_total_excluding_source_read_decode": statistics.median(stage["tile_pipeline_total_ms"] for stage in stage_timings),
            "per_repeat_stage_timings": stage_timings,
        },
        "comparison": {
            name: {
                "metrics": metrics[name],
                "target_member_coverage_and_endpoint_errors": member_details[name],
                "detector_runtime_ms_median": runtime,
                "runtime_boundary": "existing detector-call-only timing; prior tiled values sum detector calls per tile",
            }
            for name, (_result, runtime) in prior_conditions.items()
        } | {
            "targeted": {
                "metrics": target_metrics,
                "target_member_coverage_and_endpoint_errors": member_details["targeted"],
                "runtime_breakdown_ms_median": {
                    key: value for key, value in {
                        "tile_extract_and_png_encode": statistics.median(stage["tile_extract_png_encode_ms"] for stage in stage_timings),
                        "detector_call_only": statistics.median(stage["detector_call_ms"] for stage in stage_timings),
                        "coordinate_map_dedup_cluster": statistics.median(stage["coordinate_map_dedup_cluster_ms"] for stage in stage_timings),
                        "tile_pipeline_total_excluding_source_read_decode": statistics.median(stage["tile_pipeline_total_ms"] for stage in stage_timings),
                    }.items()
                },
            }
        },
        "deduplication_sensitivity": sensitivity,
        "ambiguous_crossings_excluded_from_joint_scoring": ambiguous,
        "annotation_sha256_unchanged": annotation["image"]["sha256"],
    }
    return summary


def _render_local_overlay(tile_image, local_result: dict, tile: dict, backend_root: Path) -> bytes:
    import cv2
    overlay = tile_image.copy()
    for line in local_result["lines"]:
        cv2.line(overlay, tuple(line["start"]), tuple(line["end"]), (0, 0, 235), 2, cv2.LINE_AA)
    for joint in local_result["joints"]:
        cv2.circle(overlay, tuple(round(value) for value in joint["point"]), 4, (30, 190, 40), -1, cv2.LINE_AA)
    # Mark ambiguous crossings that fall inside this tile, without asserting joints.
    for x, y in ((601, 843), (1032, 843), (1472, 843)):
        if tile["x"] <= x < tile["right_exclusive"] and tile["y"] <= y < tile["bottom_exclusive"]:
            cv2.circle(overlay, (x - tile["x"], y - tile["y"]), 9, (0, 140, 255), 2, cv2.LINE_AA)
    ok, png = cv2.imencode(".png", overlay)
    if not ok:
        raise OSError("Could not encode local tile overlay")
    return png.tobytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    out = args.output_dir.resolve()
    results = run(args.config.resolve(), out, args.repeats)
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"Target tile: {results['tile_detection']['candidate_line_count_before_deduplication']} lines; "
          f"clusters={results['tile_detection']['endpoint_cluster_count_before_deduplication']}; "
          f"cap={results['tile_detection']['candidate_cap_reached']}; "
          f"P/R={results['comparison']['targeted']['metrics']['joint_precision']:.4f}/"
          f"{results['comparison']['targeted']['metrics']['joint_recall']:.4f}")
    for member_id, detail in results["comparison"]["targeted"]["target_member_coverage_and_endpoint_errors"].items():
        print(f"{member_id}: coverage={detail['coverage_fraction']:.4f}; recovered={detail['recovered_at_80_percent']}")
    print(f"Results: {out / 'results.json'}")


if __name__ == "__main__":
    main()
