# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 5. Right sidebar tabbed workspace cleanly toggles between Tools and Design with AI
- Location: tests/e2e/final-polish.spec.js:196:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.truss-editor-workspace')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.truss-editor-workspace') with timeout 10000ms
  - waiting for locator('.truss-editor-workspace')

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
  - combobox "Target Structure:" [disabled]:
    - option "＋ New Truss Design (Blank Canvas)"
    - option "Triangular Truss (pending_review)"
    - option "Triangular Truss (pending_review)"
    - option "Triangular Truss (solved)"
    - option "Triangular Truss (pending_review)"
    - option "unloaded_triangle.png (solved)"
    - option "reference_triangle.png (solved)"
    - option "card_scroll_test.jpg (pending_review)"
    - option "canvas_repair.jpg (pending_review)"
    - option "missing-image.png (pending_review)"
    - option "validation.png (failed)"
    - option "workflow.png (solved)"
    - option "empty-proposal.png (pending_review)"
    - option "INVALID_GEMINI_RESPONSE.png (failed)"
    - option "GEMINI_NETWORK_ERROR.png (failed)"
    - option "GEMINI_TIMEOUT.png (failed)"
    - option "GEMINI_RATE_LIMITED.png (failed)"
    - option "GEMINI_AUTHENTICATION_FAILED.png (failed)"
    - option "MISSING_GEMINI_API_KEY.png (failed)"
    - 'option "Analysis #9d7e733f (failed)"'
    - 'option "Analysis #1d55d320 (failed)"'
  - button "Open in Editor"
  - text: Design proposal applied and new analysis created successfully. Rev 1
  - radiogroup "Design Intent":
    - button "Auto"
    - button "Create"
    - button "Modify"
    - button "Explain"
  - textbox "Describe structural change or question (e.g. \"Add a diagonal between J1 and J3\", \"Move J2 up 0.5m\", \"Why unstable?\")..." [disabled]: Create a triangular truss with 6 m span and 3 m height
  - text: Enter ↵ to submit · Shift+Enter for newline
  - button "Analyzing..." [disabled]
  - button "Add a diagonal between J1 and J3" [disabled]
  - button "Move J2 up by 0.5 m" [disabled]
  - button "Add 10 kN downward load at top" [disabled]
  - button "Why is this structure unstable?" [disabled]
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
  - text: "Span:"
  - strong: 6.00 m
  - text: "Height:"
  - strong: 3.00 m
  - text: "Joints:"
  - strong: "3"
  - text: "Members:"
  - strong: "3"
  - text: Loading structural geometry… Existing Member Proposed Addition Proposed Deletion Support Constraint Sketch2Solve · Local review workspace Interpretation is a starting point, not a structural check.
