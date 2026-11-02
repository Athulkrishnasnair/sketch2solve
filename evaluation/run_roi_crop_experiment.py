"""Run a default-detector comparison on original images and fixed ROI crops.

This experiment does not alter detector settings. Crop coordinates are recorded
in the companion roi_config.json before the detector is run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "evaluation/results/phase-a-2026-10-30/roi-crop-experiment/roi_config.json"
ANNOTATIONS = ROOT / "evaluation/results/phase-a-2026-10-30/annotations"


def crop_bounds(image_width: int, image_height: int, roi: dict) -> tuple[int, int, int, int]:
    """Validate an in-bounds x/y/width/height ROI and return exclusive bounds."""
    if not isinstance(roi, dict) or set(roi) != {"x", "y", "width", "height"}:
        raise ValueError("ROI must contain exactly x, y, width, and height")
    values = [roi[key] for key in ("x", "y", "width", "height")]
    if any(type(value) is not int for value in values):
        raise ValueError("ROI coordinates and dimensions must be integers")
    x, y, width, height = values
    if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > image_width or y + height > image_height:
        raise ValueError("ROI must be a positive, in-bounds rectangle")
    return x, y, x + width, y + height


def translate_result_to_original(result: dict, offset_x: int, offset_y: int,
                                  original_width: int, original_height: int) -> dict:
    """Return a detector JSON object with crop-local points shifted to source pixels."""
    if type(offset_x) is not int or type(offset_y) is not int:
        raise ValueError("crop offsets must be integers")
    translated = json.loads(json.dumps(result))
    for line in translated["lines"]:
        line["start"] = [line["start"][0] + offset_x, line["start"][1] + offset_y]
        line["end"] = [line["end"][0] + offset_x, line["end"][1] + offset_y]
    for joint in translated["joints"]:
        joint["point"] = [joint["point"][0] + offset_x, joint["point"][1] + offset_y]
    translated["image_width"] = original_width
    translated["image_height"] = original_height
    translated["coordinate_space"] = "image_pixels"
    return translated


def _measure(payload: bytes, detect, repeats: int) -> tuple[dict, dict]:
    timings, results = [], []
    for _ in range(repeats):
        started = time.perf_counter()
        result = detect(payload)
        timings.append((time.perf_counter() - started) * 1000)
        results.append(result)
    if any(result != results[0] for result in results[1:]):
        raise RuntimeError("Non-deterministic detector output across repeated runs")
    result = results[0]
    return result.to_dict(), {
        "run_count": repeats,
        "runtime_ms_median": statistics.median(timings),
        "runtime_ms_min": min(timings),
        "runtime_ms_max": max(timings),
        "deterministic_across_runs": True,
        "candidate_cap_reached": len(result.lines) == 300,
        "endpoint_cluster_count": len(result.joints),
    }


def _save_projected_overlay(source, transformed_result: dict, path: Path) -> None:
    overlay = source.copy()
    for line in transformed_result["lines"]:
        cv2.line(overlay, tuple(line["start"]), tuple(line["end"]), (0, 0, 255), 2, cv2.LINE_AA)
    for joint in transformed_result["joints"]:
        point = tuple(round(value) for value in joint["point"])
        cv2.circle(overlay, point, 4, (255, 80, 0), -1, cv2.LINE_AA)
    if not cv2.imwrite(str(path), overlay):
        raise OSError(f"Could not write overlay {path}")


def run(config_path: Path, output_dir: Path, repeats: int) -> dict:
    backend_dir = ROOT / "backend"
    sys.path.insert(0, str(backend_dir))
    sys.path.insert(0, str(ROOT / "evaluation"))
    from app.services.perception import detect_candidate_geometry, inspect_image_header, render_detections
    from perception_evaluation import evaluate_image, validate_annotation

    config = json.loads(config_path.read_text())
    if config.get("resize") is not False:
        raise ValueError("This experiment expects unchanged crop dimensions; resizing is disabled")
    output_dir.mkdir(parents=True, exist_ok=True)
    images = []
    for filename in ("test2.jpg", "test5.png"):
        image_config = config["images"][filename]
        source_path = ROOT / image_config["source"]
        payload = source_path.read_bytes()
        width, height, mime = inspect_image_header(payload)
        if (width, height) != (image_config["width"], image_config["height"]):
            raise ValueError(f"{filename}: configured source dimensions do not match image")
        decoded = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
        if decoded is None or decoded.shape[:2] != (height, width):
            raise ValueError(f"{filename}: source could not be decoded at configured dimensions")
        x0, y0, x1, y1 = crop_bounds(width, height, image_config["roi"])
        cropped = decoded[y0:y1, x0:x1]
        ok, encoded = cv2.imencode(".png", cropped)
        if not ok:
            raise RuntimeError(f"{filename}: crop PNG encoding failed")
        crop_payload = encoded.tobytes()

        original_result, original_measurement = _measure(payload, detect_candidate_geometry, repeats)
        crop_local_result, crop_measurement = _measure(crop_payload, detect_candidate_geometry, repeats)
        crop_transformed = translate_result_to_original(crop_local_result, x0, y0, width, height)

        image_dir = output_dir / Path(filename).stem
        image_dir.mkdir(parents=True, exist_ok=True)
        (image_dir / "crop.png").write_bytes(crop_payload)
        (image_dir / "original_candidate_overlay.png").write_bytes(render_detections(payload, _result_object(original_result)))
        (image_dir / "crop_candidate_overlay_local.png").write_bytes(render_detections(crop_payload, _result_object(crop_local_result)))
        _save_projected_overlay(decoded, crop_transformed, image_dir / "crop_candidates_on_original.png")

        metrics = None
        annotation_file = ANNOTATIONS / f"{Path(filename).stem}.json"
        annotation = json.loads(annotation_file.read_text())
        validate_annotation(annotation)
        if filename == "test5.png":
            if crop_transformed["image_width"] != annotation["image"]["width"] or crop_transformed["image_height"] != annotation["image"]["height"]:
                raise ValueError("Translated crop result dimensions do not match annotation source")
            metrics = {
                "original": evaluate_image(original_result, annotation),
                "cropped": evaluate_image(crop_transformed, annotation),
            }
        else:
            metrics = {
                "status": "unavailable",
                "reason": "test2 has no trustworthy single-graph reference; no accuracy metrics are reported.",
            }
        images.append({
            "filename": filename,
            "source": {
                "path": image_config["source"],
                "sha256": hashlib.sha256(payload).hexdigest(),
                "mime_type": mime,
                "width": width,
                "height": height,
            },
            "crop": {
                **image_config["roi"],
                "right_exclusive": x1,
                "bottom_exclusive": y1,
                "width": x1 - x0,
                "height": y1 - y0,
                "resize": False,
                "encoding": "PNG from decoded source raster",
                "coordinate_transform": {"original_x": "crop_x + local_x", "original_y": "crop_y + local_y"},
            },
            "original": {
                "candidate_line_count": len(original_result["lines"]),
                "endpoint_cluster_count": len(original_result["joints"]),
                "measurement": original_measurement,
                "detector_result_original_coordinates": original_result,
            },
            "cropped": {
                "candidate_line_count": len(crop_local_result["lines"]),
                "endpoint_cluster_count": len(crop_local_result["joints"]),
                "measurement": crop_measurement,
                "detector_result_crop_local_coordinates": crop_local_result,
                "detector_result_original_coordinates": crop_transformed,
            },
            "metrics": metrics,
            "overlay_paths": {
                "original": str((image_dir / "original_candidate_overlay.png").relative_to(output_dir)),
                "crop_local": str((image_dir / "crop_candidate_overlay_local.png").relative_to(output_dir)),
                "crop_on_original": str((image_dir / "crop_candidates_on_original.png").relative_to(output_dir)),
                "crop_image": str((image_dir / "crop.png").relative_to(output_dir)),
            },
        })
    return {
        "experiment": config["experiment"],
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "repeats_per_condition": repeats,
        "measurement_procedure": "perf_counter around detect_candidate_geometry(image_bytes), median of repeated calls, matching the Phase A runner",
        "detector": "unchanged default app.services.perception.detect_candidate_geometry(image_bytes)",
        "opencv_version": cv2.__version__,
        "config_path": str(config_path.relative_to(ROOT)),
        "images": images,
        "interpretation_note": "Counts and runtimes are measured. Accuracy is reported only for test5's fixed annotated ROI. Fewer lines alone do not establish improved truss detection.",
    }


def _result_object(serialized: dict):
    """Reconstruct the frozen result container for the existing PNG renderer."""
    from app.services.perception import CandidateJoint, CandidateLine, PerceptionResult

    return PerceptionResult(
        image_width=serialized["image_width"],
        image_height=serialized["image_height"],
        coordinate_space=serialized["coordinate_space"],
        lines=tuple(CandidateLine(
            id=line["id"], start=tuple(line["start"]), end=tuple(line["end"]),
            length_px=line["length_px"], evidence=line["evidence"],
        ) for line in serialized["lines"]),
        joints=tuple(CandidateJoint(
            id=joint["id"], point=tuple(joint["point"]), evidence=joint["evidence"],
            line_ids=tuple(joint["line_ids"]), endpoint_count=joint["endpoint_count"],
        ) for joint in serialized["joints"]),
        settings=serialized["settings"],
        warnings=tuple(serialized["warnings"]),
        diagnostics=serialized["diagnostics"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    result = run(args.config.resolve(), args.output_dir.resolve(), args.repeats)
    output = args.output_dir / "results.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    for image in result["images"]:
        print(f"{image['filename']}: lines {image['original']['candidate_line_count']} -> {image['cropped']['candidate_line_count']}; "
              f"clusters {image['original']['endpoint_cluster_count']} -> {image['cropped']['endpoint_cluster_count']}; "
              f"cap {image['original']['measurement']['candidate_cap_reached']} -> {image['cropped']['measurement']['candidate_cap_reached']}; "
              f"median_ms {image['original']['measurement']['runtime_ms_median']:.3f} -> "
              f"{image['cropped']['measurement']['runtime_ms_median']:.3f}")
        if image["filename"] == "test5.png":
            for mode in ("original", "cropped"):
                metrics = image["metrics"][mode]
                print(f"  {mode}: joint P/R={metrics['joint_precision']:.4f}/{metrics['joint_recall']:.4f}; "
                      f"endpoint mean={metrics['matched_joint_endpoint_error_px_mean']}; "
                      f"member coverage={metrics['members_with_at_least_80_percent_candidate_line_coverage']}/"
                      f"{metrics['confirmed_reference_member_count']} ({metrics['member_coverage_recall']:.4f})")
    print(f"Results: {output}")


if __name__ == "__main__":
    main()
