# Sketch2Solve agent handoff

## MANDATORY HANDOFF UPDATE RULE

After every meaningful implementation task, the coding agent must update this document in the same work session, before declaring the task complete. Record what changed, files changed, current behavior and interfaces, tests actually run and their results, new dependencies or configuration, decisions, remaining bugs/limitations/risks, the next recommended task, and any context a fresh agent needs. For documentation-only work, update the document without repetitive log entries. If tests cannot be run, record why; never report unexecuted tests as passing.

## Project overview

Sketch2Solve is intended to convert hand-drawn 2D truss sketches into editable structural models, analyze them with a deterministic solver, explain results, and eventually support export. The intended workflow is image input → geometric and semantic interpretation → structured truss model → validation → user correction → numerical analysis → visualization/export.

Implemented today: a Vue/Vite frontend scaffold; versioned truss-model validation and normalization; equilibrium matrix assembly; NumPy direct solving; matrix diagnostics; a Flask `POST /api/analyze` endpoint; a standalone OpenCV prototype that returns candidate image lines and clustered endpoints; and an isolated Muse Spark adapter that returns untrusted interpretation proposals. The frontend currently renders the Vite/Vue starter `HelloWorld` component and is not connected to the backend. User correction UI, export, and Muse route/UI integration remain planned.

## Technology stack

- Frontend: Vue 3, Vite 8, and PixiJS 8 are declared in `frontend/package.json`. The current source is still the starter app; PixiJS is not yet used by the application.
- Backend: Flask 3 with Flask-CORS. `backend/run.py` creates and runs the Flask app. The OpenAI-compatible `openai` Python SDK is used by the isolated Meta Muse adapter.
- Structural computation: NumPy arrays, SVD diagnostics, and `numpy.linalg.solve` in `backend/app/services/solver.py`.
- Domain model: frozen Python dataclasses in `backend/app/models/truss.py`.
- Tests: Python `unittest` tests under `backend/tests` covering validation, assembly, diagnostics, direct solution, and the Flask API.
- OpenCV: `opencv-python-headless` is declared in `backend/requirements.txt` and used by `perception.py` and to inspect input dimensions in the Muse adapter. Meta Muse Spark is called only by the standalone adapter; no Flask route invokes it.

## Repository structure

- `frontend/`: Vue/Vite client scaffold, styles, assets, and package metadata. New UI work normally belongs in `src/`.
- `backend/app/__init__.py`: Flask app factory, CORS configuration, `/api/health`, and `/api/analyze`.
- `backend/app/models/truss.py`: `Units`, `Node`, `Member`, `Support`, `Load`, `TrussModel`, and validation issue/result dataclasses.
- `backend/app/services/validation.py`: pure validation and normalization for schema version `1.0` requests.
- `backend/app/services/solver.py`: equilibrium assembly, matrix diagnostics, direct solution, residual checks, and solver result types.
- `backend/app/services/perception.py`: standalone image decoding, preprocessing, candidate line detection, endpoint clustering, JSON result serialization, and annotated PNG rendering. It does not assign structural meaning.
- `backend/app/services/muse_interpretation.py`: isolated Meta Muse Spark request and response validation. It returns a typed, proposal-only interpretation in original image pixel coordinates and is not wired to the solver or Flask routes.
- `backend/tests/`: unit and API tests. Add tests beside the service or route they cover.
- `backend/requirements.txt`: Python dependencies.
- `backend/.env.example`: placeholder-only `MODEL_API_KEY` setup example. Keep real credentials in an untracked local `.env` and never copy them into docs or test output.
- `backend/run.py`: local Flask entry point.

## Current implementation status

### Phase 1: input schema validation

`validate_truss_request(data)` returns `ValidationResult`. It accepts a JSON object with `schema_version: "1.0"`, `metadata.units` (`length` in `m`, `mm`, or `ft`; `force` in `N`, `kN`, or `lbf`), and `model` collections `nodes`, `members`, `supports`, and `loads`. It normalizes valid input into `TrussModel` and returns field-addressed `ValidationIssue` values on failure. It checks required/unknown fields, identifiers, duplicates, numeric finiteness, references, support types/directions, and zero-length members. Validation does not classify physical stability.

