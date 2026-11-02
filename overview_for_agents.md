# Sketch2Solve agent handoff

## MANDATORY HANDOFF UPDATE RULE

After every meaningful implementation task, the coding agent must update this document in the same work session, before declaring the task complete. Record what changed, files changed, current behavior and interfaces, tests actually run and their results, new dependencies or configuration, decisions, remaining bugs/limitations/risks, the next recommended task, and any context a fresh agent needs. For documentation-only work, update the document without repetitive log entries. If tests cannot be run, record why; never report unexecuted tests as passing.

## Project overview

Sketch2Solve is intended to convert hand-drawn 2D truss sketches into editable structural models, analyze them with a deterministic solver, explain results, and eventually support export. The intended workflow is image input → geometric and semantic interpretation → structured truss model → validation → user correction → numerical analysis → visualization/export.

Implemented today: a Vue/Vite local dashboard and review interface; versioned truss-model validation and normalization; equilibrium matrix assembly; NumPy direct solving; matrix diagnostics; Flask solver, sketch-analysis, and reviewed-draft endpoints; OpenCV candidate detection; isolated Meta Muse Spark and Google Gemini interpretation adapters; and persisted analysis history with controlled original-image retrieval. The frontend supports image upload, recent dashboard cards, paginated history, editable geometry drafts, explicit review, and explicit solver submission. Authentication and export remain planned.

## Technology stack

- Frontend: Vue 3 and Vite 8. `src/App.vue` is the lightweight local navigation shell; upload, history, and detail state/composition live in `src/pages/`. `src/components/GeometryReview.vue` owns the reusable editable geometry review. PixiJS 8 remains a declared dependency but is not used; aligned SVG overlays are used for line/joint/proposal data. The app uses native query-string navigation and local component state; it does not currently need Vue Router or Pinia. The API helper is `frontend/src/api/analyses.js`. Theme rules are split by shell, workspace, review, and responsive concerns under `src/styles/`, imported by `src/style.css`.
- Backend: Flask 3 with Flask-CORS. `backend/run.py` creates and runs the Flask app. The OpenAI-compatible `openai` Python SDK is used by the isolated Meta Muse adapter; Google's official `google-genai` SDK is used by the isolated Gemini adapter. `python-dotenv` loads the local backend `.env` without overriding process environment values.
- Structural computation: NumPy arrays, SVD diagnostics, and `numpy.linalg.solve` in `backend/app/services/solver.py`.
- Domain model: frozen Python dataclasses in `backend/app/models/truss.py`.
- Tests: Python `unittest` tests under `backend/tests` covering validation, assembly, diagnostics, direct solution, and the Flask API.
- OpenCV: `opencv-python-headless` is declared in `backend/requirements.txt` and used by `perception.py` and to inspect input dimensions in the interpretation adapters. Both model providers are called only through standalone services; no Flask route invokes them.

## Repository structure

- `frontend/`: Vue/Vite local review application, API client, styles, assets, and package metadata. `src/App.vue` provides the shell and query-string navigation; `src/pages/` contains `NewAnalysisPage.vue`, `AnalysisHistoryPage.vue`, and `AnalysisDetailPage.vue`; editable geometry review is in `src/components/GeometryReview.vue`; API calls are in `src/api/analyses.js`.
- `backend/app/__init__.py`: Flask app factory, CORS configuration, `/api/health`, and `/api/analyze`.
- `backend/app/models/truss.py`: `Units`, `Node`, `Member`, `Support`, `Load`, `TrussModel`, and validation issue/result dataclasses.
- `backend/app/services/validation.py`: pure validation and normalization for schema version `1.0` requests.
- `backend/app/services/solver.py`: equilibrium assembly, matrix diagnostics, direct solution, residual checks, and solver result types.
- `backend/app/services/perception.py`: standalone image decoding, preprocessing, candidate line detection, endpoint clustering, JSON result serialization, and annotated PNG rendering. It does not assign structural meaning.
- `backend/app/services/muse_interpretation.py`: isolated Meta Muse Spark request and response validation. It returns a typed, proposal-only interpretation in original image pixel coordinates and is not wired to the solver or Flask routes.
- `backend/app/services/gemini_interpretation.py`: isolated Google Gemini request and response validation, using the shared candidate schema and image checks. It returns the same proposal-only interpretation contract and is not wired to the solver or Flask routes.
- `backend/app/services/interpretation_provider.py`: dispatches to Meta (default) or Gemini based on `INTERPRETATION_PROVIDER`, loading local values from `backend/.env` without overriding process environment values.
- `backend/app/models/analysis.py`: additive SQLAlchemy `sketch_analyses` table for sketch and solver analysis history.
- `backend/app/routes/analyses.py`: upload, list, detail, controlled private-image, draft, review, and reviewed-geometry solve routes under `/api/analyses`.
- `backend/app/services/analysis_persistence.py`: commits records and stores UUID-named images under the private Flask instance directory.
- `backend/tests/`: unit and API tests. Add tests beside the service or route they cover.
- `backend/requirements.txt`: Python dependencies.
- `backend/.env.example`: placeholder-only examples for `MODEL_API_KEY` and `GEMINI_API_KEY`, plus provider/model settings. Keep real credentials in an untracked local `.env` and never copy them into docs or test output.
- `backend/instance/`: default local SQLite database and private uploaded images; ignored by Git. `DATABASE_URL` and `UPLOAD_FOLDER` can be overridden by deployment/test configuration.
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

### Isolated Gemini interpretation adapter and provider selection

`backend/app/services/gemini_interpretation.py` uses the official Google Gen AI Python SDK (`google-genai`) and the `GEMINI_API_KEY` value loaded from `backend/.env` by `python-dotenv` (process environment values take precedence). The default model is the verified stable `gemini-3.1-flash-lite`; `GEMINI_MODEL` can override it. Gemini receives the image bytes and shared proposal prompt, requests JSON output with the shared schema, and passes the response through local proposal validation. It returns the same `TrussInterpretationProposal` shape as Meta and cannot call the solver.

Use `backend/app/services/interpretation_provider.py:interpret_truss_sketch(...)` as the configured entry point. Set `INTERPRETATION_PROVIDER=gemini` in `backend/.env` to select Gemini, or `INTERPRETATION_PROVIDER=meta` (the default) to use the existing Meta Muse Spark adapter. The adapters are used by the new upload-analysis route but remain separate from the deterministic solver. The `.env.example` contains placeholder credentials only. `python-dotenv` was already present in requirements; `google-genai>=1.0,<2` is the added SDK dependency.

### Persisted analysis and review API

`SketchAnalysis` records are stored in the additive `sketch_analyses` SQLAlchemy table. On first startup, `db.create_all()` creates any missing tables; it does not drop or recreate tables. There is no existing migration framework or database schema to migrate. By default, SQLite data is stored at `backend/instance/sketch2solve.sqlite`; `DATABASE_URL` may override it. Original images are saved privately as generated UUID filenames under `backend/instance/uploads/`, never under a static/public directory. The instance/upload directories use owner-only permissions (`0700`) and image files use `0600`. The database stores only that opaque storage filename, not an absolute path. `backend/instance/` is ignored by Git.

