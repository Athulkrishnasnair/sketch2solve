# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> contextual on-canvas issue highlighting, floating action card, and AI repair workflow
- Location: tests/e2e/application.spec.js:469:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.contextual-action-card')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.contextual-action-card') with timeout 10000ms
  - waiting for locator('.contextual-action-card')

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
  - button "Back to analysis": Back
  - strong: Truss Model
  - text: "#2D826B1A pending review"
  - button "Undo" [disabled]
  - button "Redo" [disabled]
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
  - checkbox "Coords Confirmed"
  - text: Coords Confirmed
  - button "Saved" [disabled]
  - button "Mark Reviewed"
  - button "Solve" [disabled]
  - button "Design with AI"
  - toolbar "Canvas view controls":
    - button "Zoom in"
    - button "Zoom out"
    - button "Fit content to view"
    - separator
    - button "Toggle grid" [pressed]
    - button "Snap to grid" [pressed]
    - button "Toggle AI proposal layer" [pressed]
    - button "Highlight detected issues"
  - text: "X: 0.000 m · Y: 0.000 m"
  - img: (0,0) M1 M2 M3 J1 J2 J3
  - complementary:
    - tablist "Sidebar navigation":
      - tab "Tools" [selected]
      - tab "Design with AI"
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
    - strong: "0"
    - text: Loads
    - strong: "0"
    - paragraph: Select a joint or member to inspect and edit its properties.
    - button "Clear All Model Elements"
  - text: "UNSOLVABLE Statically indeterminate system: 6 equations vs 3 unknowns. Direct equilibrium requires a square determinate system. 3 joints · 3 members · 0.00, 0.00"
  - button "2 issues"