### Phase 2: equilibrium assembly

`assemble_equilibrium_system(model)` returns `EquilibriumSystem` with a coefficient matrix, RHS, deterministic equation labels, unknown labels, and force unit. Rows are node x/y equations; columns are members followed by support reactions. Applied loads move to the RHS with opposite sign. Member force is tension-positive; global x is right and y is up. Assembly raises `SolverAssemblyError` with codes such as `DUPLICATE_NODE_ID`, `UNKNOWN_NODE_REFERENCE`, `INVALID_SUPPORT`, `INVALID_LOAD`, and `INVALID_GEOMETRY` for invalid internal model data.

### Phase 3: direct numerical solution

`solve_equilibrium_system(system)` only accepts square, full-rank, acceptably conditioned systems and uses `numpy.linalg.solve`; it does not use least squares. It checks finite values, solution finiteness, and the equilibrium residual. `TrussSolution` is either `SOLVED` with complete values or `FAILED` with all value fields unset. Failure codes include `INVALID_SYSTEM`, `NONFINITE_SYSTEM`, `NONSQUARE_SYSTEM`, `RANK_DEFICIENT_SYSTEM`, `ILL_CONDITIONED_SYSTEM`, `NUMERICAL_DIAGNOSTIC_FAILED`, `LINEAR_SOLVE_FAILED`, `NONFINITE_SOLUTION`, `NONFINITE_RESIDUAL`, `RESIDUAL_TOO_LARGE`, and `INVALID_UNKNOWN_IDENTIFIER`.

The condition-number cutoff is `1e12`. Residual tolerance is `1e-12 + 1e-10 * scale`, where scale is derived from RHS and solved row force magnitudes. These are numerical heuristics, not engineering safety limits.

### Phase 4: matrix-level diagnostics

`diagnose_equilibrium_system(system)` reports equation/unknown counts, matrix shape, SVD-based numerical rank and tolerance, square/full-row/full-column properties, condition number when available, and one of `SQUARE_FULL_RANK`, `UNDERDETERMINED`, `OVERDETERMINED`, `SINGULAR_SQUARE`, `NUMERICALLY_ILL_CONDITIONED`, or `INVALID_SYSTEM`. A category describes matrix properties only; it is not a physical stability classification.

### Phase 5: Flask analysis endpoint

`POST /api/analyze` in `backend/app/__init__.py` performs parsing, validation, assembly, diagnostics, and solving in that order. Missing/non-JSON and malformed JSON return HTTP 400 with `INVALID_JSON` or `MALFORMED_JSON`. Semantic validation returns HTTP 422 with `VALIDATION_FAILED` and `validation_issues`. Assembly and solver failures return HTTP 422 with a stable solver/assembly `error_code`, message, and diagnostics where available; no partial `results` are returned. Unexpected programming errors are not broadly swallowed.

Successful responses are HTTP 200 JSON with `status: "SOLVED"`, `schema_version`, `units`, `diagnostics`, `results`, and `warnings`. Results contain `member_forces` keyed by member ID, `support_reactions` grouped by support ID and axis, `max_equilibrium_residual`, `residual_tolerance`, and `force_unit`. NumPy-derived values are converted to JSON-safe Python values. `/api/health` remains unchanged.

Reference triangular request: A=(0,0), B=(4,0), C=(2,3), members AB/AC/BC, pin at A, vertical roller at B, and a −10 kN y load at C. Under the implemented tension-positive convention: AB = `+10/3` kN, AC = BC = `-10*sqrt(13)/6` kN, A horizontal reaction = 0 kN, and both vertical reactions = 5 kN. Tiny floating-point values around zero are expected.

### Phase 4A: OpenCV visual geometry prototype