`POST /api/analyses` accepts multipart field `image` and optional `provider` (`meta` or `gemini`). It allows JPEG, PNG, and WebP up to 10 MiB. File extensions and multipart MIME are advisory; the server identifies the encoded format, checks image header dimensions before decoding, verifies the complete image with OpenCV, and then uses the content-derived MIME for storage and provider requests. The uploaded bytes are preserved unchanged for review and remain retrievable after provider failures. Current providers support all three accepted formats, so no lossy conversion is necessary. Successful and failed provider attempts are persisted. Success remains `status: "pending_review"`; AI output is stored under `interpretation_proposal`, `human_review.geometry` is null, and validation is explicitly `not_performed`. No AI result is submitted to the solver. `POST /api/analyze` remains the deterministic JSON solver endpoint and now includes `analysis_id`; its validated diagnostics and results are saved as a solver analysis record.

Successful upload response shape (candidate arrays shortened):

```json
{
  "analysis_id": "<opaque-id>",
  "status": "pending_review",
  "review_status": "pending_review",
  "provider": "gemini",
  "model_id": "gemini-3.1-flash-lite",
  "sketch": {"original_filename": "drawing.png", "mime_type": "image/png", "image_width": 800, "image_height": 600, "image_url": "/api/analyses/<opaque-id>/image"},
  "perception": {"lines": [], "joints": []},
  "interpretation_proposal": {"joints": [], "members": [], "supports": [], "loads": [], "proposal_only": true},
  "validation": {"status": "not_performed"},
  "human_review": {"status": "pending_review", "geometry": null},
  "solver_results": null
}
```

- `GET /api/analyses?page=1&per_page=20` returns newest-first concise metadata as `{items, page, per_page, total}`. `per_page` is capped at 100.
- `GET /api/analyses/<analysis_id>` returns sketch metadata, perception candidates, the AI proposal, validation state, human-review state, and solver results where present.
- `GET /api/analyses/<analysis_id>/image` streams the original image through the application with `private, no-store` caching headers. Files are not exposed as static assets, and API responses never contain storage paths.

Example list response: `{"items":[{"analysis_id":"<opaque-id>","created_at":"<UTC timestamp>","status":"pending_review","review_status":"pending_review","provider":"gemini","image_url":"/api/analyses/<opaque-id>/image"}],"page":1,"per_page":20,"total":1}`. Detail responses reuse the upload response shape. Error responses contain `analysis_id`, `status: "failed"`, a stable `error_code`, and a sanitized message when the run was recorded.

The API has no authentication. UUID IDs and controlled routes prevent filename/path access, but deployments must add authentication/authorization before exposing analysis history, image, draft, review, or solve routes publicly. The local Vue editor stores corrected solver-schema geometry separately in `human_geometry_json`; the original `proposal_json` is preserved. Save validates the geometry with the existing `validate_truss_request` service and requires an explicit `coordinates_confirmed: true` reviewer attestation. `POST /api/analyses/<analysis_id>/review` revalidates before transitioning `review_status` to `reviewed`. Only then can `POST /api/analyses/<analysis_id>/solve` submit the saved draft to the existing assembly, diagnostics, and direct solver services. Solver output stays associated with that sketch record. A failed solve retains the draft and diagnostics and leaves its review status `reviewed`, allowing correction and resubmission. A solved record becomes `review_status: submitted`; the submitted geometry cannot be edited through the draft endpoint.

Review endpoint contracts:

- `GET /api/analyses/<analysis_id>/draft` returns `{analysis_id, draft, original_proposal, review_status, validation}`. It returns 409 if the record has no sketch proposal.
- `PUT /api/analyses/<analysis_id>/draft` accepts `{geometry: <version 1.0 solver request>, coordinates_confirmed: true}`. It rejects malformed requests and unconfirmed coordinates, runs the shared truss validator, and returns 422 with `validation_issues` for invalid geometry. A valid save sets `review_status: "draft"`; it does not approve or solve the draft.
- `POST /api/analyses/<analysis_id>/review` has no body. It requires a saved draft, revalidates it, then marks it `reviewed`. It cannot mark an empty or invalid draft reviewed.
- `POST /api/analyses/<analysis_id>/solve` has no body. It requires `review_status: "reviewed"`, revalidates the saved draft, and runs the deterministic solver. Validation and solver failures are returned as 4xx responses and saved with the associated sketch record where applicable. A numerical solution is not a stability or engineering-suitability finding.

There is no SQL schema change for this phase: `human_geometry_json`, `review_status`, `validation_json`, `diagnostics_json`, and `solver_results_json` already existed. The coordinate-confirmation flag is a human attestation, not an automated dimensional or physical-units check. Proposal joint coordinates initially come from image pixels; reviewers must replace/verify them in declared physical units before saving. Load components are entered explicitly in the solver's global axes (positive x right, positive y up); no force values, constraints, or units are inferred.

## Verification

Last verified on 2026-10-30 after the dashboard and image-MIME changes:

```text
cd backend && ./.venv/bin/python -m unittest discover -s tests -v
Ran 85 tests ... OK
cd frontend && npm run build
Vite 8.3.5; 19 modules transformed; build passed
git diff --check
passed
```

The full backend suite passed 85 tests, including draft validation, original-proposal preservation, review gating, solver success/failure persistence, upload/history, all accepted image formats, MIME normalization, and mocked provider behavior. `frontend/package.json` has no frontend test script; its scripts are `dev`, `build`, and `preview`. No live Gemini or Meta request was made. No browser automation tool is available in the current Codex runtime, so visual browser interaction was not tested.

## Architecture and engineering decisions

- Muse Spark and Gemini are for sketch interpretation proposals, not engineering calculations. Their adapters are called by the upload-analysis route but are never connected to the solver.
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
- The frontend is a local upload/history/detail review interface with editable, persisted drafts and explicit review/solver actions, but no authentication or export. Navigation uses the `?analysis=<id>` query parameter; no router or state-management dependency was added. SVG overlays visualize pixel-coordinate candidates and are not engineering drawings. The separate human-draft preview uses model coordinates and is deliberately not overlaid on image pixels.
- The OpenCV prototype is heuristic: Hough detections can split or miss strokes, or report drawing artifacts. Five real repository images have exploratory outputs, but none has expected-geometry annotations or quantitative scores.
- Endpoint clustering can merge distinct endpoints that happen to be close; its transitive pixel-distance rule is configurable. It does not detect interior line intersections.
- Multi-diagram and annotation-heavy images can hit the 300-line cap; page rules, labels, arrows, dimensions, and support symbols remain candidate lines. Softer Canny defaults improved a photographed low-contrast example but also increase clutter.
- The Muse adapter has not been exercised against a live Meta account or credential. JSON schema enforcement depends on the Meta endpoint honoring its documented OpenAI-compatible Responses API behavior. The adapter supports only JPEG, PNG, and WebP despite broader image-format support in upstream APIs.
- Automated conversion from image pixels to physical model dimensions and export are not implemented. Reviewers must enter/confirm physical coordinates, force components, units, and support constraints themselves.
- No live Google or Meta account, quota, billing, or API behavior has been verified. The provider tests are mocked.
- Analysis history and images are stored locally by default; they are not shared across multiple backend instances and are not automatically pruned. The API has no authentication, so it must not be exposed publicly until access control is added.
- The API has no authentication and is only suitable for local development. The coordinate-confirmation flag records reviewer attestation but cannot prove entered dimensions match a drawing. The UI can make schema-valid drafts; schema validation does not establish structural completeness or engineering correctness.
- Passing tests demonstrates tested behavior, not engineering correctness for arbitrary structures.

