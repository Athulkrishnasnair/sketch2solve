# Sketch2Solve QA report

**Run date:** 2026-10-29  
**Scope:** Testing infrastructure and QA only. No application behavior was changed.

## Executive summary

- The backend `unittest` suite passed **85 tests**.
- `npm run build` passed.
- All five evaluation images were uploaded through the real frontend to an isolated Flask server with a deterministic mocked provider. Each upload returned HTTP 201, was persisted, and its stored image was retrievable with HTTP 200.
- Integrated-browser checks exercised dashboard/navigation, history refresh and detail opening, image display, OpenCV/proposal toggles, zoom, provider error states, upload errors, and API-level draft/review/solve persistence. The browser reported no uncaught JavaScript errors or unexpected failed requests during successful navigation and reload.
- The Playwright suite contains **23 tests**. The test runner discovered all 23, but local Chromium could not launch because system libraries are missing. Thus **0 automated Playwright assertions ran**; its 23 launch failures are environment-blocked, not 23 application-test failures.
- A confirmed frontend defect prevents starting a geometry draft from an unreviewed analysis. Evidence is saved as `geometry-review-disabled-20261029.png`.
- The evaluation dataset has no ground-truth geometry. No precision, recall, F1, or interpretation-correctness score is claimed.

## Environment and isolation

- Backend: Python 3.14.4, Flask test server on `127.0.0.1:5101`.
- Frontend: Vite 8.3.5 on `127.0.0.1:5174`.
- Playwright package: `@playwright/test` 1.64.1.
- Integrated VS Code browser: Chrome 150.0.7871.250, VS Code 1.143.1.
- Playwright's downloaded Chromium was Chrome for Testing 156.0.8078.4, but could not start because `libnspr4.so`, `libnss3.so`, `libnssutil3.so`, `libsmime3.so`, and `libasound.so.2` are absent. `npx playwright install-deps chromium` was attempted and blocked because system package installation requires sudo authorization.
- Browser test servers use a temporary SQLite database and temporary upload directory. The regular backend database, upload directory, `.env`, and credentials were not used or modified. The test backend substitutes a deterministic mock provider; **no paid or live AI requests were made**.

## Commands and automated results

| Command | Result |
|---|---|
| `cd backend && ./.venv/bin/python -m unittest discover -s tests -v` | **PASS — 85 tests** |
| `cd frontend && npm run build` | **PASS** — Vite 8.3.5, 19 modules transformed |
| `cd frontend && npx playwright test --config tests/e2e/playwright.config.js --list` | **PASS** — 23 tests discovered |
| `cd frontend && npm run test:e2e` | **BLOCKED** — all 23 test processes stopped at `browserType.launch`; missing Chromium system libraries prevented browser assertions |
| `cd frontend && npx playwright install-deps chromium` | **BLOCKED** — system dependency installation required sudo |
| `node --check` on the Playwright config, Vite test config, and browser spec; Python syntax check on the mock server | **PASS** |
| `git diff --check` | **PASS** |

The local Playwright launch diagnostics and traces are under `qa-output/run-*/playwright-artifacts/`. These are startup diagnostics, not browser screenshots or application-test failures. The separate integrated-browser screenshot of the reproduced product issue is linked below.

## Integrated-browser smoke and upload results

The integrated Chromium browser used the isolated test server. Each dataset upload went through the UI and received a synthetic test proposal, not a real interpretation. HTTP 200 for the stored-image endpoint confirms retrieval; the local automated suite additionally contains a byte-for-byte retrieval assertion, but that assertion was not run locally because Chromium could not launch.

| Evaluation image | Size | Detected format | Upload | HTTP | Saved record | Original image HTTP | OpenCV lines | Mock proposal / review state |
|---|---:|---|---|---:|---|---:|---:|---|
| `test1.jpg` | 109,870 B | WebP (`image/webp`) | Success | 201 | Yes | 200 | 153 | Synthetic mock returned; pending review |
| `test2.jpg` | 86,957 B | JPEG (`image/jpeg`) | Success | 201 | Yes | 200 | 300 (cap) | Synthetic mock returned; pending review |
| `test3.png` | 75,621 B | PNG (`image/png`) | Success | 201 | Yes | 200 | 76 | Synthetic mock returned; pending review |
| `test4.jpg` | 18,606 B | JPEG (`image/jpeg`) | Success | 201 | Yes | 200 | 49 | Synthetic mock returned; pending review |
| `test5.png` | 732,759 B | PNG (`image/png`) | Success | 201 | Yes | 200 | 300 (cap) | Synthetic mock returned; pending review |

Exact upload observations are in [`upload-results-20261029.json`](./upload-results-20261029.json). A visual original/OpenCV/mock-proposal sheet is provided for every sketch under [`review-sheets-2026-10-29/`](./review-sheets-2026-10-29/index.html). The orange triangle in each sheet is an explicitly marked deterministic mock fixture, **not** an AI interpretation or a label for that sketch. Every sheet is marked as requiring human review.

### Upload and provider error cases

