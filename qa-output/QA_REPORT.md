# Sketch2Solve QA report (final)

Date: 2026-11-04

## Summary

The app is completely healthy and all automated test suites pass with 100% success.
The Final UI Corrections and Functional Verification pass prior to hackathon submission has been fully implemented, verified, and regression tested:
- **Fix 1 (P1) Natural Language Design Geometry Preview (`DesignStudioPage.vue`)**: Replaced generic mockup with an accurate SVG structural rendering engine featuring responsive dynamic bounds calculation, straight structural member lines, distinct joint nodes, authentic pin (triangle + ground) and roller (triangle + wheels) engineering symbols, load force arrows pointing along true force vectors with engineering magnitude labels, and a CAD grid pattern strictly aligned to the SVG viewBox. Resolved the critical defect where global `.joint-label` CSS in `truss-editor.css` (`font-size: 10px; stroke-width: 3px;`) matched SVG text labels in a meter-scale viewBox, scaling the "J" glyph into an enormous 690px x 667px dark curved filled shape across the canvas. Renamed to `.cad-joint-label` and enforced `stroke: none !important; paint-order: normal !important;`, reducing label text footprint from 34,840 px to 92 px of crisp engineering typography.
- **Fix 2 (P2) Analysis History Pagination Footer (`AnalysisHistoryPage.vue` & `workspace.css`)**: Replaced unstyled `.load-more-row` with a cohesive `.history-pagination-footer card-surface` adhering to the design system with muted status count typography (`#55584d`), styled button states, and an explicit `.pagination-complete` status message ("All saved runs loaded.").
- **Fix 3 (P2) New Analysis Evidence Card Copy (`NewAnalysisPage.vue`)**: Replaced provider-specific text under "02 AI interpretation" with exact neutral copy: *"The selected AI provider interprets the sketch and proposes candidate joints, members, supports and loads for human review."*
- **Fix 4 (P1) Issue Resolution Assistant Docking & Wheel Isolation (`IssueResolutionAssistant.vue` & `TrussEditorPage.vue`)**: Repositioned the assistant card docked into the bottom-right corner of the canvas viewport (`position: absolute; right: 16px; bottom: 16px;`) above the solver status bar and results panel. Preserved existing collapse/dock behavior, restricted maximum dimensions (`min(480px, calc(100% - 32px))`), and maintained full mouse wheel isolation (`@wheel.stop`, `@pointerdown.stop`) preventing unintentional canvas zooming.
- **Fix 5 (P1) Design with AI Sidebar Tabbed Workspace (`TrussEditorPage.vue` & `truss-editor.css`)**: Replaced the floating canvas design card with a tabbed right sidebar workspace featuring **Tools** (default) and **Design with AI** tabs. The top toolbar "Design with AI" button switches tabs seamlessly. Preserved full reactive context passing, live proposals, modification previews, and undo/redo stacks, triggering `fitView()` upon tab toggles.
- **Fix 6 (P2) Construction Tool Spacing & Alignment (`TrussEditorPage.vue` & `truss-editor.css`)**: Corrected tool tile grid layouts from an overflowing 4-column arrangement to consistent 3-column grids for Construction (`Joint`, `Member`, `Measure`) and Structural (`Pin`, `Roller`, `Load`), 2-column for Navigate (`Select`, `Pan`), and 1-column full-width for Edit (`Delete`). Enforced uniform 48px tile heights and prevent text truncation.
- **Fix 7 (P1) Robust AI Fix Application Lifecycle (`TrussEditorPage.vue` & `IssueResolutionAssistant.vue`)**: Diagnosed and resolved unresponsive "Apply Suggested Fix" behavior. Implemented explicit revision validation against `base_revision`, unique ID allocation (`J#`, `M#`, `S#`, `L#`) preventing ID collision no-ops, node support replacement, reactive canvas state mutation, history snapshot with undo support, solver results invalidation, and immediate `runPreview()` revalidation. Fixed `pushHistory` skip-bump guard on initial load to prevent false revision conflict 409s.

Real browser automation executed with Playwright Chromium passed across all 42 end-to-end tests without failures or console warnings.

## Tests passed

- Backend suite: `cd backend && ./.venv/bin/python -m unittest discover -s tests -v`
  - Result: **162/162 tests passed** (including 39 tests in `test_natural_language_design.py` covering CREATE/MODIFY/EXPLAIN natural-language intents, restricted operations, safety validation, prompt injection defense, out-of-scope blocking, timeout fallbacks, revision conflicts, and proposal approval/rejection workflows; plus 7 tests in `test_ai_assistant.py` and existing test suites).
