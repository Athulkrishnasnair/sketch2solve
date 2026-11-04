# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 10. Editor Design with AI interface is docked inside right sidebar with anchored composer and unobstructed canvas
- Location: tests/e2e/final-polish.spec.js:375:3

# Error details

```
Test timeout of 45000ms exceeded.
```

```
Error: locator.fill: Test timeout of 45000ms exceeded.
Call log:
  - waiting for locator('.studio-left-pane .design-textarea')
    - locator resolved to <textarea rows="2" data-v-45fdd3ed="" class="design-textarea" placeholder="Describe structural change or question (e.g. "Add a diagonal between J1 and J3", "Move J2 up 0.5m", "Why unstable?")..."></textarea>
    - fill("Create a triangular truss with 6 m span and 3 m height")
  - attempting fill action
    - waiting for element to be visible, enabled and editable

```

# Test source

```ts
  279 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
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
  307 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  308 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  309 |     await proposalCard.locator('.btn-apply').click()
  310 | 
  311 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  312 | 
  313 |     // Wait for nodes to be rendered
  314 |     await expect(page.locator('.truss-joint-node').first()).toBeVisible({ timeout: 10_000 })
  315 |     const initialJointCount = await page.locator('.truss-joint-node').count()
  316 |     expect(initialJointCount).toBeGreaterThanOrEqual(3)
  317 | 
  318 |     // Add a joint using the joint tool
  319 |     const jointTool = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tool-tile').filter({ hasText: 'Joint' })
  320 |     await jointTool.click()
  321 | 
  322 |     const canvas = page.locator('.engineering-svg')
  323 |     await canvas.click({ position: { x: 200, y: 200 } })
  324 | 
  325 |     const afterJointCount = await page.locator('.truss-joint-node').count()
  326 |     expect(afterJointCount).toBe(initialJointCount + 1)
  327 | 
  328 |     // Click Undo
  329 |     const undoBtn = page.locator('.editor-topbar button[aria-label="Undo"]')
  330 |     await undoBtn.click()
  331 | 
  332 |     const revertedJointCount = await page.locator('.truss-joint-node').count()
  333 |     expect(revertedJointCount).toBe(initialJointCount)
  334 |   })
  335 | 
  336 |   test('9. Revision conflict handling rejects stale proposals gracefully', async ({ page }) => {
  337 |     await page.goto('/?view=design')
  338 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  339 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  340 |     await page.locator('.studio-left-pane .btn-submit').click()
  341 | 
  342 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  343 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  344 |     await proposalCard.locator('.btn-apply').click()
  345 | 
  346 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  347 | 
  348 |     // Switch to Design with AI tab
  349 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  350 |     const sidebarDesignPane = page.locator('.sidebar-design-pane')
  351 | 
  352 |     const promptInput = sidebarDesignPane.locator('textarea')
  353 |     await promptInput.fill('Add a vertical strut')
  354 |     await sidebarDesignPane.locator('.btn-submit').click()
  355 | 
  356 |     const modProposal = sidebarDesignPane.locator('.design-proposal-card')
  357 |     await expect(modProposal).toBeVisible({ timeout: 10_000 })
  358 | 
  359 |     // Now modify the canvas geometry behind the proposal's back (switch to Tools and add a joint)
  360 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' }).click()
  361 |     const jointTool = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tool-tile').filter({ hasText: 'Joint' })
  362 |     await jointTool.click()
  363 |     await page.locator('.engineering-svg').click({ position: { x: 300, y: 150 } })
  364 | 
  365 |     // Switch back to Design with AI tab and attempt to apply the stale proposal
  366 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  367 |     await modProposal.locator('.btn-apply').click()
  368 | 
  369 |     // Verify conflict error message is displayed
  370 |     const errorNotice = sidebarDesignPane.locator('.error-banner')
  371 |     await expect(errorNotice).toBeVisible()
  372 |     await expect(errorNotice).toContainText(/Revision conflict|stale|modified/i)
  373 |   })
  374 | 
  375 |   test('10. Editor Design with AI interface is docked inside right sidebar with anchored composer and unobstructed canvas', async ({ page }) => {
  376 |     // Navigate directly to editor with a demo truss
  377 |     await page.goto('/?view=design')
  378 |     const textarea = page.locator('.studio-left-pane .design-textarea')
> 379 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
      |                    ^ Error: locator.fill: Test timeout of 45000ms exceeded.
  380 |     await page.locator('.studio-left-pane .btn-submit').click()
  381 | 
  382 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  383 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  384 |     await proposalCard.locator('.btn-apply').click()
  385 | 
  386 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  387 | 
  388 |     // Activate Design with AI from topbar button
  389 |     const topbarAiBtn = page.locator('.editor-topbar .btn-ai')
  390 |     await expect(topbarAiBtn).toBeVisible()
  391 |     await topbarAiBtn.click()
  392 | 
  393 |     // Right sidebar must now show Design with AI pane
  394 |     const sidebar = page.locator('.editor-sidebar')
  395 |     await expect(sidebar).toBeVisible()
  396 | 
  397 |     const designPane = sidebar.locator('.sidebar-design-pane')
  398 |     await expect(designPane).toBeVisible()
  399 | 
  400 |     // Verify DesignInstructionPanel is inside sidebar
  401 |     const panel = designPane.locator('.design-instruction-panel')
  402 |     await expect(panel).toBeVisible()
  403 | 
  404 |     // Bounding box verification: the assistant card is completely inside the sidebar column
  405 |     const sidebarBox = await sidebar.boundingBox()
  406 |     const paneBox = await designPane.boundingBox()
  407 |     expect(paneBox.x).toBeGreaterThanOrEqual(sidebarBox.x - 2)
  408 |     expect(paneBox.x + paneBox.width).toBeLessThanOrEqual(sidebarBox.x + sidebarBox.width + 2)
  409 | 
  410 |     // Canvas must remain unobstructed
  411 |     const canvas = page.locator('.engineering-svg')
  412 |     const canvasBox = await canvas.boundingBox()
  413 |     // Pane X should be strictly to the right of the canvas right edge
  414 |     expect(paneBox.x).toBeGreaterThanOrEqual(canvasBox.x + canvasBox.width - 2)
  415 | 
  416 |     // Input container is anchored at bottom of sidebar pane
  417 |     const inputContainer = designPane.locator('.input-container')
  418 |     await expect(inputContainer).toBeVisible()
  419 |     const inputPrompt = inputContainer.locator('.design-textarea')
  420 |     await expect(inputPrompt).toBeVisible()
  421 |     const generateBtn = inputContainer.locator('.btn-submit')
  422 |     await expect(generateBtn).toBeVisible()
  423 | 
  424 |     const inputBox = await inputContainer.boundingBox()
  425 |     // Bottom of input container should be close to bottom of design pane
  426 |     expect(paneBox.y + paneBox.height - (inputBox.y + inputBox.height)).toBeLessThan(30)
  427 | 
  428 |     // Verify typing prompt and switching tabs preserves prompt state
  429 |     await inputPrompt.fill('Add a diagonal strut between J1 and J3')
  430 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' }).click()
  431 |     await expect(designPane).toBeHidden()
  432 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  433 | 
  434 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  435 |     await expect(designPane).toBeVisible()
  436 |     await expect(inputPrompt).toHaveValue('Add a diagonal strut between J1 and J3')
  437 |   })
  438 | 
  439 |   test('11. Editor viewport layout eliminates document-level scrollbars at 1920x1080 and 1366x768', async ({ page }) => {
  440 |     // Test desktop 1920x1080
  441 |     await page.setViewportSize({ width: 1920, height: 1080 })
  442 |     await page.goto('/?view=design')
  443 | 
  444 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  445 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  446 |     await page.locator('.studio-left-pane .btn-submit').click()
  447 | 
  448 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  449 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  450 |     await proposalCard.locator('.btn-apply').click()
  451 | 
  452 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  453 | 
  454 |     // Verify 0 document/body scrollbars on 1920x1080
  455 |     const scrollInfo1080 = await page.evaluate(() => ({
  456 |       scrollX: window.scrollX,
  457 |       scrollY: window.scrollY,
  458 |       htmlScrollHeight: document.documentElement.scrollHeight,
  459 |       htmlClientHeight: document.documentElement.clientHeight,
  460 |       bodyScrollHeight: document.body.scrollHeight,
  461 |       bodyClientHeight: document.body.clientHeight,
  462 |       windowHeight: window.innerHeight,
  463 |       windowWidth: window.innerWidth,
  464 |     }))
  465 | 
  466 |     expect(scrollInfo1080.scrollY).toBe(0)
  467 |     expect(scrollInfo1080.scrollX).toBe(0)
  468 |     expect(scrollInfo1080.htmlScrollHeight).toBeLessThanOrEqual(scrollInfo1080.windowHeight)
  469 |     expect(scrollInfo1080.bodyScrollHeight).toBeLessThanOrEqual(scrollInfo1080.windowHeight)
  470 | 
  471 |     // Test desktop 1366x768
  472 |     await page.setViewportSize({ width: 1366, height: 768 })
  473 |     await page.waitForTimeout(300)
  474 | 
  475 |     const scrollInfo768 = await page.evaluate(() => ({
  476 |       scrollX: window.scrollX,
  477 |       scrollY: window.scrollY,
  478 |       htmlScrollHeight: document.documentElement.scrollHeight,
  479 |       htmlClientHeight: document.documentElement.clientHeight,
```