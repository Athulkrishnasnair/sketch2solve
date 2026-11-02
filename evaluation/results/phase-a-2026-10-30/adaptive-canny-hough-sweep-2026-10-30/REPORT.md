# Adaptive Canny/Hough parameter sweep — 2026-10-30

## Scope and reproducibility

This is an offline evaluation-only parameter sweep. Production detector code and defaults, solver behavior, annotations, Phase A artifacts, and existing ROI/tile configurations were not edited. No live AI or browser workflow was used, and no dependencies were added.

The detector's fresh default run was repeated five times on all five source sketches. Candidate line and endpoint-cluster geometry matched the saved Phase A baseline exactly on every image. All five source SHA-256 hashes matched both their annotation and saved baseline records. The unchanged Phase A evaluation was applied to the four images with confirmed reference graphs; `test2.jpg` remains ambiguous and has counts only.

Image preprocessing stayed fixed: BGR to grayscale, 5×5 Gaussian blur with sigma 0, no resize, then Canny and probabilistic Hough. Candidate duplicate filtering, endpoint clustering, caps, evaluation ROI, 8° angle tolerance, `max(12 px, 0.75% diagonal)` distance/corridor tolerance, and 80% member-coverage threshold stayed unchanged. Tile origins, dimensions, coordinate mapping, and cross-tile deduplication stayed at the existing configs and 4 px primary tolerance. The three ambiguous X crossings in `test5.png` remain excluded.

## Tested settings

Stage 1 varied Canny clamps while retaining production Hough settings (`vote=25`, `min line=20 px`, `max gap=8 px`). Median-adaptive sigma remained 0.8. Actual Canny thresholds used per image are recorded in `results.json`.

| ID | Canny sigma | Minimum clamp | Maximum clamp | Hough vote / min length / max gap |
|---|---:|---:|---:|---|
| `control` | 0.8 | 40 | 160 | 25 / 20 / 8 |
| `canny_low` | 0.8 | 20 | 120 | 25 / 20 / 8 |
| `canny_high` | 0.8 | 60 | 220 | 25 / 20 / 8 |

Stage 2 first selected `canny_low` as the global alternate by confirmed-graph micro coverage, then precision, recall, and cap count. Hough settings were changed one at a time for the control Canny values and that one global alternate. The complete nine-config matrix with every `PerceptionConfig` field is in `experiment_config.json` and `results.json`.

| ID | Canny parent | Changed Hough parameter | Resulting vote / min length / max gap |
|---|---|---|---|
| `control__hough_vote_low` | control | vote 25→20 | 20 / 20 / 8 |
| `control__hough_short_lines` | control | min length 20→12 px | 25 / 12 / 8 |
| `control__hough_long_gap` | control | max gap 8→12 px | 25 / 20 / 12 |
| `canny_low__hough_vote_low` | canny_low | vote 25→20 | 20 / 20 / 8 |
| `canny_low__hough_short_lines` | canny_low | min length 20→12 px | 25 / 12 / 8 |
| `canny_low__hough_long_gap` | canny_low | max gap 8→12 px | 25 / 20 / 12 |

Each full-image condition used five detector calls per image. The original baseline config and output summaries are retained in the machine-readable results; `baseline_reproduction_differences` confirms identical line/joint geometry.

## Aggregate results

Micro-averages include only `test1`, `test3`, `test4`, and `test5` (4 annotated images, 53 members, 31 reference joints). Member coverage counts members whose candidate-line union reaches the unchanged 80% threshold. Endpoint error is weighted over matched joints. Raw candidate lines are not semantic members, so member precision is unavailable.

