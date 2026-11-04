# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 12. Minimal Save & Export MVP: Natural Language Design pathway (create -> correct -> save draft -> reopen from history -> solve -> download PNG, JSON, CSV -> stale guard)
- Location: tests/e2e/final-polish.spec.js:499:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.analysis-detail-page')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.analysis-detail-page') with timeout 10000ms
  - waiting for locator('.analysis-detail-page')

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
    - button "Analysis history 1"
  - strong: Private by default
  - paragraph: Runs stay in your local backend. Don’t expose this workspace publicly.
  - text: Backend API · localhost:5000
- main:
  - text: Workspace /
  - strong: Analysis review
  - text: LOCAL ONLY
  - button "← Analysis history"
  - text: "ANALYSIS #857BB6D3 ANALYSIS REVIEW"
  - heading "Triangular Truss" [level=1]
  - text: Nov 4, 2026, 5:19 PM No source image conversational_ai ·
  - button "Edit geometry":
    - img
    - text: Edit geometry
  - text: Pending review MODEL OUTPUT
  - heading "Interpretation proposal" [level=2]
  - text: CANDIDATE ONLY
  - strong: "0"
  - text: Joints
  - strong: "0"
  - text: Members
  - strong: "0"
  - text: Supports
  - strong: "0"
  - text: Loads
  - group: Inspect proposed elements
  - text: No ambiguities were returned. This does not confirm the geometry is correct. CHECKS & DIAGNOSTICS
  - heading "Validation state" [level=2]
  - text: valid No validation issues were saved. i
  - strong: Engineering review boundary
  - paragraph: Model validation checks the request schema and references; solver diagnostics are numerical checks. Neither establishes physical stability, code compliance, or engineering suitability. Review all dimensions and loads.
  - text: Draft saved Sketch2Solve · Local review workspace Interpretation is a starting point, not a structural check.
