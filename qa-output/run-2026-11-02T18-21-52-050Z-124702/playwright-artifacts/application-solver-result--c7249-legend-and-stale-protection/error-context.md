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

Locator: locator('.analysis-results-panel').locator('.banner-stale')
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.analysis-results-panel').locator('.banner-stale') with timeout 8000ms
  - waiting for locator('.analysis-results-panel').locator('.banner-stale')

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
  - text: "#B95F9EFB submitted"
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
  - text: "Forces Legend Tension (+) Compression (−) Zero-Force (0) Reaction (R) X: 2.000 m · Y: 0.223 m"
  - img: "(0,0) AB +3.33 kN AC -6.01 kN BC -6.01 kN Ry: +5.00 kN Ry: +5.00 kN L_C: -10 kN A B C"
  - region "Analysis Results Panel":
    - text: SOLVED
    - heading "Analysis Results" [level=3]
    - text: m · kN
    - navigation:
      - button "Summary & Matrix"
      - button "Member Forces (3)"
      - button "Support Reactions (2)"
      - button "Limitations"
    - button "Labels On"
    - button "Expand panel height"
    - button "Close results panel"
    - table "Member Forces Table":
      - rowgroup:
        - row "Member Joints Length (m) Axial Force (kN) Classification Action":
          - columnheader "Member"
          - columnheader "Joints"
          - columnheader "Length (m)"
          - columnheader "Axial Force (kN)"
          - columnheader "Classification"
          - columnheader "Action"
      - rowgroup:
        - row "AB A → B 4.000 +3.333 kN Tension (+) Inspect":
          - cell "AB"
          - cell "A → B"
          - cell "4.000"
          - cell "+3.333 kN"
          - cell "Tension (+)"
          - cell "Inspect":
            - button "Inspect"
        - row "AC A → C 3.606 -6.009 kN Compression (−) Inspect":
          - cell "AC"
          - cell "A → C"
          - cell "3.606"
          - cell "-6.009 kN"
          - cell "Compression (−)"
          - cell "Inspect":
            - button "Inspect"
        - row "BC B → C 3.606 -6.009 kN Compression (−) Inspect":
          - cell "BC"
          - cell "B → C"
          - cell "3.606"
          - cell "-6.009 kN"
          - cell "Compression (−)"
          - cell "Inspect":
            - button "Inspect"
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
    - heading "Member" [level=3]
    - text: AB Member ID
    - textbox: AB
    - text: Joint i
    - combobox:
      - option "A" [selected]
      - option "B"
      - option "C"
    - text: Joint j
    - combobox:
      - option "A"
      - option "B" [selected]
      - option "C"
    - text: Length
    - strong: 4.000 m
    - text: Analysis Result +3.33 kN TENSION
    - button "Delete Member"
  - text: SOLVED Analysis complete — results available 3 joints · 3 members · 2.00, 0.22
```

# Test source

```ts
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
  715 |   await expect(reactionLines).toHaveCount(2)
  716 |   const reactionHeads = page.locator('.reaction-arrowhead')
  717 |   await expect(reactionHeads.first()).toBeVisible()
  718 |   const reactionLabels = page.locator('.reaction-vector-label')
  719 |   await expect(reactionLabels.first()).toBeVisible()
  720 |   await expect(reactionLabels.first()).toContainText('+5.00 kN')
  721 | 
  722 |   // 10. Verify Canvas color legend
  723 |   const legend = page.locator('.canvas-forces-legend')
  724 |   await expect(legend).toBeVisible()
  725 |   await expect(legend).toContainText('Tension (+)')
  726 |   await expect(legend).toContainText('Compression (−)')
  727 |   await expect(legend).toContainText('Reaction (R)')
  728 | 
  729 |   // 11. Test Force Labels Toggle
  730 |   const toggleLabelsBtn = page.locator('.canvas-floating-controls button[title*="force labels"]')
  731 |   await expect(toggleLabelsBtn).toBeVisible()
  732 |   await toggleLabelsBtn.click()
  733 |   await expect(page.locator('.member-force-label')).toHaveCount(0)
  734 |   await toggleLabelsBtn.click()
  735 |   await expect(page.locator('.member-force-label')).toHaveCount(3)
  736 | 
  737 |   // Re-open results panel using topbar Results button
  738 |   await page.locator('.btn-results').click()
  739 |   await expect(resultsPanel).toBeVisible()
  740 | 
  741 |   // 12. Member selection to inspect detailed result in sidebar
  742 |   await resultsPanel.getByRole('button', { name: /Member Forces/ }).click()
  743 |   await resultsPanel.locator('.member-table-row').first().click()
  744 |   await expect(page.locator('.editor-sidebar .member-analysis-group')).toBeVisible()
  745 |   await expect(page.locator('.editor-sidebar .force-display')).toContainText('+3.33 kN')
  746 | 
  747 |   // 13. Stale results prevention: editing geometry invalidates results display
  748 |   const jointC = page.locator('.truss-joint-node').nth(2)
  749 |   const jointBox = await jointC.boundingBox()
  750 |   expect(jointBox).not.toBeNull()
  751 |   await page.mouse.move(jointBox.x + 5, jointBox.y + 5)
  752 |   await page.mouse.down()
  753 |   await page.mouse.move(jointBox.x + 50, jointBox.y + 50)
  754 |   await page.mouse.up()
  755 | 
  756 |   // Confirm results are marked stale and protected from presentation
> 757 |   await expect(resultsPanel.locator('.banner-stale')).toBeVisible()
      |                                                       ^ Error: expect(locator).toBeVisible() failed
  758 |   await expect(resultsPanel.locator('.badge-stale')).toHaveText(/RESULTS STALE/)
  759 |   await expect(page.locator('.member-force-label')).toHaveCount(0)
  760 |   await expect(page.locator('.reaction-vector-line')).toHaveCount(0)
  761 |   await expect(page.locator('.editor-statusbar')).toContainText('Results stale')
  762 | 
  763 |   // 14. Zero-load case verification on a separate unloaded analysis
  764 |   const { response: res2, body: body2 } = await submitFile(page, { name: 'unloaded_triangle.png', mimeType: 'image/png', buffer: bytes })
  765 |   expect(res2.status()).toBe(201)
  766 | 
  767 |   const unloadedModel = JSON.parse(JSON.stringify(triangleModel))
  768 |   unloadedModel.model.loads = []
  769 |   const draft2 = await page.request.put(`/api/analyses/${body2.analysis_id}/draft`, {
  770 |     data: { geometry: unloadedModel, coordinates_confirmed: true },
  771 |   })
  772 |   expect(draft2.status()).toBe(200)
  773 |   const rev2 = await page.request.post(`/api/analyses/${body2.analysis_id}/review`)
  774 |   expect(rev2.status()).toBe(200)
  775 | 
  776 |   await page.goto(`/?analysis=${body2.analysis_id}&view=editor`)
  777 |   await expect(page.locator('.truss-editor-workspace')).toBeVisible()
  778 | 
  779 |   // Solve the unloaded model
  780 |   await page.locator('.btn-solve').click()
  781 |   await page.locator('.cdialog-panel').locator('.cdialog-confirm').click()
  782 |   const unloadedPanel = page.locator('.analysis-results-panel')
  783 |   await expect(unloadedPanel).toBeVisible({ timeout: 10_000 })
  784 |   await expect(unloadedPanel.locator('.banner-unloaded')).toBeVisible()
  785 |   await expect(unloadedPanel.locator('.banner-unloaded')).toContainText('Model is unloaded (Zero external forces applied)')
  786 | })
  787 | 
  788 | 
```