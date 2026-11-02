# Phase A — perception accuracy baseline and reference audit

**Measured:** 2026-10-30 18:04 UTC
**Scope:** Fresh default-detector baseline, visual audit, conservative reference annotations, and exploratory metric methodology. No detector behavior or thresholds were changed.

## Reproduction and output contract

From the repository root:

```bash
backend/.venv/bin/python evaluation/run_perception_baseline.py \
  --input-dir backend/evaluation/sketches \
  --output-dir evaluation/results/phase-a-2026-10-30/detector-baseline \
  --repeats 5

backend/.venv/bin/python evaluation/perception_evaluation.py \
  --baseline evaluation/results/phase-a-2026-10-30/detector-baseline/baseline.json \
  --annotations evaluation/results/phase-a-2026-10-30/annotations \
  --output evaluation/results/phase-a-2026-10-30/metrics.json
```

The baseline is freshly measured with `detect_candidate_geometry(image_bytes)` and default `PerceptionConfig`, OpenCV 4.14.0. Each image was run five times; full outputs were identical across repeats. Runtime is reported as the median of those five process-local calls and is an approximate local measurement, not a performance guarantee. Each baseline record includes source SHA-256, detected MIME, dimensions, full detector JSON, settings, warnings, diagnostics, timing range, candidate cap status, and endpoint-cluster count. Candidate overlays are saved beside `baseline.json`.

Output schema is visual evidence only: `coordinate_space: "image_pixels"`; points use the decoded source raster, origin top-left, x right, y down. `lines[]` contains IDs, integer `start`/`end`, length, and `evidence: "probabilistic_hough"`. `joints[]` contains endpoint-centroid `point`, `evidence: "endpoint_cluster"`, contributing `line_ids`, and `endpoint_count`. These endpoint clusters include singleton groups and are **not confirmed structural joints**. The detector does not emit members, supports, loads, physical coordinates, or units. Interior segment crossings are not explicitly converted to joints.

## Fresh baseline measurements

All counts below are from the 2026-10-30 run, not copied from the 2026-10-28 exploratory report.

| Image | Actual format; dimensions | Candidate lines | Endpoint clusters | Cap | Median runtime (5 runs) | Warnings |
|---|---|---:|---:|---|---:|---|
| `test1.jpg` | WebP; 1800×2400 | 153 | 196 | No | 61.300 ms | None |
| `test2.jpg` | JPEG; 576×749 | 300 | 240 | Yes | 103.864 ms | Candidate output capped |
| `test3.png` | PNG; 1024×515 | 76 | 76 | No | 14.371 ms | None |
| `test4.jpg` | JPEG; 1300×403 | 49 | 61 | No | 8.254 ms | None |
| `test5.png` | PNG; 2046×1319 | 300 | 221 | Yes | 127.324 ms | Candidate output capped |

The fresh line and endpoint counts agree with the historical “final” counts. `test1.jpg` is mislabeled by extension: its bytes decode as WebP; the baseline records the content-detected format. At the cap, `test5.png`'s overlay shows that candidates are concentrated around the left side/text and only a small portion of the selected truss is represented; the cap is not evidence that the truss itself has 300 members.

## Visual annotation audit

Source images were reviewed independently of detector overlays. References are stored in `annotations/testN.json`, bound to image SHA-256, with coordinate/schema details in `ANNOTATION_SCHEMA.md`. The blue/orange previews are separate human-reference visualizations; detector overlays stay in `detector-baseline/`.

