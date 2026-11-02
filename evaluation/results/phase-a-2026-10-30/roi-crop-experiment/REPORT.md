# ROI cropping experiment — 2026-10-30

## Setup

The crop rectangles were selected by inspecting the original source images and the independently prepared Phase A annotation. Detector outputs were not consulted when choosing them. The frozen machine-readable configuration is `roi_config.json`. Source coordinates use the original decoded raster, with origin at top-left, x right, and y down; rectangle right/bottom bounds are exclusive. No resizing was done. Crops were PNG-encoded from the decoded source raster, so pixel values were preserved without a second lossy JPEG encode.

| Image | Original size | Crop `[x, y, width, height]` | Selection |
|---|---:|---:|---|
| `test2.jpg` | 576×749 | `[60, 565, 455, 184]` | Bottom/fourth sketch plus margin, selected as the most isolated of four alternatives. The annotation remains ambiguous. |
| `test5.png` | 2046×1319 | `[365, 630, 1380, 420]` | Exactly the existing independently selected Phase A main-truss evaluation ROI. |

The three `test5` crossing points `(601,843)`, `(1032,843)`, and `(1472,843)` remain marked ambiguous in the config and original annotation. They were not counted as joints or used as reference truth.

The unchanged default `detect_candidate_geometry(image_bytes)` was run five times per condition. Runtime is the median of `perf_counter` measurements around the detector call, matching the Phase A runner. Repeat outputs were identical. Cropped coordinates were mapped back to source pixels by adding the recorded x/y crop offset before metric evaluation. `test5` uses the same Phase A annotation, ROI, and tolerances: joint/corridor distance `max(12 px, 0.75% of source diagonal)`, 8° line-angle limit, and 80% member coverage threshold.

## Measurements

| Image / condition | Candidate lines | Cap reached | Endpoint clusters | Median runtime (5 calls) |
|---|---:|:---:|---:|---:|
| `test2.jpg` original | 300 | Yes | 240 | 88.711 ms |
| `test2.jpg` crop | 104 | No | 81 | 14.351 ms |
| `test5.png` original | 300 | Yes | 221 | 118.119 ms |
| `test5.png` crop | 300 | Yes | 211 | 84.989 ms |

`test2` has no selected trustworthy reference graph. Its accuracy metrics are unavailable; its results above and its overlays are the only reported evidence. The crop visually removes the other sketches and most page-wide rules, while candidate lines remain around the selected rough drawing and its overdrawn supports. This is not a measured accuracy improvement.

For `test5`, the same annotation evaluator was applied after transforming crop detections back to original coordinates:

| Metric | Original | Cropped | Change |
|---|---:|---:|---:|
| Joint precision | 0.0299 (2/67) | 0.0237 (5/211) | Lower |
| Joint recall | 0.250 (2/8) | 0.625 (5/8) | Higher |
| Matched endpoint localization error, mean | 15.845 px | 10.277 px | Lower |
| Matched endpoint localization error, median | 15.845 px | 9.795 px | Lower |
| Member centerline coverage recall | 3/16 = 0.1875 | 7/16 = 0.4375 | Higher |
| Member precision | unavailable | unavailable | Detector emits ungrouped lines, not member hypotheses |

The crop improved measured candidate-line coverage of the annotated main-truss centerlines and joint recall, while joint precision decreased. The crop still hit the 300-line cap. The overlays show better line coverage through more of the left and middle bays, but the rightmost bay remains largely undetected and candidates cluster around printed joints/connectors. The ambiguous X crossings remain unscored; this experiment makes no claim about their connectivity. Therefore the results support a real but partial coverage improvement for `test5`, not overall detector accuracy or reliable structural interpretation. A lower candidate count by itself is not the basis for this conclusion.

## Artifacts and reproduction

- `roi_config.json` — fixed crop coordinates, selection basis, transform convention, and ambiguous crossing points.
- `results.json` — full detector outputs for original and cropped conditions, five-run measurements, mapped coordinates, and test5 metrics.
- `test2/` and `test5/` — lossless crop inputs, detector overlay for the original, local crop overlay, and mapped crop detections drawn on the original image.
- `phase-a-metrics-reproduced.json` — evaluator run against the untouched Phase A baseline and annotations; written separately from the original `metrics.json`.

Commands run:

```bash
backend/.venv/bin/python evaluation/run_roi_crop_experiment.py \
  --output-dir evaluation/results/phase-a-2026-10-30/roi-crop-experiment --repeats 5

backend/.venv/bin/python evaluation/perception_evaluation.py \
  --baseline evaluation/results/phase-a-2026-10-30/detector-baseline/baseline.json \
  --annotations evaluation/results/phase-a-2026-10-30/annotations \
  --output evaluation/results/phase-a-2026-10-30/roi-crop-experiment/phase-a-metrics-reproduced.json

cd backend && ./.venv/bin/python -m unittest tests.test_perception_evaluation tests.test_perception_roi_experiment -v
cd backend && ./.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

The relevant evaluator/ROI tests passed (8); the full backend suite passed (93). Both evaluation commands completed. No new dependency, live AI call, baseline/annotation edit, or production detector change was made. `git diff --check` is recorded in the handoff after documentation was finalized.

## Next experiment

Test an overlapping, smaller-tile ROI pass across the `test5` bays, mapping each tile's candidates to original coordinates and deduplicating with a fixed, documented rule. This follows from the fact that the whole-truss crop still reaches the line cap and leaves the rightmost bay uncovered. Keep the same reference, ambiguity exclusions, detector configuration, and metrics; report tile combination as a distinct experiment because deduplication may affect counts and matching.
