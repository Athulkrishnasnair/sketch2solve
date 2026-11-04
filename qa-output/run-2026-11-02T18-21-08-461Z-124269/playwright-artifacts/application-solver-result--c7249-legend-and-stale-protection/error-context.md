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

Locator:  locator('.reaction-vector-line').first()
Expected: visible
Received: hidden
Timeout:  8000ms

Call log:
  - Expect "toBeVisible" locator('.reaction-vector-line').first() with timeout 8000ms
  - waiting for locator('.reaction-vector-line').first()
    20 × locator resolved to <line x1="100" x2="100" y1="550.875" y2="522.875" data-v-ae2570cd="" class="reaction-vector-line"></line>
       - unexpected value "hidden"

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
  - button "Back"
  - strong: Triangular Reference Truss
  - text: "#15187ACA submitted"
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
  - button "Solve" [disabled]
  - button "Results"
  - button "AI"
  - button "Zoom In"
  - button "Zoom Out"
  - button "Fit Content"
  - button "Toggle Grid"
  - button "Snap to Grid"
  - button "AI Proposal Layer"
  - button "Hide member force labels"
  - button "Toggle Analysis Results panel"
  - text: "Forces Legend Tension (+) Compression (−) Zero-Force (0) Reaction (R) X: 4.748 m · Y: 0.989 m"
  - img: "(0,0) AB +3.33 kN AC -6.01 kN BC -6.01 kN Ry: +5.00 kN Ry: +5.00 kN L_C: -10 kN A B C"
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
  - text: SOLVED Analysis complete — results available 3 joints · 3 members · 4.75, 0.99
```

# Test source

```ts
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
  651 |   const confirmDialog = page.locator('.cdialog-panel')
  652 |   await expect(confirmDialog).toBeVisible()
  653 |   await confirmDialog.locator('.cdialog-confirm').click()
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
  700 |   await expect(resultsPanel.locator('.warning-block')).toContainText('A numerical solution does not establish physical stability')
  701 |   await expect(resultsPanel.locator('.assumptions-list')).toContainText('Planar Ideal Pin-Jointed System')
  702 | 
  703 |   // 8. Close results panel to clearly inspect full canvas visualization
  704 |   await resultsPanel.locator('.btn-close').click()
  705 |   await expect(resultsPanel).not.toBeVisible()
  706 | 
  707 |   // Verify member force labels directly on truss
  708 |   const forceLabels = page.locator('.member-force-label')
  709 |   await expect(forceLabels).toHaveCount(3)
  710 |   await expect(page.locator('.member-force-label.tension')).toContainText('+3.33 kN')
  711 |   await expect(page.locator('.member-force-label.compression').first()).toContainText('-6.01 kN')
  712 | 
  713 |   // 9. Verify Support reaction arrows and labels on canvas
  714 |   const reactionLines = page.locator('.reaction-vector-line')
> 715 |   await expect(reactionLines.first()).toBeVisible()
      |                                       ^ Error: expect(locator).toBeVisible() failed
  716 |   const reactionLabels = page.locator('.reaction-vector-label')
  717 |   await expect(reactionLabels.first()).toContainText('+5.00 kN')
  718 | 
  719 |   // 10. Verify Canvas color legend
  720 |   const legend = page.locator('.canvas-forces-legend')
  721 |   await expect(legend).toBeVisible()
  722 |   await expect(legend).toContainText('Tension (+)')
  723 |   await expect(legend).toContainText('Compression (−)')
  724 |   await expect(legend).toContainText('Reaction (R)')
  725 | 
  726 |   // 11. Test Force Labels Toggle
  727 |   const toggleLabelsBtn = page.locator('.canvas-floating-controls button[title*="force labels"]')
  728 |   await expect(toggleLabelsBtn).toBeVisible()
  729 |   await toggleLabelsBtn.click()
  730 |   await expect(page.locator('.member-force-label')).toHaveCount(0)
  731 |   await toggleLabelsBtn.click()
  732 |   await expect(page.locator('.member-force-label')).toHaveCount(3)
  733 | 
  734 |   // Re-open results panel using topbar Results button
  735 |   await page.locator('.btn-results').click()
  736 |   await expect(resultsPanel).toBeVisible()
  737 | 
  738 |   // 12. Member selection to inspect detailed result in sidebar
  739 |   await resultsPanel.getByRole('button', { name: /Member Forces/ }).click()
  740 |   await resultsPanel.locator('.member-table-row').first().click()
  741 |   await expect(page.locator('.editor-sidebar .member-analysis-group')).toBeVisible()
  742 |   await expect(page.locator('.editor-sidebar .force-display')).toContainText('+3.33 kN')
  743 | 
  744 |   // 13. Stale results prevention: editing geometry invalidates results display
  745 |   const jointC = page.locator('.truss-joint-node').nth(2)
  746 |   const jointBox = await jointC.boundingBox()
  747 |   expect(jointBox).not.toBeNull()
  748 |   await page.mouse.move(jointBox.x + 5, jointBox.y + 5)
  749 |   await page.mouse.down()
  750 |   await page.mouse.move(jointBox.x + 50, jointBox.y + 50)
  751 |   await page.mouse.up()
  752 | 
  753 |   // Confirm results are marked stale and protected from presentation
  754 |   await expect(resultsPanel.locator('.banner-stale')).toBeVisible()
  755 |   await expect(resultsPanel.locator('.badge-stale')).toHaveText(/RESULTS STALE/)
  756 |   await expect(page.locator('.member-force-label')).toHaveCount(0)
  757 |   await expect(page.locator('.reaction-vector-line')).toHaveCount(0)
  758 |   await expect(page.locator('.editor-statusbar')).toContainText('Results stale')
  759 | 
  760 |   // 14. Zero-load case verification on a separate unloaded analysis
  761 |   const { response: res2, body: body2 } = await submitFile(page, { name: 'unloaded_triangle.png', mimeType: 'image/png', buffer: bytes })
  762 |   expect(res2.status()).toBe(201)
  763 | 
  764 |   const unloadedModel = JSON.parse(JSON.stringify(triangleModel))
  765 |   unloadedModel.model.loads = []
  766 |   const draft2 = await page.request.put(`/api/analyses/${body2.analysis_id}/draft`, {
  767 |     data: { geometry: unloadedModel, coordinates_confirmed: true },
  768 |   })
  769 |   expect(draft2.status()).toBe(200)
  770 |   const rev2 = await page.request.post(`/api/analyses/${body2.analysis_id}/review`)
  771 |   expect(rev2.status()).toBe(200)
  772 | 
  773 |   await page.goto(`/?analysis=${body2.analysis_id}&view=editor`)
  774 |   await expect(page.locator('.truss-editor-workspace')).toBeVisible()
  775 | 
  776 |   // Solve the unloaded model
  777 |   await page.locator('.btn-solve').click()
  778 |   await page.locator('.cdialog-panel').locator('.cdialog-confirm').click()
  779 |   const unloadedPanel = page.locator('.analysis-results-panel')
  780 |   await expect(unloadedPanel).toBeVisible({ timeout: 10_000 })
  781 |   await expect(unloadedPanel.locator('.banner-unloaded')).toBeVisible()
  782 |   await expect(unloadedPanel.locator('.banner-unloaded')).toContainText('Model is unloaded (Zero external forces applied)')
  783 | })
  784 | 
  785 | 
```