```

# Test source

```ts
  384 |   const invalidGeometry = {
  385 |     schema_version: '1.0',
  386 |     metadata: { name: 'invalid', source: 'human_review', units: { length: 'm', force: 'N' } },
  387 |     model: {
  388 |       nodes: [{ id: 'A', x: 0, y: 0 }, { id: 'B', x: 1, y: 0 }],
  389 |       members: [{ id: 'M1', node_i: 'A', node_j: 'missing' }],
  390 |       supports: [],
  391 |       loads: [],
  392 |     },
  393 |   }
  394 |   const invalid = await page.request.put(draftUrl, {
  395 |     data: { geometry: invalidGeometry, coordinates_confirmed: true },
  396 |   })
  397 |   expect(invalid.status()).toBe(422)
  398 |   expect((await invalid.json()).error_code).toBe('VALIDATION_FAILED')
  399 | 
  400 |   const singular = {
  401 |     schema_version: '1.0',
  402 |     metadata: { name: 'singular', source: 'human_review', units: { length: 'm', force: 'N' } },
  403 |     model: {
  404 |       nodes: [
  405 |         { id: 'A', x: 0, y: 0 },
  406 |         { id: 'B', x: 4, y: 0 },
  407 |         { id: 'C', x: 2, y: 3 },
  408 |       ],
  409 |       members: [
  410 |         { id: 'M1', node_i: 'A', node_j: 'B' },
  411 |         { id: 'M2', node_i: 'A', node_j: 'C' },
  412 |         { id: 'M3', node_i: 'A', node_j: 'C' },
  413 |       ],
  414 |       supports: [
  415 |         { id: 'S1', node: 'A', type: 'pin' },
  416 |         { id: 'S2', node: 'B', type: 'roller', direction: 'vertical' },
  417 |       ],
  418 |       loads: [{ id: 'L1', node: 'C', fx: 0, fy: -10 }],
  419 |     },
  420 |   }
  421 |   const missingUnits = structuredClone(singular)
  422 |   missingUnits.metadata.units.length = ''
  423 |   const noUnits = await page.request.put(draftUrl, {
  424 |     data: { geometry: missingUnits, coordinates_confirmed: true },
  425 |   })
  426 |   expect(noUnits.status()).toBe(422)
  427 |   expect((await noUnits.json()).error_code).toBe('VALIDATION_FAILED')
  428 | 
  429 |   expect((await page.request.put(draftUrl, {
  430 |     data: { geometry: singular, coordinates_confirmed: true },
  431 |   })).status()).toBe(200)
  432 |   expect((await page.request.post(`/api/analyses/${analysis.analysis_id}/review`)).status()).toBe(200)
  433 |   const failedSolve = await page.request.post(solveUrl)
  434 |   expect(failedSolve.status()).toBe(422)
  435 | 
  436 |   const retained = await page.request.get(`/api/analyses/${analysis.analysis_id}`)
  437 |   const detail = await retained.json()
  438 |   expect(detail.review_status).toBe('reviewed')
  439 |   expect(detail.human_review.geometry).toEqual(singular)
  440 |   expect(detail.solver_results).toBeNull()
  441 |   expect(detail.diagnostics).not.toBeNull()
  442 | })
  443 | 
  444 | test('a missing stored image is explained while geometry remains available', async ({ page }) => {
  445 |   const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  446 |   const created = await page.request.post('/api/analyses', {
  447 |     multipart: { provider: 'gemini', image: { name: 'missing-image.png', mimeType: 'image/png', buffer: bytes } },
  448 |   })
  449 |   const body = await created.json()
  450 |   expectHttpError(page, 404)
  451 |   await page.route(`**/api/analyses/${body.analysis_id}/image`, (route) => route.fulfill({
  452 |     status: 404,
  453 |     contentType: 'application/json',
  454 |     body: JSON.stringify({ error_code: 'ANALYSIS_NOT_FOUND', message: 'Image unavailable.' }),
  455 |   }))
  456 |   await page.goto(`/?analysis=${body.analysis_id}`)
  457 |   await expect(page.getByText('The original sketch file is unavailable.')).toBeVisible()
  458 |   await expect(page.getByRole('heading', { name: 'Geometry draft' })).toBeVisible()
  459 | })
  460 | 
  461 | test('network failure displays the local backend connection message', async ({ page }) => {
  462 |   expectFailedRequest(page, '/api/analyses?')
  463 |   telemetry.get(page).expectedConsoleErrors = ['net::ERR_FAILED']
  464 |   await page.route('**/api/analyses?**', (route) => route.abort())
  465 |   await page.goto('/?view=history')
  466 |   await expect(page.getByRole('alert')).toContainText('Could not reach the local Sketch2Solve backend.')
  467 | })
  468 | 
  469 | test('contextual on-canvas issue highlighting, floating action card, and AI repair workflow', async ({ page }) => {
  470 |   await page.goto('/?view=new')
  471 |   const bytes = readFileSync(path.join(evaluationDirectory, 'test4.jpg'))
  472 |   const { response, body } = await submitFile(page, { name: 'canvas_repair.jpg', mimeType: 'image/jpeg', buffer: bytes })
  473 |   expect(response.status()).toBe(201)
  474 | 
  475 |   // Navigate to interactive editor view
  476 |   await page.goto(`/?analysis=${body.analysis_id}&view=editor`)
  477 |   await expect(page.locator('.truss-editor-workspace')).toBeVisible()
  478 | 
  479 |   // Wait for canvas and initial preview calculation
  480 |   await expect(page.locator('.engineering-svg')).toBeVisible()
  481 | 
  482 |   // Verify contextual action card appears near affected geometry
  483 |   const actionCard = page.locator('.contextual-action-card')
> 484 |   await expect(actionCard).toBeVisible({ timeout: 10_000 })
      |                            ^ Error: expect(locator).toBeVisible() failed
  485 |   await expect(actionCard.locator('.classification-pill')).toBeVisible()
  486 |   await expect(actionCard.getByRole('button', { name: 'Fix with AI' })).toBeVisible()
  487 | 
  488 |   // Verify affected elements highlighting on canvas
  489 |   const affectedHighlights = page.locator('.issue-highlight-error, .issue-highlight-mechanism, .issue-highlight-warning, .joint-issue-pulse-ring')
  490 |   const highlightCount = await affectedHighlights.count()
  491 |   expect(highlightCount).toBeGreaterThan(0)
  492 | 
  493 |   // Test clearing highlight
  494 |   await page.locator('.btn-clear-highlight').click()
  495 |   await expect(actionCard).not.toBeVisible()
  496 | 
  497 |   // Test re-enabling highlight via status bar toggle
  498 |   await page.locator('.status-warnings-toggle').click()
  499 |   await expect(actionCard).toBeVisible()
  500 | 
  501 |   // Click 'Fix with AI'
  502 |   await actionCard.getByRole('button', { name: 'Fix with AI' }).click()
  503 | 
  504 |   // Verify root cause explanation and repair actions appear
  505 |   await expect(page.locator('.explanation-quote')).toBeVisible({ timeout: 8_000 })
  506 |   await expect(page.locator('.btn-apply-fix')).toBeVisible()
  507 |   await expect(page.locator('.btn-cancel-fix')).toBeVisible()
  508 | 
  509 |   // Verify AI proposed modification preview rendered on canvas (distinct blue styling)
  510 |   const proposedPreview = page.locator('.ai-fix-preview-group')
  511 |   await expect(proposedPreview).toBeVisible()
  512 | 
  513 |   // Apply suggested fix
  514 |   await page.locator('.btn-apply-fix').click()
  515 | 
  516 |   // Verify toast notification and revalidation update
  517 |   await expect(page.locator('.editor-toast')).toBeVisible()
  518 | })
  519 | 
  520 | test('issue resolution assistant independent scrolling, mouse-wheel isolation, and sticky footer', async ({ page }) => {
  521 |   await page.goto('/?view=new')
  522 |   const bytes = readFileSync(path.join(evaluationDirectory, 'test4.jpg'))
  523 |   const { response, body } = await submitFile(page, { name: 'card_scroll_test.jpg', mimeType: 'image/jpeg', buffer: bytes })
  524 |   expect(response.status()).toBe(201)
  525 | 
  526 |   // Navigate to interactive editor view
  527 |   await page.goto(`/?analysis=${body.analysis_id}&view=editor`)
  528 |   await expect(page.locator('.truss-editor-workspace')).toBeVisible()
  529 |   await expect(page.locator('.engineering-svg')).toBeVisible()
  530 | 
  531 |   // Verify contextual action card appears
  532 |   const actionCard = page.locator('.contextual-action-card')
  533 |   await expect(actionCard).toBeVisible({ timeout: 10_000 })
  534 | 
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
```