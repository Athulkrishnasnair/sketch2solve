# Target-member failure diagnostic — 2026-10-31

## Scope and provenance

This evaluation-only diagnostic explains the unchanged OpenCV candidate segments around M09, M10, and M16 in `test5.png`. It reads the saved raw outputs from the original baseline, ROI, three-wide, four-narrow, and targeted-tile experiments; it did not rerun the detector. No production detector, threshold, annotation, prior result, dependency, AI provider, or browser workflow was changed or exercised.

The source image is 2046×1319 pixels. Its SHA-256 is `5fa616402e536ecb0907d699f6e0252f4fadc556df11a3cbb475e4f184b1ca36`, matching the baseline and all four experiment artifact sets. Coordinates are original decoded raster pixels, top-left origin, x right, y down. All tile detections are already mapped from tile-local coordinates by adding their recorded tile origins; there was no resize. The fixed evaluation ROI is `[365, 630, 1380, 420]` (right and bottom exclusive).

The unchanged annotation locates M09 at F `(1252,663)`→C `(1252,1023)`, M10 at E `(1693,663)`→D `(1693,1023)`, and M16 at C `(1252,1023)`→E `(1693,663)`. The three ambiguous X crossings `(601,843)`, `(1032,843)`, and `(1472,843)` remain ambiguous and excluded from joint scoring.

Measurements reuse the Phase A centerline rules: candidate angle difference ≤8°, maximum perpendicular endpoint distance to the annotated infinite centerline ≤18.257 px, positive projection on the finite reference segment, and an 80% union-coverage recovery threshold. The best single coverage segment is the largest eligible segment. Fragment unions report observed intervals and preserve gaps. Nearby segments that fail the angle gate are reported as response/clutter evidence, not member coverage. Endpoint proximity is separate from coverage.

## Candidate totals and saved aggregate metrics

| Layout | Raw segments | Cap | Endpoint clusters | 4 px deduplicated segments | Joint precision / recall | Mean matched endpoint error | Total member coverage |
|---|---:|---|---:|---:|---:|---:|---:|
| Original full image | 300 | Reached | 221 | — | 0.0299 / 0.250 | 15.845 px | 3/16 |
| Full ROI | 300 | Reached | 211 | — | 0.0237 / 0.625 | 10.277 px | 7/16 |
| Three-wide | 577 | No tile reached | 203 raw → 210 after dedup | 477 | 0.0238 / 0.625 | 13.804 px | 12/16 |
| Four-narrow | 489 | No tile reached | 246 raw → 223 after dedup | 389 | 0.0314 / 0.875 | 12.081 px | 10/16 |
| Targeted rightmost tile | 156 | Not reached | 90 (unchanged) | 156 | 0.0333 / 0.375 | 10.883 px | 3/16 |

Tiled raw segment IDs include tile ID and detector line ID. The full lists of raw IDs, original-image endpoint coordinates, provenance, per-member measurements, nearest raw endpoints, and fragment gaps are in `results.json`. These counts and aggregate scores are copied from the original experiment outputs; they were not recomputed with altered tolerances.

## Member-level observations

“Best eligible segment” is the strongest single segment admitted by the existing angle/corridor gates. Coordinates are source-image pixels. The nearby-response listing in `results.json` also includes top candidates within the corridor that fail the angle gate, ranked by overlap then offset; these should be read as possible local strokes or clutter, not members.

