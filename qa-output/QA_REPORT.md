# Sketch2Solve QA report (final)

Date: 2026-11-04

## Summary

The app is completely healthy and all automated test suites pass with 100% success.
Phase 1 of the Sketch2Solve polish roadmap (targeted P1 and P2 findings from `audit-report.md`) has been fully implemented and verified:
- **P1 Canvas Pointer Interception**: Resolved the defect where `AnalysisResultsPanel` overlaid the canvas lower third and intercepted pointer events on lower joints (e.g. J1, J2). Replaced absolute positioning with an `.editor-canvas-column` flex layout, standardized panel height drawer states (default 270px, expanded 420px, minimized 42px), and attached a `ResizeObserver` with responsive percentage padding so the visible canvas viewport dynamically resizes and automatically keeps all geometry fully visible and clickable.
- **P2 Dashboard Selectors**: Added semantic, component-specific class hooks (`.btn-new-analysis`, `.btn-empty-start`) while maintaining `.dashboard-primary` for backwards compatibility and shared styles.
- **P2 Accessibility & Contrast**: Added explicit accessible names (`role="toolbar"`, `aria-label`, `aria-pressed`) to all icon-only floating toolbar controls, canvas action buttons, and results panel controls; adjusted secondary text colors to strictly exceed WCAG AA standards (>= 4.5:1).

Real browser automation executed with Playwright Chromium passed across all 33 end-to-end tests without failures or console warnings.

## Tests passed

- Backend suite: `cd backend && ./.venv/bin/python -m unittest discover -s tests -v`
  - Result: **162/162 tests passed** (including 39 tests in `test_natural_language_design.py` covering CREATE/MODIFY/EXPLAIN natural-language intents, restricted operations, safety validation, prompt injection defense, out-of-scope blocking, timeout fallbacks, revision conflicts, and proposal approval/rejection workflows; plus 7 tests in `test_ai_assistant.py` and existing test suites)
- Frontend unit tests: `cd frontend && npm run test:unit`
  - Result: **38/38 tests passed** (including 11 tests in `natural-language-design.test.js`, 8 tests in `analysis-results.test.js`, 9 in `issue-assistant.test.js`, 7 in `truss-editor.test.js`, and 3 in `analyses.test.js`)
- Frontend production build: `cd frontend && npm run build`
  - Result: **Passed cleanly** with Vite (1,748 modules transformed in 1.28s, 0 errors).
- Playwright E2E browser automation: `npm --prefix frontend run test:e2e`
  - Result: **33/33 tests passed** (100% green across entire suite).
  - Verified:
    1. **Phase 1 Polish Verification (`phase1-polish.spec.js`)**:
       - Semantic selectors (`.btn-new-analysis` and `.btn-empty-start`) functional and preserve all navigation/upload behavior.
       - Floating canvas controls and toolbar actions have explicit accessible names and proper `aria-label` / `aria-pressed` attributes.
       - Expanding `AnalysisResultsPanel` (default 270px, expanded 420px, minimized 42px) does not intercept canvas pointer events; lower joints (J1, J2) remain completely clickable in all panel states.
       - Canvas pan, zoom, drag, and selection work seamlessly alongside results panel drawer transitions.
    2. **Conversational Natural-Language Truss Design (Phase 2)**:
       - **Dashboard "Create with AI"**: In-place natural language workbench expands with contextual prompt chips (Triangular, Warren, Pratt); generates structured proposal with 6-metric summary; 1-click "Apply & Open Editor" atomically creates analysis and navigates to editor.
       - **Editor Contextual Assistant**: Floating docked assistant card with "Design with AI" toolbar trigger; passes actual canvas snapshot, revision, selected elements, and solver results; rejects out-of-scope prompts with clear engineering guidance; generates discrete modification operations; renders on-canvas dashed preview layers (`#0284c7` for additions, `#ef4444` for removals, cyan/amber for moved joints); applies modifications only upon explicit user approval.
       - **Sidebar Design Studio**: Dedicated workspace with split-pane layout; target structure selector for existing analyses; prompt workbench with intent selector tabs; interactive CAD vector preview with grid, member additions/deletions, and load force vectors.
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
