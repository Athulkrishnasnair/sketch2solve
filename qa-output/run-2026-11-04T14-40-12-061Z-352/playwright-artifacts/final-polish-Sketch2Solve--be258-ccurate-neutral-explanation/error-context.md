# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 3. New Analysis evidence-card copy provides accurate, neutral explanation
- Location: tests/e2e/final-polish.spec.js:63:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.new-analysis-page')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.new-analysis-page') with timeout 10000ms
  - waiting for locator('.new-analysis-page')

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
  - strong: New analysis
  - text: LOCAL ONLY SKETCH INTERPRETATION
  - heading "Review a structure, before you solve it." [level=1]:
    - text: Review a structure,
    - emphasis: before
    - text: you solve it.
  - paragraph: Compare computer vision evidence with a model interpretation. Each proposal requires a human review before it can reach the solver.
  - text: 01 / INTAKE STEP 1
  - heading "Add a sketch" [level=2]
  - text: MAX 10 MiB
  - button "Choose File"
  - button "Drop your sketch here or browse files on your device JPEG, PNG or WebP":
    - strong: Drop your sketch here
    - text: or browse files on your device JPEG, PNG or WebP
  - text: Interpretation provider
  - combobox "Interpretation provider":
    - option "Gemini · Flash-Lite" [selected]
    - option "Meta · Muse Spark"
  - button "Start analysis" [disabled]
  - paragraph: Provider credentials stay on the backend.
  - text: A CONTROLLED WORKFLOW
  - heading "Evidence stays distinct" [level=2]
  - text: ⌁ 01
  - strong: Visual evidence
  - paragraph: OpenCV reports candidate lines and endpoint clusters. These are not verified truss members.
  - text: VISION 02
  - strong: AI interpretation
  - paragraph: The selected AI provider interprets the sketch and proposes candidate joints, members, supports and loads for human review.
  - text: GEMINI 03
  - strong: Human review
  - paragraph: Correct a separate draft, check its units, then explicitly mark it reviewed before solver submission.
  - text: REVIEW i
  - paragraph: Nothing is solved automatically from the AI proposal. Solver output describes only the geometry you explicitly reviewed and submitted.
  - text: Sketch2Solve · Local review workspace Interpretation is a starting point, not a structural check.
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
  16  |     const previewCanvas = page.locator('.studio-canvas-stage .large-preview-svg')
  17  |     await expect(previewCanvas).toBeVisible()
  18  | 
  19  |     // 1. Check straight structural lines exist
  20  |     const memberLines = previewCanvas.locator('.truss-member-line')
  21  |     await expect(memberLines).toHaveCount(3)
  22  | 
  23  |     // 2. Check joints and labels exist
  24  |     const joints = previewCanvas.locator('.truss-joint-node')
  25  |     await expect(joints).toHaveCount(3)
  26  | 
  27  |     // 3. Check pin and roller support symbols exist
  28  |     const pinSymbol = previewCanvas.locator('.support-pin')
  29  |     const rollerSymbol = previewCanvas.locator('.support-roller')
  30  |     await expect(pinSymbol).toBeVisible()
  31  |     await expect(rollerSymbol).toBeVisible()
  32  | 
  33  |     // 4. Check load vector arrow and magnitude label exist
  34  |     const loadArrow = previewCanvas.locator('.load-vector-arrow')
  35  |     const loadLabel = previewCanvas.locator('.load-label')
  36  |     await expect(loadArrow).toBeVisible()
  37  |     await expect(loadLabel).toBeVisible()
  38  |     await expect(loadLabel).toContainText('10')
  39  | 
  40  |     // 5. Check CAD grid pattern exists
  41  |     const gridPattern = previewCanvas.locator('#cad-grid')
  42  |     await expect(gridPattern).toBeAttached()
  43  |   })
  44  | 
  45  |   test('2. Analysis History pagination footer adheres to design standards', async ({ page }) => {
  46  |     await page.goto('/?view=history')
  47  |     await expect(page.locator('.analysis-history-page')).toBeVisible({ timeout: 10_000 })
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
> 65  |     await expect(page.locator('.new-analysis-page')).toBeVisible({ timeout: 10_000 })
      |                                                      ^ Error: expect(locator).toBeVisible() failed
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
  118 | 
  119 |     // Verify tabs exist in sidebar
  120 |     const tabsNav = page.locator('.sidebar-tabs-nav')
  121 |     await expect(tabsNav).toBeVisible()
  122 | 
  123 |     const toolsTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' })
  124 |     const designTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' })
  125 |     await expect(toolsTab).toBeVisible()
  126 |     await expect(designTab).toBeVisible()
  127 | 
  128 |     // Initially Tools tab is active
  129 |     await expect(toolsTab).toHaveClass(/active/)
  130 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  131 |     await expect(page.locator('.sidebar-design-pane')).not.toBeVisible()
  132 | 
  133 |     // Click Design with AI tab
  134 |     await designTab.click()
  135 |     await expect(designTab).toHaveClass(/active/)
  136 |     await expect(page.locator('.sidebar-design-pane')).toBeVisible()
  137 |     await expect(page.locator('.sidebar-tools-pane')).not.toBeVisible()
  138 | 
  139 |     // Topbar btn-ai switches back to Tools tab or toggles
  140 |     const topbarAiBtn = page.locator('.editor-topbar .btn-ai')
  141 |     await expect(topbarAiBtn).toHaveClass(/active/)
  142 |     await topbarAiBtn.click()
  143 |     await expect(toolsTab).toHaveClass(/active/)
  144 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  145 |   })
  146 | 
  147 |   test('6. Construction and Structural tools use 3-column grid with uniform 48px tile height', async ({ page }) => {
  148 |     await page.goto('/?view=design')
  149 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  150 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  151 |     await page.locator('.studio-left-pane .btn-submit').click()
  152 | 
  153 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  154 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  155 |     await proposalCard.locator('.btn-apply').click()
  156 | 
  157 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  158 | 
  159 |     // Verify 3-column grid for Construction
  160 |     const constructionGrid = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tools-grid-3')
  161 |     await expect(constructionGrid).toBeVisible()
  162 |     await expect(constructionGrid.locator('.tool-tile')).toHaveCount(3)
  163 | 
  164 |     // Verify 3-column grid for Structural
  165 |     const structuralGrid = page.locator('.toolbox-group').filter({ hasText: 'Structural' }).locator('.tools-grid-3')
```