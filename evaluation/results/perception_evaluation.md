# Phase 4B perception evaluation

## Run details

- Evaluation date: 2026-10-28.
- Environment: Python 3.14.4 in `backend/.venv`; OpenCV headless 4.14.0.
- Inputs: all five files found in `backend/evaluation/sketches/`. The requested root `evaluation/sketches/` directory did not exist. No expected-geometry or annotation files were found, so every input is an exploratory test and no precision, recall, or geometric-accuracy score is claimed.
- Interface: `detect_candidate_geometry(image_bytes, PerceptionConfig())`, called twice per image. Results were compared by value and serialized with `json.dumps(result.to_dict(), allow_nan=False)`. Annotated PNGs were created with `render_detections`.
- Before-fix defaults: `canny_sigma=0.33`, Canny min/max `30/220`; annotations displayed IDs by default.
- Final defaults: `canny_sigma=0.8`, Canny min/max `40/160`; annotation IDs are opt-in. Final line and endpoint counts below are after both changes.
- All five images decoded. All repeated runs were equal and all outputs serialized as strict JSON. The actual image runs raised no exceptions.

To repeat with the same environment, call the service on each file in `backend/evaluation/sketches/` using default `PerceptionConfig()`, call it a second time and compare the results, run `json.dumps(result.to_dict(), allow_nan=False)`, and save `render_detections(image_bytes, result)` under a new filename. Existing outputs in this folder are preserved as initial and final snapshots.

## Inventory and results

| Image | Format / dimensions (px) | Suitable for current pipeline? | Before: segments / endpoint clusters | Final: segments / endpoint clusters | Warning | JSON valid | Repeatable | Issues |
|---|---|---|---:|---:|---|---|---|---|
| `test1.jpg` | JPEG, 1800×2400 | Exploratory; photographed tan paper, rotated drawing, low contrast, uneven light, handwritten labels and arrows | 28 / 41 | 153 / 196 | None | Yes | Yes | Original defaults mostly found page edges and small marks; final thresholds expose several visible truss diagonals but also text and page artifacts. |
| `test2.jpg` | JPEG, 576×749 | Poor fit; several rough diagrams share ruled paper, with shadows and dense strokes | 300 / 275 | 300 / 240 | Candidate line output capped | Yes | Yes | Multiple diagrams and paper rules dominate; returned geometry is highly cluttered. |
| `test3.png` | PNG, 1024×515 | Useful clean diagram, but includes labels, load arrows, and support symbols | 67 / 67 | 76 / 76 | None | Yes | Yes | Main truss outline appears strongly; labels, arrows, and support details also generate candidates. |
| `test4.jpg` | JPEG, 1300×403 | Best fit; clean high-contrast truss on a gray field, with support symbols | 49 / 61 | 49 / 61 | None | Yes | Yes | Main geometry is clear; support details and multiple stroke edges add candidates. |
| `test5.png` | PNG, 2046×1319 | Exploratory; textbook truss plus prose, labels, arrows, dimensions, and cross-bracing | 300 / 291 | 300 / 221 | Candidate line output capped | Yes | Yes | Text, dimensions, and load/support symbols create many unrelated candidates; line cap is reached. |

The before counts and JSON snapshots are `testN_detections_opencv_4_14_0.json`; final counts and snapshots are `testN_final_default_opencv_4_14_0.json`. The `endpoint clusters` count includes singleton endpoint groups; it is not a count of confirmed physical joints.

## Annotated outputs

Initial annotations, with segment IDs enabled, preserve the original behavior for comparison:

- [`test1 initial`](test1_annotated_opencv_4_14_0.png)
- [`test2 initial`](test2_annotated_opencv_4_14_0.png)
- [`test3 initial`](test3_annotated_opencv_4_14_0.png)
- [`test4 initial`](test4_annotated_opencv_4_14_0.png)
- [`test5 initial`](test5_annotated_opencv_4_14_0.png)

Final annotations use the revised thresholds and omit IDs unless explicitly requested:

- [`test1 final`](test1_final_default_opencv_4_14_0.png)
- [`test2 final`](test2_final_default_opencv_4_14_0.png)
- [`test3 final`](test3_final_default_opencv_4_14_0.png)
- [`test4 final`](test4_final_default_opencv_4_14_0.png)
- [`test5 final`](test5_final_default_opencv_4_14_0.png)

An intermediate annotation-only snapshot (`*_after_ids_off_annotated_*.png`) records the ID-display change before the threshold adjustment. Files use new output names; source images were not changed.

## Findings and fixes