```

# Test source

```ts
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
  480 |       bodyScrollHeight: document.body.scrollHeight,
  481 |       bodyClientHeight: document.body.clientHeight,
  482 |       windowHeight: window.innerHeight,
  483 |       windowWidth: window.innerWidth,
  484 |     }))
  485 | 
  486 |     expect(scrollInfo768.scrollY).toBe(0)
  487 |     expect(scrollInfo768.scrollX).toBe(0)
  488 |     expect(scrollInfo768.htmlScrollHeight).toBeLessThanOrEqual(scrollInfo768.windowHeight)
  489 |     expect(scrollInfo768.bodyScrollHeight).toBeLessThanOrEqual(scrollInfo768.windowHeight)
  490 | 
  491 |     // Key elements must all be visible within the 1366x768 viewport
  492 |     await expect(page.locator('.sidebar')).toBeVisible()
  493 |     await expect(page.locator('.editor-topbar')).toBeVisible()
  494 |     await expect(page.locator('.canvas-container')).toBeVisible()
  495 |     await expect(page.locator('.editor-sidebar')).toBeVisible()
  496 |     await expect(page.locator('.editor-statusbar')).toBeVisible()
  497 |   })
  498 | 
  499 |   test('12. Minimal Save & Export MVP: Natural Language Design pathway (create -> correct -> save draft -> reopen from history -> solve -> download PNG, JSON, CSV -> stale guard)', async ({ page }) => {
  500 |     // 1. Create via NL Design
  501 |     await page.goto('/?view=design')
  502 |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  503 | 
  504 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  505 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
  506 |     await page.locator('.studio-left-pane .btn-submit').click()
  507 | 
  508 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  509 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  510 |     await proposalCard.locator('.btn-apply').click()
  511 | 
  512 |     // 2. Lands in Editor
  513 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  514 | 
  515 |     // 3. Confirm coordinates and save draft
  516 |     const confirmCheckbox = page.locator('.confirm-checkbox input')
  517 |     await confirmCheckbox.check()
  518 |     await expect(confirmCheckbox).toBeChecked()
  519 | 
  520 |     const saveBtn = page.locator('.editor-topbar .btn-save')
  521 |     await saveBtn.click()
  522 |     await expect(page.locator('.editor-topbar .btn-save')).toContainText('Saved', { timeout: 10_000 })
  523 | 
  524 |     // 4. Reopen saved model from Analysis History
  525 |     await page.goto('/?view=history')
  526 |     await expect(page.locator('.history-list')).toBeVisible({ timeout: 10_000 })
  527 |     const topRow = page.locator('.history-row').first()
  528 |     await expect(topRow).toBeVisible()
  529 |     await topRow.click()
  530 | 
  531 |     // Lands on detail page
> 532 |     await expect(page.locator('.analysis-detail-page')).toBeVisible({ timeout: 10_000 })
      |                                                         ^ Error: expect(locator).toBeVisible() failed
  533 |     const editBtn = page.getByRole('button', { name: 'Edit geometry' })
  534 |     await expect(editBtn).toBeVisible()
  535 |     await editBtn.click()
  536 | 
  537 |     // Reopened in Truss Editor
  538 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  539 | 
  540 |     // 5. Mark Reviewed and Solve
  541 |     const reviewBtn = page.locator('.editor-topbar .btn-review')
  542 |     await reviewBtn.click()
  543 |     await expect(page.locator('.editor-topbar .btn-solve')).toBeEnabled({ timeout: 10_000 })
  544 | 
  545 |     const solveBtn = page.locator('.editor-topbar .btn-solve')
  546 |     await solveBtn.click()
  547 | 
  548 |     // 6. Results Panel appears with SOLVED status
  549 |     const resultsPanel = page.locator('.analysis-results-panel')
  550 |     await expect(resultsPanel).toBeVisible({ timeout: 15_000 })
  551 |     await expect(resultsPanel.locator('.badge-solved')).toBeVisible()
  552 | 
  553 |     // 7. Test Export Menu & Downloads
  554 |     const exportBtn = resultsPanel.locator('.btn-export')
  555 |     await expect(exportBtn).toBeVisible()
  556 |     await exportBtn.click()
  557 | 
  558 |     const exportMenu = resultsPanel.locator('.export-menu')
  559 |     await expect(exportMenu).toBeVisible()
  560 | 
  561 |     // PNG Download
  562 |     const [pngDownload] = await Promise.all([
  563 |       page.waitForEvent('download'),
  564 |       exportMenu.locator('.export-menu-item:has-text("PNG Diagram")').click(),
  565 |     ])
  566 |     expect(pngDownload.suggestedFilename()).toMatch(/\.png$/)
  567 | 
  568 |     // Reopen menu for JSON
  569 |     await exportBtn.click()
  570 |     await expect(exportMenu).toBeVisible()
  571 | 
  572 |     // JSON Download
  573 |     const [jsonDownload] = await Promise.all([
  574 |       page.waitForEvent('download'),
  575 |       exportMenu.locator('.export-menu-item:has-text("JSON Model")').click(),
  576 |     ])
  577 |     expect(jsonDownload.suggestedFilename()).toMatch(/\.json$/)
  578 | 
  579 |     // Reopen menu for CSV
  580 |     await exportBtn.click()
  581 |     await expect(exportMenu).toBeVisible()
  582 | 
  583 |     // CSV Download
  584 |     const [csvDownload] = await Promise.all([
  585 |       page.waitForEvent('download'),
  586 |       exportMenu.locator('.export-menu-item:has-text("CSV Results")').click(),
  587 |     ])
  588 |     expect(csvDownload.suggestedFilename()).toMatch(/\.csv$/)
  589 | 
  590 |     // 8. Stale Results Protection
  591 |     // Select a joint and move it slightly to invalidate results
  592 |     const jointJ2 = page.locator('.truss-canvas .joint-circle').nth(1)
  593 |     const bbox = await jointJ2.boundingBox()
  594 |     if (bbox) {
  595 |       await page.mouse.move(bbox.x + bbox.width / 2, bbox.y + bbox.height / 2)
  596 |       await page.mouse.down()
  597 |       await page.mouse.move(bbox.x + bbox.width / 2 + 30, bbox.y + bbox.height / 2)
  598 |       await page.mouse.up()
  599 |     }
  600 | 
  601 |     // Results panel must now indicate STALE
  602 |     await expect(resultsPanel.locator('.badge-stale')).toBeVisible({ timeout: 10_000 })
  603 | 
  604 |     // Open export menu: CSV option must be disabled and tagged stale
  605 |     await exportBtn.click()
  606 |     await expect(exportMenu).toBeVisible()
  607 |     const csvItem = exportMenu.locator('.export-menu-item:has-text("CSV Results")')
  608 |     await expect(csvItem).toBeDisabled()
  609 |     await expect(csvItem.locator('.export-badge-tag.tag-stale')).toBeVisible()
  610 | 
  611 |     // Save draft again (reopen in place without duplicate records)
  612 |     await saveBtn.click()
  613 |     await expect(page.locator('.editor-topbar .btn-save')).toContainText('Saved', { timeout: 10_000 })
  614 |   })
  615 | 
  616 |   test('13. Minimal Save & Export MVP: Direct export endpoints and JSON draft persistence', async ({ page }) => {
  617 |     // Verify direct API export behavior
  618 |     await page.goto('/?view=design')
  619 |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  620 | 
  621 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  622 |     await textarea.fill('Create a triangular truss with 4 m span and 2 m height')
  623 |     await page.locator('.studio-left-pane .btn-submit').click()
  624 | 
  625 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  626 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  627 |     await proposalCard.locator('.btn-apply').click()
  628 | 
  629 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  630 |     const confirmCheckbox = page.locator('.confirm-checkbox input')
  631 |     await confirmCheckbox.check()
  632 |     await page.locator('.editor-topbar .btn-save').click()
```