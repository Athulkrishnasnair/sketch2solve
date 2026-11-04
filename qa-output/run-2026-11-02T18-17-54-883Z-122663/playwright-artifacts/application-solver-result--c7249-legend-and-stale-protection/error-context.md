# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> solver-result experience: triangular reference model verification, results panel, on-canvas forces, reactions, legend, and stale protection
- Location: tests/e2e/application.spec.js:596:1

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 200
Received: 400
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - complementary [ref=e4]:
    - link "Sketch2Solve STRUCTURE REVIEW" [ref=e5] [cursor=pointer]:
      - /url: /
      - generic [ref=e13]:
        - strong [ref=e14]: Sketch2Solve
        - generic [ref=e15]: STRUCTURE REVIEW
    - generic [ref=e16]: Local workspace
    - navigation "Main navigation" [ref=e18]:
      - button "Dashboard" [ref=e19] [cursor=pointer]
      - button "New analysis" [ref=e26] [cursor=pointer]
      - button "Analysis history 1" [ref=e30] [cursor=pointer]:
        - generic [ref=e36]: Analysis history
        - generic [ref=e37]: "1"
    - generic [ref=e43]:
      - strong [ref=e44]: Private by default
      - paragraph [ref=e45]: Runs stay in your local backend. Don’t expose this workspace publicly.
    - generic [ref=e46]: Backend API · localhost:5000
  - main [ref=e48]:
    - generic [ref=e49]:
      - generic [ref=e50]:
        - generic [ref=e51]: Workspace
        - generic [ref=e52]: /
        - strong [ref=e53]: Analysis review
      - generic [ref=e54]:
        - generic [ref=e55]: LOCAL ONLY
        - generic [aria-hidden] [ref=e57]: S
    - generic [ref=e58]:
      - generic [ref=e59]:
        - button "← Analysis history" [ref=e60] [cursor=pointer]
        - generic [ref=e61]: "ANALYSIS #49F28109"
      - generic [ref=e62]:
        - generic [ref=e63]:
          - generic [ref=e64]: ANALYSIS REVIEW
          - heading "reference_triangle.png" [level=1] [ref=e65]
          - generic [ref=e66]:
            - generic [ref=e67]: Nov 2, 2026, 6:17 PM
            - generic [ref=e69]: 1024 × 515 px
            - generic [ref=e71]: gemini · gemini-3.1-flash-lite
        - generic [ref=e72]:
          - button "Edit geometry" [ref=e73] [cursor=pointer]
          - generic [ref=e76]: Pending review
      - generic [ref=e78]:
        - generic [ref=e79]:
          - generic [ref=e80]:
            - generic [ref=e81]: SIDE-BY-SIDE EVIDENCE
            - heading "Compare the readings" [level=2] [ref=e82]
          - generic [ref=e83]: Pending review
        - generic "Visualization controls" [ref=e85]:
          - generic [ref=e86] [cursor=pointer]:
            - checkbox "OpenCV detections" [checked] [ref=e87]
            - text: OpenCV detections
          - generic [ref=e88] [cursor=pointer]:
            - checkbox "Endpoint clusters" [ref=e89]
            - text: Endpoint clusters
          - generic [ref=e90] [cursor=pointer]:
            - checkbox "AI proposal" [checked] [ref=e91]
            - text: AI proposal
          - generic [ref=e92] [cursor=pointer]:
            - checkbox "Element IDs" [ref=e93]
            - text: Element IDs
          - generic [ref=e94] [cursor=pointer]:
            - text: Zoom
            - slider "Zoom 1.00×" [ref=e95]: "1"
            - generic [ref=e96]: 1.00×
        - generic [ref=e97]:
          - article [ref=e98]:
            - generic [ref=e99]:
              - generic [ref=e100]:
                - generic [ref=e101]: A
                - generic [ref=e102]:
                  - strong [ref=e103]: Original sketch
                  - generic [ref=e104]: Uploaded source
              - link "Open original image" [ref=e105] [cursor=pointer]:
                - /url: http://127.0.0.1:5174/api/analyses/49f2810996cb4f098c79a0211ada5f65/image
                - text: ↗
            - img "Original uploaded truss sketch" [ref=e107]
            - generic [ref=e108]:
              - generic [ref=e109]: image/png
              - generic [ref=e110]: 1024 × 515 px
          - article [ref=e111]:
            - generic [ref=e112]:
              - generic [ref=e113]:
                - generic [ref=e114]: B
                - generic [ref=e115]:
                  - strong [ref=e116]: OpenCV detections
                  - generic [ref=e117]: Visual evidence only
              - generic [ref=e118]: 76 segments
            - generic [ref=e119]:
              - img "Sketch under OpenCV detections" [ref=e120]
              - img "OpenCV candidate segments and endpoint clusters" [ref=e121]:
                - button [ref=e122]
                - button [ref=e123]
                - button [ref=e124]
                - button [ref=e125]
                - button [ref=e126]
                - button [ref=e127]
                - button [ref=e128]
                - button [ref=e129]
                - button
                - button
                - button
                - button [ref=e130]
                - button
                - button [ref=e131]
                - button [ref=e132]
                - button [ref=e133]
                - button
                - button [ref=e134]
                - button
                - button [ref=e135]
                - button [ref=e136]
                - button
                - button
                - button [ref=e137]
                - button
                - button [ref=e138]
                - button [ref=e139]
                - button [ref=e140]
                - button [ref=e141]
                - button
                - button
                - button [ref=e142]
                - button
                - button [ref=e143]
                - button
                - button [ref=e144]
                - button
                - button
                - button [ref=e145]
                - button [ref=e146]
                - button [ref=e147]
                - button [ref=e148]
                - button [ref=e149]
                - button [ref=e150]
                - button
                - button
                - button [ref=e151]
                - button [ref=e152]
                - button [ref=e153]
                - button [ref=e154]
                - button [ref=e155]
                - button
                - button [ref=e156]
                - button
                - button
                - button [ref=e157]
                - button
                - button
                - button [ref=e158]
                - button [ref=e159]
                - button
                - button [ref=e160]
                - button [ref=e161]
                - button
                - button [ref=e162]
                - button [ref=e163]
                - button [ref=e164]
                - button [ref=e165]
                - button [ref=e166]
                - button [ref=e167]
                - button [ref=e168]
                - button [ref=e169]
                - button
                - button [ref=e170]
                - button [ref=e171]
                - button [ref=e172]
            - generic [ref=e173]:
              - generic [ref=e174]: Candidate line
              - generic [ref=e176]: Endpoint cluster
          - article [ref=e178]:
            - generic [ref=e179]:
              - generic [ref=e180]:
                - generic [ref=e181]: C
                - generic [ref=e182]:
                  - strong [ref=e183]: AI-proposed geometry
                  - generic [ref=e184]: Candidate interpretation · unapproved
              - generic [ref=e185]: 3 members
            - generic [ref=e186]:
              - img "Sketch under AI-proposed geometry" [ref=e187]
              - img "AI candidate joints, members, supports and loads" [ref=e188]:
                - button
                - button [ref=e189] [cursor=pointer]
                - button [ref=e191] [cursor=pointer]
                - button [ref=e193] [cursor=pointer]
                - button [ref=e195] [cursor=pointer]
                - button [ref=e197] [cursor=pointer]
                - button "pin support" [ref=e199]
                - button "roller support" [ref=e200]
                - button "downward load"
            - generic [ref=e201]:
              - generic [ref=e202]: Proposed member
              - generic [ref=e204]: Proposed joint
      - generic [ref=e206]:
        - generic [ref=e207]:
          - generic [ref=e208]:
            - generic [ref=e209]:
              - generic [ref=e210]: MODEL OUTPUT
              - heading "Interpretation proposal" [level=2] [ref=e211]
            - generic [ref=e212]: CANDIDATE ONLY
          - generic [ref=e213]:
            - generic [ref=e214]:
              - strong [ref=e215]: "3"
              - generic [ref=e216]: Joints
            - generic [ref=e217]:
              - strong [ref=e218]: "3"
              - generic [ref=e219]: Members
            - generic [ref=e220]:
              - strong [ref=e221]: "2"
              - generic [ref=e222]: Supports
            - generic [ref=e223]:
              - strong [ref=e224]: "1"
              - generic [ref=e225]: Loads
          - group [ref=e226]:
            - generic "Inspect proposed elements" [ref=e227] [cursor=pointer]
          - generic [ref=e228]:
            - heading "Ambiguities to check" [level=3] [ref=e229]
            - list [ref=e230]:
              - listitem [ref=e231]: This is synthetic test data, not an interpretation of the uploaded image.
          - generic [ref=e232]:
            - heading "Information not visible" [level=3] [ref=e233]
            - list [ref=e234]:
              - listitem [ref=e235]: Physical dimensions and units are not inferred.
        - generic [ref=e236]:
          - generic [ref=e237]:
            - generic [ref=e238]:
              - generic [ref=e239]: CHECKS & DIAGNOSTICS
              - heading "Validation state" [level=2] [ref=e240]
            - generic [ref=e241]: NOT RUN
          - paragraph [ref=e242]: Candidate geometry has not been converted into a solver model. Nothing is approved or solved from this proposal.
      - generic [ref=e243]:
        - generic [ref=e244]:
          - generic [ref=e245]:
            - generic [ref=e246]: HUMAN-CORRECTED MODEL
            - heading "Geometry draft" [level=2] [ref=e247]
          - generic [ref=e248]:
            - button "Open Interactive Editor ↗" [ref=e249] [cursor=pointer]
            - generic [ref=e250]: NOT SAVED
        - paragraph [ref=e251]: AI output remains preserved above. Draft coordinates use physical length units and are separate from the AI's image-pixel coordinates. No unit or load value is inferred.
        - button "Correct interpretation" [ref=e253] [cursor=pointer]
      - generic [ref=e254]:
        - generic [ref=e255]: i
        - generic [ref=e256]:
          - strong [ref=e257]: Engineering review boundary
          - paragraph [ref=e258]: Model validation checks the request schema and references; solver diagnostics are numerical checks. Neither establishes physical stability, code compliance, or engineering suitability. Review all dimensions and loads.
        - generic [ref=e259]: Pending review
    - generic [ref=e261]:
      - generic [ref=e262]: Sketch2Solve · Local review workspace
      - generic [ref=e263]: Interpretation is a starting point, not a structural check.
