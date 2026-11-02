"""Offline staged Canny/Hough sweep; production detector defaults stay unchanged."""
from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
import math
import statistics
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
BASE = ROOT / "evaluation/results/phase-a-2026-10-30"
OUT = BASE / "adaptive-canny-hough-sweep-2026-10-30"
INPUT = BACKEND / "evaluation/sketches"
ANNOTATIONS = BASE / "annotations"
BASELINE_PATH = BASE / "detector-baseline/baseline.json"
ROI_RESULTS = BASE / "roi-crop-experiment/results.json"
TILE_CONFIG = BASE / "overlapping-tile-experiment-2026-10-30/tile_config.json"
TARGET_TILE_CONFIG = BASE / "rightmost-bay-targeted-tile-2026-10-30/tile_config.json"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "evaluation"))

from app.services.perception import PerceptionConfig, detect_candidate_geometry, render_detections
from perception_evaluation import evaluate_image, _member_coverage, validate_annotation
from run_overlapping_tile_experiment import _build_combined_result, deduplicate_segments, map_segment_to_original

REPEATS = 5
CONTROL = PerceptionConfig()
CANNY_SETTINGS = {
    "control": {"canny_sigma": 0.8, "canny_min_threshold": 40, "canny_max_threshold": 160},
    "canny_low": {"canny_sigma": 0.8, "canny_min_threshold": 20, "canny_max_threshold": 120},
    "canny_high": {"canny_sigma": 0.8, "canny_min_threshold": 60, "canny_max_threshold": 220},
}
HOUGH_SETTINGS = {
    "control": {},
    "hough_vote_low": {"hough_threshold": 20},
    "hough_short_lines": {"min_line_length": 12.0},
    "hough_long_gap": {"max_line_gap": 12.0},
}


def _png_bytes(image):
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("PNG encoding failed")
    return encoded.tobytes()


def _evaluate(image_record, annotation):
    return evaluate_image(image_record, annotation)


def _member_fractions(image_record, annotation):
    nodes = {node["id"]: node for node in annotation["joints"]}
    lines = [(line["start"], line["end"]) for line in image_record["lines"]]
    diagonal = math.hypot(annotation["image"]["width"], annotation["image"]["height"])
    corridor = max(12.0, .0075 * diagonal)
    output = {}
    for member in annotation["members"]:
        if member["status"] != "confirmed":
            continue
        a, b = nodes[member["node_i"]], nodes[member["node_j"]]
        output[member["id"]] = _member_coverage(((a["x"], a["y"]), (b["x"], b["y"])), lines, corridor, 8.0)
    return output


def _record(result, timings, payload, filename, sha256):
    item = result.to_dict()
    item["input"] = {"filename": filename, "sha256": sha256, "image_width": result.image_width, "image_height": result.image_height}
    item["measurement"] = {
        "repeat_count": len(timings),
        "runtime_ms_median": statistics.median(timings),
        "runtime_ms_min": min(timings),
        "runtime_ms_max": max(timings),
        "runtime_ms_each_repeat": timings,
        "deterministic_across_repeats": True,
        "candidate_cap_reached": len(result.lines) == 300,
        "candidate_line_count": len(result.lines),
        "endpoint_cluster_count": len(result.joints),
        "raw_hough_segment_count": result.diagnostics["raw_hough_segment_count"],
        "edge_pixel_count": result.diagnostics["edge_pixel_count"],
        "retained_to_raw_hough_ratio": len(result.lines) / max(1, result.diagnostics["raw_hough_segment_count"]),
        "canny_lower_used": item["settings"]["canny_lower_used"],
        "canny_upper_used": item["settings"]["canny_upper_used"],
    }
    return item


def _run_detector(payload, config, repeats, filename, digest):
    results, timings = [], []
    for _ in range(repeats):
        started = time.perf_counter()
        result = detect_candidate_geometry(payload, config)
        timings.append((time.perf_counter() - started) * 1000)
        results.append(result)
    if any(result != results[0] for result in results[1:]):
        raise RuntimeError(f"Non-deterministic detector output for {filename}")
    return _record(results[0], timings, payload, filename, digest), results[0]


def _make_configs():
    configs = {"control": CONTROL}
    for name, changes in CANNY_SETTINGS.items():
        if name != "control":
            configs[name] = replace(CONTROL, **changes)
    return configs