| Member / layout | Best eligible segment: ID, endpoints | Angle | Offset | Single / union coverage | Uncovered interval(s), member-axis px |
|---|---|---:|---:|---:|---|
| M09 original | none | — | — | 0 / 0% | `[0,360]` |
| M09 full ROI | none | — | — | 0 / 0% | `[0,360]` |
| M09 three-wide | `three_wide-T02:L165`, `(1250,989)`→`(1252,969)` | 5.7° | 2.0 px | 5.6 / 5.6% | `[0,306]`, `[326,360]` |
| M09 four-narrow | `four_narrow-T03:L055`, `(1257,988)`→`(1261,1036)` | 4.8° | 9.0 px | 9.7 / 9.7% | `[0,325]` |
| M09 targeted | `rightmost-target-T01:L029`, `(1242,760)`→`(1249,709)` | 7.8° | 10.0 px | 14.2 / 14.2% | `[0,46]`, `[97,360]` |
| M10 original | none | — | — | 0 / 0% | `[0,360]` |
| M10 full ROI | none | — | — | 0 / 0% | `[0,360]` |
| M10 three-wide | `three_wide-T03:L163`, `(1701,986)`→`(1702,1024)` | 1.5° | 9.0 px | 10.3 / 10.3% | `[0,323]` |
| M10 four-narrow | `four_narrow-T04:L100`, `(1691,718)`→`(1692,763)` | 1.3° | 2.0 px | 12.5 / 12.5% | `[0,55]`, `[100,360]` |
| M10 targeted | none | — | — | 0 / 0% | `[0,360]` |
| M16 original | none | — | — | 0 / 0% | `[0,569.28]` |
| M16 full ROI | none | — | — | 0 / 0% | `[0,569.28]` |
| M16 three-wide | `three_wide-T03:L041`, `(1252,1007)`→`(1300,977)` | 7.2° | 12.4 px | 9.9 / 11.6% | `[66.27,569.28]` |
| M16 four-narrow | `four_narrow-T03:L054`, `(1254,1036)`→`(1280,1010)` | 5.8° | 11.3 px | 5.3 / 5.3% | `[29.91,569.28]` |
| M16 targeted | none | — | — | 0 / 0% | `[0,569.28]` |

For M16 in three-wide, four eligible raw segments union to `[0,66.27]` from endpoint C, then leave a 503.01 px uncovered span. This is a short localized cluster of aligned responses followed by a long missing response, not evidence that a complete member is present. M09 and M10 have at most one eligible segment per layout, so there is no meaningful multi-fragment recovery to claim. No member reaches the existing 80% threshold in any layout.

The targeted raw candidate `rightmost-target-T01:L070` for M16 is only 0.15° from the member direction and overlaps 56.6% of the member's longitudinal span, but its centerline offset is 63.7 px, outside the existing 18.257 px corridor. It is therefore a nearby parallel/shifted stroke, not coverage. The top targeted M10 candidates similarly have offsets near the corridor but angular mismatches around 52–85°; the M09 targeted best candidate has acceptable angle/offset but only 14.2% longitudinal overlap. Exact data are in JSON and IDs are labeled on the overlays.

### Endpoint evidence

Prior experiment one-to-one joint matching gives the following per-member endpoint errors in order `F/C`, `E/D`, `C/E`. “—” means no matched cluster for that reference joint under the unchanged 18.257 px tolerance.

| Layout | M09 F/C | M10 E/D | M16 C/E |
|---|---|---|---|
| Original | — / — | — / — | — / — |
| Full ROI | 8.94 / 7.34 px | — / — | 7.34 / — px |
| Three-wide | 14.14 / 12.63 px | 14.56 / — px | 12.63 / 14.56 px |
| Four-narrow | 13.60 / — px | 10.77 / 12.09 px | — / 10.77 px |
| Targeted | 12.65 / 17.00 px | — / 3.00 px | 17.00 / — px |

Nearest raw segment endpoints can be close to a reference joint even if they are not part of an aligned, sufficiently long member response. For example, targeted M10 has a raw endpoint 3 px from D while no segment passes the M10 coverage gates. The per-joint nearest raw segment IDs and coordinates are separately recorded in `results.json`. This evidence does not support endpoint clustering as the primary cause of the three member misses: endpoint clusters can match several joints while the corresponding member centerlines remain under-covered.

## Failure-mode assessment

