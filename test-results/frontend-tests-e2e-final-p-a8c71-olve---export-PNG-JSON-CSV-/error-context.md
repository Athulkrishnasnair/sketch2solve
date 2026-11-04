# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/e2e/final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 14. Minimal Save & Export MVP: Sketch upload pathway (upload -> edit geometry -> save draft -> reopen -> solve -> export PNG/JSON/CSV)
- Location: frontend/tests/e2e/final-polish.spec.js:662:3

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/?view=new", waiting until "load"

```

# Test source

```ts
  564 |     // PNG Download
  565 |     const [pngDownload] = await Promise.all([
  566 |       page.waitForEvent('download'),
  567 |       exportMenu.locator('.export-menu-item:has-text("PNG Diagram")').click(),
  568 |     ])
  569 |     expect(pngDownload.suggestedFilename()).toMatch(/\.png$/)
  570 | 
  571 |     // Reopen menu for JSON
  572 |     await exportBtn.click()
  573 |     await expect(exportMenu).toBeVisible()
  574 | 
  575 |     // JSON Download
  576 |     const [jsonDownload] = await Promise.all([
  577 |       page.waitForEvent('download'),
  578 |       exportMenu.locator('.export-menu-item:has-text("JSON Model")').click(),
  579 |     ])
  580 |     expect(jsonDownload.suggestedFilename()).toMatch(/\.json$/)
  581 | 
  582 |     // Reopen menu for CSV
  583 |     await exportBtn.click()
  584 |     await expect(exportMenu).toBeVisible()
  585 | 
  586 |     // CSV Download
  587 |     const [csvDownload] = await Promise.all([
  588 |       page.waitForEvent('download'),
  589 |       exportMenu.locator('.export-menu-item:has-text("CSV Results")').click(),
  590 |     ])
  591 |     expect(csvDownload.suggestedFilename()).toMatch(/\.csv$/)
  592 | 
  593 |     // 8. Stale Results Protection
  594 |     // Select a joint and modify its coordinate to invalidate results
  595 |     const jointNode = page.locator('.truss-joint-node').first()
  596 |     await jointNode.click({ force: true })
  597 | 
  598 |     const xInput = page.locator('.inspector-fields input[type="number"]').first()
  599 |     await expect(xInput).toBeVisible({ timeout: 5_000 })
  600 |     await xInput.fill('1.5')
  601 |     await xInput.dispatchEvent('change')
  602 | 
  603 |     // Results panel must now indicate STALE
  604 |     await expect(resultsPanel.locator('.badge-stale')).toBeVisible({ timeout: 10_000 })
  605 | 
  606 |     // Open export menu: CSV option must be disabled and tagged stale
  607 |     await exportBtn.click()
  608 |     await expect(exportMenu).toBeVisible()
  609 |     const csvItem = exportMenu.locator('.export-menu-item:has-text("CSV Results")')
  610 |     await expect(csvItem).toBeDisabled()
  611 |     await expect(csvItem.locator('.export-badge-tag.tag-stale')).toBeVisible()
  612 | 
  613 |     // Save draft again (reopen in place without duplicate records)
  614 |     await saveBtn.click()
  615 |     await expect(page.locator('.editor-topbar .btn-save')).toContainText('Saved', { timeout: 10_000 })
  616 |   })
  617 | 
  618 |   test('13. Minimal Save & Export MVP: Direct export endpoints and JSON draft persistence', async ({ page }) => {
  619 |     // Verify direct API export behavior
  620 |     await page.goto('/?view=design')
  621 |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  622 | 
  623 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  624 |     await textarea.fill('Create a triangular truss with 4 m span and 2 m height')
  625 |     await page.locator('.studio-left-pane .btn-submit').click()
  626 | 
  627 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  628 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  629 |     await proposalCard.locator('.btn-apply').click()
  630 | 
  631 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  632 |     const confirmCheckbox = page.locator('.confirm-checkbox input')
  633 |     await confirmCheckbox.check()
  634 |     await page.locator('.editor-topbar .btn-save').click()
  635 |     await expect(page.locator('.editor-topbar .btn-save')).toContainText('Saved', { timeout: 10_000 })
  636 | 
  637 |     // Get current analysis ID from URL
  638 |     const url = new URL(page.url())
  639 |     const analysisId = url.searchParams.get('analysis')
  640 |     expect(analysisId).toBeTruthy()
  641 | 
  642 |     // Test direct JSON export on draft (unsolved)
  643 |     const jsonRes = await page.request.get(`/api/analyses/${analysisId}/export/json`)
  644 |     expect(jsonRes.status()).toBe(200)
  645 |     const jsonData = await jsonRes.json()
  646 |     expect(jsonData.schema_version).toBe('1.0')
  647 |     expect(jsonData.model.nodes.length).toBe(3)
  648 |     expect(jsonData.solver_results).toBeUndefined()
  649 | 
  650 |     // Test CSV export on draft (unsolved) returns 409
  651 |     const csvRes = await page.request.get(`/api/analyses/${analysisId}/export/csv`)
  652 |     expect(csvRes.status()).toBe(409)
  653 |     const csvErr = await csvRes.json()
  654 |     expect(csvErr.error_code).toBe('RESULTS_REQUIRED')
  655 | 
  656 |     // Test PNG export on draft (unsolved) succeeds
  657 |     const pngRes = await page.request.get(`/api/analyses/${analysisId}/export/png`)
  658 |     expect(pngRes.status()).toBe(200)
  659 |     expect(pngRes.headers()['content-type']).toBe('image/png')
  660 |   })
  661 | 
  662 |   test('14. Minimal Save & Export MVP: Sketch upload pathway (upload -> edit geometry -> save draft -> reopen -> solve -> export PNG/JSON/CSV)', async ({ page }) => {
  663 |     // 1. Upload sketch
> 664 |     await page.goto('/?view=new')
      |                ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
  665 |     await expect(page.locator('.upload-card')).toBeVisible({ timeout: 10_000 })
  666 | 
  667 |     const sketchPath = path.resolve(import.meta.dirname, '../../../backend/evaluation/sketches/test1.jpg')
  668 |     const fileBytes = readFileSync(sketchPath)
  669 |     await page.locator('input[type="file"]').setInputFiles({
  670 |       name: 'test1.jpg',
  671 |       mimeType: 'image/jpeg',
  672 |       buffer: fileBytes,
  673 |     })
  674 | 
  675 |     const uploadBtn = page.getByRole('button', { name: 'Start analysis' })
  676 |     await expect(uploadBtn).toBeEnabled()
  677 |     await uploadBtn.click()
  678 | 
  679 |     // 2. Lands on detail page
  680 |     await expect(page.locator('.detail-page')).toBeVisible({ timeout: 15_000 })
  681 |     const editBtn = page.getByRole('button', { name: 'Edit geometry' })
  682 |     await expect(editBtn).toBeVisible()
  683 |     await editBtn.click()
  684 | 
  685 |     // 3. Lands in Truss Editor
  686 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 15_000 })
  687 |     const confirmCheckbox = page.locator('.confirm-checkbox input')
  688 |     await confirmCheckbox.check()
  689 | 
  690 |     // Save draft
  691 |     const saveBtn = page.locator('.editor-topbar .btn-save')
  692 |     await saveBtn.click()
  693 |     await expect(saveBtn).toContainText('Saved', { timeout: 10_000 })
  694 | 
  695 |     // 4. Mark Reviewed and Solve
  696 |     const reviewBtn = page.locator('.editor-topbar .btn-review')
  697 |     await reviewBtn.click()
  698 |     await expect(page.locator('.editor-topbar .btn-solve')).toBeEnabled({ timeout: 10_000 })
  699 | 
  700 |     await page.locator('.editor-topbar .btn-solve').click()
  701 |     await page.locator('.cdialog-confirm').click()
  702 | 
  703 |     // 5. Results Panel appears with SOLVED status
  704 |     const resultsPanel = page.locator('.analysis-results-panel')
  705 |     await expect(resultsPanel).toBeVisible({ timeout: 15_000 })
  706 |     await expect(resultsPanel.locator('.badge-solved')).toBeVisible()
  707 | 
  708 |     // 6. Test Export
  709 |     const exportBtn = resultsPanel.locator('.btn-export')
  710 |     await expect(exportBtn).toBeVisible()
  711 |     await exportBtn.click()
  712 | 
  713 |     const exportMenu = resultsPanel.locator('.export-menu')
  714 |     await expect(exportMenu).toBeVisible()
  715 | 
  716 |     // CSV Download
  717 |     const [csvDownload] = await Promise.all([
  718 |       page.waitForEvent('download'),
  719 |       exportMenu.locator('.export-menu-item:has-text("CSV Results")').click(),
  720 |     ])
  721 |     expect(csvDownload.suggestedFilename()).toMatch(/\.csv$/)
  722 | 
  723 |     // JSON Download
  724 |     await exportBtn.click()
  725 |     const [jsonDownload] = await Promise.all([
  726 |       page.waitForEvent('download'),
  727 |       exportMenu.locator('.export-menu-item:has-text("JSON Model")').click(),
  728 |     ])
  729 |     expect(jsonDownload.suggestedFilename()).toMatch(/\.json$/)
  730 | 
  731 |     // PNG Download
  732 |     await exportBtn.click()
  733 |     const [pngDownload] = await Promise.all([
  734 |       page.waitForEvent('download'),
  735 |       exportMenu.locator('.export-menu-item:has-text("PNG Diagram")').click(),
  736 |     ])
  737 |     expect(pngDownload.suggestedFilename()).toMatch(/\.png$/)
  738 |   })
  739 | })
  740 | 
```