`detect_candidate_geometry(image_bytes, config=None)` in `backend/app/services/perception.py` accepts encoded image bytes and returns a `PerceptionResult`; invalid, empty, undersized (below 8×8), oversized, and undecodable images raise `PerceptionInputError`. Limits are 10 MiB encoded, 6000 pixels per dimension, and 24 million pixels. Decoding uses OpenCV's supported `imdecode` formats. Processing converts BGR to grayscale, applies a 5×5 Gaussian blur, selects Canny thresholds from the blurred-image median, then runs `HoughLinesP`.

`PerceptionConfig` exposes Canny, Hough, duplicate filtering, and endpoint clustering settings. Current Canny defaults are `sigma=0.8`, min threshold 40, and max threshold 160; these were adjusted after a low-contrast real photo and a synthetic pencil-like line demonstrated missed strokes under the previous defaults. Segments are canonicalized, sorted, and near-duplicates filtered using angle, line distance, and projected overlap. Hough output is bounded at 5,000 raw detections and 300 retained candidate lines. Stable IDs (`L001`...) follow sorted segment coordinates. Endpoints within the configured Euclidean pixel tolerance (default 12 px) are clustered transitively with deterministic union-find ordering; their joint coordinates are endpoint centroids. Joints carry `evidence: "endpoint_cluster"` and source line IDs. Interior intersections are intentionally deferred; they are not promoted to joints. `PerceptionResult.to_dict()` emits JSON-ready primitive values and states `coordinate_space: "image_pixels"`. `render_detections(image_bytes, result, show_ids=False)` returns annotated PNG bytes without opening a GUI; line IDs are opt-in because they collided with drawing text in dense inputs.

This service is independent of Flask and the truss model/validation schema. Its output is visual candidate geometry only, not truss members, supports, loads, or physical coordinates. Install dependencies from `backend/requirements.txt` into the backend environment; this environment was verified with Python 3.14.4 and `opencv-python-headless 4.14.0.94`.

### Isolated Muse Spark interpretation adapter

`interpret_truss_sketch(image_bytes, *, mime_type=None, timeout_seconds=60.0, client=None)` in `backend/app/services/muse_interpretation.py` accepts encoded JPEG, PNG, or WebP bytes (up to 50 MB, with 6000-pixel/24-million-pixel decoding bounds). It uses `MODEL_API_KEY`, base URL `https://api.meta.ai/v1`, and model `muse-spark-1.3`. The request sends the image inline as a base64 data URL, uses the Responses API and strict JSON Schema output, sets `store=False`, and disables automatic retries. The `client` injection point supports mocked testing.

Muse returns joint/support/load image points on its documented normalized 0–1000 grid; the adapter maps them to the original image's integer pixel range and includes original width/height plus coordinate convention `origin_top_left_x_right_y_down`. It does not map to physical units or solver coordinates. Its frozen `TrussInterpretationProposal` contains candidate joints, members, supports, loads, ambiguity notes, and missing information; `to_dict()` is JSON-ready and includes `proposal_only: true`. Member references, unique IDs, coordinate bounds, enum/boolean/string fields, finite load magnitudes, and paired magnitude/unit values are checked locally. Magnitudes and units are left null unless both were legible per the prompt.

Expected controlled failures derive from `MuseInterpretationError`: missing credentials (`MISSING_MODEL_API_KEY`), invalid encoded image (`INVALID_SKETCH_IMAGE`), timeout (`MUSE_TIMEOUT`), connection failure (`MUSE_NETWORK_ERROR`), API failure (`MUSE_API_ERROR`, with HTTP status when available), and malformed or invalid output (`INVALID_MUSE_RESPONSE`). Messages omit API response bodies and credentials. Invalid timeout values raise `ValueError` as caller configuration errors. No model API call is made by tests. This proposal is not automatically validated as a truss model, passed to `/api/analyze`, or treated as confirmed geometry.

Configuration: install the new `openai>=2.0,<3` dependency from `backend/requirements.txt` and set `MODEL_API_KEY` in the local environment. The example file contains only a placeholder. The local `.env` is not part of this integration and must remain untracked. SDK compatibility was inspected with OpenAI Python SDK 2.54.0; Meta's first-party documentation confirms base64 image input, Muse Spark 1.3, and Responses API schema-constrained output.