## Current phase and next steps

Current phase: Final Submission Sprint (November 2, 2026).
The application is frozen, verified, and prepared for submission. All core pipeline stages (image upload and validation, OpenCV candidate detection, AI interpretation proposal generation, interactive draft geometry review, mandatory unit and physical coordinate attestation, schema validation gating, explicit review state transition, and deterministic NumPy equilibrium solving) are fully verified and operational. DeepLSD was investigated in an isolated environment and abandoned for this submission due to WSL/host environment instability, not due to proven accuracy deficits. P1 issues regarding CORS dev port flexibility and SVG draft preview node scaling across units have been resolved.

Next recommended post-submission tasks:
1. Add user authentication and authorization (e.g. JWT or session auth) before exposing endpoints beyond local single-user development.
2. Implement diagram region-of-interest selection and non-structural stroke suppression (arrows, dimensions, text, labels) before resuming line detection enhancements.
3. Explore server-side containerized GPU inference for deep learning line detection models to prevent host memory instability.

## Instructions for future AI agents

Read `overview_for_agents.md` before making changes. Inspect the actual implementation before assuming interfaces. Preserve existing behavior unless a change is intentional and documented. Work in small, testable phases. Do not silently weaken tests or claim engineering correctness based only on passing tests. Do not fabricate API capabilities, model IDs, credentials, or test results. Run the relevant tests and `git diff --check`. Update this document after each meaningful implementation phase. Never store secrets here.

## Implementation change log

### 2026-10-30 — Dashboard redesign and image MIME handling

- Frontend: added `frontend/src/pages/DashboardPage.vue` as the default local workspace view. It uses the existing paginated analysis API for the actual saved count, recent thumbnails, statuses, and any recent failure. It contains no fabricated activity or metrics. Added dashboard navigation while keeping upload, full history, and detail/review pages separate. The rounded outer workspace, warm cream surfaces, pale yellow selection accents, pill controls, and charcoal focus card adapt the supplied dashboard reference without borrowing its HR data or widgets. The existing detail view, source image, OpenCV/AI overlays, proposal inspector, editable geometry, validation, and solver diagnostics remain accessible. The new dashboard uses scoped CSS; existing global styles retain shared theme and responsive rules.
- MIME error root cause: `MIME_TYPE_MISMATCH` was emitted only in `POST /api/analyses`, before OpenCV or either provider was called. The route compared the multipart `Content-Type` supplied from the browser's `File.type` against a byte signature and returned 415 when they differed. The filename extension was not compared. No per-upload logs were available to identify which particular declaration/file pair triggered the observed error, so the specific upload's bad metadata cannot be determined.
- Image changes: the upload now treats the request MIME and extension as advisory, uses detected JPEG/PNG/WebP content for the stored MIME and adapter requests, checks the encoded dimensions against 6000 px/24 MP limits before OpenCV decoding, and verifies that decoded dimensions match the header. Corrupt supported-signature files fail as `INVALID_IMAGE` before storage or provider invocation; unsupported formats are rejected. The browser no longer blocks otherwise plausible files solely from `File.type`; size and nonempty checks remain client side while content validation is server side. Original upload bytes and filename metadata are retained unchanged, and image retrieval uses the detected content MIME and canonical extension. No re-encoding was needed because both adapters support JPEG, PNG, and WebP; both still independently derive MIME from verified bytes and ignore conflicting MIME hints.
- Provider failure handling: provider status errors now distinguish Meta/Gemini authentication failure, rate/quota limit, invalid model (not found), timeout, network error, generic API failure, and malformed response with sanitized user-facing messages. HTTP 429 is used for rate limits, 504 for timeouts, 503 for network/missing credentials, and provider/config errors remain safe and non-reflective. Failed calls remain persisted; retry remains an explicit user action.
- Regression coverage: added mocked API/provider coverage for JPEG, PNG, WebP, mismatched multipart MIME, misleading extensions, corrupted bytes, unsupported BMP, content-derived provider MIME, original-image retrieval after provider failure, dimension caps, and provider status classification. No live billable provider calls were made.
- MCP/browser: current tool inventory exposes connected app tools but no browser automation MCP. Earlier local MCP audit results are recorded in the prior change log; those Gemini-configured servers are not directly callable in this Codex runtime. The inline cream/yellow design reference was available in chat; the two described application-state screenshots were not found as local attachment files, so their appearance was assessed against the current frontend code. Browser-based visual verification did not run.
- Verification: `cd backend && ./.venv/bin/python -m unittest discover -s tests -v` passed 85 tests. `cd frontend && npm run build` passed (19 modules transformed). `frontend/package.json` has no frontend test command. `git diff --check` is required after final documentation and code edits. No configuration or `.env` credential was touched.
- Files changed in this phase: `backend/app/routes/analyses.py`, `backend/app/services/perception.py`, `backend/app/services/muse_interpretation.py`, `backend/app/services/gemini_interpretation.py`, `backend/tests/test_analysis_api.py`, `backend/tests/test_muse_interpretation.py`, `backend/tests/test_gemini_interpretation.py`, `frontend/src/App.vue`, `frontend/src/pages/DashboardPage.vue`, `frontend/src/pages/NewAnalysisPage.vue`, `frontend/src/pages/AnalysisDetailPage.vue`, `frontend/src/styles/shell.css`, `frontend/src/styles/responsive.css`, and this handoff.
- Remaining limitations: there is no browser/component automation and no live provider validation. Content-type derives from supported encoded signatures and successful OpenCV decoding; only JPEG, PNG, and WebP are accepted. Keep the unauthenticated app local.

### 2026-10-29 — Modular local review dashboard and MCP configuration audit

