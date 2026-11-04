# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase1-polish.spec.js >> Phase 1 Polish Verification >> 1. Dashboard: semantic selectors and buttons retain existing behavior
- Location: tests/e2e/phase1-polish.spec.js:9:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.sketch-uploader, .dropzone, input[type="file"]')
Expected: visible
Error: strict mode violation: locator('.sketch-uploader, .dropzone, input[type="file"]') resolved to 2 elements:
    1) <input type="file" class="visually-hidden" accept="image/jpeg,image/png,image/webp"/> aka getByRole('button', { name: 'Choose File' })
    2) <div tabindex="0" role="button" class="dropzone">…</div> aka getByRole('button', { name: 'Drop your sketch here or' })

Call log:
  - Expect "toBeVisible" locator('.sketch-uploader, .dropzone, input[type="file"]') with timeout 8000ms
  - waiting for locator('.sketch-uploader, .dropzone, input[type="file"]')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - complementary [ref=e4]:
    - link "Sketch2Solve STRUCTURE REVIEW" [ref=e5] [cursor=pointer]:
      - /url: /
      - generic [ref=e13]:
        - strong [ref=e14]: Sketch2Solve
        - generic [ref=e15]: STRUCTURE REVIEW
    - generic [ref=e16]: Local workspace
    - navigation "Main navigation" [ref=e18]:
      - button "Dashboard" [ref=e19] [cursor=pointer]
      - button "Natural Language Design" [ref=e26] [cursor=pointer]
      - button "New analysis" [ref=e32] [cursor=pointer]
      - button "Analysis history 0" [ref=e36] [cursor=pointer]:
        - generic [ref=e42]: Analysis history
        - generic [ref=e43]: "0"
    - generic [ref=e49]:
      - strong [ref=e50]: Private by default
      - paragraph [ref=e51]: Runs stay in your local backend. Don’t expose this workspace publicly.
    - generic [ref=e52]: Backend API · localhost:5000
  - main [ref=e54]:
    - generic [ref=e55]:
      - generic [ref=e56]:
        - generic [ref=e57]: Workspace
        - generic [ref=e58]: /
        - strong [ref=e59]: New analysis
      - generic [ref=e60]:
        - generic [ref=e61]: LOCAL ONLY
        - generic [aria-hidden] [ref=e63]: S
    - generic [ref=e64]:
      - generic [ref=e65]:
        - generic [ref=e66]:
          - generic [ref=e67]: SKETCH INTERPRETATION
          - heading [level=1] [ref=e68]:
            - text: Review a structure,
            - emphasis [ref=e69]: before
            - text: you solve it.
          - paragraph [ref=e70]: Compare computer vision evidence with a model interpretation. Each proposal requires a human review before it can reach the solver.
        - generic [ref=e71]: 01 / INTAKE
      - generic [ref=e74]:
        - generic [ref=e75]:
          - generic [ref=e76]:
            - generic [ref=e77]:
              - generic [ref=e78]: STEP 1
              - heading "Add a sketch" [level=2] [ref=e79]
            - generic [ref=e80]: MAX 10 MiB
          - button "Choose File" [ref=e81]
          - button "Drop your sketch here or browse files on your device JPEG, PNG or WebP" [ref=e82] [cursor=pointer]:
            - strong [ref=e86]: Drop your sketch here
            - generic [ref=e87]: or browse files on your device
            - generic [ref=e88]: JPEG, PNG or WebP
          - generic [ref=e89]:
            - generic [ref=e90]: Interpretation provider
            - combobox "Interpretation provider" [ref=e91]:
              - option "Gemini · Flash-Lite" [selected]
              - option "Meta · Muse Spark"
          - button "Start analysis" [disabled] [ref=e92]
          - paragraph [ref=e95]: Provider credentials stay on the backend.
        - generic [ref=e99]:
          - generic [ref=e100]:
            - generic [ref=e101]:
              - generic [ref=e102]: A CONTROLLED WORKFLOW
              - heading "Evidence stays distinct" [level=2] [ref=e103]
            - generic [ref=e104]: ⌁
          - generic [ref=e105]:
            - generic [ref=e106]: "01"
            - generic [ref=e107]:
              - strong [ref=e108]: Visual evidence
              - paragraph [ref=e109]: OpenCV reports candidate lines and endpoint clusters. These are not verified truss members.
            - generic [ref=e110]: VISION
          - generic [ref=e111]:
            - generic [ref=e112]: "02"
            - generic [ref=e113]:
              - strong [ref=e114]: AI interpretation
              - paragraph [ref=e115]: Gemini proposes possible joints, members, supports and loads from the sketch.
            - generic [ref=e116]: GEMINI
          - generic [ref=e117]:
            - generic [ref=e118]: "03"
            - generic [ref=e119]:
              - strong [ref=e120]: Human review
              - paragraph [ref=e121]: Correct a separate draft, check its units, then explicitly mark it reviewed before solver submission.
            - generic [ref=e122]: REVIEW
          - generic [ref=e123]:
            - generic [ref=e124]: i
            - paragraph [ref=e125]: Nothing is solved automatically from the AI proposal. Solver output describes only the geometry you explicitly reviewed and submitted.
    - generic [ref=e126]:
      - generic [ref=e127]: Sketch2Solve · Local review workspace
      - generic [ref=e128]: Interpretation is a starting point, not a structural check.
