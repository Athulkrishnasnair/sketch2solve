# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> contextual on-canvas issue highlighting, floating action card, and AI repair workflow
- Location: tests/e2e/application.spec.js:469:1

# Error details

```
Error: expect(received).toBeGreaterThan(expected)

Expected: > 0
Received:   0
```

# Page snapshot

```yaml
- generic [ref=f1e3]:
  - complementary [ref=f1e4]:
    - link "Sketch2Solve STRUCTURE REVIEW" [ref=f1e5] [cursor=pointer]:
      - /url: /
      - generic [ref=f1e13]:
        - strong [ref=f1e14]: Sketch2Solve
        - generic [ref=f1e15]: STRUCTURE REVIEW
    - generic [ref=f1e16]: Local workspace
    - navigation "Main navigation" [ref=f1e18]:
      - button "Dashboard" [ref=f1e19] [cursor=pointer]
      - button "New analysis" [ref=f1e26] [cursor=pointer]
      - button "Analysis history 0" [ref=f1e30] [cursor=pointer]:
        - generic [ref=f1e36]: Analysis history
        - generic [ref=f1e37]: "0"
    - generic [ref=f1e43]:
      - strong [ref=f1e44]: Private by default
      - paragraph [ref=f1e45]: Runs stay in your local backend. Don’t expose this workspace publicly.
    - generic [ref=f1e46]: Backend API · localhost:5000
  - main [ref=f1e48]:
    - generic [ref=f1e49]:
      - generic [ref=f1e50]:
        - generic [ref=f1e51]:
          - button "Back" [ref=f1e52] [cursor=pointer]
          - generic [ref=f1e56]:
            - strong [ref=f1e57]: Truss Model
            - generic [ref=f1e58]:
              - text: "#A793AC09"
              - generic [ref=f1e59]: pending review
        - generic [ref=f1e60]:
          - button "Undo (Ctrl+Z)" [disabled] [ref=f1e61]
          - button "Redo (Ctrl+Y)" [disabled] [ref=f1e65]
          - generic [ref=f1e70]:
            - generic [ref=f1e71]: Length
            - combobox [ref=f1e72] [cursor=pointer]:
              - option "m" [selected]
              - option "mm"
              - option "ft"
            - generic [ref=f1e73]: Force
            - combobox [ref=f1e74] [cursor=pointer]:
              - option "kN" [selected]
              - option "N"
              - option "lbf"
          - generic [ref=f1e75] [cursor=pointer]:
            - checkbox "Coords Confirmed" [ref=f1e76]
            - generic [ref=f1e77]: Coords Confirmed
        - generic [ref=f1e78]:
          - button "Saved" [disabled] [ref=f1e79]
          - button "Mark Reviewed" [ref=f1e85] [cursor=pointer]
          - button "Solve" [disabled] [ref=f1e89]
          - button "AI" [ref=f1e94] [cursor=pointer]
      - generic [ref=f1e98]:
        - generic [ref=f1e99]:
          - generic [ref=f1e100]:
            - button "Zoom In" [ref=f1e101] [cursor=pointer]
            - button "Zoom Out" [ref=f1e105] [cursor=pointer]
            - button "Fit Content" [ref=f1e109] [cursor=pointer]
            - button "Toggle Grid" [ref=f1e116] [cursor=pointer]
            - button "Snap to Grid" [ref=f1e119] [cursor=pointer]
            - button "AI Proposal Layer" [ref=f1e124] [cursor=pointer]
            - button "Clear issue highlighting" [ref=f1e128] [cursor=pointer]
          - generic: "X: 0.000 m · Y: 0.000 m"
          - img [ref=f1e131]:
            - generic [ref=f1e133]: (0,0)
            - generic [ref=f1e136]:
              - generic [ref=f1e137] [cursor=pointer]
              - generic [ref=f1e138] [cursor=pointer]
              - generic [ref=f1e139] [cursor=pointer]
              - generic [ref=f1e140] [cursor=pointer]
              - generic [ref=f1e141] [cursor=pointer]
            - generic [ref=f1e142]:
              - generic [ref=f1e143]: M1
              - generic [ref=f1e145]:
                - generic [ref=f1e146] [cursor=pointer]
                - generic [ref=f1e147] [cursor=pointer]: M2
              - generic [ref=f1e148]:
                - generic [ref=f1e149] [cursor=pointer]
                - generic [ref=f1e150] [cursor=pointer]: M3
            - generic [ref=f1e151]:
              - generic [ref=f1e152]:
                - generic [ref=f1e153] [cursor=pointer]
                - generic: J1
              - generic [ref=f1e154]:
                - generic [ref=f1e155] [cursor=pointer]
                - generic: J2
              - generic [ref=f1e156]:
                - generic [ref=f1e157] [cursor=pointer]
                - generic: J3
          - region "Contextual Issue Resolution" [ref=f1e158]:
            - generic [ref=f1e159]:
              - generic [ref=f1e160]:
                - generic [ref=f1e161]: Under-constrained
                - generic [ref=f1e166]: 1 / 2
              - generic [ref=f1e167]:
                - generic [ref=f1e168]:
                  - button "Previous issue" [disabled] [ref=f1e169]
                  - button "Next issue" [ref=f1e172] [cursor=pointer]
                - button "Clear issue highlighting" [ref=f1e175] [cursor=pointer]
                - button "Minimize" [ref=f1e181] [cursor=pointer]
            - generic [ref=f1e185]:
              - strong [ref=f1e187]: INSUFFICIENT SUPPORTS
              - paragraph [ref=f1e188]: The structure has 0 support constraints (at least 3 non-parallel constraints are required for stable planar equilibrium).
              - button "Fix with AI" [ref=f1e190] [cursor=pointer]
        - complementary [ref=f1e195]:
          - generic [ref=f1e196]:
            - generic [ref=f1e197]:
              - generic [ref=f1e198]: Navigate
              - generic [ref=f1e199]:
                - button "Select" [ref=f1e200] [cursor=pointer]
                - button "Pan" [ref=f1e204] [cursor=pointer]
            - generic [ref=f1e210]:
              - generic [ref=f1e211]: Construction
              - generic [ref=f1e212]:
                - button "Joint" [ref=f1e213] [cursor=pointer]
                - button "Member" [ref=f1e216] [cursor=pointer]
                - button "Measure" [ref=f1e221] [cursor=pointer]
            - generic [ref=f1e228]:
              - generic [ref=f1e229]: Structural
              - generic [ref=f1e230]:
                - button "Pin" [ref=f1e231] [cursor=pointer]
                - button "Roller" [ref=f1e235] [cursor=pointer]
                - button "Load" [ref=f1e239] [cursor=pointer]
            - generic [ref=f1e242]:
              - generic [ref=f1e243]: Edit
              - button "Delete" [ref=f1e245] [cursor=pointer]
          - generic [ref=f1e250]:
            - generic [ref=f1e251]:
              - heading "Model" [level=3] [ref=f1e252]
              - generic [ref=f1e253]: TRUSS
            - generic [ref=f1e254]:
              - generic [ref=f1e255]:
                - text: Joints
                - strong [ref=f1e256]: "3"
              - generic [ref=f1e257]:
                - text: Members
                - strong [ref=f1e258]: "3"
              - generic [ref=f1e259]:
                - text: Supports
                - strong [ref=f1e260]: "0"
              - generic [ref=f1e261]:
                - text: Loads
                - strong [ref=f1e262]: "0"
            - paragraph [ref=f1e263]: Select a joint or member to inspect and edit its properties.
            - button "Clear All Model Elements" [ref=f1e264] [cursor=pointer]
      - generic [ref=f1e268]:
        - generic [ref=f1e269]:
          - generic [ref=f1e270]: UNSOLVABLE
          - generic [ref=f1e275]: "Statically indeterminate system: 6 equations vs 3 unknowns. Direct equilibrium requires a square determinate system."
        - generic [ref=f1e276]: 3 joints · 3 members · 0.00, 0.00
        - button "Clear Highlight" [ref=f1e278] [cursor=pointer]
```

# Test source

```ts
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
  484 |   await expect(actionCard).toBeVisible({ timeout: 10_000 })
  485 |   await expect(actionCard.locator('.classification-pill')).toBeVisible()
  486 |   await expect(actionCard.getByRole('button', { name: 'Fix with AI' })).toBeVisible()
  487 | 
  488 |   // Verify affected elements highlighting on canvas
  489 |   const affectedHighlights = page.locator('.issue-highlight-error, .issue-highlight-mechanism, .issue-highlight-warning, .joint-issue-pulse-ring')
  490 |   const highlightCount = await affectedHighlights.count()
> 491 |   expect(highlightCount).toBeGreaterThan(0)
      |                          ^ Error: expect(received).toBeGreaterThan(expected)
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
```