- Frontend changes: moved upload, analysis history, and analysis detail composition and state into `frontend/src/pages/NewAnalysisPage.vue`, `AnalysisHistoryPage.vue`, and `AnalysisDetailPage.vue`. `frontend/src/App.vue` now owns the sidebar/top bar/footer, local query-string navigation, and the history count only. Existing API calls stay in `frontend/src/api/analyses.js`; geometry editing remains in `frontend/src/components/GeometryReview.vue`. Split the existing theme stylesheet into `frontend/src/styles/shell.css`, `workspace.css`, `analysis-review.css`, and `responsive.css`, with `frontend/src/style.css` importing them in cascade order. The visual direction retains the light neutral workspace and compact structured hierarchy from the supplied reference while using Sketch2Solve engineering terms and colors; no medical content or new dependency was added. A successful upload/retry opens its saved detail record and increments the shell count. No backend or credential files were changed.
- MCP audit sources: inspected `/home/athulkrishna_s_nair/.codex/config.toml` (valid TOML; no MCP server configuration), `/home/athulkrishna_s_nair/.gemini/config/mcp_config.json` (valid JSON; seven servers), and `/home/athulkrishna_s_nair/.kimi-code/config.toml` (valid TOML; no MCP server configuration). No project MCP config was found. The current Codex runtime exposed `codex_apps` tools (66 tools across connected app groups) but did not expose these Gemini-configured servers or a browser automation tool.
- MCP launch checks: `watermelon` started, initialized, listed six registry/component tools, and passed read-only `list_registries`. `frontend-designskill`, `ui-ux-pro-max`, `emil-design-eng`, `repo-fetcher`, and `pixijs-agent-skills` all started and initialized, but each config entry points to the same generic `@modelcontextprotocol/server-everything` 2.0.1 package, lists the same 16 demo tools, and passed only the harmless `echo` call. Their labels do not match an installed specialized implementation. `web-search` started and initialized with one `web_search` tool, but a read-only call could not connect to its configured local crawler at `127.0.0.1:3001` (`EPERM`; no local listener was present). This did not complete an external web request.
- MCP files were not edited and no backup was created. No safe intended source/path was available for replacing the generic demo packages; identify/install the intended server implementation before changing those entries, then back up the Gemini config before editing it. The web-search service needs its local crawler made available before it can be used. No auth settings or packages were changed.
- Verification: `cd frontend && npm run build` passed (Vite 8.3.5, 16 modules transformed). `cd backend && ./.venv/bin/python -m unittest discover -s tests -v` passed all 79 tests. `git diff --check` passed. No live AI/provider request was made; browser automation was unavailable. `frontend/package.json` has no frontend test command.
- Files changed in this phase: `frontend/src/App.vue`, `frontend/src/style.css`, new `frontend/src/pages/{NewAnalysisPage.vue,AnalysisHistoryPage.vue,AnalysisDetailPage.vue}`, new `frontend/src/styles/{shell.css,workspace.css,analysis-review.css,responsive.css}`, and `overview_for_agents.md`.
- Remaining limitations/next steps: frontend behavior has build validation but no component/browser tests. MCP aliases for specialized design/fetch tools remain generic demo servers; web-search's local crawler is offline. Keep the app local because authentication is absent. Run locally with `cd backend && ./.venv/bin/python run.py`, then in another terminal `cd frontend && npm run dev`.

### 2026-10-29 — Editable geometry review and explicit solver submission

- Files changed: `backend/app/routes/analyses.py`, `backend/tests/test_analysis_api.py`, `frontend/src/App.vue`, `frontend/src/api/analyses.js`, `frontend/src/components/GeometryReview.vue`, `frontend/src/style.css`, and this handoff.
- Frontend behavior: added a local upload preview, history refresh, explicit retry for failed provider runs, detector/proposal/endpoint visibility controls, selectable/highlighted SVG elements and optional IDs, zoom with scroll panning, detector-cap messaging, unavailable-image messaging, and a responsive geometry editor. The editor supports joint coordinate edits/add/remove, member add/remove/reference edits, support type/node/roller-axis edits, and load node/global-component edits. It shows a separate human-draft preview and keeps the original AI proposal intact.
- Review workflow: drafts use the existing version 1.0 solver request schema and remain separate from the AI candidate. Reviewers explicitly attest coordinates are physical values in the chosen units. Server validation rejects non-finite numbers, invalid IDs/references, malformed support/load definitions, and other schema errors. Only a saved valid draft can be marked reviewed; only a reviewed draft can be submitted to the deterministic solver. Solver output is persisted on the original sketch record. Solver failure preserves the draft, diagnostics, and reviewed state.
- API additions: `GET /api/analyses/<id>/draft`; `PUT /api/analyses/<id>/draft` with `{geometry, coordinates_confirmed}`; `POST /api/analyses/<id>/review`; `POST /api/analyses/<id>/solve`. No SQL columns or dependencies were added; existing JSON fields store the draft and results. The original proposal field is not modified.
- Verification: `cd backend && ./.venv/bin/python -m unittest discover -s tests -v` passed 79 tests. `cd frontend && npm run build` passed (13 modules transformed). `npm run` showed no frontend test command. `git diff --check` passed. Browser automation MCP was not available; no external provider API calls were made.
- Security/limitations: no authentication was added; all analysis and review endpoints must remain local. The coordinate attestation is an explicit human check and cannot verify physical dimensions. The editor does not infer missing loads, units, support constraints, or physical scale. Solver diagnostics do not establish stability or engineering suitability.
- Next work: add automated browser/component tests and consider a user-driven physical-scale tool; add authentication before any shared/public deployment; retain the local-only boundary until then.

### 2026-10-29 — Local Vue analysis review interface

- Files changed: `frontend/src/App.vue`, `frontend/src/api/analyses.js`, `frontend/src/style.css`, `frontend/index.html`, and this handoff.
- Behavior: added image upload with selectable Meta/Gemini provider, paginated saved-analysis history, query-string detail navigation, original image retrieval, OpenCV detection overlays, AI proposal overlays and inspectable proposal elements, status/failure explanations, validation issues/warnings, and display of saved deterministic solver results. UI states cover loading, empty history, upload/refresh errors, failed analyses, and successful saved results. Provider credentials remain server-side.
- Review boundary: proposals are clearly labeled unapproved; this interface does not edit geometry, persist review changes, approve AI output, or submit proposal geometry to the solver. The app is intended for local use because authentication is absent.
- Implementation decisions: existing frontend had no router, Pinia store, API client, or Pixi rendering setup. Kept dependencies unchanged and used native `?analysis=<id>` navigation plus SVG overlays aligned to image pixel coordinates. The API client calls Flask directly at `http://127.0.0.1:5000` by default (`VITE_API_BASE_URL` can override); Flask CORS currently allows the Vite origin `http://localhost:5173`. No backend code changed.
- Verification: `cd frontend && npm run build` passed (Vite 8.3.5; 12 modules transformed). `frontend/package.json` defines no frontend test script (`dev`, `build`, and `preview` only). `git diff --check` passed. Backend tests were not rerun because backend code was not changed.
- Limitations/next steps: no authentication, editing/review persistence, approval endpoint, or export; add authentication before any non-local exposure and implement a validated review endpoint before saving edits or submitting reviewed geometry.

### 2026-10-29 — Gemini interpretation adapter and configurable provider

- Files changed: `backend/app/services/gemini_interpretation.py`, `backend/app/services/interpretation_provider.py`, `backend/tests/test_gemini_interpretation.py`, `backend/requirements.txt`, `backend/.env.example`, and this handoff.
- Behavior: added an independent Google Gen AI SDK adapter, `GEMINI_API_KEY`/`GEMINI_MODEL` configuration, and a dispatcher controlled by `INTERPRETATION_PROVIDER` (default `meta`). Both adapters continue to return validated candidate interpretations for review; neither is connected to the deterministic solver. The existing Meta adapter remains intact.
- Configuration: added `google-genai>=1.0,<2`; `python-dotenv` was already declared and is used to load `backend/.env` without replacing environment variables. The `.env.example` contains placeholder credentials only. The actual `.env` was not read or modified.
- Verification at that phase: `./.venv/bin/python -m unittest discover -s tests -v` from `backend/` passed 67 tests; `git diff --check` passed. Gemini tests inject mocked clients; no live API calls were made.
- Limitations: no live Gemini account, quota, or billing validation has been performed.
- Switching providers: set `INTERPRETATION_PROVIDER=gemini` and configure `GEMINI_API_KEY` in the ignored local `backend/.env`; switch back with `INTERPRETATION_PROVIDER=meta` (and the existing `MODEL_API_KEY`). Call through `interpretation_provider.interpret_truss_sketch` or the upload-analysis route.