| Case | Result |
|---|---|
| Browser-generated valid WebP | HTTP 201; detected as `image/webp` |
| PNG bytes uploaded as `misleading.jpg` | HTTP 201; detected from bytes as `image/png` |
| Corrupted PNG | HTTP 422 `INVALID_IMAGE`; failed analysis record saved |
| Unsupported text file | HTTP 415 `UNSUPPORTED_IMAGE_TYPE`; failed analysis record saved |
| 10 MiB + 1 byte | UI rejected the file with a clear 10 MiB message and disabled submission; direct request returned HTTP 413 `IMAGE_TOO_LARGE` |
| Missing Gemini credential (mock) | HTTP 503; persisted as failed; UI explained that server-side credentials are not configured |
| Provider authentication failure (mock) | HTTP 502; persisted as failed; UI explained the account/credential failure |
| Provider rate limit (mock) | HTTP 429; persisted as failed; UI advised trying later |
| Provider timeout (mock) | HTTP 504; persisted as failed; UI explained the timeout |
| Provider network failure (mock) | HTTP 503; persisted as failed; UI explained backend connectivity to Gemini |
| Malformed provider response (mock) | HTTP 502 `INVALID_GEMINI_RESPONSE`; persisted as failed and explained in the UI |
| Empty proposal (mock) | HTTP 201 with zero joints/members; remains `pending_review`, not approved |

No secrets were included in browser-visible messages or the QA report. These provider scenarios were simulated; no provider credentials were tested.

## Navigation, visualization, review, and solver

Integrated-browser checks confirmed that the dashboard loaded, New Analysis and Analysis History navigation worked, history refreshed, an existing uploaded analysis could be reopened, the original image rendered, OpenCV and proposal overlays could be toggled, and zoom changed to 2.00×. A normal reload and history/detail navigation produced no uncaught page errors, browser console errors, or failed requests.

The API review workflow was exercised against the isolated backend:

1. A new AI proposal started as `pending_review`, with no human geometry.
2. Saving a valid triangle draft returned HTTP 200 and `draft`.
3. Explicit review returned HTTP 200 and `reviewed`.
4. Explicit solver submission returned HTTP 200 / `SOLVED`.
5. Reloaded detail retained the draft, submitted state, and member forces.

Invalid geometry and missing units each returned HTTP 422 `VALIDATION_FAILED`. Unconfirmed coordinates returned HTTP 422 `COORDINATES_NOT_CONFIRMED`; solving before review returned HTTP 409 `REVIEW_REQUIRED`. A singular reviewed model returned HTTP 422 `RANK_DEFICIENT_SYSTEM`, while retaining the reviewed geometry and diagnostics.

The numerical oracle remains the documented solver unit tests. The full backend suite passed, including the analytical triangle force/reaction checks and residual tolerance checks. No evaluation sketch was assigned solver forces: known loads, support conditions, units, and reference solutions do not exist for those images. A solvable model is not a physical-stability or engineering-safety finding.

## Ground truth and visual review

No expected geometry, annotated joints/members, or reference solver solutions were found under `backend/evaluation/expected/` or the other evaluation inputs. Existing files in `evaluation/results/` are OpenCV detections/overlays, not ground truth. The prior [`perception_evaluation.md`](../evaluation/results/perception_evaluation.md) also explicitly disclaims precision/recall scoring and records candidate clutter. No geometry comparison metrics are therefore reported.

The existing evaluation report describes `test1.jpg` as JPEG at line 19, but its actual bytes start with a WebP `RIFF...WEBP` signature; the upload endpoint correctly detected and stored it as `image/webp`. This is a confirmed evaluation metadata discrepancy, not an upload defect.

## Confirmed bugs

1. **Geometry editing is inaccessible for a new unreviewed proposal.** Reproduction: upload an image using the isolated mocked provider, open its detail, and inspect “Geometry draft.” The record is `pending_review`, `busy` is the empty string, but “Correct interpretation” is rendered disabled. This blocks the intended upload → edit → save → review → solve UI workflow. Direct API draft/review/solve requests work, so that API result does not clear the UI defect. See [`GeometryReview.vue:223`](../frontend/src/components/GeometryReview.vue#L223) and the [captured screenshot](./geometry-review-disabled-20261029.png). No application fix was made, per scope.

## Expected limitations

- OpenCV reports candidate lines, not structural members. It reached its 300-line cap on `test2.jpg` and `test5.png`; labels, ruled lines, dimensions, and drawing artifacts remain possible candidates.
- A valid mocked JSON proposal is not evidence that a sketch was interpreted correctly.
- The evaluation dataset is exploratory and has no truth labels or documented physical model data.
- The product is local-only and not authenticated; this QA run did not expose or test it publicly.

## Inconclusive or blocked

- The complete local Playwright suite could not execute until Chromium's missing shared libraries are installed. Browser test assertions, built-in failure screenshots, and tests for a missing stored-image response and an aborted network request remain unverified by the local runner. Manual integrated-browser smoke checks cover successful loading and several upload/provider cases, but do not replace that suite.
- Separate integrated-browser checks did simulate a stored-image 404 and an aborted history request; the UI retained the saved draft in the first case and showed a backend-connection message in the second. These do not count as executed local Playwright tests.
- No live AI provider, credentials, rate quota, or paid request was used or tested.
- Subjective geometry interpretation for all five images remains **unreviewed by a human**.

## Evidence and reproduction

- Reproduce the local runner blocker: `cd frontend && npm run test:e2e`; install the Chromium host dependencies with an administrator-approved system package step, then rerun the same command.
- Reproduce the geometry UI defect: start the configured isolated E2E servers, upload an evaluation sketch with the mocked provider, open the pending analysis, and verify that “Correct interpretation” is disabled despite no saved draft.
- Screenshot: [`geometry-review-disabled-20261029.png`](./geometry-review-disabled-20261029.png).
- Evaluation review sheets: [`review-sheets-2026-10-29/`](./review-sheets-2026-10-29/index.html).
- Per-image and edge upload observations: [`upload-results-20261029.json`](./upload-results-20261029.json).
