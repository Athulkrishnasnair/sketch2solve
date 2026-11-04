# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> solver-result experience: triangular reference model verification, results panel, on-canvas forces, reactions, legend, and stale protection
- Location: tests/e2e/application.spec.js:596:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.dialog-modal')
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.dialog-modal') with timeout 8000ms
  - waiting for locator('.dialog-modal')

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
    - button "New analysis"
    - button "Analysis history 0"
  - strong: Private by default
  - paragraph: Runs stay in your local backend. Don’t expose this workspace publicly.
  - text: Backend API · localhost:5000
- main:
  - dialog:
    - heading "Submit to Solver" [level=2]
    - paragraph: Submit the reviewed geometry to the deterministic equilibrium solver? This will compute member forces and support reactions.
    - button "Cancel"
    - button "Submit"
  - button "Back"
  - strong: Triangular Reference Truss
  - text: "#E05F77C8 reviewed"
  - button "Undo (Ctrl+Z)" [disabled]
  - button "Redo (Ctrl+Y)" [disabled]
  - text: Length
  - combobox:
    - option "m" [selected]
    - option "mm"
    - option "ft"
  - text: Force
  - combobox:
    - option "kN" [selected]
    - option "N"
    - option "lbf"
  - checkbox "Coords Confirmed" [checked]
  - text: Coords Confirmed
  - button "Saved"
  - button "Mark Reviewed"
  - button "Solve"
  - button "AI"
  - button "Zoom In"
  - button "Zoom Out"
  - button "Fit Content"
  - button "Toggle Grid"
  - button "Snap to Grid"
  - button "AI Proposal Layer"
  - text: "X: 0.000 m · Y: 0.000 m"
  - img: "(0,0) AB AC BC L_C: -10 kN A B C"
  - complementary:
    - text: Navigate
    - button "Select"
    - button "Pan"
    - text: Construction
    - button "Joint"
    - button "Member"
    - button "Measure"
    - text: Structural
    - button "Pin"
    - button "Roller"
    - button "Load"
    - text: Edit
    - button "Delete"
    - heading "Model" [level=3]
    - text: TRUSS Joints
    - strong: "3"
    - text: Members
    - strong: "3"
    - text: Supports
    - strong: "2"
    - text: Loads
    - strong: "1"
    - paragraph: Select a joint or member to inspect and edit its properties.
    - button "Clear All Model Elements"
  - text: SOLVABLE Truss is statically determinate and in static equilibrium. 3 joints · 3 members · 0.00, 0.00