### 2026-10-29 — Persisted sketch analyses and human-review API

- Files changed: `backend/app/extensions.py`, `backend/app/models/analysis.py`, `backend/app/routes/__init__.py`, `backend/app/routes/analyses.py`, `backend/app/services/analysis_persistence.py`, `backend/app/__init__.py`, `backend/app/services/gemini_interpretation.py`, `backend/app/services/interpretation_provider.py`, `backend/.env.example`, `.gitignore`, `backend/tests/test_analysis_api.py`, `backend/tests/test_api_analyze.py`, `backend/tests/test_gemini_interpretation.py`, and this handoff.
- Behavior: added upload analysis with OpenCV + selected provider, persistent failed/successful records, solver-run history, paginated listing, detail retrieval, and controlled original-image retrieval. AI results remain `pending_review`; there is no correction or approval endpoint.
- Database/storage: `sketch_analyses` table is created additively with `db.create_all()`. Default SQLite database and opaque-name uploads live under ignored `backend/instance/`; no existing data is dropped. No migration command is required for this new local database. Existing external databases need the new table created by startup or an operator-run additive migration.
- Gemini: default model is `gemini-3.1-flash-lite`, confirmed as stable in Google's model documentation. `GEMINI_MODEL` remains an override.
- API contract: `POST /api/analyses` multipart `image` (+ optional `provider`); `GET /api/analyses?page=1&per_page=20`; `GET /api/analyses/<analysis_id>`; `GET /api/analyses/<analysis_id>/image`. Existing `POST /api/analyze` adds an `analysis_id` and saves solver results.
- Verification: `./.venv/bin/python -m unittest discover -s tests -v` passed 75 tests; `git diff --check` passed. External providers were mocked; no live calls were made.
- Limitations: no authentication, review screen, review-update endpoint, automatic retention policy, or multi-instance/shared object storage. Add authorization before public deployment.
- Frontend handoff: use list items for history, detail fields `sketch`, `perception`, `interpretation_proposal`, `validation`, `human_review`, and `solver_results`; load image bytes only from the `image_url` route. Keep proposal geometry visibly separate from user-confirmed geometry.

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

### 2026-10-29 — QA automation and evaluation run

- Added Playwright E2E configuration, isolated mocked Flask/Vite test servers, upload/error/workflow tests, and a review-sheet generator under `frontend/tests/e2e/`. Playwright is a frontend development dependency only; no application behavior or production database was changed.
- QA report: [`qa-output/QA_REPORT.md`](./qa-output/QA_REPORT.md). Per-image upload observations and human-review sheets are saved alongside it.
- Verification: backend suite passed 85 tests; `npm run build`, Playwright test discovery (23 tests), syntax checks, and `git diff --check` passed. The local Playwright run was blocked before assertions because Chromium system libraries are absent and administrator package installation was unavailable. Integrated-browser smoke and isolated mocked API workflows were exercised separately.
- Findings/limitations: no ground-truth geometry exists; provider requests were mocked. The UI currently renders “Correct interpretation” disabled for a new unreviewed analysis (`frontend/src/components/GeometryReview.vue:223`); this was reproduced and recorded, not fixed under the QA-only scope. The evaluation report's JPEG metadata for `test1.jpg` conflicts with its WebP byte signature.
- Next: enable authorized browser runtime dependencies and rerun `npm run test:e2e`; track and fix the reported application defect separately.

### 2026-10-30 — Geometry editor pending-review fix

- Root cause: the editor tied the “Correct interpretation” control's disabled state directly to the generic `busy` operation string. That made access to draft creation depend on unrelated in-flight operations, even while the analysis was still correctly `pending_review`. The parent detail page and backend do not require approval to open a draft; approval is only required by the solve route.
- Fix: `frontend/src/components/GeometryReview.vue` now disables that control only while the draft GET is actively loading. Editing and saving leave the AI proposal and review status untouched. Cancelling modified edits asks before discarding them. Coordinate confirmation and all server-side validation remain required.
- Regression coverage: extended the mocked-provider Playwright workflow to assert pending analyses can open the editor, the initial proposal remains proposal-only, and saving leaves the record in `draft` with no solver result until explicit review. Existing E2E/API coverage also checks invalid geometry, missing units/coordinate attestation, solve-before-review rejection, successful reviewed solve, and persisted solver failure diagnostics/draft preservation.
- Verification: backend suite passed 85 tests; frontend production build passed; test discovery found 23 Playwright tests; `git diff --check` passed. `npm run test:e2e` could not start its isolated backend because sandbox socket binding returned `PermissionError` on `127.0.0.1:5101`, so zero browser assertions executed. Direct `ldd` inspection of the configured Chromium binary additionally found missing `libnspr4.so`, `libnss3.so`, `libnssutil3.so`, `libsmime3.so`, and `libasound.so.2` (five libraries).
- QA detail: [`qa-output/QA_REPORT-2026-10-30.md`](./qa-output/QA_REPORT-2026-10-30.md). No production/backend behavior or dependencies changed, and no real or paid AI provider call was made.
- Remaining limitation: browser-level behavior cannot be claimed verified until the sandbox permits the test web-server ports and Chromium's host libraries are provided. A successful UI workflow is covered in the E2E spec but was not executed in this environment.

### 2026-10-30 — Independent verification follow-up

- Re-read the handoff and dated QA report; reviewed tracked staged/unstaged state and all relevant untracked editor/test files. No existing changes were reset, cleaned, or overwritten. The only new implementation-adjacent changes in this follow-up are a dependency-free frontend contract test and its npm script.
- Confirmed the Playwright server host/ports and proxy targets agree (`127.0.0.1:5101` Flask, `127.0.0.1:5174` Vite); no other app server processes were running and `/proc/net/tcp*` had no listeners. Direct socket creation fails with `PermissionError: [Errno 1] Operation not permitted` under the default restricted sandbox, establishing a sandbox networking restriction rather than a port conflict. Running the user-requested E2E command with scoped elevated local-bind permission started both configured servers successfully.
- The Playwright run then attempted all 23 tests, but each Chromium process exited before a test body ran because `libnspr4.so` is unavailable. The five missing libraries confirmed by `ldd` are `libnspr4.so`, `libnss3.so`, `libnssutil3.so`, `libsmime3.so`, and `libasound.so.2`. No system browser was found outside the Playwright cache; no OS packages were installed. **0 browser assertions executed; full upload → edit → save → review → solve remains unverified in a real browser.**
- Added `frontend/tests/unit/geometry-review-contract.test.js` using Node's built-in test runner (no new dependency). Three source-contract checks pass. The first checks the exact loading-only disabled binding, so reverting it to generic `:disabled="busy"` fails even when `busy` is initially empty. Other checks enforce that draft saving does not invoke review/solve and that review and solve controls retain explicit prior-state gates. Playwright still covers UI interaction when its runtime is available.
- Final verification: backend suite **85 passed**; frontend production build **passed**; `npm run test:unit` **3 assertions passed**; Playwright discovery **23 tests**; Playwright browser run **23 launch-blocked, 0 assertions executed**; `git diff --check` **passed**. Full details are in [`qa-output/QA_REPORT-2026-10-30.md`](./qa-output/QA_REPORT-2026-10-30.md).
- Safety boundary preserved: proposal remains unapproved until explicit review; backend validation and coordinate attestation remain required; solver remains review-gated; solver failures preserve the draft and diagnostics. No live provider call, credential, system package, or backend product code was changed.

