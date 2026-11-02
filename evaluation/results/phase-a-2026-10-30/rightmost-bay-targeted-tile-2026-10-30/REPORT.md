# Targeted rightmost-bay tile experiment — 2026-10-30

## Fixed selection and reference coordinates

Source image `test5.png` is 2046×1319. The unchanged evaluation ROI is `[x=365, y=630, width=1380, height=420]`, with original-raster coordinates, top-left origin, x right, y down, and exclusive right/bottom bounds.

The three below-threshold members were located from the existing annotation before running the detector:

| Member | Annotated endpoints (original pixels) | Reference interpretation |
|---|---|---|
| M09 | F `(1252,663)` → C `(1252,1023)` | Vertical at the left edge of the rightmost bay |
| M10 | E `(1693,663)` → D `(1693,1023)` | Right boundary vertical |
| M16 | C `(1252,1023)` → E `(1693,663)` | Diagonal across the rightmost bay |

The fixed tile is `[x=1200, y=630, width=545, height=420]`, ending at exclusive `(1745,1050)`. It contains all three complete centerlines and their endpoints. Padding from the target endpoint bounds is about 52 px at left and right, 33 px above, and 27 px below. The existing four-narrow boundary at x=1265 is 13 px to the right of F/C; this tile moves that boundary 52 px to the left of F/C. It removes 55 px of preceding-bay context relative to the three-wide tile at x=1145 while retaining the full target bay. This coordinate choice uses only the original raster and reference, not detector output. The frozen configuration is `tile_config.json`.

The three X-brace crossings `(601,843)`, `(1032,843)`, and `(1472,843)` remain ambiguous and excluded from joint scoring. The source annotation and SHA-256 were unchanged.

## Detection and deduplication

The unchanged default detector was run five times on this one PNG-encoded tile, with no resizing. Output was deterministic. It returned **156 candidate lines and 90 endpoint clusters; the 300-line cap was not reached**. Lines and joints were mapped by adding the tile origin to local coordinates. Each mapped line retains tile ID, detector line ID, origin, and both mapped endpoints.

The existing experiment-only deduplication was applied at its primary 4 px tolerance and at 2 px and 8 px sensitivity settings. This configuration has one tile, so there are no cross-tile duplicate sources: all three tolerances left the set at **156 lines, removed 0**. Metrics and all three target-member coverage values were identical for all tolerances. This shows no deduplication dependence in this single-tile result; it does not test within-tile duplicates beyond the unchanged detector's own filtering.

## Target member coverage and endpoint localization

The fixed 80% centerline-coverage threshold was not reached by any target member. Existing-layout values are included for comparison; fractions use the same original reference and Phase A tolerances.

| Member | Original | Full ROI | Three wide | Four narrow | Targeted tile | Targeted matched endpoint errors |
|---|---:|---:|---:|---:|---:|---|
| M09 | 0.0% | 0.0% | 5.6% | 9.7% | **14.2%** | F 12.65 px; C 17.00 px |
| M10 | 0.0% | 0.0% | 10.3% | 12.5% | **0.0%** | E unmatched; D 3.00 px |
| M16 | 0.0% | 0.0% | 11.6% | 5.3% | **0.0%** | C 17.00 px; E unmatched |

Endpoint error is conditional on an endpoint-cluster prediction matching a confirmed reference joint within the 18.257 px Phase A tolerance. It is not evidence that a member centerline was recovered. M09 has candidate endpoints near both joints but only 14.2% centerline coverage. M10 has a candidate near D but none matched at E and zero centerline coverage. M16 has a candidate near C but none matched at E and zero centerline coverage. These are nearby candidate observations, not adequate detections of the annotated members.

## Comparison with all existing layouts

| Condition | Lines before → after dedup | Cap | Endpoint clusters | Joint precision / recall | Endpoint error mean / median | Total member coverage |
|---|---:|---|---:|---:|---:|---:|
| Original image | 300 → 300 | Reached | 221 | 0.0299 / 0.250 | 15.845 / 15.845 px | 3/16 (0.188) |
| Full ROI | 300 → 300 | Reached | 211 | 0.0237 / 0.625 | 10.277 / 9.795 px | 7/16 (0.438) |
| Three wide | 577 → 477 | No tile capped | 210 | 0.0238 / 0.625 | 13.804 / 14.142 px | 12/16 (0.750) |
| Four narrow | 489 → 389 | No tile capped | 223 | 0.0314 / 0.875 | 12.081 / 12.093 px | 10/16 (0.625) |
| Targeted tile | 156 → 156 | Not reached | 90 | 0.0333 / 0.375 | 10.883 / 12.649 px | 3/16 (0.188) |

The targeted tile has the highest joint precision of these conditions (3.33%) and a low endpoint error among only three matched joints. Its joint recall is 0.375, and total member coverage is just 3/16, equal to the original full-image result and below all ROI/tiled layouts. It therefore **did not outperform the existing layouts overall**. It modestly raises M09's coverage but does not recover M09, M10, or M16 at the defined threshold; M10 and M16 coverage is lower than in both tiled layouts.

The mapped overlay shows many candidate strokes near printed connectors and visible strokes along portions of the verticals/diagonal. The evaluator counts centerline overlap only when orientation and distance criteria are also met; the low measured fractions remain the result. The X crossings are orange-marked only as ambiguity references, not promoted to joints.

## Runtime breakdown

Five tile-pipeline passes were timed. Median stages were:

| Stage | Median |
|---|---:|
| Source image decode, once | 26.633 ms |
| Tile extraction and PNG encoding | 3.915 ms |
| Detector call only | 24.615 ms |
| Coordinate mapping, deduplication, endpoint clustering | 8.658 ms |
| Tile pipeline total, excluding source read/decode | 37.792 ms |

The pipeline total is timed per pass and need not equal the sum of independently computed stage medians. Prior original, ROI, and multi-tile runtimes measure detector calls only (with tiled detector-call times summed across tiles); their crop/encoding and postprocessing stages were not recorded. The 37.792 ms pipeline value is therefore reported separately and is not compared as if it were the same runtime boundary. The targeted detector-call median is comparable to those detector-only figures.

## Artifacts and verification

- `tile_config.json` — fixed tile coordinates, rationale, target endpoints, coordinate map, and ambiguity points.
- `results.json` — per-call results, full mapped line/joint detections with provenance, dedup tolerance sweep, member coverage/error details, cross-layout metrics, and runtime breakdown.
- `tile.png`, `tile_candidate_overlay.png`, `targeted_on_original.png` — selected crop and local/source-coordinate overlays.
- Runner: `evaluation/run_rightmost_targeted_tile_experiment.py`.
- Configuration regression test: `backend/tests/test_rightmost_targeted_tile_experiment.py`.

The runner completed five deterministic repeats. Relevant evaluation tests passed (18, including the new fixed-tile check); the full backend suite passed (103); `git diff --check` passed after the report and handoff updates. No dependencies, AI calls, production detector changes, annotation changes, or previous experiment-output changes were made.

## Next experiment

Tile placement alone did not raise the three target members above 14.2% coverage, despite including their full endpoints and margin. The highest-value next step is an evaluation-only per-member audit of the unchanged detector's raw segments, separating angular mismatch, perpendicular offset, and fragmentation for M09/M10/M16. That will show whether further tile-placement trials are justified or whether the misses come from candidate-line quality rather than clipping.