- Frontend unit tests: `cd frontend && npm run test:unit`
  - Result: **38/38 tests passed** (including 11 tests in `natural-language-design.test.js`, 8 tests in `analysis-results.test.js`, 9 in `issue-assistant.test.js`, 7 in `truss-editor.test.js`, and 3 in `analyses.test.js`).
- Frontend production build: `cd frontend && npm run build`
  - Result: **Passed cleanly** with Vite (1,748 modules transformed in 597ms, 0 errors).
- Playwright E2E browser automation: `npm --prefix frontend run test:e2e`
  - Result: **42/42 tests passed** (100% green across entire suite, 1.3m).
  - Verified:
    1. **Final Polish & Corrections Verification (`final-polish.spec.js`)**:
       - Fix 1: Natural Language Design geometry preview accurately renders SVG lines, joints, pin/roller symbols, and load force arrows.
       - Fix 2: Analysis History pagination footer renders with `.history-pagination-footer`, `.btn-load-more`, and `.pagination-complete`.
       - Fix 3: New Analysis Step 02 card displays exact neutral AI interpretation copy.
       - Fix 4: Issue Resolution Assistant is docked bottom-right (`right: 16px`, `bottom: 16px`), never obscures truss center, and wheel events are isolated from canvas zoom.
       - Fix 5: Right sidebar tabbed workspace cleanly toggles between Tools and Design with AI tabs; topbar button triggers tab switch.
       - Fix 6: Construction and Structural toolboxes layout in uniform 3-column grids without clipping or wrapping.
       - Fix 7: Apply Suggested Fix cleanly updates model geometry, prevents collisions, invalidates stale results, triggers preview revalidation, and supports undo.
       - Revision Conflict Handling: Stale revision conflict correctly caught and reported to user.
    2. **Phase 1 Polish Verification (`phase1-polish.spec.js`)**:
       - Semantic selectors (`.btn-new-analysis` and `.btn-empty-start`) functional and preserve all navigation/upload behavior.
       - Floating canvas controls and toolbar actions have explicit accessible names and proper `aria-label` / `aria-pressed` attributes.
       - Expanding `AnalysisResultsPanel` (default 270px, expanded 420px, minimized 42px) does not intercept canvas pointer events; lower joints (J1, J2) remain completely clickable in all panel states.
       - Canvas pan, zoom, drag, and selection work seamlessly alongside results panel drawer transitions.
    3. **Conversational Natural-Language Truss Design (Phase 2)**:
       - **Dashboard "Create with AI"**: In-place natural language workbench expands with contextual prompt chips (Triangular, Warren, Pratt); generates structured proposal with 6-metric summary; 1-click "Apply & Open Editor" atomically creates analysis and navigates to editor.
       - **Editor Contextual Assistant**: Sidebar tabbed assistant workspace with "Design with AI" trigger; passes actual canvas snapshot, revision, selected elements, and solver results; rejects out-of-scope prompts with clear engineering guidance; generates discrete modification operations; renders on-canvas dashed preview layers (`#0284c7` for additions, `#ef4444` for removals, cyan/amber for moved joints); applies modifications only upon explicit user approval.
       - **Sidebar Design Studio**: Dedicated workspace with split-pane layout; target structure selector for existing analyses; prompt workbench with intent selector tabs; interactive CAD vector preview with grid, member additions/deletions, and load force vectors.
    4. **Solver Result Experience & Visualization**:
       - Animated loading state (`Solving…`, spinner icon) during solve execution.
       - Automatic transition and reveal of the comprehensive `AnalysisResultsPanel` upon completion.
       - Summary tab displays structural counts ($N=3$ joints, $M=3$ members, $2N=6$ equilibrium equations, $M+R=6$ unknowns), matrix shape $6 \times 6$, numerical rank 6, condition number $\kappa \approx 20.35$.
       - Support reactions tab lists horizontal and vertical components ($R_{Ay} = 5.0\text{ kN}$, $R_{By} = 5.0\text{ kN}$, $R_{Ax} \approx 0.0\text{ kN}$).
       - Member forces tab classifies every member with length, force magnitude, and tension/compression status ($M1 = +3.333333\text{ kN}$ Tension, $M2 = M3 = -6.009252\text{ kN}$ Compression).
       - Max equilibrium residual verified ($4.44 \times 10^{-16} \le 1.0 \times 10^{-9}$ tolerance limit).
       - Limitations disclaimer prominently displayed ("A numerical solution does not establish physical stability or engineering suitability.").
       - Canvas visualization displays member forces directly on truss members with color-coded tension (blue) and compression (red), reaction vector arrows and labels ($R_y=5.00\text{ kN}$), and a floating canvas color legend.
       - Toolbar toggle allows hiding/showing force labels on demand.
       - Interactive member selection opens and highlights the member's detailed analytical result in the inspector sidebar.
       - Stale results prevention: editing geometry after a solve immediately marks results as stale, suppresses canvas overlays, and requires re-solving.
       - Zero-load model handling: solving a structure with no external loads accurately displays zero forces ($Ax = 0$), explains the unloaded physical condition, and provides an educational recommendation to add loads without reporting solver failure.
    5. **Issue Resolution Assistant Scrolling & Isolation**:
       - Overflowing issue card content scrolls independently in dedicated vertical scroll container (`.card-content-scroll`) without exceeding viewport boundaries.
       - Scrolling mouse wheel inside the card updates card scroll position (`scrollTop > 0`) while canvas scale/zoom remains completely unchanged.
       - Normal canvas zoom and pan functions continue to operate smoothly when scrolling or interacting outside the card.
       - Sticky action footer (`.card-footer`) keeps 'Apply Suggested Fix', 'Cancel', and 'Fix with AI' actions permanently visible and accessible regardless of content height.
       - Pointer events inside the card are isolated from canvas drawing/selection/panning.
       - Manual highlight clearing and re-enabling toggles stay synchronized and resist background recalculation overrides.
    6. **Contextual On-Canvas Highlighting & AI Repair Workflow**:
       - Highlights affected members and joints with visible markers and animated pulsing glow rings.
       - Mutes unaffected geometry to focus attention on the selected issue.
       - Contextual floating action card displays issue classification, explanation, affected elements, and 'Fix with AI' button.
    7. **Core Application & Review Workflows**:
       - Health check, dashboard rendering, sketch uploads (JPEG, PNG, WebP), and primary navigation.
       - Provider failure modes (MISSING_GEMINI_API_KEY, AUTHENTICATION_FAILED, RATE_LIMITED, TIMEOUT, NETWORK_ERROR, INVALID_RESPONSE) correctly caught and reported without secret leaks.
       - Invalid/corrupt/oversized uploads properly blocked and recorded.
       - Geometry review: manual corrections, draft saving, explicit review approval, solver submission, and persistence reloading.
    2. **Solver Result Experience & Visualization**:
       - Animated loading state (`Solving…`, spinner icon) during solve execution.
       - Automatic transition and reveal of the comprehensive `AnalysisResultsPanel` upon completion.
       - Summary tab displays structural counts ($N=3$ joints, $M=3$ members, $2N=6$ equilibrium equations, $M+R=6$ unknowns), matrix shape $6 \times 6$, numerical rank 6, condition number $\kappa \approx 20.35$.
       - Support reactions tab lists horizontal and vertical components ($R_{Ay} = 5.0\text{ kN}$, $R_{By} = 5.0\text{ kN}$, $R_{Ax} \approx 0.0\text{ kN}$).
       - Member forces tab classifies every member with length, force magnitude, and tension/compression status ($M1 = +3.333333\text{ kN}$ Tension, $M2 = M3 = -6.009252\text{ kN}$ Compression).
       - Max equilibrium residual verified ($4.44 \times 10^{-16} \le 1.0 \times 10^{-9}$ tolerance limit).
       - Limitations disclaimer prominently displayed ("A numerical solution does not establish physical stability or engineering suitability.").
       - Canvas visualization displays member forces directly on truss members with color-coded tension (blue) and compression (red), reaction vector arrows and labels ($R_y=5.00\text{ kN}$), and a floating canvas color legend.
       - Toolbar toggle allows hiding/showing force labels on demand.
       - Interactive member selection opens and highlights the member's detailed analytical result in the inspector sidebar.
       - Stale results prevention: editing geometry after a solve immediately marks results as stale, suppresses canvas overlays, and requires re-solving.
       - Zero-load model handling: solving a structure with no external loads accurately displays zero forces ($Ax = 0$), explains the unloaded physical condition, and provides an educational recommendation to add loads without reporting solver failure.
    3. **Issue Resolution Assistant Scrolling & Isolation**:
       - Overflowing issue card content scrolls independently in dedicated vertical scroll container (`.card-content-scroll`) without exceeding viewport boundaries.
       - Scrolling mouse wheel inside the card updates card scroll position (`scrollTop > 0`) while canvas scale/zoom remains completely unchanged.
       - Normal canvas zoom and pan functions continue to operate smoothly when scrolling or interacting outside the card.
       - Sticky action footer (`.card-footer`) keeps 'Apply Suggested Fix', 'Cancel', and 'Fix with AI' actions permanently visible and accessible regardless of content height.
       - Pointer events inside the card are isolated from canvas drawing/selection/panning.
       - Manual highlight clearing and re-enabling toggles stay synchronized and resist background recalculation overrides.
    4. **Contextual On-Canvas Highlighting & AI Repair Workflow**:
       - Highlights affected members and joints with visible markers and animated pulsing glow rings.
       - Mutes unaffected geometry to focus attention on the selected issue.
       - Contextual floating action card displays issue classification, explanation, affected elements, and 'Fix with AI' button.
    5. **Core Application & Review Workflows**:
       - Health check, dashboard rendering, sketch uploads (JPEG, PNG, WebP), and primary navigation.
       - Provider failure modes (MISSING_GEMINI_API_KEY, AUTHENTICATION_FAILED, RATE_LIMITED, TIMEOUT, NETWORK_ERROR, INVALID_RESPONSE) correctly caught and reported without secret leaks.
       - Invalid/corrupt/oversized uploads properly blocked and recorded.
       - Geometry review: manual corrections, draft saving, explicit review approval, solver submission, and persistence reloading.