## Verification

Last verified on 2026-10-28 after the Muse adapter work:

```text
cd backend && ./.venv/bin/python -m unittest discover -s tests -v
Ran 62 tests ... OK
```

The full suite passed 62 tests, including 8 mocked Muse adapter tests; `git diff --check` passed. Python 3.14.4 imports OpenCV 4.14.0 and OpenAI SDK 2.54.0 in `backend/.venv`. No live Meta request was made. No frontend test command is configured beyond the package scripts (`dev`, `build`, `preview`).

## Architecture and engineering decisions

- Muse Spark is for sketch interpretation proposals and interaction, not engineering calculations. Its adapter is isolated and not integrated with a route or solver.
- Structural calculations remain deterministic and independent of AI-generated force values.
- OpenCV is used for preprocessing, candidate-line detection, and geometric evidence. It does not decide structural meaning.
- Any AI-derived model must pass the existing validation before reaching assembly and the solver.
- Ambiguous interpretations should be exposed for user correction.
- Matrix diagnostics must not be presented as definitive physical stability classifications.

These are accepted project directions. The isolated adapter is current code but has not been verified against a live account; treat every interpretation as untrusted visual proposal data.

## Known limitations and risks

- The solver rejects nonsquare systems and does not implement least-squares solving.
- Rank and condition diagnostics are numerical heuristics and do not establish every physical stability, mechanism, or load-path property.
- Residual and condition tolerances depend on float64 scaling and declared force units.
- The frontend is a scaffold and has no model editor, API client, visualization, or export flow.
- The OpenCV prototype is heuristic: Hough detections can split or miss strokes, or report drawing artifacts. Five real repository images have exploratory outputs, but none has expected-geometry annotations or quantitative scores.
- Endpoint clustering can merge distinct endpoints that happen to be close; its transitive pixel-distance rule is configurable. It does not detect interior line intersections.
- Multi-diagram and annotation-heavy images can hit the 300-line cap; page rules, labels, arrows, dimensions, and support symbols remain candidate lines. Softer Canny defaults improved a photographed low-contrast example but also increase clutter.
- The Muse adapter has not been exercised against a live Meta account or credential. JSON schema enforcement depends on the Meta endpoint honoring its documented OpenAI-compatible Responses API behavior. The adapter supports only JPEG, PNG, and WebP despite broader image-format support in upstream APIs.
- Sketch-to-model conversion, human correction UI, route-level upload handling, frontend integration, and export are not implemented.
- Passing tests demonstrates tested behavior, not engineering correctness for arbitrary structures.

## Current phase and next steps

The isolated Muse adapter is complete. The next recommended task is to plan a human-review integration boundary that can compare OpenCV evidence with Muse proposals, preserve unresolved ambiguities, and produce an explicitly user-confirmed model for existing validation. Before any live API smoke test, configure a local credential without recording it. Keep the adapter output as candidates for user review.

## Instructions for future AI agents

Read `overview_for_agents.md` before making changes. Inspect the actual implementation before assuming interfaces. Preserve existing behavior unless a change is intentional and documented. Work in small, testable phases. Do not silently weaken tests or claim engineering correctness based only on passing tests. Do not fabricate API capabilities, model IDs, credentials, or test results. Run the relevant tests and `git diff --check`. Update this document after each meaningful implementation phase. Never store secrets here.

## Implementation change log

### 2026-10-28 — Isolated Muse Spark interpretation adapter

