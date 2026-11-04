# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/e2e/final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 11. Editor viewport layout eliminates document-level scrollbars at 1920x1080 and 1366x768
- Location: frontend/tests/e2e/final-polish.spec.js:441:3

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/?view=design", waiting until "load"

```

# Test source

```ts
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
  405 | 
  406 |     // Bounding box verification: the assistant card is completely inside the sidebar column
  407 |     const sidebarBox = await sidebar.boundingBox()
  408 |     const paneBox = await designPane.boundingBox()
  409 |     expect(paneBox.x).toBeGreaterThanOrEqual(sidebarBox.x - 2)
  410 |     expect(paneBox.x + paneBox.width).toBeLessThanOrEqual(sidebarBox.x + sidebarBox.width + 2)
  411 | 
  412 |     // Canvas must remain unobstructed
  413 |     const canvas = page.locator('.engineering-svg')
  414 |     const canvasBox = await canvas.boundingBox()
  415 |     // Pane X should be strictly to the right of the canvas right edge
  416 |     expect(paneBox.x).toBeGreaterThanOrEqual(canvasBox.x + canvasBox.width - 2)
  417 | 
  418 |     // Input container is anchored at bottom of sidebar pane
  419 |     const inputContainer = designPane.locator('.input-container')
  420 |     await expect(inputContainer).toBeVisible()
  421 |     const inputPrompt = inputContainer.locator('.design-textarea')
  422 |     await expect(inputPrompt).toBeVisible()
  423 |     const generateBtn = inputContainer.locator('.btn-submit')
  424 |     await expect(generateBtn).toBeVisible()
  425 | 
  426 |     const inputBox = await inputContainer.boundingBox()
  427 |     // Bottom of input container should be close to bottom of design pane
  428 |     expect(paneBox.y + paneBox.height - (inputBox.y + inputBox.height)).toBeLessThan(30)
  429 | 
  430 |     // Verify typing prompt and switching tabs preserves prompt state
  431 |     await inputPrompt.fill('Add a diagonal strut between J1 and J3')
  432 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' }).click()
  433 |     await expect(designPane).toBeHidden()
  434 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  435 | 
  436 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  437 |     await expect(designPane).toBeVisible()
  438 |     await expect(inputPrompt).toHaveValue('Add a diagonal strut between J1 and J3')
  439 |   })
  440 | 
  441 |   test('11. Editor viewport layout eliminates document-level scrollbars at 1920x1080 and 1366x768', async ({ page }) => {
  442 |     // Test desktop 1920x1080
  443 |     await page.setViewportSize({ width: 1920, height: 1080 })
> 444 |     await page.goto('/?view=design')
      |                ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
  445 | 
  446 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  447 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  448 |     await page.locator('.studio-left-pane .btn-submit').click()
  449 | 
  450 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  451 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  452 |     await proposalCard.locator('.btn-apply').click()
  453 | 
  454 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  455 | 
  456 |     // Verify 0 document/body scrollbars on 1920x1080
  457 |     const scrollInfo1080 = await page.evaluate(() => ({
  458 |       scrollX: window.scrollX,
  459 |       scrollY: window.scrollY,
  460 |       htmlScrollHeight: document.documentElement.scrollHeight,
  461 |       htmlClientHeight: document.documentElement.clientHeight,
  462 |       bodyScrollHeight: document.body.scrollHeight,
  463 |       bodyClientHeight: document.body.clientHeight,
  464 |       windowHeight: window.innerHeight,
  465 |       windowWidth: window.innerWidth,
  466 |     }))
  467 | 
  468 |     expect(scrollInfo1080.scrollY).toBe(0)
  469 |     expect(scrollInfo1080.scrollX).toBe(0)
  470 |     expect(scrollInfo1080.htmlScrollHeight).toBeLessThanOrEqual(scrollInfo1080.windowHeight)
  471 |     expect(scrollInfo1080.bodyScrollHeight).toBeLessThanOrEqual(scrollInfo1080.windowHeight)
  472 | 
  473 |     // Test desktop 1366x768
  474 |     await page.setViewportSize({ width: 1366, height: 768 })
  475 |     await page.waitForTimeout(300)
  476 | 
  477 |     const scrollInfo768 = await page.evaluate(() => ({
  478 |       scrollX: window.scrollX,
  479 |       scrollY: window.scrollY,
  480 |       htmlScrollHeight: document.documentElement.scrollHeight,
  481 |       htmlClientHeight: document.documentElement.clientHeight,
  482 |       bodyScrollHeight: document.body.scrollHeight,
  483 |       bodyClientHeight: document.body.clientHeight,
  484 |       windowHeight: window.innerHeight,
  485 |       windowWidth: window.innerWidth,
  486 |     }))
  487 | 
  488 |     expect(scrollInfo768.scrollY).toBe(0)
  489 |     expect(scrollInfo768.scrollX).toBe(0)
  490 |     expect(scrollInfo768.htmlScrollHeight).toBeLessThanOrEqual(scrollInfo768.windowHeight)
  491 |     expect(scrollInfo768.bodyScrollHeight).toBeLessThanOrEqual(scrollInfo768.windowHeight)
  492 | 
  493 |     // Key elements must all be visible within the 1366x768 viewport
  494 |     await expect(page.locator('.sidebar')).toBeVisible()
  495 |     await expect(page.locator('.editor-topbar')).toBeVisible()
  496 |     await expect(page.locator('.canvas-container')).toBeVisible()
  497 |     await expect(page.locator('.editor-sidebar')).toBeVisible()
  498 |     await expect(page.locator('.editor-statusbar')).toBeVisible()
  499 |   })
  500 | 
  501 |   test('12. Minimal Save & Export MVP: Natural Language Design pathway (create -> correct -> save draft -> reopen from history -> solve -> download PNG, JSON, CSV -> stale guard)', async ({ page }) => {
  502 |     // 1. Create via NL Design
  503 |     await page.goto('/?view=design')
  504 |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  505 | 
  506 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  507 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
  508 |     await page.locator('.studio-left-pane .btn-submit').click()
  509 | 
  510 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  511 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  512 |     await proposalCard.locator('.btn-apply').click()
  513 | 
  514 |     // 2. Lands in Editor
  515 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  516 | 
  517 |     // 3. Confirm coordinates and save draft
  518 |     const confirmCheckbox = page.locator('.confirm-checkbox input')
  519 |     await confirmCheckbox.check()
  520 |     await expect(confirmCheckbox).toBeChecked()
  521 | 
  522 |     const saveBtn = page.locator('.editor-topbar .btn-save')
  523 |     await saveBtn.click()
  524 |     await expect(page.locator('.editor-topbar .btn-save')).toContainText('Saved', { timeout: 10_000 })
  525 | 
  526 |     // 4. Reopen saved model from Analysis History
  527 |     await page.goto('/?view=history')
  528 |     await expect(page.locator('.history-list')).toBeVisible({ timeout: 10_000 })
  529 |     const topRow = page.locator('.history-row').first()
  530 |     await expect(topRow).toBeVisible()
  531 |     await topRow.click()
  532 | 
  533 |     // Lands on detail page
  534 |     await expect(page.locator('.detail-page')).toBeVisible({ timeout: 10_000 })
  535 |     const editBtn = page.getByRole('button', { name: 'Edit geometry' })
  536 |     await expect(editBtn).toBeVisible()
  537 |     await editBtn.click()
  538 | 
  539 |     // Reopened in Truss Editor
  540 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  541 | 
  542 |     // 5. Mark Reviewed and Solve
  543 |     const reviewBtn = page.locator('.editor-topbar .btn-review')
  544 |     await reviewBtn.click()
```