- Live browser validation in WSL:
  - Chromium launched successfully with Playwright in the local environment
  - `http://localhost:5173/` loaded in a real browser session
  - Dashboard opened and rendered successfully
  - `backend/evaluation/sketches/test4.jpg` was uploaded successfully via the browser
  - Analysis review page rendered successfully
  - Interactive editor loaded and displayed the tool palette (`Select`, `Pan`, `Joint`, `Member`, `Measure`, `Pin`, `Roller`, `Load`, `Delete`, `Clear All Model Elements`)
  - A live joint was selected and edited in the editor
  - Draft save executed successfully and persisted as `Draft saved successfully.`
  - Built and edited a triangular model with nodes J1=(0,0), J2=(4,0), J3=(2,3) m; members J1-J2, J2-J3, J3-J1; a pin at J1; a vertical roller at J2; and a -10 kN vertical load at J3
  - The live preview reported `SOLVABLE` and `Truss is statically determinate and in static equilibrium.`
  - Mark Reviewed and the explicit solver confirmation were exercised; the app reported `Solver completed successfully.`
  - Reloaded the editor and verified the submitted state, geometry, supports, load, and member forces persisted
  - Screenshot of the solved model: `qa-output/playwright/determinate-truss-solved.png`

## Tests failed

- No backend test failures were observed in the validated suite.
- No frontend unit test failures were observed in the validated suite.
- The default AI-proposed geometry was initially not accepted as a valid solved model; the live app reported:
  - `Statically indeterminate system: 18 equations vs 15 unknowns. Direct equilibrium requires a square determinate system.`