- Files changed: `backend/app/services/muse_interpretation.py`, `backend/tests/test_muse_interpretation.py`, `backend/requirements.txt`, `backend/.env.example`, and this handoff.
- Behavior: added an injectable OpenAI-compatible Meta client, inline base64 image input, configurable timeout, strict structured output request, local response validation, and normalized-to-original-pixel coordinate mapping. The adapter returns a typed, proposal-only result and is not connected to Flask, perception semantics, or the solver.
- Configuration: added `openai>=2.0,<3`; documented `MODEL_API_KEY` using a placeholder only. No real `.env` was read or changed.
- Verification: OpenAI SDK 2.54.0 installed in `.venv`; full backend suite passed 62 tests, including mocked API/error/output tests. No external API calls were made. `git diff --check` passed.
- Limitations: only JPEG/PNG/WebP; no live API/account check; candidate interpretation still needs review and a separate validated conversion path before it can become a solver request.
- Next step: design a human review flow that combines visual evidence and model proposals into a user-confirmed, schema-valid truss model.

### 2026-10-28 — Phase 4B: real-image perception evaluation and limited fixes

- Files changed: `backend/app/services/perception.py`, `backend/tests/test_perception.py`, `evaluation/results/perception_evaluation.md`, `evaluation/results/` annotated PNG and JSON artifacts, and this handoff.
- Images: evaluated all five existing files in `backend/evaluation/sketches/`; all decoded, repeated identically, and serialized to strict JSON. No expected-geometry files were present.
- Findings: default ID labels obscured dense images; old Canny defaults missed a low-contrast pencil-like stroke and most visible lines in `test1.jpg`; `test2.jpg` and `test5.png` remain capped and noisy from page/text/dimension geometry. Thick stroke boundaries can also yield nearby duplicate-like lines.
- Fixes: disable ID labels by default (`show_ids=True` remains available) and lower Canny defaults to sigma 0.8/min 40/max 160. Added a synthetic low-contrast regression test and a check that optional ID rendering differs.
- Verification: baseline 53 tests passed before fixes; final 54 tests passed; Python 3.14.4 imports OpenCV 4.14.0; final `git diff --check` passed.
- Limitations: no ground-truth geometry, so no precision/recall or endpoint accuracy is measured. Multi-diagram selection, annotation suppression, robust stroke centerlines, interior crossing semantics, and resolution normalization remain unresolved.
- Next step: create labeled sketch examples with selected regions, line/joint annotations, and paired resolutions before further algorithm tuning.

### 2026-10-28 — Phase 4A: OpenCV candidate geometry prototype

- Files changed: `backend/app/services/perception.py`, `backend/tests/test_perception.py`, `backend/requirements.txt`, `overview_for_agents.md`.
- Behavior: added bounded image decoding, grayscale/blur/adaptive Canny preprocessing, Hough line candidates, deterministic near-duplicate filtering and endpoint clustering, JSON-ready results, and annotated PNG output. No application route or structural interpretation was added.
- Dependency: installed and verified `opencv-python-headless 4.14.0.94` in `backend/.venv`; requirement is `opencv-python-headless>=4.11,<5`.
- Verification at Phase 4A: pre-change baseline 46 tests passed; after changes 53 backend tests passed; `git diff --check` passed.
- Limitations: heuristic line detection; endpoint clusters only; interior crossings deferred; no representative real sketch evaluation yet.
- Next step: Phase 4B evaluation on representative sketches.

### 2026-10-28 — Phase 3 reported/current implementation: Flask analysis integration

- Files changed: `backend/app/__init__.py`, `backend/tests/test_api_analyze.py` (working-tree changes; verify history before committing).
- Behavior: added `POST /api/analyze`, structured success/failure responses, safe JSON serialization, and API tests for valid, malformed, invalid, singular, nonsquare, and health cases.
- Verification: 46 backend `unittest` tests passed; `git diff --check` passed.
- Limitations: direct solver restrictions and all perception/frontend limitations above remain.
- Next step at that time: OpenCV perception prototype (now started as Phase 4A).

### 2026-10-27 — Reported history: deterministic solver and diagnostics

The repository history contains commit `17982c1` dated 2026-10-27, titled “Implement truss equilibrium solver and diagnostics along with project scafold”. The exact implementation details are independently verified from the current source; phase labeling and historical task context are reported from repository history.

### 2026-10-26 — Verified repository history: project license

Repository history contains commit `1eede86` dated 2026-10-26, titled `chore: add MIT license`. This handoff document does not infer additional implementation work from that commit.