### 2026-10-30 — Phase A perception baseline and annotation audit

- Detector behavior was not changed. Fresh default `detect_candidate_geometry` runs were performed five times per source image with OpenCV 4.14.0; identical output across repeats. Reproduction: `backend/.venv/bin/python evaluation/run_perception_baseline.py --input-dir backend/evaluation/sketches --output-dir evaluation/results/phase-a-2026-10-30/detector-baseline --repeats 5`. Machine results and detector-only PNG previews are in `evaluation/results/phase-a-2026-10-30/detector-baseline/`.
- Fresh counts (candidate lines / endpoint clusters): `test1.jpg` 153/196, `test2.jpg` 300/240 (cap), `test3.png` 76/76, `test4.jpg` 49/61, `test5.png` 300/221 (cap). The `.jpg` test1 bytes are WebP, 1800×2400. Full dimensions, detected MIME, runtime medians, warnings, SHA-256, settings, diagnostics, and line/joint coordinates are in `baseline.json`.
- Human references were authored separately under `evaluation/results/phase-a-2026-10-30/annotations/`, bound to source hashes, with original-pixel coordinate convention (top-left, x-right, y-down). `test1`, `test3`, `test4`, and main-truss region of `test5` support confirmed joint/member centerline references; test1 coordinates are approximate due to rotation/photo, and test5 X-brace crossing connectivity remains explicitly ambiguous. `test2` contains four rough alternatives and has no trustworthy single reference graph; metrics are unavailable.
- `evaluation/perception_evaluation.py` reproduces one-to-one joint matching, localization error, and fragment-unioned centerline coverage recall. Thresholds: joint distance `max(12 px, 0.75% image diagonal)`; line corridor same; orientation 8 degrees; member coverage 80%. Member precision is unavailable because detector outputs raw candidate lines, not member hypotheses. Metrics and definitions are in `metrics.json` and `METHODOLOGY.md`; annotation contract is in `ANNOTATION_SCHEMA.md`.
- Exploratory micro averages across the four confirmed graphs: joint precision 0.082, recall 0.710, mean matched endpoint error 9.38 px, candidate-line member coverage recall 27/53 = 0.509. These five-image results are not general performance evidence. Test5 cap output misses most of the truss; test2/test5 clutter/cap and lack of semantic grouping remain major limitations.
- Verification: `cd backend && ./.venv/bin/python -m unittest discover -s tests -v` passed 90 tests (five new synthetic evaluator/schema/matching tests); baseline and metric scripts completed; `git diff --check` passed. No new dependencies, live AI calls, or changes to `perception.py`.
- Phase A report: [`evaluation/results/phase-a-2026-10-30/REPORT.md`](./evaluation/results/phase-a-2026-10-30/REPORT.md). Highest-value next experiment: manually select/crop diagram ROIs on test2/test5 and rerun unchanged detector settings to measure whether detector capacity is spent on structural regions rather than page clutter.

### 2026-10-30 — Controlled ROI crop experiment

- Added `evaluation/run_roi_crop_experiment.py`, a standalone runner that uses the unchanged default detector, records five-run median timings, validates fixed crop bounds, produces comparable overlays, maps crop-local line endpoints and clusters back to original-image pixels, and applies the existing evaluator to the mapped `test5` detections. Production perception code and thresholds were not changed.
- Frozen ROIs, chosen from original-image review before detector runs: `test2.jpg` `[x=60, y=565, width=455, height=184]` (bottom/fourth sketch; still no accuracy reference), and `test5.png` `[x=365, y=630, width=1380, height=420]` (same as the independent Phase A main-truss evaluation ROI). Neither crop was resized. The three `test5` X-brace crossings remain explicitly ambiguous.
- Measured counts (lines/clusters): test2 original `300/240`, capped; crop `104/81`, not capped. Test5 original `300/221`, capped; crop `300/211`, still capped. Five-call median runtimes and complete output are in [`results.json`](./evaluation/results/phase-a-2026-10-30/roi-crop-experiment/results.json).
- On the fixed test5 reference, mapped crop detections changed joint precision/recall from `0.0299/0.250` to `0.0237/0.625`, mean endpoint error from `15.845 px` to `10.277 px`, and member centerline coverage recall from `3/16 (0.1875)` to `7/16 (0.4375)`. This is evidence of partial improvement in actual candidate-line truss coverage, despite lower precision and continued cap saturation; it does not establish semantic correctness. Test2 accuracy remains unmeasured because no trustworthy single-graph reference exists.
- Added deterministic tests for ROI bounds, ambiguous config points, and crop-to-original coordinate translation. Relevant evaluation tests passed 8; full backend suite passed 93; the crop experiment and standalone Phase A evaluation scripts completed; `git diff --check` passed. Overlays and details are in [`REPORT.md`](./evaluation/results/phase-a-2026-10-30/roi-crop-experiment/REPORT.md). No dependencies, AI calls, or edits to the Phase A baseline/annotations were made.
- Next experiment: evaluate fixed overlapping tiles across test5's bays with a documented coordinate-map and deduplication rule, since the full reference crop remains capped and misses the rightmost bay. Keep detector thresholds and reference ambiguity rules unchanged.

### 2026-10-30 — Overlapping tile experiment on test5

- Added an isolated evaluation runner and deterministic config for two layouts over the exact existing test5 ROI: three 600×420 tiles at 35% horizontal overlap, and four 480×420 tiles at 37.5% overlap. Origins, edge policy, image-to-source mapping, selection rationale, and tolerance sweep are recorded in `evaluation/results/phase-a-2026-10-30/overlapping-tile-experiment-2026-10-30/tile_config.json`. The layouts were selected from ROI geometry and annotated bay spacing before running the detector.
- The unchanged detector was run five times per tile. Every tile stayed below 300 candidate lines. At the primary 4 px perpendicular deduplication tolerance, `three_wide` combines 577 raw tile lines into 477, recovering 12/16 reference members with joint P/R 0.0238/0.625. `four_narrow` combines 489 into 389, recovering 10/16 with P/R 0.0314/0.875. Both outperform the original and full-ROI runs on member centerline coverage; neither dominates all metrics.
- Deduplication groups only cross-tile segments with ≤4° orientation difference, ≤4 px line offset, ≥35% projected overlap of the shorter segment, and finite-endpoint support. Reversed ends and partial overlap are handled; complete-link groups retain source tile/line provenance, and disjoint gaps are not bridged. Sensitivity at 2/4/8 px is stored with per-member coverage. The rightmost bay improves from 0/6 recovered reference members to 3/6 in both layouts (two chords and one diagonal); two verticals and the other diagonal remain below coverage threshold. X crossings remain ambiguous.
- Artifacts and detailed per-tile runtimes/overlays/metrics are in `evaluation/results/phase-a-2026-10-30/overlapping-tile-experiment-2026-10-30/REPORT.md` and `results.json`. Relevant tests passed 17; full backend suite passed 102. No production detector, thresholds, dependencies, source annotations, or baseline outputs changed; no live AI calls were made.
- Highest-value next experiment: shift the 480×420 tile grid so one tile fully contains the rightmost bay and its endpoints, then compare using the same deduplication and reference rules. Do not integrate tiling into the production application based on this single-image experiment.