def _config_summary(configs):
    return {name: {"stage": "canny_control" if name in CANNY_SETTINGS else "hough_sweep", "parameters": asdict(config)} for name, config in configs.items()}


def _score_config(records, annotations):
    image_metrics = []
    for filename, image in records.items():
        annotation = annotations[filename]
        metric = _evaluate(image, annotation)
        metric["member_coverage_fraction_by_id"] = _member_fractions(image, annotation)
        image_metrics.append(metric)
    included = [metric for metric in image_metrics if metric.get("metrics_status") in {"available", "partial"}]
    tp = sum(metric["matched_joints"] for metric in included)
    predicted = sum(metric["detected_candidate_joints_in_roi"] for metric in included)
    references = sum(metric["confirmed_reference_joint_count"] for metric in included)
    matched = sum(metric["matched_joints"] for metric in included)
    members = sum(metric["confirmed_reference_member_count"] for metric in included)
    covered = sum(metric["members_with_at_least_80_percent_candidate_line_coverage"] for metric in included)
    endpoint_sum = sum((metric["matched_joint_endpoint_error_px_mean"] or 0.0) * metric["matched_joints"] for metric in included)
    aggregate = {
        "metrics_status": "exploratory_micro_average",
        "included_images": [metric["filename"] for metric in included],
        "excluded_images": [metric["filename"] for metric in image_metrics if metric not in included],
        "joint_precision": tp / predicted if predicted else None,
        "joint_recall": tp / references if references else None,
        "matched_joint_endpoint_error_px_mean": endpoint_sum / matched if matched else None,
        "member_coverage_recall": covered / members if members else None,
        "member_precision": None,
        "member_precision_unavailable_reason": "The detector does not emit semantic member hypotheses.",
        "note": "Same Phase A micro-average formula; zero-match images contribute no endpoint-error sum.",
    }
    return {"aggregate": aggregate, "images": image_metrics}


def _parse_saved_baseline():
    saved = json.loads(BASELINE_PATH.read_text())
    return {item["input"]["filename"]: item for item in saved["images"]}