| Image | Reference assessment | What is confirmed / uncertain |
|---|---|---|
| `test1.jpg` | Confirmed, approximate | One rotated photographed free-body truss has a readable seven-joint/eleven-member graph. Paper perspective, low contrast, handwriting, and photo texture limit pixel precision. The dotted projection near B is explicitly ambiguous and excluded as a member. Loads/reactions/dimensions are out of scope. |
| `test2.jpg` | Ambiguous; no metric reference | Four rough truss/bridge alternatives share ruled paper, shadows, overdrawn abutments, and crowded intersections. Without selecting a target sketch, a single reference graph would be manufactured. Four ambiguous regions are recorded; no confirmed joints or members are labeled. |
| `test3.png` | Confirmed | Clean seven-joint/eleven-member diagram with explicit joint circles and clear centerlines. Load/support symbols and labels are excluded from the structural member reference. |
| `test4.jpg` | Confirmed | Isolated high-contrast nine-joint/fifteen-member truss. Support symbols are visible but excluded from the joint/member target. |
| `test5.png` | Main graph confirmed; crossing status ambiguous | The main eight-joint/sixteen-member graph is readable. Each of the three X-brace overlap locations is marked ambiguous as to connection/joint status; no crossing joint is asserted. The printed problem text, loads, dimensions, and supports are not labels for the joint/member metric. |

## Method and measured metrics

See `METHODOLOGY.md` for fixed thresholds and matching rules. Joint matching is one-to-one within `max(12 px, 0.75% of image diagonal)`. Endpoint localization error is measured on matched centroids. Candidate-line coverage recall counts a reference member once when the union of eligible line fragments covers at least 80% of its centerline, within the same distance corridor and 8° angular tolerance. The method unions fragment intervals to avoid double-counting a reference member.

`test2.jpg` is excluded from all metrics. Member precision is unavailable for every image because the detector emits raw candidate segments, not grouped/semantically classified member predictions. The member coverage metric is therefore reported by that name; it is not structural member precision or an end-to-end semantic member score.

| Image | Joint P | Joint R | Matched endpoint error mean | Candidate-line member coverage recall |
|---|---:|---:|---:|---:|
| `test1.jpg` | 0.040 | 0.571 | 10.05 px | 0/11 = 0.000 |
| `test2.jpg` | N/A | N/A | N/A | N/A |
| `test3.png` | 0.137 | 1.000 | 8.10 px | 9/11 = 0.818 |
| `test4.jpg` | 0.180 | 1.000 | 8.63 px | 15/15 = 1.000 |
| `test5.png` | 0.030 | 0.250 | 15.85 px | 3/16 = 0.188 |
| **Micro average, confirmed images only** | **0.082** | **0.710** | **9.38 px** | **27/53 = 0.509** |

Joint precision's denominator includes all detected endpoint clusters inside the annotated ROI; text, dimension marks, support/load graphics, and duplicate stroke endpoints can therefore be false candidates. These scores are exploratory and sensitive to approximate manual centers, ROI choice, and tolerance. Only four images have confirmed selected-region graphs, and the data has no expert adjudication or annotator-agreement estimate. Do not generalize these figures or treat them as engineering validation.

## Tests and limitations

- `cd backend && ./.venv/bin/python -m unittest discover -s tests -v` — **90 passed**, including five new synthetic evaluator/schema/matching tests and the existing perception suite.
- `backend/.venv/bin/python evaluation/run_perception_baseline.py ... --repeats 5` — completed over all five images with deterministic outputs.
- `backend/.venv/bin/python evaluation/perception_evaluation.py ...` — completed; generated machine-readable `metrics.json`.
- `git diff --check` — **passed**.
- No live AI/provider calls or new dependencies were used. `backend/app/services/perception.py` was not modified.

Limitations include the two-image candidate cap, clutter/duplicates, raw-pixel tolerance sensitivity, missing semantic member classification, rough and photographed source variation, one ambiguous multi-sketch page, and approximate hand placement. `test5.png` cap behavior makes full-page line extraction a poor evaluation target without selecting the truss region first.

## Highest-value next experiment

Evaluate a manually selected/cropped diagram ROI before running the unchanged detector on `test2.jpg` and `test5.png`, using the same detector settings and the confirmed reference graphs where available. `test2` contains four alternative sketches on one page; `test5` reaches 300 candidates and the saved overlay misses most of its truss. Comparing full-page versus selected-region output will isolate the value of diagram selection and test whether the candidate cap is being spent on structural geometry, without tuning thresholds or pretending candidates are members.