- **Missing line responses — strongly supported.** In original and ROI outputs, no M09/M10/M16 segments satisfy both existing geometry gates. Tiled runs recover only 5.3–14.2% of any target centerline. Large portions of the reference intervals have no eligible response at all.
- **Fragmentation — supported but limited.** M16 three-wide has four eligible short segments in one 66.27 px interval. M09/M10 have only one eligible segment in a layout at a time. Fragment merging cannot fill the large unobserved spans, and must not bridge the reported gaps.
- **Angular mismatch — supported for nearby non-coverage candidates, especially M10 and M16 in the targeted tile.** Some local segments overlap the member's longitudinal extent but are 39–85° off-angle. Correctly aligned fragments also exist in tiled layouts, so angle mismatch does not explain every failure.
- **Centerline offset — supported for some candidates.** Targeted `rightmost-target-T01:L070` is nearly parallel to M16 but 63.7 px offset, beyond the fixed corridor. It is an example of proximity without member coverage.
- **Duplicate/clutter responses — supported.** High raw line and endpoint counts, low joint precision (2–3.3%), and nearby off-angle strokes around connectors demonstrate clutter. The detector does not label candidates semantically, so individual nearby candidates are not all declared false positives; the objective gate failures are reported instead.
- **Endpoint clustering errors — not supported as the primary cause.** Several endpoints match joints within tolerance, including both M09 joints in some layouts, but their line coverage remains far below 80%. Clustering may affect joint metrics separately, but it cannot explain missing centerline length.

These are observations under the fixed Phase A thresholds. “Missing response” describes absence of qualifying raw candidate coverage, not the physical absence of a visible stroke in the source image.

## Overlays and machine-readable outputs

Five overlays in `overlays/` use the same source-coordinate crop `[1190,630,555,420]`: all raw candidates are faint gray; annotated M09/M10/M16 centerlines use distinct colors; the top three objectively nearby responses per member are highlighted and labeled with IDs; ambiguous crossings in view are orange. The full endpoint coordinates and all segment IDs remain in `results.json`.

- `diagnostic_config.json` — frozen source hash, input artifact list, coordinate region, scoring gates, and ambiguous points.
- `results.json` — all measured candidate geometries, segment provenance, best eligible segments, angular/offset/overlap values, union intervals and gaps, endpoint proximity, and per-layout candidate/cap counts.
- `overlays/original_target_members.png`
- `overlays/full_roi_target_members.png`
- `overlays/three_wide_target_members.png`
- `overlays/four_narrow_target_members.png`
- `overlays/targeted_tile_target_members.png`

Reproduction command:

```bash
backend/.venv/bin/python evaluation/diagnose_target_member_failures.py
```

Verification commands:

```bash
cd backend && ./.venv/bin/python -m unittest tests.test_target_member_failure_diagnostic tests.test_perception_evaluation tests.test_perception_roi_experiment tests.test_overlapping_tile_experiment tests.test_rightmost_targeted_tile_experiment -v
cd backend && ./.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

Results: focused evaluation suite **21 passed**; full backend suite **106 passed**; `git diff --check` **passed**. The diagnostic generator completed successfully. The source file hash matched the fixed experiment artifacts. No real-browser verification was performed.

## Recommendation

Test **A. Adaptive Canny/Hough parameters** first, in a separate offline evaluation sweep with unchanged annotations and coverage gates. The strongest evidence is missing qualifying line response across most of each target centerline, with only small correctly aligned fragments in some tiled outputs. Fragment merging (B) cannot recover hundreds of pixels without observed strokes; endpoint clustering (C) cannot repair centerline absence. A parameter sweep can directly test whether those visible but weak/overdrawn strokes yield additional aligned response while tracking the substantial clutter and cap/precision costs. If that controlled sweep fails to increase target coverage without worsening clutter materially, then test D, a different stroke-detection approach. This is a recommendation for the next experiment only; no detector improvement is implemented here.

## Verification

The diagnostic does not verify upload/edit/save/review/solve in a real browser.