| Configuration | Joint precision | Joint recall | Mean endpoint error | Member coverage | Capped full images | Median detector time across 5 images |
|---|---:|---:|---:|---:|---:|---:|
| `control` | 0.0824 | 0.7097 | 9.377 px | 27/53 = 0.5094 | 2 | 59.0 ms |
| `canny_low` | 0.0659 | 0.7097 | 8.705 px | 30/53 = 0.5660 | 3 | 106.7 ms |
| `canny_high` | 0.1086 | 0.6129 | 8.641 px | 27/53 = 0.5094 | 2 | 45.4 ms |
| `control__hough_vote_low` | 0.0827 | 0.6774 | 9.120 px | 28/53 = 0.5283 | 2 | 61.4 ms |
| `control__hough_short_lines` | 0.0866 | 0.7097 | 9.415 px | 25/53 = 0.4717 | 2 | 81.0 ms |
| `control__hough_long_gap` | 0.0885 | 0.7419 | 10.024 px | 28/53 = 0.5283 | 2 | 68.0 ms |
| `canny_low__hough_vote_low` | 0.0627 | 0.7097 | 9.092 px | 28/53 = 0.5283 | 3 | 104.9 ms |
| `canny_low__hough_short_lines` | 0.1223 | 0.5484 | 8.309 px | 25/53 = 0.4717 | 3 | 106.9 ms |
| `canny_low__hough_long_gap` | 0.0882 | 0.6774 | 8.935 px | 28/53 = 0.5283 | 3 | 116.5 ms |

The time column is the median of the five per-image detector medians. Full per-image values, endpoint-error medians, retained/raw-Hough ratios, edge and Hough counts, effective thresholds, line counts, endpoint clusters, and cap statuses are in `results.json` under `all_configuration_scores` and `detection_summaries_by_configuration`.

### Per-image control and best-coverage-screened candidate

`control__hough_long_gap` was the only candidate passing the predeclared aggregate screen: micro member coverage improved, joint precision and recall did not fall, cap count did not increase, and no annotated image lost more than one recovered member. It is an exploratory screen, not a production-readiness test.

| Image | Control lines / clusters; cap | Control P / R | Control endpoint error mean / median | Control coverage | `control__hough_long_gap` lines / clusters; cap | Candidate P / R | Candidate endpoint error mean / median | Candidate coverage |
|---|---|---|---|---|---|---|---|---|
| `test1.jpg` | 153 / 196; no | 0.0404 / 0.5714 | 10.046 / 8.164 px | 0/11 | 191 / 209; no | 0.0472 / 0.7143 | 15.798 / 15.811 px | 1/11 |
| `test2.jpg` | 300 / 240; yes | N/A | N/A | N/A | 300 / 239; yes | N/A | N/A | N/A |
| `test3.png` | 76 / 76; no | 0.1373 / 1.000 | 8.103 / 8.062 px | 9/11 | 77 / 69; no | 0.1556 / 1.000 | 8.203 / 9.341 px | 10/11 |
| `test4.jpg` | 49 / 61; no | 0.1800 / 1.000 | 8.634 / 8.846 px | 15/15 | 51 / 60; no | 0.1837 / 1.000 | 8.588 / 8.846 px | 15/15 |
| `test5.png` | 300 / 221; yes | 0.0299 / 0.250 | 15.845 / 15.845 px | 3/16 | 300 / 201; yes | 0.0333 / 0.250 | 8.422 / 8.422 px | 2/16 |

The `canny_low` setting produced the largest member-coverage gain, but precision fell from 0.0824 to 0.0659, and `test1.jpg` newly reached the 300-line cap. `canny_high` raised precision but reduced recall without increasing aggregate member coverage. Shorter Hough lines reduced member coverage; lowering the vote threshold improved coverage by one member but reduced recall. No single sweep setting dominated the metrics.

## Test5 layouts, including the three target members

The best-screened experimental setting was rerun on the fixed full ROI, three-wide, four-narrow, and targeted rightmost tile. Existing coordinate mapping and deduplication were retained. Percentages below use the same annotated member centerlines; reaching 80%, not merely a nearby endpoint, is the recovery criterion.

| Layout / setting | Lines raw→deduplicated | Clusters | Cap | Joint P / R | Endpoint mean / median | Total coverage | M09 / M10 / M16 coverage |
|---|---:|---:|---|---:|---:|---:|---:|
| Full ROI control | 300→300 | 211 | yes | 0.0237 / 0.625 | 10.277 / 9.795 px | 7/16 | 0 / 0 / 0% |
| Full ROI long gap | 300→300 | 208 | yes | 0.0288 / 0.750 | 10.783 / 13.024 px | 8/16 | 0 / 0 / 0% |
| Three-wide control | 577→477 | 210 | no tile cap | 0.0238 / 0.625 | 13.804 / 14.142 px | 12/16 | 5.6 / 10.3 / 11.6% |
| Three-wide long gap | 573→463 | 216 | no tile cap | 0.0324 / 0.875 | 10.739 / 11.885 px | 12/16 | 7.2 / 0 / 12.0% |
| Four-narrow control | 489→389 | 223 | no tile cap | 0.0314 / 0.875 | 12.081 / 12.093 px | 10/16 | 9.7 / 12.5 / 5.3% |
| Four-narrow long gap | 463→377 | 223 | no tile cap | 0.0224 / 0.625 | 9.381 / 10.308 px | 12/16 | 18.6 / 0 / 0% |
| Target tile control | 156→156 | 90 | no | 0.0333 / 0.375 | 10.883 / 12.649 px | 3/16 | 14.2 / 0 / 0% |
| Target tile long gap | 138→138 | 92 | no | 0.0435 / 0.500 | see JSON | 3/16 | 0 / 0 / 9.6% |

