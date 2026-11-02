# Overlapping tile experiment — 2026-10-30

## Design fixed before detection

Source: `test5.png` (2046×1319), exact existing ROI `[365, 630, 1380, 420]`. Coordinates and origins are original-image pixels, origin top-left, x right, y down; right/bottom bounds are exclusive. Configurations were selected from the ROI and annotated bay spacing before detector output was collected.

| Layout | Tile size | Overlap | Origins (x,y), original pixels | Rationale |
|---|---:|---:|---|---|
| `three_wide` | 600×420 | 210 px horizontal (35%); 0 vertical | (365,630), (755,630), (1145,630) | Each tile is wider than one roughly 440 px bay, retaining neighboring-bay context with three calls. |
| `four_narrow` | 480×420 | 180 px horizontal (37.5%); 0 vertical | (365,630), (665,630), (965,630), (1265,630) | Each tile is about one bay wide, reducing horizontal scene width while retaining boundary context. |

Both layouts cover the ROI exactly with no partial tiles or padding. `tile_config.json` also records an edge-alignment policy for non-divisible future ROIs. Tiles are PNG-encoded from decoded source pixels; no resizing is done.

The unchanged default detector ran five times per tile; each tile's outputs were deterministic. Runtime covers detector calls only, excluding crop/encoding and deduplication, matching the timing boundary of the original and ROI runs. Tiled runtime is the median of five per-pass sums over all tiles.

## Deduplication and tolerance sensitivity

Deduplication is evaluation-only. At the primary 4 px perpendicular tolerance, a pair can match only across different tiles, with orientation difference ≤4°, symmetric endpoint-to-line distance ≤4 px, projected overlap at least 35% of the shorter segment, and at least one endpoint within 4 px of the other finite segment. Reversed endpoint order is immaterial. Deterministic greedy complete-link grouping prevents transitive chains and allows at most one detection per tile in a group. The merged segment is the union of observed projected intervals along a length-weighted mean orientation, at median normal offset; gaps are not bridged. All source tile/line IDs, origins, and mapped endpoints are retained.

The primary distance matches the detector's existing 4 px duplicate-distance scale; 35% overlap was chosen to admit partial boundary fragments. Sensitivity values are 2, 4, and 8 px. Combined lines and endpoint clusters are reconstructed before evaluation; metrics are never averaged across tiles. Joint/centerline tolerances are the existing Phase A values. A 6 px separation can merge at 8 px (covered by a synthetic test), so larger tolerance is not automatically safer.

| Layout | Raw lines | Tol. | After dedup | Removed (%) | Joint P/R | Mean endpoint error | Member coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| `three_wide` | 577 | 2 px | 494 | 83 (14.4%) | 0.0191 / 0.500 | 14.097 px | 12/16 (0.750) |
| `three_wide` | 577 | 4 px | 477 | 100 (17.3%) | 0.0238 / 0.625 | 13.804 px | 12/16 (0.750) |
| `three_wide` | 577 | 8 px | 464 | 113 (19.6%) | 0.0282 / 0.750 | 13.159 px | 12/16 (0.750) |
| `four_narrow` | 489 | 2 px | 395 | 94 (19.2%) | 0.0314 / 0.875 | 12.081 px | 10/16 (0.625) |
| `four_narrow` | 489 | 4 px | 389 | 100 (20.4%) | 0.0314 / 0.875 | 12.081 px | 10/16 (0.625) |
| `four_narrow` | 489 | 8 px | 383 | 106 (21.7%) | 0.0310 / 0.875 | 12.100 px | 10/16 (0.625) |

For `three_wide`, joint recall varies from 0.500 to 0.750 as tolerance grows, while member coverage stays at 12/16. For `four_narrow`, recall and member coverage are stable, and line removals vary from 94 to 106. The primary 4 px figures are used below.

## Comparison at the primary 4 px tolerance

