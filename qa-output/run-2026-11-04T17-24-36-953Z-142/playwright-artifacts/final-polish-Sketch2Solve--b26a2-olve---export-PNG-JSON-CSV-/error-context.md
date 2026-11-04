# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 14. Minimal Save & Export MVP: Sketch upload pathway (upload -> edit geometry -> save draft -> reopen -> solve -> export PNG/JSON/CSV)
- Location: tests/e2e/final-polish.spec.js:660:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.upload-form')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.upload-form') with timeout 10000ms
  - waiting for locator('.upload-form')

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
  563 |     const [pngDownload] = await Promise.all([
  564 |       page.waitForEvent('download'),
  565 |       exportMenu.locator('.export-menu-item:has-text("PNG Diagram")').click(),
  566 |     ])
  567 |     expect(pngDownload.suggestedFilename()).toMatch(/\.png$/)
  568 | 
  569 |     // Reopen menu for JSON
  570 |     await exportBtn.click()
  571 |     await expect(exportMenu).toBeVisible()
  572 | 
  573 |     // JSON Download
  574 |     const [jsonDownload] = await Promise.all([
  575 |       page.waitForEvent('download'),
  576 |       exportMenu.locator('.export-menu-item:has-text("JSON Model")').click(),
  577 |     ])
  578 |     expect(jsonDownload.suggestedFilename()).toMatch(/\.json$/)
  579 | 
  580 |     // Reopen menu for CSV
  581 |     await exportBtn.click()
  582 |     await expect(exportMenu).toBeVisible()
  583 | 
  584 |     // CSV Download
  585 |     const [csvDownload] = await Promise.all([
  586 |       page.waitForEvent('download'),
  587 |       exportMenu.locator('.export-menu-item:has-text("CSV Results")').click(),
  588 |     ])
  589 |     expect(csvDownload.suggestedFilename()).toMatch(/\.csv$/)
  590 | 
  591 |     // 8. Stale Results Protection
  592 |     // Select a joint and modify its coordinate to invalidate results
  593 |     const jointNode = page.locator('.truss-joint-node').first()
  594 |     await jointNode.click({ force: true })
  595 | 
  596 |     const xInput = page.locator('.inspector-fields input[type="number"]').first()
  597 |     await expect(xInput).toBeVisible({ timeout: 5_000 })
  598 |     await xInput.fill('1.5')
  599 |     await xInput.dispatchEvent('change')
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
  633 |     await expect(page.locator('.editor-topbar .btn-save')).toContainText('Saved', { timeout: 10_000 })
  634 | 
  635 |     // Get current analysis ID from URL
  636 |     const url = new URL(page.url())
  637 |     const analysisId = url.searchParams.get('analysis')
  638 |     expect(analysisId).toBeTruthy()
  639 | 
  640 |     // Test direct JSON export on draft (unsolved)
  641 |     const jsonRes = await page.request.get(`/api/analyses/${analysisId}/export/json`)
  642 |     expect(jsonRes.status()).toBe(200)
  643 |     const jsonData = await jsonRes.json()
  644 |     expect(jsonData.schema_version).toBe('1.0')
  645 |     expect(jsonData.model.nodes.length).toBe(3)
  646 |     expect(jsonData.solver_results).toBeUndefined()
  647 | 
  648 |     // Test CSV export on draft (unsolved) returns 409
  649 |     const csvRes = await page.request.get(`/api/analyses/${analysisId}/export/csv`)
  650 |     expect(csvRes.status()).toBe(409)
  651 |     const csvErr = await csvRes.json()
  652 |     expect(csvErr.error_code).toBe('RESULTS_REQUIRED')
  653 | 
  654 |     // Test PNG export on draft (unsolved) succeeds
  655 |     const pngRes = await page.request.get(`/api/analyses/${analysisId}/export/png`)
  656 |     expect(pngRes.status()).toBe(200)
  657 |     expect(pngRes.headers()['content-type']).toBe('image/png')
  658 |   })
  659 | 
  660 |   test('14. Minimal Save & Export MVP: Sketch upload pathway (upload -> edit geometry -> save draft -> reopen -> solve -> export PNG/JSON/CSV)', async ({ page }) => {
  661 |     // 1. Upload sketch
  662 |     await page.goto('/?view=new')
> 663 |     await expect(page.locator('.upload-form')).toBeVisible({ timeout: 10_000 })
      |                                                ^ Error: expect(locator).toBeVisible() failed
  664 | 
  665 |     const png1x1 = Buffer.from(
  666 |       'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAADElEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  667 |       'base64',
  668 |     )
  669 |     await page.locator('input[type="file"]').setInputFiles({
  670 |       name: 'truss_sketch.png',
  671 |       mimeType: 'image/png',
  672 |       buffer: png1x1,
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