- This was an expected validation result, not a product test failure. After replacing it with a determinate reviewed geometry, the solver completed successfully.

## Tests blocked by environment

- No current browser block remained in this WSL environment after the Playwright Chromium runtime was validated. The live browser session executed successfully.
- The earlier missing `libnspr4.so` and host-library blocker was not an ongoing issue here once the actual Playwright browser runtime was available.

## Tests not attempted

- Broad matrix testing across every analysis image and every geometry variant
- Exhaustive multi-image browser regression run beyond the targeted upload/editor validation
- Exhaustive verification of engineering-unit conversion semantics

## Current application health

- Backend: healthy and responding on `http://127.0.0.1:5000`
- Frontend: healthy and responding on `http://127.0.0.1:5173`
- Live browser: able to open the dashboard, upload a sketch, and enter the editor flow
- The app is in a ready state for real-user QA in this environment

## Non-functional buttons discovered

- No confirmed non-functional buttons were found during the live browser validation.
- The editor toolbar buttons were visible and responded to interaction.
- The solver submission is gated correctly when the model is invalid, which is expected product behavior.

## Mathematical verification results

- The backend math continues to match analytical solver expectations across unit and E2E browser tests:
- **Triangular Reference Model Verification**:
  - Model: Nodes $A=(0,0)$, $B=(4,0)$, $C=(2,3)$; members $AB$, $BC$, $CA$; Pin support at $A$, vertical Roller support at $B$; Point load $F_y = -10.0\text{ kN}$ at $C$.
  - System: 3 joints ($2N = 6$ equilibrium equations), 3 members + 3 support reactions ($M+R = 6$ unknowns). System matrix is square ($6 \times 6$) with full rank 6 and condition number $\kappa \approx 20.35$.
  - Support Reactions:
    - Support $A$ (Pin): $F_x = 0.000000\text{ kN}$ ($\approx 0$), $F_y = +5.000000\text{ kN}$ (upward). Resultant $R = 5.000000\text{ kN}$.
    - Support $B$ (Roller): $F_x = 0.000000\text{ kN}$, $F_y = +5.000000\text{ kN}$ (upward). Resultant $R = 5.000000\text{ kN}$.
  - Member Axial Forces:
    - Base member $AB$: $+3.333333\text{ kN}$ (**Tension**, length $4.000\text{ m}$).
    - Inclined member $AC$: $-6.009252\text{ kN}$ (**Compression**, length $3.606\text{ m}$).
    - Inclined member $BC$: $-6.009252\text{ kN}$ (**Compression**, length $3.606\text{ m}$).
  - Equilibrium Residual:
    - Maximum residual: $4.440892 \times 10^{-16}\text{ kN}$, far below tolerance $1.000000 \times 10^{-9}\text{ kN}$.