```

# Test source

```ts
  106 |     // 8. Test different container aspect ratios (wide 1600x900 and narrow 800x700)
  107 |     await page.setViewportSize({ width: 1600, height: 900 })
  108 |     await page.waitForTimeout(300)
  109 |     let canvasBox = await previewCanvas.boundingBox()
  110 |     expect(canvasBox.width).toBeGreaterThan(600)
  111 | 
  112 |     await page.setViewportSize({ width: 850, height: 700 })
  113 |     await page.waitForTimeout(300)
  114 |     canvasBox = await previewCanvas.boundingBox()
  115 |     expect(canvasBox.width).toBeGreaterThan(400)
  116 | 
  117 |     // Restore standard viewport
  118 |     await page.setViewportSize({ width: 1280, height: 800 })
  119 |   })
  120 | 
  121 |   test('2. Analysis History pagination footer adheres to design standards', async ({ page }) => {
  122 |     // 1. Ensure a record exists by creating one via Design Studio first
  123 |     await page.goto('/?view=design')
  124 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  125 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  126 |     await page.locator('.studio-left-pane .btn-submit').click()
  127 | 
  128 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  129 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  130 |     await proposalCard.locator('.btn-apply').click()
  131 | 
  132 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  133 | 
  134 |     // 2. Now navigate to History page
  135 |     await page.goto('/?view=history')
  136 |     await expect(page.locator('.history-page')).toBeVisible({ timeout: 10_000 })
  137 | 
  138 |     // Check pagination footer exists with consistent design tokens
  139 |     const footer = page.locator('.history-pagination-footer')
  140 |     await expect(footer).toBeVisible()
  141 | 
  142 |     const paginationInfo = footer.locator('.pagination-info')
  143 |     await expect(paginationInfo).toBeVisible()
  144 |     await expect(paginationInfo).toContainText(/Showing \d+ of \d+ saved runs/)
  145 | 
  146 |     // Verify either Load More button is visible or All saved runs loaded is visible
  147 |     const hasLoadMore = await footer.locator('.btn-load-more').isVisible()
  148 |     const hasComplete = await footer.locator('.pagination-complete').isVisible()
  149 |     expect(hasLoadMore || hasComplete).toBe(true)
  150 |   })
  151 | 
  152 |   test('3. New Analysis evidence-card copy provides accurate, neutral explanation', async ({ page }) => {
  153 |     await page.goto('/?view=new')
  154 |     await expect(page.locator('.upload-card')).toBeVisible({ timeout: 10_000 })
  155 | 
  156 |     const step2 = page.locator('.workflow-step').nth(1)
  157 |     await expect(step2).toBeVisible()
  158 |     await expect(step2.locator('p')).toHaveText(
  159 |       'The selected AI provider interprets the sketch and proposes candidate joints, members, supports and loads for human review.'
  160 |     )
  161 |   })
  162 | 
  163 |   test('4. Issue Resolution Assistant docks in bottom-right corner and closes when highlighting is cleared', async ({ page }) => {
  164 |     // Navigate into the editor with a sample model
  165 |     await page.goto('/?view=design')
  166 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  167 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  168 |     await page.locator('.studio-left-pane .btn-submit').click()
  169 | 
  170 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  171 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  172 |     await proposalCard.locator('.btn-apply').click()
  173 | 
  174 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  175 | 
  176 |     // Assistant card is docked at bottom-right
  177 |     const assistantCard = page.locator('.contextual-action-card')
  178 |     if (await assistantCard.isVisible()) {
  179 |       const box = await assistantCard.boundingBox()
  180 |       expect(box).toBeTruthy()
  181 | 
  182 |       // Verify close/clear button closes it
  183 |       const closeBtn = assistantCard.locator('.card-close-btn')
  184 |       await closeBtn.click()
  185 |       await expect(assistantCard).not.toBeVisible()
  186 | 
  187 |       // Toggle highlight using floating canvas control re-opens it
  188 |       const alertBtn = page.locator('.canvas-floating-controls button[title*="Highlight detected issues"], .canvas-floating-controls button[aria-label*="Highlight detected issues"]')
  189 |       if (await alertBtn.isVisible()) {
  190 |         await alertBtn.click()
  191 |         await expect(assistantCard).toBeVisible()
  192 |       }
  193 |     }
  194 |   })
  195 | 
  196 |   test('5. Right sidebar tabbed workspace cleanly toggles between Tools and Design with AI', async ({ page }) => {
  197 |     await page.goto('/?view=design')
  198 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  199 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  200 |     await page.locator('.studio-left-pane .btn-submit').click()
  201 | 
  202 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  203 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  204 |     await proposalCard.locator('.btn-apply').click()
  205 | 
> 206 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
      |                                                           ^ Error: expect(locator).toBeVisible() failed
  207 | 
  208 |     // Verify tabs exist in sidebar
  209 |     const tabsNav = page.locator('.sidebar-tabs-nav')
  210 |     await expect(tabsNav).toBeVisible()
  211 | 
  212 |     const toolsTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' })
  213 |     const designTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' })
  214 |     await expect(toolsTab).toBeVisible()
  215 |     await expect(designTab).toBeVisible()
  216 | 
  217 |     // Initially Tools tab is active
  218 |     await expect(toolsTab).toHaveClass(/active/)
  219 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  220 |     await expect(page.locator('.sidebar-design-pane')).not.toBeVisible()
  221 | 
  222 |     // Click Design with AI tab
  223 |     await designTab.click()
  224 |     await expect(designTab).toHaveClass(/active/)
  225 |     await expect(page.locator('.sidebar-design-pane')).toBeVisible()
  226 |     await expect(page.locator('.sidebar-tools-pane')).not.toBeVisible()
  227 | 
  228 |     // Topbar btn-ai switches back to Tools tab or toggles
  229 |     const topbarAiBtn = page.locator('.editor-topbar .btn-ai')
  230 |     await expect(topbarAiBtn).toHaveClass(/active/)
  231 |     await topbarAiBtn.click()
  232 |     await expect(toolsTab).toHaveClass(/active/)
  233 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  234 |   })
  235 | 
  236 |   test('6. Construction and Structural tools use 3-column grid with uniform 48px tile height', async ({ page }) => {
  237 |     await page.goto('/?view=design')
  238 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  239 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  240 |     await page.locator('.studio-left-pane .btn-submit').click()
  241 | 
  242 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  243 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  244 |     await proposalCard.locator('.btn-apply').click()
  245 | 
  246 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  247 | 
  248 |     // Verify 3-column grid for Construction
  249 |     const constructionGrid = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tools-grid-3')
  250 |     await expect(constructionGrid).toBeVisible()
  251 |     await expect(constructionGrid.locator('.tool-tile')).toHaveCount(3)
  252 | 
  253 |     // Verify 3-column grid for Structural
  254 |     const structuralGrid = page.locator('.toolbox-group').filter({ hasText: 'Structural' }).locator('.tools-grid-3')
  255 |     await expect(structuralGrid).toBeVisible()
  256 |     await expect(structuralGrid.locator('.tool-tile')).toHaveCount(3)
  257 | 
  258 |     // Verify 1-column grid for Edit
  259 |     const editGrid = page.locator('.toolbox-group').filter({ hasText: 'Edit' }).locator('.tools-grid-1')
  260 |     await expect(editGrid).toBeVisible()
  261 |     await expect(editGrid.locator('.tool-tile')).toHaveCount(1)
  262 | 
  263 |     // Check height of tiles
  264 |     const tile = constructionGrid.locator('.tool-tile').first()
  265 |     const box = await tile.boundingBox()
  266 |     expect(box?.height).toBeGreaterThanOrEqual(47)
  267 |   })
  268 | 
  269 |   test('7. Sequential AI proposal generation, application, and model mutation', async ({ page }) => {
  270 |     await page.goto('/?view=design')
  271 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  272 |     await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
  273 |     await page.locator('.studio-left-pane .btn-submit').click()
  274 | 
  275 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  276 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  277 |     await proposalCard.locator('.btn-apply').click()
  278 | 
  279 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  280 | 
  281 |     // Switch to Design with AI tab in the editor
  282 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  283 |     const sidebarDesignPane = page.locator('.sidebar-design-pane')
  284 |     await expect(sidebarDesignPane).toBeVisible()
  285 | 
  286 |     // Formulate sequential modification
  287 |     const promptInput = sidebarDesignPane.locator('textarea')
  288 |     await promptInput.fill('Add a vertical strut from the apex to the bottom chord')
  289 |     await sidebarDesignPane.locator('.btn-submit').click()
  290 | 
  291 |     const modProposal = sidebarDesignPane.locator('.design-proposal-card')
  292 |     await expect(modProposal).toBeVisible({ timeout: 10_000 })
  293 | 
  294 |     // Apply the proposal
  295 |     await modProposal.locator('.btn-apply').click()
  296 | 
  297 |     // Verify toast notification and success
  298 |     await expect(page.locator('.editor-toast')).toBeVisible()
  299 |   })
  300 | 
  301 |   test('8. Model mutation and Undo support restores previous geometry state', async ({ page }) => {
  302 |     await page.goto('/?view=design')
  303 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  304 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  305 |     await page.locator('.studio-left-pane .btn-submit').click()
  306 | 
```