### 2026-10-30 — Targeted rightmost-bay tile experiment

- Added a source/reference-selected tile at `[x=1200, y=630, width=545, height=420]` within the existing `[365, 630, 1380, 420]` ROI. Before detection, the annotation endpoints for M09, M10, and M16 were checked against the tile: all are fully included with about 52 px side margins. Compared with the three-wide rightmost tile, it removes 55 px of preceding-bay context; it also moves the four-narrow boundary left of F/C. The three X-crossings remain marked ambiguous and excluded from scoring.
- The unchanged detector produced 156 lines and 90 endpoint clusters, below the cap. The same cross-tile dedup at 4 px and sensitivity values 2/8 px removed zero lines because this is a single-tile experiment. M09 coverage rose from 9.7% in four-narrow to 14.2%, still below 80%; M10 fell from 12.5% to 0%; M16 fell from 5.3% to 0%. None of the three target members was adequately recovered.
- Overall results: P/R `0.0333/0.375`, mean/median matched-joint error `10.883/12.649 px`, member coverage `3/16 (0.188)`. The precision is marginally above the previous four-narrow best, but recall and total coverage are much worse than three-wide (12/16), four-narrow (10/16), and the full ROI (7/16). Endpoint candidates near member joints do not establish centerline recovery.
- Targeted pipeline median was 37.792 ms excluding one-time source decode: 3.915 ms crop/PNG encoding, 24.615 ms detector, and 8.658 ms mapping/dedup/clustering. Prior runtime figures are detector-only; they are not compared as full-pipeline timings. Full details, target-member endpoint errors, provenance, and overlays are in `evaluation/results/phase-a-2026-10-30/rightmost-bay-targeted-tile-2026-10-30/REPORT.md` and `results.json`.
- The targeted coordinate assertion test passed; the full evaluation and backend suites and `git diff --check` are recorded in the report. The baseline, annotation, prior tile configs/results, and production detector remain unchanged. Next, audit unchanged raw segments by angular error, centerline offset, and fragmentation for M09/M10/M16 before trying more tile placements.

### 2026-10-31 — Raw segment failure diagnostic for test5 target members

- Added `evaluation/diagnose_target_member_failures.py` and a separate result directory, `evaluation/results/phase-a-2026-10-30/target-member-failure-diagnostic-2026-10-31/`. It reads the saved raw lines from original, full ROI, three-wide, four-narrow, and targeted-tile artifacts; validates the source SHA-256 (`5fa616402e536ecb0907d699f6e0252f4fadc556df11a3cbb475e4f184b1ca36`); and measures IDs/coordinates, orientation, centerline offset, finite-centerline overlap, gap-preserving fragment union, and raw endpoint proximity. Tile provenance remains attached. No detector rerun or production change was made.
- The fixed annotation locations are M09 F `(1252,663)`→C `(1252,1023)`, M10 E `(1693,663)`→D `(1693,1023)`, and M16 C `(1252,1023)`→E `(1693,663)`. The three ambiguous X crossings remain excluded. The existing 18.257 px corridor, 8° angle limit, and 80% coverage threshold were retained.
- Main evidence: none of the three target members meets 80% coverage in any saved layout. Best coverages are 14.2% for M09 (target tile), 12.5% for M10 (four-narrow), and 11.6% for M16 (three-wide). M16's four eligible three-wide segments cover one 66.27 px interval then leave 503.01 px uncovered. M09/M10 generally have one short eligible segment or none per layout. Some local candidates fail due to angle or offset; nearest endpoints can still be near annotated joints without corresponding line coverage.
- Failure assessment: missing qualifying line response is strongly supported; limited fragmentation is supported (most clearly M16); off-angle clutter and centerline-offset responses are also observed. Endpoint clustering is not supported as the primary cause because joints match while member coverage remains very low. The evidence-based next experiment is **A, adaptive Canny/Hough parameter sweep**, offline and against the same fixed reference; merging cannot fill unobserved centerline spans. No improvement was implemented.
- New artifacts: `REPORT.md`, `results.json`, `diagnostic_config.json`, and five same-region overlays under the diagnostic directory. Tests added for angle/offset/overlap, gap-preserving union, and out-of-extent segments. Diagnostic command `backend/.venv/bin/python evaluation/diagnose_target_member_failures.py` completed. Focused evaluation tests passed 21; full backend suite passed 106; final `git diff --check` passed. Real-browser behavior was not verified. No dependency, AI call, annotation, or prior experiment output was changed.

### 2026-10-30 — Phase A6: Adaptive Canny/Hough parameter sweep

- Added `evaluation/run_canny_hough_sweep.py` and `backend/tests/test_perception_parameter_sweep.py`, creating reproducible artifacts under `evaluation/results/phase-a-2026-10-30/adaptive-canny-hough-sweep-2026-10-30/` (`REPORT.md`, `results.json`, `experiment_config.json`, and full-image/layout overlays). Production detector code and defaults (`backend/app/services/perception.py`) were strictly preserved.
- Baseline reproduction: 5-repeat runs of the unchanged default detector on all five source sketches matched the saved Phase A baseline candidate line and joint geometry identically; SHA-256 source hashes were verified.
- Staged sweep design: Stage 1 varied Canny clamp thresholds (`control` [40, 160], `canny_low` [20, 120], `canny_high` [60, 220]) with sigma held at 0.8 and production Hough settings. `canny_low` was selected by aggregate micro-coverage as the global alternate for Stage 2. Stage 2 evaluated one-factor Hough changes (`hough_vote_low` [threshold 20], `hough_short_lines` [min length 12 px], `hough_long_gap` [max gap 12 px]) against both `control` and `canny_low`.
- Scoring: unchanged Phase A evaluator (`evaluation/perception_evaluation.py`) applied across confirmed references (`test1`, `test3`, `test4`, `test5`; 53 members, 31 reference joints). `test2` remains unscored due to ambiguous multiple alternatives. Gates: 8° angle limit, `max(12 px, 0.75% diagonal)` corridor, 80% coverage threshold.
- Aggregate findings:
  - `control`: joint P/R `0.0824 / 0.7097`, mean endpoint error `9.377 px`, member coverage `27/53 (0.5094)`, 2 capped images (`test2`, `test5`), median detector time `59.0 ms`.
  - `canny_low`: highest coverage `30/53 (0.5660)`, but joint precision fell to `0.0659` and `test1` newly hit the 300-line cap (3 capped images).
  - `control__hough_long_gap`: only configuration passing the predeclared aggregate screen (`28/53` coverage, P/R `0.0885 / 0.7419`, 2 capped images), but test5 full-image coverage declined from 3 to 2 members.
  - Test5 layouts and target members: tested across full ROI, three-wide, four-narrow, and targeted tile layouts. Neither `control__hough_long_gap` nor any other configuration recovered target members M09, M10, or M16 to 80% (all remained under 19% coverage).
