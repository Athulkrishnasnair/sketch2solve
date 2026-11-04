# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 1. Natural Language Design geometry preview accurately renders geometry, supports, loads, and CAD grid
- Location: tests/e2e/final-polish.spec.js:4:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.studio-canvas-stage .cad-svg')
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.studio-canvas-stage .cad-svg') with timeout 8000ms
  - waiting for locator('.studio-canvas-stage .cad-svg')

```

```yaml
- complementary:
  - link "Sketch2Solve STRUCTURE REVIEW":
    - /url: /
    - strong: Sketch2Solve
    - text: STRUCTURE REVIEW
  - text: Local workspace
  - navigation "Main navigation":
    - button "Dashboard"
    - button "Natural Language Design"
    - button "New analysis"
    - button "Analysis history 0"
  - strong: Private by default
  - paragraph: Runs stay in your local backend. Don’t expose this workspace publicly.
  - text: Backend API · localhost:5000
- main:
  - text: Workspace /
  - strong: Natural Language Design
  - text: LOCAL ONLY CONVERSATIONAL TRUSS WORKBENCH
  - heading "Natural Language Design Studio" [level=1]
  - paragraph: Synthesize new structural geometries, modify canvas snapshots, and inspect determinacy using deterministic engineering rules.
  - text: "Target Structure:"
  - combobox "Target Structure:":
    - option "＋ New Truss Design (Blank Canvas)" [selected]
  - text: Rev 1
  - radiogroup "Design Intent":
    - button "Auto"
    - button "Create"
    - button "Modify"
    - button "Explain"
  - textbox "Describe structural change or question (e.g. \"Add a diagonal between J1 and J3\", \"Move J2 up 0.5m\", \"Why unstable?\")...": Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top
  - text: Enter ↵ to submit · Shift+Enter for newline
  - button "Generate"
  - text: "CREATE #b2452b4a rev 1 rev 2 Valid"
  - paragraph: Generated a statically determinate triangular truss with a 6.0 m span, 3.0 m height, pin support at left, roller support at right, and applied vertical load.
  - text: Topology Preview
  - img
  - text: "3 Joints 3 Members 2 Supports 1 Loads 6.00 m Span 3.00 m Height Predicted:"
  - strong: SQUARE_FULL_RANK
  - text: (6 eq vs 6 unk)
  - button "Discard"
  - button "Apply & Open Editor"
  - strong: CAD Design Conventions
  - list:
    - listitem:
      - strong: "CREATE:"
      - text: Specify span, height, panel count, and support conditions (e.g.
      - emphasis: "\"Warren truss, 6 m span, 4 panels\""
      - text: ).
    - listitem:
      - strong: "MODIFY:"
      - text: Reference existing joint/member IDs (e.g.
      - emphasis: "\"Add diagonal between J1 and J3\""
      - text: ","
      - emphasis: "\"Move J2 up 0.5 m\""
      - text: ).
    - listitem:
      - strong: "EXPLAIN:"
      - text: Ask about determinacy, stability, or support reactions (e.g.
      - emphasis: "\"Why is this unstable?\""
      - text: ).
    - listitem:
      - strong: "SAFETY GATE:"
      - text: AI proposals are strictly non-destructive previews until explicitly approved.
  - strong: Structural Geometry Preview
  - text: "Previewing Proposal #b2452b Span:"
  - strong: 6.00 m
  - text: "Height:"
  - strong: 3.00 m
  - text: "Joints:"
  - strong: "3"
  - text: "Members:"
  - strong: "3"
  - img: 10 kN J1 J2 J3
  - text: Existing Member Proposed Addition Proposed Deletion Support Constraint Sketch2Solve · Local review workspace Interpretation is a starting point, not a structural check.
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test'
  2   | 
  3   | test.describe('Sketch2Solve Final Polish and Verification', () => {
  4   |   test('1. Natural Language Design geometry preview accurately renders geometry, supports, loads, and CAD grid', async ({ page }) => {
  5   |     await page.goto('/?view=design')
  6   |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  7   | 
  8   |     const textarea = page.locator('.studio-left-pane .design-textarea')
  9   |     await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
  10  |     await page.locator('.studio-left-pane .btn-submit').click()
  11  | 
  12  |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  13  |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  14  | 
  15  |     // Inspect large geometry preview on the right
  16  |     const previewCanvas = page.locator('.studio-canvas-stage .cad-svg')
> 17  |     await expect(previewCanvas).toBeVisible()
      |                                 ^ Error: expect(locator).toBeVisible() failed
  18  | 
  19  |     // 1. Check straight structural lines exist
  20  |     const memberLines = previewCanvas.locator('.cad-member')
  21  |     await expect(memberLines).toHaveCount(3)
  22  | 
  23  |     // 2. Check joints and labels exist
  24  |     const joints = previewCanvas.locator('.cad-joint')
  25  |     await expect(joints).toHaveCount(3)
  26  | 
  27  |     // 3. Check pin and roller support symbols exist
  28  |     const pinSymbol = previewCanvas.locator('.cad-support.pin')
  29  |     const rollerSymbol = previewCanvas.locator('.cad-support.roller')
  30  |     await expect(pinSymbol).toBeVisible()
  31  |     await expect(rollerSymbol).toBeVisible()
  32  | 
  33  |     // 4. Check load vector arrow and magnitude label exist
  34  |     const loadArrow = previewCanvas.locator('.cad-load-arrow')
  35  |     const loadLabel = previewCanvas.locator('.cad-load-label')
  36  |     await expect(loadArrow).toBeVisible()
  37  |     await expect(loadLabel).toBeVisible()
  38  |     await expect(loadLabel).toContainText('10')
  39  | 
  40  |     // 5. Check CAD grid pattern exists
  41  |     const gridPattern = previewCanvas.locator('#cad-grid-pattern')
  42  |     await expect(gridPattern).toBeAttached()
  43  |   })
  44  | 
  45  |   test('2. Analysis History pagination footer adheres to design standards', async ({ page }) => {
  46  |     await page.goto('/?view=history')
  47  |     await expect(page.locator('.history-page')).toBeVisible({ timeout: 10_000 })
  48  | 
  49  |     // Check pagination footer exists with consistent design tokens
  50  |     const footer = page.locator('.history-pagination-footer')
  51  |     await expect(footer).toBeVisible()
  52  | 
  53  |     const paginationInfo = footer.locator('.pagination-info')
  54  |     await expect(paginationInfo).toBeVisible()
  55  |     await expect(paginationInfo).toContainText(/Showing \d+ of \d+ saved runs/)
  56  | 
  57  |     // Verify either Load More button is visible or All saved runs loaded is visible
  58  |     const hasLoadMore = await footer.locator('.btn-load-more').isVisible()
  59  |     const hasComplete = await footer.locator('.pagination-complete').isVisible()
  60  |     expect(hasLoadMore || hasComplete).toBe(true)
  61  |   })
  62  | 
  63  |   test('3. New Analysis evidence-card copy provides accurate, neutral explanation', async ({ page }) => {
  64  |     await page.goto('/?view=new')
  65  |     await expect(page.locator('.upload-card')).toBeVisible({ timeout: 10_000 })
  66  | 
  67  |     const step2 = page.locator('.workflow-step').nth(1)
  68  |     await expect(step2).toBeVisible()
  69  |     await expect(step2.locator('p')).toHaveText(
  70  |       'The selected AI provider interprets the sketch and proposes candidate joints, members, supports and loads for human review.'
  71  |     )
  72  |   })
  73  | 
  74  |   test('4. Issue Resolution Assistant is hidden by default and docks in bottom-right corner when opened', async ({ page }) => {
  75  |     // Navigate into the editor with a sample model
  76  |     await page.goto('/?view=design')
  77  |     const textarea = page.locator('.studio-left-pane .design-textarea')
  78  |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  79  |     await page.locator('.studio-left-pane .btn-submit').click()
  80  | 
  81  |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  82  |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  83  |     await proposalCard.locator('.btn-apply').click()
  84  | 
  85  |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  86  | 
  87  |     // Verify IssueResolutionAssistant card is NOT visible initially
  88  |     const assistantCard = page.locator('.contextual-action-card')
  89  |     await expect(assistantCard).not.toBeVisible()
  90  | 
  91  |     // Toggle highlight using floating canvas control
  92  |     const alertBtn = page.locator('.canvas-floating-controls button[title*="Highlight detected issues"], .canvas-floating-controls button[aria-label*="Highlight detected issues"]')
  93  |     if (await alertBtn.isVisible()) {
  94  |       await alertBtn.click()
  95  |       // Now assistant card should be visible and docked at bottom-right
  96  |       await expect(assistantCard).toBeVisible()
  97  |       const box = await assistantCard.boundingBox()
  98  |       expect(box).toBeTruthy()
  99  | 
  100 |       // Verify close/clear button closes it
  101 |       const closeBtn = assistantCard.locator('.card-close-btn')
  102 |       await closeBtn.click()
  103 |       await expect(assistantCard).not.toBeVisible()
  104 |     }
  105 |   })
  106 | 
  107 |   test('5. Right sidebar tabbed workspace cleanly toggles between Tools and Design with AI', async ({ page }) => {
  108 |     await page.goto('/?view=design')
  109 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  110 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  111 |     await page.locator('.studio-left-pane .btn-submit').click()
  112 | 
  113 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  114 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  115 |     await proposalCard.locator('.btn-apply').click()
  116 | 
  117 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
```