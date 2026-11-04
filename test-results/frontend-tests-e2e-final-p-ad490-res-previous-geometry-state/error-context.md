# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/e2e/final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 8. Model mutation and Undo support restores previous geometry state
- Location: frontend/tests/e2e/final-polish.spec.js:303:3

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/?view=design", waiting until "load"

```

# Test source

```ts
  204 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  205 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  206 |     await proposalCard.locator('.btn-apply').click()
  207 | 
  208 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  209 | 
  210 |     // Verify tabs exist in sidebar
  211 |     const tabsNav = page.locator('.sidebar-tabs-nav')
  212 |     await expect(tabsNav).toBeVisible()
  213 | 
  214 |     const toolsTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' })
  215 |     const designTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' })
  216 |     await expect(toolsTab).toBeVisible()
  217 |     await expect(designTab).toBeVisible()
  218 | 
  219 |     // Initially Tools tab is active
  220 |     await expect(toolsTab).toHaveClass(/active/)
  221 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  222 |     await expect(page.locator('.sidebar-design-pane')).not.toBeVisible()
  223 | 
  224 |     // Click Design with AI tab
  225 |     await designTab.click()
  226 |     await expect(designTab).toHaveClass(/active/)
  227 |     await expect(page.locator('.sidebar-design-pane')).toBeVisible()
  228 |     await expect(page.locator('.sidebar-tools-pane')).not.toBeVisible()
  229 | 
  230 |     // Topbar btn-ai switches back to Tools tab or toggles
  231 |     const topbarAiBtn = page.locator('.editor-topbar .btn-ai')
  232 |     await expect(topbarAiBtn).toHaveClass(/active/)
  233 |     await topbarAiBtn.click()
  234 |     await expect(toolsTab).toHaveClass(/active/)
  235 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  236 |   })
  237 | 
  238 |   test('6. Construction and Structural tools use 3-column grid with uniform 48px tile height', async ({ page }) => {
  239 |     await page.goto('/?view=design')
  240 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  241 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  242 |     await page.locator('.studio-left-pane .btn-submit').click()
  243 | 
  244 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  245 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  246 |     await proposalCard.locator('.btn-apply').click()
  247 | 
  248 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  249 | 
  250 |     // Verify 3-column grid for Construction
  251 |     const constructionGrid = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tools-grid-3')
  252 |     await expect(constructionGrid).toBeVisible()
  253 |     await expect(constructionGrid.locator('.tool-tile')).toHaveCount(3)
  254 | 
  255 |     // Verify 3-column grid for Structural
  256 |     const structuralGrid = page.locator('.toolbox-group').filter({ hasText: 'Structural' }).locator('.tools-grid-3')
  257 |     await expect(structuralGrid).toBeVisible()
  258 |     await expect(structuralGrid.locator('.tool-tile')).toHaveCount(3)
  259 | 
  260 |     // Verify 1-column grid for Edit
  261 |     const editGrid = page.locator('.toolbox-group').filter({ hasText: 'Edit' }).locator('.tools-grid-1')
  262 |     await expect(editGrid).toBeVisible()
  263 |     await expect(editGrid.locator('.tool-tile')).toHaveCount(1)
  264 | 
  265 |     // Check height of tiles
  266 |     const tile = constructionGrid.locator('.tool-tile').first()
  267 |     const box = await tile.boundingBox()
  268 |     expect(box?.height).toBeGreaterThanOrEqual(47)
  269 |   })
  270 | 
  271 |   test('7. Sequential AI proposal generation, application, and model mutation', async ({ page }) => {
  272 |     await page.goto('/?view=design')
  273 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  274 |     await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
  275 |     await page.locator('.studio-left-pane .btn-submit').click()
  276 | 
  277 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  278 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  279 |     await proposalCard.locator('.btn-apply').click()
  280 | 
  281 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  282 | 
  283 |     // Switch to Design with AI tab in the editor
  284 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  285 |     const sidebarDesignPane = page.locator('.sidebar-design-pane')
  286 |     await expect(sidebarDesignPane).toBeVisible()
  287 | 
  288 |     // Formulate sequential modification
  289 |     const promptInput = sidebarDesignPane.locator('textarea')
  290 |     await promptInput.fill('Add a vertical strut from the apex to the bottom chord')
  291 |     await sidebarDesignPane.locator('.btn-submit').click()
  292 | 
  293 |     const modProposal = sidebarDesignPane.locator('.design-proposal-card')
  294 |     await expect(modProposal).toBeVisible({ timeout: 10_000 })
  295 | 
  296 |     // Apply the proposal
  297 |     await modProposal.locator('.btn-apply').click()
  298 | 
  299 |     // Verify toast notification and success
  300 |     await expect(page.locator('.editor-toast')).toBeVisible()
  301 |   })
  302 | 
  303 |   test('8. Model mutation and Undo support restores previous geometry state', async ({ page }) => {
> 304 |     await page.goto('/?view=design')
      |                ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
  305 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  306 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  307 |     await page.locator('.studio-left-pane .btn-submit').click()
  308 | 
  309 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  310 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  311 |     await proposalCard.locator('.btn-apply').click()
  312 | 
  313 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  314 | 
  315 |     // Wait for nodes to be rendered
  316 |     await expect(page.locator('.truss-joint-node').first()).toBeVisible({ timeout: 10_000 })
  317 |     const initialJointCount = await page.locator('.truss-joint-node').count()
  318 |     expect(initialJointCount).toBeGreaterThanOrEqual(3)
  319 | 
  320 |     // Add a joint using the joint tool
  321 |     const jointTool = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tool-tile').filter({ hasText: 'Joint' })
  322 |     await jointTool.click()
  323 | 
  324 |     const canvas = page.locator('.engineering-svg')
  325 |     await canvas.click({ position: { x: 200, y: 200 } })
  326 | 
  327 |     const afterJointCount = await page.locator('.truss-joint-node').count()
  328 |     expect(afterJointCount).toBe(initialJointCount + 1)
  329 | 
  330 |     // Click Undo
  331 |     const undoBtn = page.locator('.editor-topbar button[aria-label="Undo"]')
  332 |     await undoBtn.click()
  333 | 
  334 |     const revertedJointCount = await page.locator('.truss-joint-node').count()
  335 |     expect(revertedJointCount).toBe(initialJointCount)
  336 |   })
  337 | 
  338 |   test('9. Revision conflict handling rejects stale proposals gracefully', async ({ page }) => {
  339 |     await page.goto('/?view=design')
  340 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  341 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  342 |     await page.locator('.studio-left-pane .btn-submit').click()
  343 | 
  344 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  345 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  346 |     await proposalCard.locator('.btn-apply').click()
  347 | 
  348 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  349 | 
  350 |     // Switch to Design with AI tab
  351 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  352 |     const sidebarDesignPane = page.locator('.sidebar-design-pane')
  353 | 
  354 |     const promptInput = sidebarDesignPane.locator('textarea')
  355 |     await promptInput.fill('Add a vertical strut')
  356 |     await sidebarDesignPane.locator('.btn-submit').click()
  357 | 
  358 |     const modProposal = sidebarDesignPane.locator('.design-proposal-card')
  359 |     await expect(modProposal).toBeVisible({ timeout: 10_000 })
  360 | 
  361 |     // Now modify the canvas geometry behind the proposal's back (switch to Tools and add a joint)
  362 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' }).click()
  363 |     const jointTool = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tool-tile').filter({ hasText: 'Joint' })
  364 |     await jointTool.click()
  365 |     await page.locator('.engineering-svg').click({ position: { x: 300, y: 150 } })
  366 | 
  367 |     // Switch back to Design with AI tab and attempt to apply the stale proposal
  368 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  369 |     await modProposal.locator('.btn-apply').click()
  370 | 
  371 |     // Verify conflict error message is displayed
  372 |     const errorNotice = sidebarDesignPane.locator('.error-banner')
  373 |     await expect(errorNotice).toBeVisible()
  374 |     await expect(errorNotice).toContainText(/Revision conflict|stale|modified/i)
  375 |   })
  376 | 
  377 |   test('10. Editor Design with AI interface is docked inside right sidebar with anchored composer and unobstructed canvas', async ({ page }) => {
  378 |     // Navigate directly to editor with a demo truss
  379 |     await page.goto('/?view=design')
  380 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  381 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  382 |     await page.locator('.studio-left-pane .btn-submit').click()
  383 | 
  384 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  385 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  386 |     await proposalCard.locator('.btn-apply').click()
  387 | 
  388 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  389 | 
  390 |     // Activate Design with AI from topbar button
  391 |     const topbarAiBtn = page.locator('.editor-topbar .btn-ai')
  392 |     await expect(topbarAiBtn).toBeVisible()
  393 |     await topbarAiBtn.click()
  394 | 
  395 |     // Right sidebar must now show Design with AI pane
  396 |     const sidebar = page.locator('.editor-sidebar')
  397 |     await expect(sidebar).toBeVisible()
  398 | 
  399 |     const designPane = sidebar.locator('.sidebar-design-pane')
  400 |     await expect(designPane).toBeVisible()
  401 | 
  402 |     // Verify DesignInstructionPanel is inside sidebar
  403 |     const panel = designPane.locator('.design-instruction-panel')
  404 |     await expect(panel).toBeVisible()
```