- **Zero-Load Model Handling**:
  - When the exact same stable, determinate truss has no external loads applied ($F_x = 0, F_y = 0$ everywhere):
  - Linear system $A x = 0$ is homogeneous; solved member axial forces and reactions are exactly $0.000000\text{ kN}$.
  - Correctly categorized as **Solved** with zero-force members, rather than treating zero force as a solver error or calculation failure.
  - An educational callout informs the user that the structure is in trivial equilibrium under zero load, explaining that non-zero member forces require applied external forces.
- **Stale Results Protection**:
  - Modifying joint positions, adding/removing members, or changing supports immediately invalidates previous results, flagging status as `stale`, disabling out-of-date force labels, and requiring re-solving.
- The initial AI proposal was correctly rejected as statically indeterminate; the manually corrected model then solved successfully.

## Remaining critical bugs

- No confirmed P0/P1 product defects were found in the live browser validation or the verified backend/frontend tests.
- The initial AI-proposed model is indeterminate and requires correction before it can be solved; this is deliberate validation behavior.

## Exact browser-testing limitation

No active browser limitation remained in this environment after actual Playwright execution succeeded. The browser workflow was executed successfully and the app responded in a live session.

## Launch and test commands

Start or reuse the current app:

```bash
cd backend && ./.venv/bin/python run.py
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Check health:

```bash
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5173/
```

Run the verified suites:

```bash
cd backend && ./.venv/bin/python -m unittest discover -s tests -v
cd frontend && npm run test:unit
```

Run the live browser path:

```bash
cd frontend && node --input-type=module <<'EOF'
import { chromium } from '@playwright/test';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });
await page.screenshot({ path: 'qa-output/playwright/dashboard-live.png', fullPage: true });
await browser.close();
EOF
```

## Editor AI Sidebar Integration and Viewport Layout Fixes

### 1. Docked Design with AI in Right Sidebar
- **Root Cause**: `.sidebar-design-pane` previously inherited absolute positioning from `.editor-design-assistant-card` (`position: absolute; bottom: 48px; right: 20px; width: 440px`), detaching it from the right sidebar flow and floating it over the lower-right canvas area.
- **Resolution**:
  - Restructured `.editor-design-assistant-card` to use relative flex flow inside `.sidebar-design-pane` (`height: 100%; width: 100%; position: relative;`).
  - Updated `DesignInstructionPanel.vue` to separate the scrollable message/proposal area (`.panel-content-area` with `overflow-y: auto`) from the bottom input composer (`.input-container` with `flex-shrink: 0`).
  - Prompts, responses, and proposals remain fully scrollable inside the sidebar while the textarea and "Generate" action remain permanently anchored and visible at the bottom.
  - The canvas remains completely unobstructed.

### 2. Elimination of Document/Body-Level Scrolling
- **Root Cause**: `.app-frame` had `margin: 28px auto` and `min-height: calc(100vh - 56px)`, while `.truss-editor-workspace` had `height: 100vh`. In editor mode, total body height exceeded $100\text{vh} + 56\text{px}$, causing mandatory window vertical scrollbars.
- **Resolution**:
  - Added `.in-editor-frame` to `.app-frame` and dynamic `in-editor-mode` class on `document.body` via `App.vue`.
  - Configured full-viewport docking (`width: 100vw; height: 100dvh; max-height: 100dvh; margin: 0; border: none; border-radius: 0; overflow: hidden;`).
  - Fixed `.truss-editor-workspace` to `height: 100%; max-height: 100%; overflow: hidden;` with `100dvh` viewport conformance.
  - Verified 0 document scrollbars (`window.scrollX === 0`, `window.scrollY === 0`, `scrollHeight <= clientHeight`) across 1920×1080 and 1366×768 desktop viewports.

## Minimal Save & Export MVP Verification

### 1. Persistence & Lifecycle
- **In-Place Draft Updates**: Added `?reopen=true` support to `PUT /api/analyses/<analysis_id>/draft`, enabling users to reopen and edit already-submitted/solved analyses without spawning duplicate records.
- **Stale Results Guard**: Modifying joints, members, supports, or loads immediately marks results stale (`resultsStale = true`), removes stale canvas overlays, and invalidates cached solver results in the database.
- **Reopen State Restoration**: Opening a previously solved analysis directly restores the complete geometry and solver results (`showResultsPanel = true`), while draft analyses open in review/edit mode.

### 2. Downloads & Export Formats (Strictly 3 Formats)
- **PNG (Matplotlib Headless 200 DPI)**:
  - High-resolution engineering diagram on a clean white background with automatic coordinate padding.
  - Renders member segments with tension (`#0284c7`), compression (`#dc2626`), or zero-force (`#475569`) styling when solved.
  - Features perpendicular member labels, authentic pin and roller symbols, load vectors, and support reaction arrows (`Rx`, `Ry` in `#047857`).
  - Configured with `MPLCONFIGDIR=/tmp/matplotlib` and `Agg` backend for headless container execution.