```

# Test source

```ts
  552 |   await expect(applyButton).toBeVisible()
  553 |   await expect(cancelButton).toBeVisible()
  554 | 
  555 |   // 3. Record initial canvas element screen coordinate
  556 |   const firstJoint = page.locator('.truss-joint-node').first()
  557 |   const initialJointCx = await firstJoint.getAttribute('cx')
  558 | 
  559 |   // 4. Scroll inside the card using mouse wheel
  560 |   const cardBox = await scrollArea.boundingBox()
  561 |   expect(cardBox).not.toBeNull()
  562 |   await page.mouse.move(cardBox.x + cardBox.width / 2, cardBox.y + cardBox.height / 2)
  563 |   await page.mouse.wheel(0, 150)
  564 |   await page.waitForTimeout(200)
  565 | 
  566 |   // 5. Confirm the card scroll position changed
  567 |   const scrolledPosition = await scrollArea.evaluate((el) => el.scrollTop)
  568 |   expect(scrolledPosition).toBeGreaterThan(0)
  569 | 
  570 |   // 6. Confirm canvas zoom/scale remains unchanged
  571 |   const postCardScrollCx = await firstJoint.getAttribute('cx')
  572 |   expect(postCardScrollCx).toBe(initialJointCx)
  573 | 
  574 |   // 7. Scroll over the canvas outside the card (hover over open canvas SVG)
  575 |   const canvasSvg = page.locator('.engineering-svg')
  576 |   await canvasSvg.hover({ position: { x: 200, y: 200 } })
  577 |   await page.mouse.wheel(0, -200)
  578 |   await page.waitForTimeout(300)
  579 | 
  580 |   // 8. Confirm canvas zoom DID change when scrolled outside the card
  581 |   const postCanvasZoomCx = await firstJoint.getAttribute('cx')
  582 |   expect(postCanvasZoomCx).not.toBe(initialJointCx)
  583 | 
  584 |   // 9. Verify cancellation works without modifying original model
  585 |   await cancelButton.click()
  586 |   await expect(page.locator('.explanation-quote')).not.toBeVisible()
  587 |   await expect(actionCard.getByRole('button', { name: 'Fix with AI' })).toBeVisible()
  588 | 
  589 |   // 10. Re-open resolution and verify Apply Suggested Fix operates cleanly from sticky footer
  590 |   await actionCard.getByRole('button', { name: 'Fix with AI' }).click()
  591 |   await expect(page.locator('.explanation-quote')).toBeVisible({ timeout: 8_000 })
  592 |   await applyButton.click()
  593 |   await expect(page.locator('.editor-toast')).toBeVisible()
  594 | })
  595 | 
  596 | test('solver-result experience: triangular reference model verification, results panel, on-canvas forces, reactions, legend, and stale protection', async ({ page }) => {
  597 |   await page.goto('/?view=new')
  598 |   const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  599 |   const { response, body } = await submitFile(page, { name: 'reference_triangle.png', mimeType: 'image/png', buffer: bytes })
  600 |   expect(response.status()).toBe(201)
  601 | 
  602 |   // 1. Establish the known triangular reference model:
  603 |   // A=(0,0), B=(4,0), C=(2,3), Pin at A, vertical Roller at B, 10 kN downward load at C
  604 |   const triangleModel = {
  605 |     schema_version: '1.0',
  606 |     metadata: {
  607 |       name: 'Triangular Reference Truss',
  608 |       units: { length: 'm', force: 'kN' },
  609 |     },
  610 |     model: {
  611 |       nodes: [
  612 |         { id: 'A', x: 0.0, y: 0.0 },
  613 |         { id: 'B', x: 4.0, y: 0.0 },
  614 |         { id: 'C', x: 2.0, y: 3.0 },
  615 |       ],
  616 |       members: [
  617 |         { id: 'AB', node_i: 'A', node_j: 'B' },
  618 |         { id: 'AC', node_i: 'A', node_j: 'C' },
  619 |         { id: 'BC', node_i: 'B', node_j: 'C' },
  620 |       ],
  621 |       supports: [
  622 |         { id: 'S_A', node: 'A', type: 'pin' },
  623 |         { id: 'S_B', node: 'B', type: 'roller', direction: 'vertical' },
  624 |       ],
  625 |       loads: [
  626 |         { id: 'L_C', node: 'C', fx: 0.0, fy: -10.0 },
  627 |       ],
  628 |     },
  629 |   }
  630 | 
  631 |   // Persist draft and mark reviewed
  632 |   const draftRes = await page.request.put(`/api/analyses/${body.analysis_id}/draft`, {
  633 |     data: { geometry: triangleModel, coordinates_confirmed: true },
  634 |   })
  635 |   expect(draftRes.status()).toBe(200)
  636 | 
  637 |   const reviewRes = await page.request.post(`/api/analyses/${body.analysis_id}/review`)
  638 |   expect(reviewRes.status()).toBe(200)
  639 | 
  640 |   // Open the interactive geometry editor
  641 |   await page.goto(`/?analysis=${body.analysis_id}&view=editor`)
  642 |   await expect(page.locator('.truss-editor-workspace')).toBeVisible()
  643 |   await expect(page.locator('.engineering-svg')).toBeVisible()
  644 | 
  645 |   // 2. Solve button interaction: loading state, confirm dialog, and execution
  646 |   const solveButton = page.locator('.btn-solve')
  647 |   await expect(solveButton).toBeEnabled()
  648 |   await solveButton.click()
  649 | 
  650 |   // Confirm in dialog
  651 |   const confirmDialog = page.locator('.dialog-modal')
> 652 |   await expect(confirmDialog).toBeVisible()
      |                               ^ Error: expect(locator).toBeVisible() failed
  653 |   await confirmDialog.getByRole('button', { name: 'Submit' }).click()
  654 | 
  655 |   // 3. Clear transition to expanded Analysis Results view
  656 |   const resultsPanel = page.locator('.analysis-results-panel')
  657 |   await expect(resultsPanel).toBeVisible({ timeout: 10_000 })
  658 |   await expect(resultsPanel.locator('.badge-solved')).toHaveText(/SOLVED/)
  659 | 
  660 |   // 4. Verify structural counts and matrix diagnostics
  661 |   await expect(resultsPanel.getByText('Summary & Matrix')).toBeVisible()
  662 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('Joints (N)')
  663 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('3')
  664 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('Members (M)')
  665 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('3')
  666 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('Equilibrium Equations (2N)')
  667 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('6')
  668 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('Unknowns (M + R)')
  669 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('6')
  670 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('Matrix Shape')
  671 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('6 × 6')
  672 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('Numerical Rank')
  673 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('6')
  674 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('Condition Number (κ)')
  675 |   await expect(resultsPanel.locator('.summary-grid')).toContainText('4.38')
  676 | 
  677 |   // 5. Verify analytical support reactions: 5 kN upward at each support
  678 |   await resultsPanel.getByRole('button', { name: /Support Reactions/ }).click()
  679 |   const reactionsTable = resultsPanel.locator('.results-table')
  680 |   await expect(reactionsTable).toBeVisible()
  681 |   // S_A: Rx ~ 0.000 kN, Ry = +5.000 kN, Magnitude = 5.000 kN
  682 |   await expect(reactionsTable).toContainText('S_A')
  683 |   await expect(reactionsTable).toContainText('+5.000 kN')
  684 |   // S_B: Ry = +5.000 kN, Magnitude = 5.000 kN
  685 |   await expect(reactionsTable).toContainText('S_B')
  686 | 
  687 |   // 6. Verify analytical member forces:
  688 |   // Base member AB: +3.333333 kN tension
  689 |   // Inclined members AC and BC: -6.009252 kN compression
  690 |   await resultsPanel.getByRole('button', { name: /Member Forces/ }).click()
  691 |   const memberTable = resultsPanel.locator('.results-table')
  692 |   await expect(memberTable).toBeVisible()
  693 |   await expect(memberTable).toContainText('+3.333 kN')
  694 |   await expect(memberTable).toContainText('Tension (+)')
  695 |   await expect(memberTable).toContainText('-6.009 kN')
  696 |   await expect(memberTable).toContainText('Compression (−)')
  697 | 
  698 |   // 7. Verify limitations & equilibrium residual
  699 |   await resultsPanel.getByRole('button', { name: 'Limitations' }).click()
  700 |   await expect(resultsPanel.locator('.warning-block')).toContainText('A numerical equilibrium solution does not establish physical stability')
  701 |   await expect(resultsPanel.locator('.assumptions-list')).toContainText('Planar Ideal Pin-Jointed System')
  702 | 
  703 |   // 8. Verify Canvas visualization: member force labels directly on truss
  704 |   const forceLabels = page.locator('.member-force-label')
  705 |   await expect(forceLabels).toHaveCount(3)
  706 |   await expect(page.locator('.member-force-label.tension')).toContainText('+3.33 kN')
  707 |   await expect(page.locator('.member-force-label.compression').first()).toContainText('-6.01 kN')
  708 | 
  709 |   // 9. Verify Support reaction arrows and labels on canvas
  710 |   const reactionLines = page.locator('.reaction-vector-line')
  711 |   await expect(reactionLines.first()).toBeVisible()
  712 |   const reactionLabels = page.locator('.reaction-vector-label')
  713 |   await expect(reactionLabels.first()).toContainText('+5.00 kN')
  714 | 
  715 |   // 10. Verify Canvas color legend
  716 |   const legend = page.locator('.canvas-forces-legend')
  717 |   await expect(legend).toBeVisible()
  718 |   await expect(legend).toContainText('Tension (+)')
  719 |   await expect(legend).toContainText('Compression (−)')
  720 |   await expect(legend).toContainText('Reaction (R)')
  721 | 
  722 |   // 11. Test Force Labels Toggle
  723 |   const toggleLabelsBtn = page.locator('.canvas-floating-controls button[title*="force labels"]')
  724 |   await expect(toggleLabelsBtn).toBeVisible()
  725 |   await toggleLabelsBtn.click()
  726 |   await expect(page.locator('.member-force-label')).toHaveCount(0)
  727 |   await toggleLabelsBtn.click()
  728 |   await expect(page.locator('.member-force-label')).toHaveCount(3)
  729 | 
  730 |   // 12. Member selection to inspect detailed result in sidebar
  731 |   await resultsPanel.getByRole('button', { name: /Member Forces/ }).click()
  732 |   await resultsPanel.locator('.member-table-row').first().click()
  733 |   await expect(page.locator('.editor-sidebar .member-analysis-group')).toBeVisible()
  734 |   await expect(page.locator('.editor-sidebar .force-display')).toContainText('+3.33 kN')
  735 | 
  736 |   // 13. Stale results prevention: editing geometry invalidates results display
  737 |   const jointC = page.locator('.truss-joint-node').nth(2)
  738 |   const jointBox = await jointC.boundingBox()
  739 |   expect(jointBox).not.toBeNull()
  740 |   await page.mouse.move(jointBox.x + 5, jointBox.y + 5)
  741 |   await page.mouse.down()
  742 |   await page.mouse.move(jointBox.x + 50, jointBox.y + 50)
  743 |   await page.mouse.up()
  744 | 
  745 |   // Confirm results are marked stale and protected from presentation
  746 |   await expect(resultsPanel.locator('.banner-stale')).toBeVisible()
  747 |   await expect(resultsPanel.locator('.badge-stale')).toHaveText(/RESULTS STALE/)
  748 |   await expect(page.locator('.member-force-label')).toHaveCount(0)
  749 |   await expect(page.locator('.reaction-vector-line')).toHaveCount(0)
  750 |   await expect(page.locator('.editor-statusbar')).toContainText('Results stale')
  751 | 
  752 |   // 14. Zero-load case verification on a separate unloaded analysis
```