def _run_test5_contexts(config, condition_name):
    """Run the unchanged ROI/tile layouts with a supplied detector config."""
    source_path = INPUT / "test5.png"
    source_bytes = source_path.read_bytes()
    source = cv2.imdecode(np.frombuffer(source_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    annotation = json.loads((ANNOTATIONS / "test5.json").read_text())
    roi_cfg = json.loads((BASE / "roi-crop-experiment/roi_config.json").read_text())
    roi = roi_cfg["images"]["test5.png"]["roi"]
    x, y, width, height = roi["x"], roi["y"], roi["width"], roi["height"]

    contexts = {}
    roi_crop = source[y:y + height, x:x + width]
    roi_payload = _png_bytes(roi_crop)
    roi_item, roi_obj = _run_detector(roi_payload, config, REPEATS, "test5.png:full_roi", hashlib.sha256(source_bytes).hexdigest())
    roi_item["image_width"], roi_item["image_height"] = source.shape[1], source.shape[0]
    for line in roi_item["lines"]:
        line["start"] = [line["start"][0] + x, line["start"][1] + y]
        line["end"] = [line["end"][0] + x, line["end"][1] + y]
    for joint in roi_item["joints"]:
        joint["point"] = [joint["point"][0] + x, joint["point"][1] + y]
    roi_obj_lines = [{"id": line.id, "start": (line.start[0] + x, line.start[1] + y), "end": (line.end[0] + x, line.end[1] + y), "length_px": line.length_px, "evidence": line.evidence} for line in roi_obj.lines]
    from app.services.perception import CandidateLine, PerceptionResult, _cluster_endpoints
    roi_candidates = tuple(CandidateLine(id=line["id"], start=tuple(line["start"]), end=tuple(line["end"]), length_px=line["length_px"], evidence=line["evidence"]) for line in roi_obj_lines)
    roi_result_obj = PerceptionResult(source.shape[1], source.shape[0], "image_pixels", roi_candidates, _cluster_endpoints(roi_candidates, config.endpoint_tolerance), roi_item["settings"], tuple(roi_item["warnings"]), roi_item["diagnostics"])
    contexts["full_roi"] = {"image": roi_item, "object": roi_result_obj, "runtime_breakdown_ms": {"tile_extraction_and_png_encoding": None, "detector_call_only_median": roi_item["measurement"]["runtime_ms_median"], "map_and_cluster": None}}

    tile_config = json.loads(TILE_CONFIG.read_text())
    layout_results = {}
    from run_overlapping_tile_experiment import _validate_tile_config
    _validate_tile_config(tile_config["roi"], tile_config["configurations"])
    for layout_name, layout in tile_config["configurations"].items():
        mapped, tile_records, detector_repeat_timings = [], [], []
        extraction_timings = []
        for index, origin in enumerate(layout["origins_original_pixels"], start=1):
            ox, oy = origin
            started = time.perf_counter()
            crop = source[oy:oy + layout["tile_height"], ox:ox + layout["tile_width"]]
            payload = _png_bytes(crop)
            extraction_timings.append((time.perf_counter() - started) * 1000)
            item, obj = _run_detector(payload, config, REPEATS, f"{layout_name}-T{index:02d}", hashlib.sha256(source_bytes).hexdigest())
            detector_repeat_timings.append(item["measurement"]["runtime_ms_each_repeat"])
            tile_id = f"{layout_name}-T{index:02d}"
            tile_records.append({"tile_id": tile_id, "origin": origin, "candidate_lines": len(item["lines"]), "endpoint_clusters": len(item["joints"]), "cap_reached": item["measurement"]["candidate_cap_reached"], "runtime_ms_median": item["measurement"]["runtime_ms_median"]})
            for line in item["lines"]:
                source_line = {"id": line["id"], "line_id": line["id"], "tile_id": tile_id, "tile_origin": origin, "start": line["start"], "end": line["end"], "length_px": line["length_px"], "evidence": line["evidence"]}
                mapped.append(map_segment_to_original(source_line, ox, oy))
        started = time.perf_counter()
        combined = deduplicate_segments(mapped, perpendicular_tolerance_px=tile_config["deduplication"]["primary_perpendicular_tolerance_px"], angle_tolerance_degrees=tile_config["deduplication"]["orientation_tolerance_degrees"], minimum_overlap_ratio=tile_config["deduplication"]["minimum_projected_overlap_ratio_of_shorter_segment"])
        image, obj = _build_combined_result(combined, source.shape[1], source.shape[0], config.endpoint_tolerance)
        post_ms = (time.perf_counter() - started) * 1000
        image["input"] = {"filename": "test5.png", "sha256": hashlib.sha256(source_bytes).hexdigest()}
        detector_pass_sums = [sum(tile_runs[repeat] for tile_runs in detector_repeat_timings) for repeat in range(REPEATS)]
        detector_median = statistics.median(detector_pass_sums)
        extraction_total = sum(extraction_timings)
        image["measurement"] = {"candidate_line_count": len(image["lines"]), "endpoint_cluster_count": len(image["joints"]), "candidate_cap_reached": any(tile["cap_reached"] for tile in tile_records), "raw_tile_lines_before_deduplication": len(mapped), "runtime_ms_detector_calls_only_median_of_per_pass_sums": detector_median, "runtime_ms_detector_call_pass_sums": detector_pass_sums, "runtime_ms_tile_extract_and_encode_once": extraction_total, "runtime_ms_dedup_cluster_once": post_ms, "runtime_ms_pipeline_estimate_excluding_source_decode": extraction_total + detector_median + post_ms}
        layout_results[layout_name] = {"image": image, "object": obj, "tiles": tile_records, "deduplicated_segments": combined}
    contexts.update({"three_wide": layout_results["three_wide"], "four_narrow": layout_results["four_narrow"]})
    target_cfg = json.loads(TARGET_TILE_CONFIG.read_text())["tile"]
    tx, ty = target_cfg["x"], target_cfg["y"]
    started = time.perf_counter()
    target_crop = source[ty:ty + target_cfg["height"], tx:tx + target_cfg["width"]]
    target_payload = _png_bytes(target_crop)
    target_encode_ms = (time.perf_counter() - started) * 1000
    target_item, target_obj_local = _run_detector(target_payload, config, REPEATS, "targeted_tile-T01", hashlib.sha256(source_bytes).hexdigest())
    from app.services.perception import CandidateLine, PerceptionResult, _cluster_endpoints
    map_started = time.perf_counter()
    target_lines = tuple(CandidateLine(line.id, (line.start[0] + tx, line.start[1] + ty), (line.end[0] + tx, line.end[1] + ty), line.length_px, line.evidence) for line in target_obj_local.lines)
    target_obj = PerceptionResult(source.shape[1], source.shape[0], "image_pixels", target_lines, _cluster_endpoints(target_lines, config.endpoint_tolerance), target_item["settings"], tuple(target_item["warnings"]), target_item["diagnostics"])
    target_map_cluster_ms = (time.perf_counter() - map_started) * 1000
    target_item["image_width"], target_item["image_height"] = source.shape[1], source.shape[0]
    for line in target_item["lines"]:
        line["start"] = [line["start"][0] + tx, line["start"][1] + ty]
        line["end"] = [line["end"][0] + tx, line["end"][1] + ty]
    for joint in target_item["joints"]:
        joint["point"] = [joint["point"][0] + tx, joint["point"][1] + ty]
    target_item["measurement"]["tile_extract_and_encode_once_ms"] = target_encode_ms
    target_item["measurement"]["map_and_cluster_once_ms"] = target_map_cluster_ms
    contexts["targeted_tile"] = {"image": target_item, "object": target_obj, "runtime_breakdown_ms": {"tile_extract_and_png_encode_once": target_encode_ms, "detector_call_only_median": target_item["measurement"]["runtime_ms_median"], "map_and_cluster_once": target_map_cluster_ms, "pipeline_estimate_excluding_source_decode": target_encode_ms + target_item["measurement"]["runtime_ms_median"] + target_map_cluster_ms}}
    for name, context in contexts.items():
        metric = _evaluate(context["image"], annotation)
        metric["member_coverage_fraction_by_id"] = _member_fractions(context["image"], annotation)
        context["metrics"] = metric
    return contexts


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    image_paths = sorted(path for path in INPUT.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"})
    baseline_saved = _parse_saved_baseline()
    annotations = {}
    sources = {}
    for path in image_paths:
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        annotation_path = ANNOTATIONS / f"{path.stem}.json"
        annotation = json.loads(annotation_path.read_text())
        validate_annotation(annotation)
        if annotation["image"]["sha256"] != digest or baseline_saved[path.name]["input"]["sha256"] != digest:
            raise ValueError(f"Source hash mismatch for {path.name}")
        if annotation["image"]["width"] != baseline_saved[path.name]["image_width"] or annotation["image"]["height"] != baseline_saved[path.name]["image_height"]:
            raise ValueError(f"Source dimensions mismatch for {path.name}")
        annotations[path.name] = annotation
        sources[path.name] = {"path": str(path.relative_to(ROOT)), "sha256": digest, "width": annotation["image"]["width"], "height": annotation["image"]["height"]}

    configs = _make_configs()
    config_records = {}
    records_by_config = {}
    objects_by_config = {}
    # Stage 1: Canny bands only; all Hough settings stay at the production default.
    for name, config in configs.items():
        records_by_config[name], objects_by_config[name] = {}, {}
        config_records[name] = {"parameters": asdict(config), "stage": "canny_sweep", "parent": "control", "changed_parameters": sorted(k for k in asdict(config) if asdict(config)[k] != asdict(CONTROL)[k])}
        for path in image_paths:
            payload = path.read_bytes()
            image, obj = _run_detector(payload, config, REPEATS, path.name, sources[path.name]["sha256"])
            records_by_config[name][path.name] = image
            objects_by_config[name][path.name] = obj

    stage1_scores = {name: _score_config(records, annotations) for name, records in records_by_config.items()}
    alternate_names = ["canny_low", "canny_high"]
    # One global alternate Canny choice: confirmed-graph micro coverage, then
    # precision, recall, and line-cap rate; no image-specific selection.
    alt_canny = max(alternate_names, key=lambda name: (
        stage1_scores[name]["aggregate"]["member_coverage_recall"] or 0,
        stage1_scores[name]["aggregate"]["joint_precision"] or 0,
        stage1_scores[name]["aggregate"]["joint_recall"] or 0,
        -sum(image["measurement"]["candidate_cap_reached"] for image in records_by_config[name].values()),
    ))

    # Stage 2: vary one Hough parameter at a time for control and selected Canny.
    stage2_parent_names = ["control", alt_canny]
    for parent_name in stage2_parent_names:
        parent = configs[parent_name]
        for hough_name, changes in HOUGH_SETTINGS.items():
            if hough_name == "control":
                continue
            config_name = f"{parent_name}__{hough_name}"
            config = replace(parent, **changes)
            configs[config_name] = config
            config_records[config_name] = {"parameters": asdict(config), "stage": "hough_one_factor", "parent": parent_name, "changed_parameters": sorted(changes)}
            records_by_config[config_name], objects_by_config[config_name] = {}, {}
            for path in image_paths:
                payload = path.read_bytes()
                image, obj = _run_detector(payload, config, REPEATS, path.name, sources[path.name]["sha256"])
                records_by_config[config_name][path.name] = image
                objects_by_config[config_name][path.name] = obj

    scores = {name: _score_config(records, annotations) for name, records in records_by_config.items()}
    control_aggregate = scores["control"]["aggregate"]

    def defensible(name):
        agg = scores[name]["aggregate"]
        if name == "control":
            return False
        # Strict evidence bar: coverage must rise, aggregate joint precision may
        # not fall, recall may not fall, cap status may not worsen, and no
        # confirmed image can lose more than one reference member to 80%-coverage.
        if (agg["member_coverage_recall"] or 0) <= (control_aggregate["member_coverage_recall"] or 0):
            return False
        if (agg["joint_precision"] or 0) < (control_aggregate["joint_precision"] or 0):
            return False
        if (agg["joint_recall"] or 0) < (control_aggregate["joint_recall"] or 0):
            return False
        control_caps = sum(r["measurement"]["candidate_cap_reached"] for r in records_by_config["control"].values())
        candidate_caps = sum(r["measurement"]["candidate_cap_reached"] for r in records_by_config[name].values())
        if candidate_caps > control_caps:
            return False
        base_by_image = {r["filename"]: r for r in scores["control"]["images"]}
        cand_by_image = {r["filename"]: r for r in scores[name]["images"]}
        return all(cand_by_image[key]["members_with_at_least_80_percent_candidate_line_coverage"] >= base_by_image[key]["members_with_at_least_80_percent_candidate_line_coverage"] - 1 for key in base_by_image if "members_with_at_least_80_percent_candidate_line_coverage" in base_by_image[key])

    qualifying = [name for name in scores if defensible(name)]
    # Report the strongest coverage candidate regardless of qualification for
    # transparent comparison, and separately nominate only a qualifying choice.
    strongest_coverage = max((name for name in scores if name != "control"), key=lambda n: (scores[n]["aggregate"]["member_coverage_recall"] or 0, scores[n]["aggregate"]["joint_precision"] or 0))
    selected = max(qualifying, key=lambda n: (scores[n]["aggregate"]["member_coverage_recall"], scores[n]["aggregate"]["joint_precision"], -statistics.median([r["measurement"]["runtime_ms_median"] for r in records_by_config[n].values()]))) if qualifying else None
    compare_name = selected or strongest_coverage
    compare_contexts = _run_test5_contexts(configs[compare_name], compare_name)
    control_contexts = _run_test5_contexts(CONTROL, "control")

    # Baseline reproduction differences: compare deterministic geometry output,
    # not wall-clock timing, against frozen Phase A records.
    baseline_differences = {}
    for filename in records_by_config["control"]:
        fresh, saved = records_by_config["control"][filename], baseline_saved[filename]
        baseline_differences[filename] = {
            "saved_candidate_lines": len(saved["lines"]), "fresh_candidate_lines": len(fresh["lines"]),
            "saved_endpoint_clusters": len(saved["joints"]), "fresh_endpoint_clusters": len(fresh["joints"]),
            "line_geometry_identical": [(x["start"], x["end"]) for x in saved["lines"]] == [(x["start"], x["end"]) for x in fresh["lines"]],
            "joint_geometry_identical": [x["point"] for x in saved["joints"]] == [x["point"] for x in fresh["joints"]],
        }

    results = {
        "experiment": "phase-a-adaptive-canny-hough-parameter-sweep-2026-10-30",
        "source_images": sources,
        "opencv_version": cv2.__version__,
        "repeat_count_per_detector_condition": REPEATS,
        "scoring": "Unchanged Phase A evaluator (8 degree angle, max(12 px, 0.75% diagonal) joint/corridor, 80% member threshold). test2 remains unscored.",
        "source_hash_validation": "All five source hashes matched both saved Phase A baseline and annotation records.",
        "baseline_reproduction_differences": baseline_differences,
        "stage1_canny_scores": stage1_scores,
        "stage2_scores": {name: scores[name] for name in scores if name not in stage1_scores},
        "all_configuration_scores": scores,
        "tested_configurations": config_records,
        "detection_summaries_by_configuration": {
            name: {
                filename: {
                    "candidate_line_count": record["measurement"]["candidate_line_count"],
                    "endpoint_cluster_count": record["measurement"]["endpoint_cluster_count"],
                    "candidate_lines_per_endpoint_cluster": record["measurement"]["candidate_line_count"] / max(1, record["measurement"]["endpoint_cluster_count"]),
                    "candidate_cap_reached": record["measurement"]["candidate_cap_reached"],
                    "raw_hough_segment_count": record["measurement"]["raw_hough_segment_count"],
                    "edge_pixel_count": record["measurement"]["edge_pixel_count"],
                    "retained_to_raw_hough_ratio": record["measurement"]["retained_to_raw_hough_ratio"],
                    "runtime_ms_median": record["measurement"]["runtime_ms_median"],
                    "runtime_ms_min": record["measurement"]["runtime_ms_min"],
                    "runtime_ms_max": record["measurement"]["runtime_ms_max"],
                    "canny_lower_used": record["measurement"]["canny_lower_used"],
                    "canny_upper_used": record["measurement"]["canny_upper_used"],
                }
                for filename, record in records.items()
            }
            for name, records in records_by_config.items()
        },
        "stage2_selected_alternate_canny": alt_canny,
        "selection_rule": {"qualification": "member micro-recall strictly above control; joint precision and recall no lower; no increase in capped image count; per annotated image no more than one recovered-member loss", "selected_configuration": selected, "strongest_coverage_configuration_even_if_not_qualified": strongest_coverage, "comparison_configuration_for_roi_and_tiles": compare_name, "qualifying_configurations": qualifying},
        "test5_existing_context_comparison": {"control": {name: {"metrics": item["metrics"], "measurement": item["image"]["measurement"], "tiles": item.get("tiles")} for name, item in control_contexts.items()}, "experimental": {name: {"metrics": item["metrics"], "measurement": item["image"]["measurement"], "tiles": item.get("tiles")} for name, item in compare_contexts.items()}, "experimental_config": compare_name},
    }
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    machine_config = {
        "experiment": results["experiment"], "fixed_preprocessing": {"grayscale": "OpenCV BGR2GRAY", "gaussian_blur": [5, 5], "sigma": 0, "image_resize": False},
        "repeat_count": REPEATS, "current_production_config": asdict(CONTROL),
        "stage1_canny_variants": {name: {**asdict(CONTROL), **values} for name, values in CANNY_SETTINGS.items()},
        "stage2_hough_one_factor_variants": HOUGH_SETTINGS,
        "tested_configurations": config_records,
        "selection": results["selection_rule"], "source_images": sources,
        "evaluation": {"annotations_directory": "evaluation/results/phase-a-2026-10-30/annotations", "joint_tolerance": "max(12 px, 0.75% image diagonal)", "member_corridor": "max(12 px, 0.75% image diagonal)", "angle_tolerance_degrees": 8, "member_coverage_threshold": .8},
    }
    (OUT / "experiment_config.json").write_text(json.dumps(machine_config, indent=2) + "\n")

    # Store comparable full-image overlays for every annotated-source baseline
    # and the selected/strongest experimental setting.
    for config_name in {"control", compare_name}:
        for filename in records_by_config[config_name]:
            path = INPUT / filename
            payload = path.read_bytes()
            (OUT / "overlays" / config_name).mkdir(parents=True, exist_ok=True)
            (OUT / "overlays" / config_name / f"{Path(filename).stem}_full_image.png").write_bytes(render_detections(payload, objects_by_config[config_name][filename]))
    source_payload = (INPUT / "test5.png").read_bytes()
    for config_name, contexts in (("control", control_contexts), (compare_name, compare_contexts)):
        for context_name, context in contexts.items():
            (OUT / "overlays" / config_name).mkdir(parents=True, exist_ok=True)
            (OUT / "overlays" / config_name / f"test5_{context_name}.png").write_bytes(render_detections(source_payload, context["object"]))
    print(json.dumps({"stage2_alternate_canny": alt_canny, "qualifying": qualifying, "selected": selected, "strongest_coverage": strongest_coverage, "compare": compare_name, "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    run()