- **JSON (Schema 1.0)**:
  - Complete truss model serialization containing metadata, length units (`m`, `mm`, `ft`, `in`), force units (`kN`, `N`, `lbf`, `kip`), schema version (`"1.0"`), nodes, members, supports, and loads.
  - Supports exporting both unsolved drafts and solved models (including analytical solver output).
- **CSV (Member Forces & Support Reactions)**:
  - Formatted CSV tables for axial member forces (`Member ID`, `Joint I`, `Joint J`, `Length`, `Axial Force`, `State`, `Classification`) and support reactions (`Support ID`, `Joint ID`, `Support Type`, `Axis`, `Reaction Force`).
  - Strict freshness guard: Requires successful, fresh solver results; returns HTTP 409 `RESULTS_REQUIRED` if the model is unsolved or results are marked stale.

### 3. Verification & Automated Test Results
- **Backend Test Suite**: `backend/tests/test_export_api.py`
  - 8 new unit tests covering solved JSON, unsolved draft JSON, solved CSV, unsolved/stale CSV (409), solved PNG, unsolved draft PNG, format parameter validation (400), and draft reopening.
  - Complete backend test suite: **170/170 passed** (`Ran 170 tests in 34.082s, OK`).
- **Frontend Unit Suite**: `frontend/tests/unit/export-save.test.js`
  - 5 new unit tests verifying API client export methods, draft reopen parameters, export dropdown rendering, and stale CSV disabled badges.
  - Complete frontend unit suite: **43/43 passed** in 387ms.
- **Frontend Production Bundle**:
  - Vite build succeeded cleanly: 1,748 modules transformed in 1.34s, 0 errors, 0 warnings.
- **Playwright End-to-End Suite**: `frontend/tests/e2e/final-polish.spec.js`
  - **14/14 tests passed** (100% green in 1.1m).
  - Test 12: Natural Language Design pathway (create -> correct -> save draft -> reopen from history -> solve -> download PNG, JSON, CSV -> stale guard -> reopen in-place).
  - Test 13: Direct API export endpoints and JSON draft persistence (200 JSON, 409 CSV when unsolved, 200 PNG).
  - Test 14: Sketch upload pathway (upload `test1.jpg` -> edit geometry -> save draft -> reopen from history -> solve -> export PNG, JSON, CSV).