```

# Test source

```ts
  1   | import { readFileSync } from 'node:fs'
  2   | import path from 'node:path'
  3   | import { test, expect } from '@playwright/test'
  4   | 
  5   | const configDirectory = import.meta.dirname
  6   | const evaluationDirectory = path.resolve(configDirectory, '../../../backend/evaluation/sketches')
  7   | 
  8   | test.describe('Phase 1 Polish Verification', () => {
  9   |   test('1. Dashboard: semantic selectors and buttons retain existing behavior', async ({ page }) => {
  10  |     await page.goto('/')
  11  |     await expect(page.locator('.dashboard-welcome')).toBeVisible()
  12  | 
  13  |     // 1. Verify semantic classes exist and are distinct
  14  |     const headerNewBtn = page.locator('.btn-new-analysis')
  15  |     await expect(headerNewBtn).toBeVisible()
  16  |     await expect(headerNewBtn).toHaveClass(/dashboard-primary/)
  17  |     await expect(headerNewBtn).toHaveText(/New analysis/)
  18  | 
  19  |     // 2. Verify AI Workbench button still functions
  20  |     const aiBtn = page.locator('.dashboard-ai-btn')
  21  |     await expect(aiBtn).toBeVisible()
  22  |     await aiBtn.click()
  23  |     const workbench = page.locator('.dashboard-ai-workbench')
  24  |     await expect(workbench).toBeVisible()
  25  | 
  26  |     // Close workbench
  27  |     await page.locator('.btn-close-workbench').click()
  28  |     await expect(workbench).not.toBeVisible()
  29  | 
  30  |     // 3. Click New Analysis button to navigate to upload page
  31  |     await headerNewBtn.click()
> 32  |     await expect(page.locator('.sketch-uploader, .dropzone, input[type="file"]')).toBeVisible()
      |                                                                                   ^ Error: expect(locator).toBeVisible() failed
  33  |   })
  34  | 
  35  |   test('2. Accessibility: canvas floating controls and header actions have explicit accessible names', async ({ page }) => {
  36  |     // Create a new analysis via design studio to jump into the editor
  37  |     await page.goto('/?view=design')
  38  |     await expect(page.locator('.design-studio-page')).toBeVisible()
  39  | 
  40  |     const textarea = page.locator('.studio-left-pane .design-textarea')
  41  |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  42  |     await page.locator('.studio-left-pane .btn-submit').click()
  43  | 
  44  |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  45  |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  46  |     await proposalCard.locator('.btn-apply').click()
  47  | 
  48  |     // In editor workspace
  49  |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  50  | 
  51  |     // Verify accessible names on canvas toolbar
  52  |     const controls = page.locator('.canvas-floating-controls')
  53  |     await expect(controls).toBeVisible()
  54  |     await expect(controls).toHaveAttribute('role', 'toolbar')
  55  |     await expect(controls).toHaveAttribute('aria-label', 'Canvas view controls')
  56  | 
  57  |     await expect(controls.locator('button[aria-label="Zoom in"]')).toBeVisible()
  58  |     await expect(controls.locator('button[aria-label="Zoom out"]')).toBeVisible()
  59  |     await expect(controls.locator('button[aria-label="Fit content to view"]')).toBeVisible()
  60  |     await expect(controls.locator('button[aria-label="Toggle grid"]')).toBeVisible()
  61  |     await expect(controls.locator('button[aria-label="Snap to grid"]')).toBeVisible()
  62  |     await expect(controls.locator('button[aria-label="Toggle AI proposal layer"]')).toBeVisible()
  63  | 
  64  |     // Verify topbar accessible names
  65  |     await expect(page.locator('.editor-topbar button[aria-label="Return to Dashboard"], .editor-topbar .back-btn[aria-label]')).toBeVisible()
  66  |     await expect(page.locator('.editor-topbar button[aria-label="Undo"]')).toBeVisible()
  67  |     await expect(page.locator('.editor-topbar button[aria-label="Redo"]')).toBeVisible()
  68  |   })
  69  | 
  70  |   test('3. P1 Fix: AnalysisResultsPanel viewport management, lower joints clickability, expand/minimize states, and pan/zoom', async ({ page }) => {
  71  |     // 1. Create a determinate triangular truss with J1 at (0,0), J2 at (4,0), J3 at (2,3)
  72  |     await page.goto('/?view=design')
  73  |     const textarea = page.locator('.studio-left-pane .design-textarea')
  74  |     await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
  75  |     await page.locator('.studio-left-pane .btn-submit').click()
  76  | 
  77  |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  78  |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  79  |     await proposalCard.locator('.btn-apply').click()
  80  | 
  81  |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  82  | 
  83  |     // 2. Mark reviewed and solve
  84  |     const reviewBtn = page.locator('.btn-review')
  85  |     await expect(reviewBtn).toBeEnabled()
  86  |     await reviewBtn.click()
  87  | 
  88  |     const solveBtn = page.locator('.btn-solve')
  89  |     await expect(solveBtn).toBeEnabled({ timeout: 5_000 })
  90  |     await solveBtn.click()
  91  | 
  92  |     // Confirm dialog
  93  |     const confirmDialog = page.locator('.cdialog-panel')
  94  |     await expect(confirmDialog).toBeVisible()
  95  |     await confirmDialog.locator('.cdialog-confirm').click()
  96  | 
  97  |     // 3. Results panel opens
  98  |     const resultsPanel = page.locator('.analysis-results-panel')
  99  |     await expect(resultsPanel).toBeVisible({ timeout: 10_000 })
  100 |     await expect(resultsPanel.locator('.badge-solved')).toBeVisible()
  101 | 
  102 |     // Verify editor-canvas-column layout
  103 |     const column = page.locator('.editor-canvas-column')
  104 |     await expect(column).toBeVisible()
  105 |     const canvasContainer = page.locator('.canvas-container')
  106 |     await expect(canvasContainer).toBeVisible()
  107 | 
  108 |     // 4. LOWER JOINTS REMAIN FULLY CLICKABLE WHILE RESULTS PANEL IS OPEN
  109 |     // Select tool
  110 |     await page.locator('.tool-tile[title*="Select"]').click()
  111 | 
  112 |     // Joint 1 (J1) is at the bottom left (Y=0), the lowest part of the truss
  113 |     const jointNodes = page.locator('.truss-joints-group circle.truss-joint-node')
  114 |     await expect(jointNodes).toHaveCount(3)
  115 | 
  116 |     // Click the first joint (bottom joint)
  117 |     const firstJoint = jointNodes.first()
  118 |     await expect(firstJoint).toBeVisible()
  119 |     await firstJoint.click()
  120 | 
  121 |     // Inspector opens and displays the selected joint properties
  122 |     const inspector = page.locator('.editor-sidebar .inspector-section')
  123 |     await expect(inspector).toBeVisible()
  124 |     await expect(inspector.locator('.element-badge')).toBeVisible()
  125 | 
  126 |     // 5. EXPAND PANEL: test expanded state
  127 |     const expandBtn = resultsPanel.locator('.btn-expand')
  128 |     await expect(expandBtn).toBeVisible()
  129 |     await expandBtn.click()
  130 |     await expect(resultsPanel).toHaveClass(/is-expanded/)
  131 | 
  132 |     // Lower joints must remain clickable in expanded state
```