```

# Test source

```ts
  535 |   // Click 'Fix with AI' to generate extensive resolution content (root cause, rationale, proposed fixes, alternatives)
  536 |   await actionCard.getByRole('button', { name: 'Fix with AI' }).click()
  537 |   await expect(page.locator('.explanation-quote')).toBeVisible({ timeout: 8_000 })
  538 | 
  539 |   // 1. Verify card content area has overflowed and is independently scrollable
  540 |   const scrollArea = page.locator('.card-content-scroll')
  541 |   await expect(scrollArea).toBeVisible()
  542 |   const scrollMetrics = await scrollArea.evaluate((el) => ({
  543 |     scrollHeight: el.scrollHeight,
  544 |     clientHeight: el.clientHeight,
  545 |     scrollTop: el.scrollTop,
  546 |   }))
  547 |   expect(scrollMetrics.scrollHeight).toBeGreaterThan(scrollMetrics.clientHeight)
  548 | 
  549 |   // 2. Verify sticky footer with Apply and Cancel actions remains visible and accessible
  550 |   const applyButton = page.locator('.btn-apply-fix')
  551 |   const cancelButton = page.locator('.btn-cancel-fix')
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
  633 |     data: { draft: triangleModel, coordinate_confirmation: true },
  634 |   })
> 635 |   expect(draftRes.status()).toBe(200)
      |                             ^ Error: expect(received).toBe(expected) // Object.is equality
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
  652 |   await expect(confirmDialog).toBeVisible()
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
```