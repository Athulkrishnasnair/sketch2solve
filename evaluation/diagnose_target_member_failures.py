"""Explain raw detector segment behavior for selected test5 members.

This evaluation-only script reads frozen experiment outputs and does not invoke
or modify the production detector.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evaluation/results/phase-a-2026-10-30"
OUT = BASE / "target-member-failure-diagnostic-2026-10-31"
SOURCE = ROOT / "backend/evaluation/sketches/test5.png"
EXPECTED_SHA256 = "5fa616402e536ecb0907d699f6e0252f4fadc556df11a3cbb475e4f184b1ca36"
MEMBER_IDS = ("M09", "M10", "M16")
CONDITIONS = ("original", "full_roi", "three_wide", "four_narrow", "targeted_tile")


def segment_metrics(member_start, member_end, candidate_start, candidate_end):
    """Measure one segment against a finite annotated centerline."""
    ax, ay = member_start
    bx, by = member_end
    vx, vy = bx - ax, by - ay
    length = math.hypot(vx, vy)
    if length == 0:
        raise ValueError("reference member must have positive length")
    ux, uy = vx / length, vy / length
    p, q = candidate_start, candidate_end
    dx, dy = q[0] - p[0], q[1] - p[1]
    candidate_length = math.hypot(dx, dy)
    if candidate_length == 0:
        return {"angle_mismatch_deg": None, "centerline_offset_px": None,
                "overlap_px": 0.0, "coverage_fraction": 0.0,
                "projection_interval_px": None, "endpoint_errors_px": None}
    cosine = min(1.0, abs((vx * dx + vy * dy) / (length * candidate_length)))
    angle = math.degrees(math.acos(cosine))
    offsets = [abs(vx * (point[1] - ay) - vy * (point[0] - ax)) / length for point in (p, q)]
    projections = sorted(((p[0] - ax) * ux + (p[1] - ay) * uy,
                          (q[0] - ax) * ux + (q[1] - ay) * uy))
    lo, hi = max(0.0, projections[0]), min(length, projections[1])
    overlap = max(0.0, hi - lo)
    endpoint_errors = [
        min(math.dist(p, member_start), math.dist(q, member_start)),
        min(math.dist(p, member_end), math.dist(q, member_end)),
    ]
    return {
        "angle_mismatch_deg": angle,
        "centerline_offset_px": max(offsets),
        "endpoint_offsets_px": offsets,
        "overlap_px": overlap,
        "coverage_fraction": overlap / length,
        "projection_interval_px": [lo, hi] if overlap > 0 else None,
        "endpoint_errors_px": endpoint_errors,
    }


def _union(intervals):
    if not intervals:
        return [], 0.0
    merged = []
    for lo, hi in sorted(intervals):
        if not merged or lo > merged[-1][1]:
            merged.append([lo, hi])
        else:
            merged[-1][1] = max(merged[-1][1], hi)
    return merged, sum(hi - lo for lo, hi in merged)


def _load_candidates():
    baseline = json.loads((BASE / "detector-baseline/baseline.json").read_text())
    original = next(x for x in baseline["images"] if x["input"]["filename"] == "test5.png")
    roi = json.loads((BASE / "roi-crop-experiment/results.json").read_text())
    roi_record = next(x for x in roi["images"] if x["filename"] == "test5.png")
    tiles = json.loads((BASE / "overlapping-tile-experiment-2026-10-30/results.json").read_text())
    targeted = json.loads((BASE / "rightmost-bay-targeted-tile-2026-10-30/results.json").read_text())

    def plain(lines, prefix=""):
        return [{"id": prefix + line["id"], "start": line["start"], "end": line["end"], "provenance": line.get("source_detections", [])} for line in lines]

    raw = {
        "original": plain(original["lines"]),
        "full_roi": plain(roi_record["cropped"]["detector_result_original_coordinates"]["lines"]),
    }
    raw["original_joints"] = original["joints"]
    raw["full_roi_joints"] = roi_record["cropped"]["detector_result_original_coordinates"]["joints"]
    for name in ("three_wide", "four_narrow"):
        detections = [line for tile in tiles["configurations"][name]["tiles"] for line in tile["mapped_line_detections"]]
        raw[name] = [{"id": f'{line["tile_id"]}:{line["line_id"]}', "start": line["start"], "end": line["end"], "provenance": [{"tile_id": line["tile_id"], "line_id": line["line_id"], "tile_origin": line["tile_origin"]}]} for line in detections]
    raw["targeted_tile"] = [{"id": f'{line["tile_id"]}:{line["line_id"]}', "start": line["start"], "end": line["end"], "provenance": [{"tile_id": line["tile_id"], "line_id": line["line_id"], "tile_origin": line["tile_origin"]}]} for line in targeted["tile_detection"]["mapped_line_detections"]]
    return raw, tiles, targeted


def analyze_member(member, nodes, candidates, corridor, angle_limit):
    start = [nodes[member["node_i"]]["x"], nodes[member["node_i"]]["y"]]
    end = [nodes[member["node_j"]]["x"], nodes[member["node_j"]]["y"]]
    length = math.dist(start, end)
    measured = []
    for segment in candidates:
        metrics = segment_metrics(start, end, segment["start"], segment["end"])
        metrics.update({"segment_id": segment["id"], "start": segment["start"], "end": segment["end"], "provenance": segment["provenance"]})
        metrics["coverage_eligible"] = (metrics["angle_mismatch_deg"] is not None and metrics["angle_mismatch_deg"] <= angle_limit and metrics["centerline_offset_px"] <= corridor and metrics["overlap_px"] > 0)
        measured.append(metrics)
    eligible = [x for x in measured if x["coverage_eligible"]]
    best = max(eligible, key=lambda x: x["overlap_px"], default=None)
    best_longitudinal = max(measured, key=lambda x: (x["overlap_px"], -(x["centerline_offset_px"] if x["centerline_offset_px"] is not None else 1e9)), default=None)
    intervals = [x["projection_interval_px"] for x in eligible]
    merged, covered = _union(intervals)
    gaps = []
    cursor = 0.0
    for lo, hi in merged:
        if lo > cursor:
            gaps.append([cursor, lo])
        cursor = max(cursor, hi)
    if cursor < length:
        gaps.append([cursor, length])
    # Nearby non-eligible candidates are explicit clutter/response evidence,
    # ranked by longitudinal overlap then offset and angle; no semantic label.
    nearby = [x for x in measured if x["overlap_px"] > 0 and x["centerline_offset_px"] is not None and x["centerline_offset_px"] <= corridor]
    nearby.sort(key=lambda x: (-x["overlap_px"], x["centerline_offset_px"], x["angle_mismatch_deg"]))
    return {
        "reference_start": start, "reference_end": end, "reference_length_px": length,
        "best_single_coverage_segment": best,
        "best_longitudinal_overlap_candidate": best_longitudinal,
        "best_single_eligible_segment": max(eligible, key=lambda x: x["overlap_px"], default=None),
        "eligible_fragment_count": len(eligible),
        "fragment_union_intervals_px": merged,
        "fragment_union_coverage_px": covered,
        "fragment_union_coverage_fraction": covered / length,
        "uncovered_gaps_px": gaps,
        "meets_80_percent_threshold": covered / length >= 0.80,
        "nearby_candidates_within_corridor_and_longitudinal_extent": nearby[:12],
        "nearby_candidate_count": len(nearby),
        "eligible_candidate_count": len(eligible),
    }


def main():
    source_bytes = SOURCE.read_bytes()
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"source hash mismatch: {digest}")
    annotation = json.loads((BASE / "annotations/test5.json").read_text())
    nodes = {node["id"]: node for node in annotation["joints"]}
    members = {member["id"]: member for member in annotation["members"]}
    # Same evaluator defaults: diagonal-fraction corridor and 8 degree angle.
    corridor = max(12.0, 0.0075 * math.hypot(annotation["image"]["width"], annotation["image"]["height"]))
    angle_limit = 8.0
    raw, tile_results, targeted = _load_candidates()
    detector_by_condition = {}
    for condition in CONDITIONS:
        if condition in ("original", "full_roi"):
            detector_by_condition[condition] = {"raw_lines": len(raw[condition]), "cap_reached": len(raw[condition]) >= 300, "endpoint_clusters": len(raw[f"{condition}_joints"])}
        elif condition in ("three_wide", "four_narrow"):
            config = tile_results["configurations"][condition]
            detector_by_condition[condition] = {
                "raw_lines": len(raw[condition]),
                "cap_reached": any(tile["candidate_cap_reached"] for tile in config["tiles"]),
                "endpoint_clusters_before_deduplication": config["raw_reconstructed_endpoint_cluster_count_before_deduplication"],
                "endpoint_clusters_after_primary_deduplication": len(config["primary_reconstructed_candidate_result_original_coordinates"]["joints"]),
                "deduplicated_lines_primary_4px": len(config["primary_deduplicated_lines_with_provenance"]),
                "tile_counts": [{"tile_id": t["tile_id"], "candidate_lines": t["candidate_line_count"], "endpoint_clusters": t["endpoint_cluster_count"], "cap_reached": t["candidate_cap_reached"]} for t in config["tiles"]],
            }
        else:
            d = targeted["tile_detection"]
            detector_by_condition[condition] = {"raw_lines": len(raw[condition]), "cap_reached": d["candidate_cap_reached"], "endpoint_clusters": d["endpoint_cluster_count_before_deduplication"], "deduplicated_lines_primary_4px": len(targeted["primary_deduplication"]["deduplicated_lines_with_provenance"]), "tile": targeted["tile"]}
    members_out = {}
    for member_id in MEMBER_IDS:
        members_out[member_id] = {}
        for condition in CONDITIONS:
            members_out[member_id][condition] = analyze_member(members[member_id], nodes, raw[condition], corridor, angle_limit)

    # Endpoint-nearness is a separate diagnostic; it never implies line coverage.
    endpoints = {}
    for member_id in MEMBER_IDS:
        member = members[member_id]
        for node_id in (member["node_i"], member["node_j"]):
            target = [nodes[node_id]["x"], nodes[node_id]["y"]]
            endpoints.setdefault(member_id, {})[node_id] = {}
            for condition in CONDITIONS:
                nearest = min(((math.dist(target, point), segment["id"], point) for segment in raw[condition] for point in (segment["start"], segment["end"])), default=None)
                endpoints[member_id][node_id][condition] = None if nearest is None else {"distance_px": nearest[0], "segment_id": nearest[1], "candidate_endpoint": nearest[2]}

    results = {
        "experiment": "test5-target-member-failure-diagnostic",
        "source": {"path": "backend/evaluation/sketches/test5.png", "sha256": digest, "width": 2046, "height": 1319},
        "coordinates": "original raster pixels; x right, y down; raw segments mapped back to source coordinates",
        "reference_annotation": "evaluation/results/phase-a-2026-10-30/annotations/test5.json (unchanged)",
        "ambiguous_crossings_excluded_from_joint_scoring": [r["point"] for r in annotation["ambiguous_regions"]],
        "method": {"corridor_px": corridor, "angle_tolerance_deg": angle_limit, "coverage_threshold": 0.80,
                   "single_segment_overlap": "candidate projection clipped to annotated finite member centerline",
                   "fragment_union": "union only of segments satisfying existing angle and corridor gates; uncovered gaps reported; no gaps bridged",
                   "nearby_responses": "positive longitudinal overlap, offset within corridor, including candidates that fail the 8 degree gate; not considered member coverage",
                   "endpoint_errors": "nearest detector endpoint to each annotated joint, independent of line coverage"},
        "conditions": detector_by_condition,
        "member_diagnostics": members_out,
        "nearest_raw_endpoint_by_annotated_joint": endpoints,
        "limitations": ["Candidate response alignment is not proof of semantic member detection.", "Endpoint cluster counts are unavailable for the two saved single-image candidate sets in this diagnostic record; line segment endpoint proximity is reported independently.", "No detector was rerun; all comparisons use saved raw outputs."]
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    config = {
        "experiment": results["experiment"], "source_sha256": digest,
        "input_artifacts": ["detector-baseline/baseline.json", "roi-crop-experiment/results.json", "overlapping-tile-experiment-2026-10-30/results.json", "rightmost-bay-targeted-tile-2026-10-30/results.json"],
        "candidate_filter": "all raw lines for each layout, no posthoc score filtering",
        "target_members": list(MEMBER_IDS), "corridor_px": corridor, "angle_tolerance_deg": angle_limit,
        "coverage_threshold": 0.80, "overlay_region_original_pixels": [1190, 630, 1745, 1050],
        "ambiguous_points_original_pixels": [r["point"] for r in annotation["ambiguous_regions"]]
    }
    (OUT / "diagnostic_config.json").write_text(json.dumps(config, indent=2) + "\n")
    image = cv2.imdecode(__import__("numpy").frombuffer(source_bytes, dtype=__import__("numpy").uint8), cv2.IMREAD_COLOR)
    colors = {"M09": (255, 80, 20), "M10": (20, 160, 255), "M16": (220, 40, 210)}
    def put_clamped_label(canvas, text, x, y, color, scale=.28):
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        x = max(2, min(canvas.shape[1] - tw - 2, x))
        y = max(th + 2, min(canvas.shape[0] - 2, y))
        cv2.putText(canvas, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)
    # Save consistent source-coordinate crops for each condition; show all raw
    # lines faintly and annotate the best 3 proximity-ranked candidates/member.
    display_ids = {}
    x0, y0, x1, y1 = config["overlay_region_original_pixels"]
    for condition in CONDITIONS:
        crop = image[y0:y1, x0:x1].copy()
        header = 62
        canvas = __import__("numpy").zeros((crop.shape[0] + header, crop.shape[1], 3), dtype=crop.dtype)
        canvas[:header] = (35, 35, 35)
        canvas[header:] = crop
        for line in raw[condition]:
            p = tuple(round(c) for c in line["start"]); q = tuple(round(c) for c in line["end"])
            if max(p[0], q[0]) < x0 or min(p[0], q[0]) > x1 or max(p[1], q[1]) < y0 or min(p[1], q[1]) > y1:
                continue
            cv2.line(canvas, (p[0]-x0,p[1]-y0+header), (q[0]-x0,q[1]-y0+header), (155,155,155), 1, cv2.LINE_AA)
        for member_id in MEMBER_IDS:
            diag = members_out[member_id][condition]
            member = members[member_id]
            a, b = diag["reference_start"], diag["reference_end"]
            cv2.line(canvas, (a[0]-x0,a[1]-y0+header), (b[0]-x0,b[1]-y0+header), colors[member_id], 2, cv2.LINE_AA)
            put_clamped_label(canvas, member_id, a[0]-x0+4, a[1]-y0+header-4, colors[member_id], .42)
        shown = {}
        legend_rows = []
        for member_id in MEMBER_IDS:
            candidates = members_out[member_id][condition]["nearby_candidates_within_corridor_and_longitudinal_extent"][:3]
            shown[member_id] = [x["segment_id"] for x in candidates]
            legend_rows.append((member_id, candidates))
            for candidate_index, item in enumerate(candidates, start=1):
                p, q = item["start"], item["end"]
                color = colors[member_id]
                cv2.line(canvas, (p[0]-x0,p[1]-y0+header), (q[0]-x0,q[1]-y0+header), color, 2, cv2.LINE_AA)
                mid = ((p[0]+q[0])//2-x0,(p[1]+q[1])//2-y0+header)
                put_clamped_label(canvas, str(candidate_index), mid[0], mid[1], color, .32)
        for row, (member_id, candidates) in enumerate(legend_rows):
            ids = ", ".join(f'{index}:{item["segment_id"]}' for index, item in enumerate(candidates, start=1)) or "no nearby candidates"
            put_clamped_label(canvas, f"{member_id}: {ids}", 5, 15 + row * 20, colors[member_id], .27)
        for point in config["ambiguous_points_original_pixels"]:
            if x0 <= point[0] <= x1 and y0 <= point[1] <= y1:
                cv2.circle(canvas, (point[0]-x0,point[1]-y0+header), 7, (0,140,255), 2, cv2.LINE_AA)
        path = OUT / "overlays" / f"{condition}_target_members.png"
        path.parent.mkdir(exist_ok=True)
        cv2.imwrite(str(path), canvas)
        display_ids[condition] = shown
    results["overlay_candidate_ids"] = display_ids
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