No tested configuration recovered M09, M10, or M16 to 80%, including the targeted tile. The Hough gap change improves some measurements in full ROI and three-wide, but worsens four-narrow precision/recall and leaves the target members far below threshold. The test5 full-image result also drops from 3 to 2 recovered members.

## Clutter and runtime interpretation

Joint precision is the existing objective clutter indicator: endpoint clusters inside each reference ROI that do not match confirmed joints count against precision. The runner also records raw Hough detections versus retained candidate segments and candidate-lines-per-endpoint-cluster. The raw-to-retained difference is **not** a pure duplicate count; it also includes length filtering, duplicate suppression, and the 300-line bound. No semantic false-member count is claimed.

The lower Canny cap pair drives `test1` from 153 to 300 candidates and 196 to 371 clusters while its joint precision falls; it also leaves `test2` and `test5` at the cap. This is evidence that added line response can grow clutter faster than useful structural geometry. The control `max_line_gap=12` decreases retained test5 lines and improves joint precision/recall, but its whole-image test5 member coverage declines by one.

For full images, detector runtime is five-call median around `detect_candidate_geometry`, matching the Phase A timing boundary. For tile layouts, detector-only time is the median of per-pass sums across tiles. Tile extraction/PNG encode and deduplication/cluster times are reported separately and were measured once for the deterministic mapped output; their sum with detector time is a pipeline estimate, not a repeated end-to-end timing statistic. For example, three-wide control/long-gap detector medians are 107.9/109.1 ms, with estimated pipeline times 308.0/302.9 ms; four-narrow is 72.4/70.3 ms detector-only and 232.4/216.5 ms estimated pipeline. The targeted tile control/long-gap detector medians are 25.1/22.7 ms, plus 3.8/3.9 ms extraction and 5.3/4.2 ms map/cluster. These are measured separately from one-time source decode.

## Overlays and files

- `experiment_config.json` — complete exact configuration list, stage design, fixed preprocessing, source hashes, and evaluation gates.
- `results.json` — baseline reproduction, per-image metrics, aggregate metrics, counts, caps, raw Hough counts, effective Canny thresholds, runtimes, layout comparisons, and selection record.
- `overlays/control/` and `overlays/control__hough_long_gap/` — comparable overlays for all five full images plus test5 ROI and all three established tile contexts.
- `evaluation/run_canny_hough_sweep.py` — evaluation-only runner; it constructs `PerceptionConfig` variants and calls the unchanged detector.

Reproduction command:

```bash
backend/.venv/bin/python evaluation/run_canny_hough_sweep.py
```

Focused test command:

```bash
cd backend && ./.venv/bin/python -m unittest tests.test_perception_parameter_sweep tests.test_perception_evaluation tests.test_perception_roi_experiment tests.test_overlapping_tile_experiment tests.test_rightmost_targeted_tile_experiment -v
```

Full suite and hygiene commands:

```bash
cd backend && ./.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

## Decision

Choose **C. Investigate image cleanup and structural-stroke separation** next. The Canny-low setting gains 3/53 members but drops joint precision by about 20% relative and causes a new cap hit; Hough gap gains only 1/53 in aggregate and regresses the test5 full-image coverage. The target members remain below threshold in every setting and layout. This result does not support promoting a parameter set, nor does it expose enough useful continuous fragments to prioritize reconstruction. First investigate whether page text, dimension marks, connector graphics, and other non-member strokes can be suppressed without hiding the truss. Any subsequent detector change still needs evaluation beyond these five sketches; no production change was made here.

Verification completed: focused evaluation tests **21 passed**, full backend suite **109 passed**, `git diff --check` **passed**. No real-browser behavior was tested.