| Condition | Lines | Cap | Clusters | Median detector runtime | Joint P/R | Endpoint error mean/median | Member coverage |
|---|---:|---|---:|---:|---:|---:|---:|
| Original full image | 300 | Reached | 221 | 127.324 ms | 0.0299 / 0.250 | 15.845 / 15.845 px | 3/16 (0.188) |
| Existing full ROI | 300 | Reached | 211 | 84.989 ms | 0.0237 / 0.625 | 10.277 / 9.795 px | 7/16 (0.438) |
| `three_wide`, deduplicated | 477 (577 raw) | No tile reached cap | 210 | 99.934 ms | 0.0238 / 0.625 | 13.804 / 14.142 px | 12/16 (0.750) |
| `four_narrow`, deduplicated | 389 (489 raw) | No tile reached cap | 223 | 64.681 ms | 0.0314 / 0.875 | 12.081 / 12.093 px | 10/16 (0.625) |

All tiles stayed below the 300-line cap:

| Tile | Origin | Lines | Clusters | Cap | Median runtime |
|---|---:|---:|---:|:---:|---:|
| `three_wide-T01` | (365,630) | 180 | 115 | No | 30.261 ms |
| `three_wide-T02` | (755,630) | 219 | 117 | No | 40.845 ms |
| `three_wide-T03` | (1145,630) | 178 | 115 | No | 29.491 ms |
| `four_narrow-T01` | (365,630) | 124 | 78 | No | 16.759 ms |
| `four_narrow-T02` | (665,630) | 124 | 94 | No | 16.173 ms |
| `four_narrow-T03` | (965,630) | 124 | 90 | No | 15.927 ms |
| `four_narrow-T04` | (1265,630) | 117 | 79 | No | 16.001 ms |

The `three_wide` layout recovers more reference members; `four_narrow` has higher joint recall and precision with lower measured detector-call time. Neither dominates across metrics. Member precision is unavailable because raw segments are not classified member hypotheses.

## Rightmost bay and overlay review

The rightmost bay reference consists of M03, M06, M09, M10, M15, and M16. Original and full-ROI results recover 0/6 at the 80% coverage threshold. Both tiled layouts recover 3/6: M03 (top chord), M06 (bottom chord), and M15 (one diagonal). M09 and M10 (verticals) and M16 (the other diagonal) remain below threshold. Overlays show strokes across this bay, but the member-level coverage confirms several are too fragmented or misaligned to count as recovered.

Tiling reveals more annotated centerlines and removes page prose from detection. Dense duplicate strokes remain around printed connectors and joints, and tile outputs contain partial lines at boundaries; some fragments are reconciled by overlap deduplication, while others do not meet its explicit rule. The three X crossings remain marked ambiguous in the config, annotation, and overlays and are excluded from joint scoring. Candidate strokes at a crossing do not establish connectivity.

The measurements support improved candidate-line coverage and removal of per-image cap saturation, but do not establish structural meaning or a reliable truss graph. Results are specific to this raster and deduplication heuristic.

## Artifacts and verification

- `tile_config.json` — dimensions, overlaps, origins, edge policy, rationale, mapping, deduplication rules, and ambiguity markers.
- `results.json` — per-tile counts/timings, mapped detections and provenance, raw/deduplicated counts, tolerance sensitivity, member coverage, and comparison metrics.
- `overlays/` — original and previous ROI overlays plus raw and deduplicated overlays for each layout.
- `tiles/` — per-tile detector overlays.
- Runner: `evaluation/run_overlapping_tile_experiment.py`.
- Tests: `backend/tests/test_overlapping_tile_experiment.py`.

The runner was executed with five repeats. Relevant evaluation tests passed (17); the full backend suite passed (102); `git diff --check` passed after documentation was updated. No dependencies, live AI calls, annotation/baseline changes, or production detector modifications were made.

## Next experiment

Run a shifted 480×420 grid that places one full tile around the rightmost bay's two verticals and both diagonals, with the same deduplication and reference. Current layouts both miss three members there; a grid-phase shift directly tests whether tile boundaries truncate those strokes. Fix the grid before detection and compare it to these recorded layouts.
