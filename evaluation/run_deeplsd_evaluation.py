"""Evaluate DeepLSD pretrained model on the five evaluation sketches.

Preserves the existing Phase A evaluation methodology and scoring gates.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import statistics
import time

import cv2
import numpy as np
import torch
from deeplsd.models.deeplsd_inference import DeepLSD

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SKETCHES_DIR = BACKEND / "evaluation/sketches"
ANNOTATIONS_DIR = ROOT / "evaluation/results/phase-a-2026-10-30/annotations"
BASELINE_METRICS = ROOT / "evaluation/results/phase-a-2026-10-30/metrics.json"
WEIGHTS_PATH = ROOT / "evaluation/DeepLSD/weights/deeplsd_wireframe.tar"
OUT_DIR = ROOT / "evaluation/results/deep-learning-perception-2026-11-02"
OVERLAYS_DIR = OUT_DIR / "overlays"

import sys
sys.path.insert(0, str(ROOT / "evaluation"))
from perception_evaluation import (
    evaluate_image,
    validate_annotation,
    _member_coverage,
)


def get_vmirss_mb() -> float:
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    return 0.0


def cluster_endpoints(lines: list[tuple[tuple[float, float], tuple[float, float]]], tolerance: float = 12.0) -> list[dict]:
    """Transitive endpoint clustering matching the Phase A OpenCV perception clustering."""
    endpoints = []
    for line_idx, (p1, p2) in enumerate(lines):
        endpoints.append((f"L{line_idx:04d}", p1))
        endpoints.append((f"L{line_idx:04d}", p2))

    parent = list(range(len(endpoints)))

    def find(idx: int) -> int:
        while parent[idx] != idx:
            parent[idx] = parent[parent[idx]]
            idx = parent[idx]
        return idx

    for left in range(len(endpoints)):
        for right in range(left + 1, len(endpoints)):
            if math.dist(endpoints[left][1], endpoints[right][1]) <= tolerance:
                root_l, root_r = find(left), find(right)
                if root_l != root_r:
                    parent[max(root_l, root_r)] = min(root_l, root_r)

    groups: dict[int, list] = {}
    for idx, ep in enumerate(endpoints):
        groups.setdefault(find(idx), []).append(ep)

    clusters = sorted(
        groups.values(),
        key=lambda g: (min(p[1][1] for p in g), min(p[1][0] for p in g), tuple(sorted(p[0] for p in g)))
    )

    joints = []
    for idx, g in enumerate(clusters, start=1):
        cx = sum(p[1][0] for p in g) / len(g)
        cy = sum(p[1][1] for p in g) / len(g)
        joints.append({
            "id": f"J{idx:04d}",
            "point": [cx, cy],
            "endpoint_count": len(g),
            "line_ids": sorted(list({p[0] for p in g}))
        })
    return joints


def run_deeplsd_on_image(net, image_path: Path):
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"Could not load image: {image_path}")
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    tensor = torch.tensor(gray[None, None], dtype=torch.float32) / 255.0

    mem_before = get_vmirss_mb()
    t0 = time.perf_counter()
    with torch.no_grad():
        out = net({"image": tensor})
    t1 = time.perf_counter()
    mem_after = get_vmirss_mb()

    raw_lines = out["lines"][0]  # shape (N, 2, 2)
    lines_list = []
    formatted_lines = []
    for idx, (p1, p2) in enumerate(raw_lines):
        pt1 = (float(p1[0]), float(p1[1]))
        pt2 = (float(p2[0]), float(p2[1]))
        lines_list.append((pt1, pt2))
        formatted_lines.append({
            "id": f"L{idx:04d}",
            "start": [pt1[0], pt1[1]],
            "end": [pt2[0], pt2[1]],
            "length_px": math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1]),
        })

    joints = cluster_endpoints(lines_list, tolerance=12.0)

    result_dict = {
        "image_width": w,
        "image_height": h,
        "lines": formatted_lines,
        "joints": joints,
        "timing_sec": t1 - t0,
        "mem_peak_mb": mem_after,
        "mem_delta_mb": max(0.0, mem_after - mem_before),
    }
    return img_bgr, lines_list, result_dict


def render_overlay(img_bgr, lines_list, joints, output_path: Path):
    overlay = img_bgr.copy()
    for (x1, y1), (x2, y2) in lines_list:
        cv2.line(overlay, (round(x1), round(y1)), (round(x2), round(y2)), (235, 70, 30), 2, cv2.LINE_AA)
    for j in joints:
        pt = (round(j["point"][0]), round(j["point"][1]))
        cv2.circle(overlay, pt, 4, (30, 200, 30), -1, cv2.LINE_AA)
    cv2.imwrite(str(output_path), overlay)


def render_comparison_overlay(img_bgr, opencv_lines, deeplsd_lines, output_path: Path):
    """Side-by-side or dual-channel comparison of OpenCV vs DeepLSD."""
    h, w = img_bgr.shape[:2]
    panel_left = img_bgr.copy()
    panel_right = img_bgr.copy()

    # Left: OpenCV
    for line in opencv_lines:
        s, e = line["start"], line["end"]
        cv2.line(panel_left, (round(s[0]), round(s[1])), (round(e[0]), round(e[1])), (30, 70, 235), 2, cv2.LINE_AA)
    cv2.putText(panel_left, f"OpenCV Canny/Hough ({len(opencv_lines)} lines)", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (15, 45, 180), 3, cv2.LINE_AA)

    # Right: DeepLSD
    for (x1, y1), (x2, y2) in deeplsd_lines:
        cv2.line(panel_right, (round(x1), round(y1)), (round(x2), round(y2)), (235, 70, 30), 2, cv2.LINE_AA)
    cv2.putText(panel_right, f"DeepLSD Pretrained ({len(deeplsd_lines)} lines)", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (180, 45, 15), 3, cv2.LINE_AA)

    combined = np.hstack([panel_left, panel_right])
    cv2.imwrite(str(output_path), combined)


def render_target_member_crop(img_bgr, deeplsd_lines, ann, output_path: Path):
    """Detailed crop around M09, M10, and M16 on test5.png matching Phase A5 diagnostic."""
    # Fixed diagnostic crop region: [1190, 630, 555, 420]
    cx, cy, cw, ch = 1190, 630, 555, 420
    crop = img_bgr[cy:cy + ch, cx:cx + cw].copy()

    # Draw all DeepLSD lines in faint gray
    for (x1, y1), (x2, y2) in deeplsd_lines:
        if max(x1, x2) >= cx and min(x1, x2) <= cx + cw and max(y1, y2) >= cy and min(y1, y2) <= cy + ch:
            cv2.line(crop, (round(x1 - cx), round(y1 - cy)), (round(x2 - cx), round(y2 - cy)), (180, 180, 180), 1, cv2.LINE_AA)

    # Highlight annotated M09, M10, M16
    nodes = {n["id"]: (n["x"], n["y"]) for n in ann["joints"]}
    colors = {
        "M09": (0, 0, 255),    # Red
        "M10": (255, 0, 0),    # Blue
        "M16": (0, 165, 255),  # Orange
    }
    for m in ann["members"]:
        if m["id"] in colors:
            p1, p2 = nodes[m["node_i"]], nodes[m["node_j"]]
            cv2.line(crop, (round(p1[0] - cx), round(p1[1] - cy)), (round(p2[0] - cx), round(p2[1] - cy)), colors[m["id"]], 3, cv2.LINE_AA)

    cv2.imwrite(str(output_path), crop)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading DeepLSD pretrained model...")
    conf = {
        "detect_lines": True,
        "line_detection_params": {
            "merge": False,
            "filtering": True,
            "grad_thresh": 3,
            "grad_nfa": True,
        },
    }
    ckpt = torch.load(str(WEIGHTS_PATH), map_location="cpu", weights_only=False)
    net = DeepLSD(conf)
    net.load_state_dict(ckpt["model"])
    net.eval()
    print("Model loaded successfully.")

    # Load baseline metrics for comparison
    baseline_metrics = json.loads(BASELINE_METRICS.read_text())
    base_by_name = {img["filename"]: img for img in baseline_metrics["images"]}
    baseline_raw = json.loads((ROOT / "evaluation/results/phase-a-2026-10-30/detector-baseline/baseline.json").read_text())
    base_raw_by_name = {img["input"]["filename"]: img for img in baseline_raw["images"]}

    image_files = sorted(list(SKETCHES_DIR.glob("test*.*")))
    results_by_image = []

    for img_path in image_files:
        filename = img_path.name
        ann_path = ANNOTATIONS_DIR / f"{img_path.stem}.json"
        ann = json.loads(ann_path.read_text())
        validate_annotation(ann)

        print(f"\nProcessing {filename}...")
        img_bgr, lines_list, detection_result = run_deeplsd_on_image(net, img_path)
        print(f"  Inference time: {detection_result['timing_sec']:.2f} s")
        print(f"  Detected lines: {len(lines_list)}")
        print(f"  Endpoint clusters (joints): {len(detection_result['joints'])}")

        eval_metric = evaluate_image(detection_result, ann)
        eval_metric["timing_sec"] = detection_result["timing_sec"]
        eval_metric["detected_lines_count"] = len(lines_list)
        eval_metric["detected_joints_count"] = len(detection_result["joints"])
        eval_metric["memory_peak_mb"] = detection_result["mem_peak_mb"]

        # Per-member coverage fractions
        nodes = {n["id"]: (n["x"], n["y"]) for n in ann["joints"]}
        diag = math.hypot(ann["image"]["width"], ann["image"]["height"])
        corridor = max(12.0, 0.0075 * diag)
        per_member_cov = {}
        for m in ann["members"]:
            if m["status"] == "confirmed":
                p1, p2 = nodes[m["node_i"]], nodes[m["node_j"]]
                per_member_cov[m["id"]] = _member_coverage((p1, p2), lines_list, corridor, 8.0)
        eval_metric["member_coverage_fraction_by_id"] = per_member_cov

        if filename == "test5.png":
            eval_metric["target_members_coverage"] = {
                "M09": per_member_cov.get("M09", 0.0),
                "M10": per_member_cov.get("M10", 0.0),
                "M16": per_member_cov.get("M16", 0.0),
            }
            render_target_member_crop(img_bgr, lines_list, ann, OVERLAYS_DIR / "test5_target_members_crop.png")

        # Save overlays
        render_overlay(img_bgr, lines_list, detection_result["joints"], OVERLAYS_DIR / f"{img_path.stem}_deeplsd_overlay.png")
        if filename in base_raw_by_name:
            render_comparison_overlay(
                img_bgr,
                base_raw_by_name[filename]["lines"],
                lines_list,
                OVERLAYS_DIR / f"{img_path.stem}_comparison_opencv_vs_deeplsd.png"
            )

        results_by_image.append(eval_metric)
        print(f"  Joint P/R: {eval_metric.get('joint_precision')}, {eval_metric.get('joint_recall')}")
        print(f"  Member coverage: {eval_metric.get('members_with_at_least_80_percent_candidate_line_coverage')}/{eval_metric.get('confirmed_reference_member_count')} (Recall: {eval_metric.get('member_coverage_recall')})")

    # Aggregate micro-averages over confirmed reference graphs
    included = [m for m in results_by_image if m["metrics_status"] in {"available", "partial"}]
    tp = sum(m["matched_joints"] for m in included)
    predicted_joints = sum(m["detected_candidate_joints_in_roi"] for m in included)
    ref_joints = sum(m["confirmed_reference_joint_count"] for m in included)
    ref_members = sum(m["confirmed_reference_member_count"] for m in included)
    cov_members = sum(m["members_with_at_least_80_percent_candidate_line_coverage"] for m in included)
    err_sum = sum((m["matched_joint_endpoint_error_px_mean"] or 0.0) * m["matched_joints"] for m in included)

    aggregate = {
        "metrics_status": "exploratory_micro_average",
        "included_images": [m["filename"] for m in included],
        "excluded_images": [m["filename"] for m in results_by_image if m not in included],
        "joint_precision": tp / predicted_joints if predicted_joints else None,
        "joint_recall": tp / ref_joints if ref_joints else None,
        "matched_joint_endpoint_error_px_mean": err_sum / tp if tp else None,
        "member_coverage_recall": cov_members / ref_members if ref_members else None,
        "total_confirmed_members": ref_members,
        "total_covered_members": cov_members,
        "member_precision": None,
        "member_precision_unavailable_reason": "The detector outputs raw line segments, not grouped semantic truss members.",
    }

    output_payload = {
        "experiment": "deep-learning-perception-deeplsd-2026-11-02",
        "model": "DeepLSD (CVPR 2023)",
        "weights": "deeplsd_wireframe.tar (official)",
        "device": "cpu",
        "scoring_protocol": "Unchanged Phase A evaluator: 8 degree angle, max(12 px, 0.75% diag) corridor, 80% member coverage threshold.",
        "aggregate": aggregate,
        "baseline_comparison": baseline_metrics["aggregate"],
        "images": results_by_image,
    }

    results_json_path = OUT_DIR / "results.json"
    results_json_path.write_text(json.dumps(output_payload, indent=2))
    print(f"\nWrote results to {results_json_path}")


if __name__ == "__main__":
    main()