| Image / risk | Expected behavior | Actual behavior and evidence | Likely cause | Severity / repeatability | Fix and regression coverage |
|---|---|---|---|---|---|
| `test2.jpg`, `test3.png`, `test5.png`: visualization IDs | IDs should help inspect detections without obscuring the source | Initial previews show labels colliding with one another and with sketch text on dense images; repeatable with the default renderer | Every line ID was drawn at its midpoint even when many detections were close | Low; reproduced in the initial saved annotations | Fixed: `render_detections(..., show_ids=False)` by default, with explicit opt-in. Test asserts outputs differ when IDs are enabled. |
| `test1.jpg`: low-contrast missed lines | Candidate output should expose visible long strokes in a photographed pencil sketch | Before fix, 28 segments were mostly around page edges/small marks; the preview misses most central truss strokes. After fix, 153 segments include several visible central diagonals, alongside artifacts. A synthetic 60-level contrast stroke also changes from zero to a line candidate under defaults. | Canny thresholds derived from the median brightness were too high for low-contrast strokes | Medium; repeated on the saved photo and synthetic input | Partially addressed: gentler defaults (`sigma=.8`, thresholds `40/160`) and a synthetic low-contrast regression test. The photo still has missed or fragmented members and artifacts. |
| `test2.jpg`, `test5.png`: line cap and clutter | Report useful candidates without losing important geometry to unrelated page/text lines | Both still return 300 segments and a cap warning; ruled lines, text, dimensions, arrows, and diagram elements are visible in the annotations | Hough detects every strong line-like mark; there is no page-rule removal, diagram crop/selection, or text/annotation filtering. The deterministic cap limits output but cannot prioritize truss geometry | Medium; reproduced on both images | Not fixed. Correctly separating multiple diagrams and suppressing text/dimensions needs a broader perception step and labeled examples. |
| `test3.png`, `test4.jpg`, `test5.png`: stroke edges / duplicate-like candidates | A thick drawn member ideally has one centerline candidate | Some thick strokes show two nearby red tracks or extra short segments around support details | Canny detects stroke boundaries; current geometric deduplication only removes sufficiently overlapping, near-collinear segments | Low to medium; visible in saved previews | Not fixed. Centerline/skeleton extraction risks merging nearby members and needs separate evaluation. |
| `test1.jpg`, `test2.jpg`, `test3.png`, `test5.png`: arrows, labels, supports, dimensions | Keep candidate output visual and avoid claiming semantics | Text and symbols appear as line candidates. No result says these are members; each line remains `probabilistic_hough` evidence | The detector is intentionally line-based and has no semantic classification | Medium; visible and repeatable | Not fixed by design. Require review or future semantic interpretation; do not feed candidates straight into structural analysis. |
| Interior crossings | Do not silently confirm every crossing as a joint | The service has no explicit segment-intersection inference. Endpoint clusters are labeled `endpoint_cluster`, though a Hough split at a crossing can still place endpoints nearby and form a candidate cluster | Endpoint clustering cannot distinguish a structural joint from a visual crossing | Risk remains; no ground truth to score | No change. Preserve “candidate” semantics and investigate on labeled crossing examples later. |
| Endpoint merge/split accuracy | Merge intended joints while keeping distinct nearby endpoints separate | Outputs can be inspected, but no reference joint coordinates exist for these images; correctness is N/A | Default 12 px transitive clustering can merge chains whose total span exceeds 12 px; image pixel scale varies | Unscored; no reproducible mismerge established here | Not changed. Collect labeled endpoint examples before changing tolerance/algorithm. |
| Image quality / JPEG / shadows | Decode and return candidates for supported inputs | All five saved JPEG/PNG files decoded. `test1` has uneven lighting; `test2` is shadowed/noisy. Counts are not proof that all geometry survived | Current blur/Canny/Hough approach is sensitive to contrast, texture, and artifacts | Successful decode is reproducible; geometric quality varies as above | No additional fix. Representative failure cases remain. |
| Resolution sensitivity | Similar geometry should have comparable pixel-space detections after scaling | N/A: no equivalent drawing appears at multiple resolutions, and no expected geometry is defined | The current set cannot isolate resolution from content/style | Unmeasured | Add paired scaled images to a future labeled evaluation; tolerance is currently in raw pixels. |
| Corrupt / unsupported / oversized input | Raise controlled errors rather than crash | No corrupt file exists in the evaluation directory. Service tests cover invalid bytes, undersized images, encoded-size limit, and decoded-dimension limit; these raise `PerceptionInputError` | OpenCV decode failure is converted to the service error; size guards are in the service | Covered by tests, not by saved evaluation images | No new bug observed. A valid file format outside this OpenCV build's decoder support was not available to test. |

## Before-and-after summary

The threshold adjustment increased visible long-stroke detections on `test1.jpg` (28 to 153 total candidates) and on the clean diagram `test3.png` (67 to 76), with `test4.jpg` unchanged. `test2.jpg` and `test5.png` remain at the 300-candidate cap. The increase is not a precision/recall improvement claim: there is no ground truth, and additional lines also include artifacts. Turning IDs off by default materially clears the rendered source, but dense line and endpoint overlays remain noisy.

## Limitations and next step

This is an exploratory visual-evidence service only. It produces pixel coordinates, not member centerlines or physical measurements; candidate segments and endpoint clusters are not validated truss members/joints. It does not handle multiple drawing selection, page-rule removal, text/arrow/support classification, perspective correction, interior crossing interpretation, or resolution normalization. The 300-line cap can truncate useful geometry. No real-image expected-geometry annotations were found.

Recommended next step: create a small labeled evaluation set with one selected sketch region per image and approximate line/joint annotations, including paired resolutions and cluttered examples. Use it to tune stroke-centerline/deduplication and annotation suppression, retaining user review before any candidate reaches validation or the solver.