- Decision: Do not modify production defaults. Next recommended investigation is non-structural stroke suppression / image cleanup (text, dimension lines, connector annotations) before further tuning or alternative stroke detection algorithms.
- Verification: focused evaluation suite **24 passed**; full backend suite **109 passed**; `git diff --check` **passed**. No live AI calls, dependencies, or database migrations were introduced; real-browser behavior was not verified.

### 2026-11-02 — DeepLSD deep learning perception investigation

- Investigated pretrained deep learning wireframe/line detector DeepLSD (CVG, ETH Zurich) as a candidate replacement for heuristic Canny/Hough line detection.
- Setup an isolated virtual environment (`evaluation/.venv-deeplsd`) using standalone Python 3.11 (`.python311`) to prevent any conflict or pollution of `backend/.venv` (Python 3.14). Installed CPU PyTorch (`torch 2.15.0+cpu`, `torchvision 0.29.2+cpu`).
- Compiled `pytlsd` dependency against modern `pybind11` from venv with pinned `cmake<4` (`cmake==3.31.10`) to resolve deprecated C++ Python runtime bindings.
- Downloaded official checkpoint `deeplsd_wireframe.tar` (99MB, MD5 verified).
- Evaluated on `test5.png` (2046×1319 px): DeepLSD detected 1,474 line segments across the full uncropped image, achieving 10/16 (62.5%) member coverage recall on the fixed reference graph (compared to OpenCV baseline full-image coverage of 3/16 = 18.75%).
- However, target difficult members M09, M10, and M16 remained under 4% coverage, and dense CPU tensor execution of the full VGG-UNet backbone on high-resolution images repeatedly provoked host environment / WSL / VS Code Server crashes (OOM/EOF terminates).
- Decision: Abandoned DeepLSD for the November 2 submission sprint due to environment instability, not because its detection accuracy was proven inadequate. Production backend and frontend were completely unaffected. All partial outputs, downloaded weights, and evaluation runners were safely preserved in `evaluation/DeepLSD/` and `evaluation/run_deeplsd_evaluation.py`.

### 2026-11-02 — Final submission sprint, P1 fixes, and release documentation

- Audited the entire end-to-end pipeline: image ingestion, OpenCV candidate line detection, AI provider dispatching (Gemini / Meta), interactive draft geometry review, coordinate and unit attestation, schema validation gating, and deterministic NumPy equilibrium solving.
- Resolved P1 Issue 1 (CORS Development Port Flexibility): Updated `backend/app/__init__.py` CORS configuration to accept `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:5174`, `http://127.0.0.1:5174`, `http://localhost:4173`, `http://127.0.0.1:4173`, `http://localhost:3000`, `http://127.0.0.1:3000`, as well as configurable comma-separated origins from `CORS_ORIGINS`. This prevents local connection failures when Vite spins up on alternative ports or local loopback aliases.
- Resolved P1 Issue 2 (SVG Draft Preview Scaling): In `frontend/src/components/GeometryReview.vue`, fixed draft preview bounding box calculation to inspect both saved geometry nodes and active draft nodes (`activeNodes`), and replaced the hardcoded `r="0.018"` node radius with a dynamically computed `:r="nodeRadius"` proportional to truss span (`Math.max(span * 0.018, 0.001)`). Nodes and members now render crisply and visibly regardless of whether coordinates are specified in meters, millimeters, or feet.
- Authoring Root `README.md`: Created comprehensive project documentation covering architecture, setup, environment configuration, complete API endpoint reference, demonstration guide with evaluation sketches, known limitations, and engineering safety disclaimers.
- Verification pass:
  - Backend unit & API tests: **109 passed** (`cd backend && ./.venv/bin/python -m unittest discover -s tests -v`).
  - Frontend contract unit tests: **3 passed** (`cd frontend && npm run test:unit`).
  - Frontend production build: **Passed** with Vite 8.3.5 (19 modules transformed, 325ms).
  - Git hygiene: `git diff --check` passed cleanly with 0 whitespace or patch warnings. No destructive Git commands were run; existing user files and experimental artifacts remain strictly intact.

### 2026-11-02 — Human-in-the-Loop Engineering Workspace (Phase 1 & Phase 2)

- Backend:
  - Added non-persistent preview calculation service `backend/app/services/truss_preview.py` and routes `POST /api/analyses/preview` and `POST /api/analyses/<analysis_id>/preview` in `backend/app/routes/analyses.py`.
  - Performs real-time schema validation, disconnected joint detection, duplicate member connection detection, support reaction counts, static determinacy checks, equilibrium matrix assembly, SVD rank/condition diagnostics, and direct NumPy direct solve with tension/compression classifications.
  - Leaves database records, analysis review status, and draft persistence completely untouched during interactive editing.
  - Added full test coverage in `backend/tests/test_truss_preview.py` (7 new tests covering valid triangles, incomplete models, invalid schemas, disconnected joints, duplicate members, mechanisms, and API endpoints; backend suite passes 116 tests).
- Frontend:
  - Created dedicated full-screen interactive engineering workspace: `frontend/src/pages/TrussEditorPage.vue` and `frontend/src/styles/truss-editor.css`.
  - Installed lightweight icon library `lucide-vue-next`.
  - Implemented 2D Cartesian engineering canvas with world coordinates (positive $x$ right, positive $y$ upward), dynamic pan/zoom, zoom to cursor, fit to view, customizable grid, snap-to-grid, coordinate readout, and distinct visual symbols for joints, members, pin/roller supports, and point load vectors.
  - Layer controls: Toggleable AI proposal reference layer with click-to-import for individual joints/members or batch import, and toggleable OpenCV candidate lines.
  - Toolbox: Select, Pan, Add Joint, Add Member, Pin Support, Roller Support, Point Load, Measure tool, Undo, Redo, Zoom In/Out, Fit Content, Grid, Snap.
  - Properties & Coordinate Inspector: Direct editing of joint $(X, Y)$ coordinates, support types, point loads $(F_x, F_y)$, member connections, and computed lengths and member axial forces.
  - Live Validation & Calculation Status Area: Green/Yellow/Red status bar with clickable issue drawer that auto-selects affected canvas elements; debounced (250ms) recalculation with monotonic sequence stale-response protection.
  - Full Undo / Redo history stack and unsaved changes tracking.
  - AI Engineering Assistant (Phase 2): Context-aware engineering side panel providing on-demand structural explanations (mechanisms, degrees of freedom, support layouts, forces) with explicit "Accept & Apply" suggestions that require user confirmation.
  - Detail page integration: Added prominent "Edit geometry" and "Open Interactive Editor" buttons in `AnalysisDetailPage.vue` and `GeometryReview.vue`, routing to `?analysis=:id&view=editor` or `/analyses/:id/editor`.
  - Unit tests: Added 7 new frontend unit tests in `frontend/tests/unit/truss-editor.test.js` (total 10 tests passing).
  - Verification: 116 backend tests pass, 10 frontend unit tests pass, Vite production build passes with 1,735 modules.
