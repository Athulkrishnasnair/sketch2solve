# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> geometry review saves, validates, explicitly reviews, solves, and reloads persisted results
- Location: tests/e2e/application.spec.js:309:1

# Error details

```
Error: expect(locator).toBeEnabled() failed

Locator:  getByRole('button', { name: 'Mark reviewed' })
Expected: enabled
Received: disabled
Timeout:  8000ms

Call log:
  - Expect "toBeEnabled" getByRole('button', { name: 'Mark reviewed' }) with timeout 8000ms
  - waiting for getByRole('button', { name: 'Mark reviewed' })
    20 × locator resolved to <button disabled type="button" class="button button-primary">Mark reviewed</button>
       - unexpected value "disabled"

```

```yaml
- button "Mark reviewed" [disabled]
```

# Test source

```ts
  242 |   await expect(page.getByRole('alert')).toContainText('larger than the 10 MiB upload limit')
  243 |   await expect(page.getByRole('button', { name: 'Start analysis' })).toBeDisabled()
  244 | 
  245 |   const response = await page.request.post('http://127.0.0.1:5101/api/analyses', {
  246 |     multipart: {
  247 |       provider: 'gemini',
  248 |       image: { name: 'over-limit.jpg', mimeType: 'image/jpeg', buffer: oversized },
  249 |     },
  250 |   })
  251 |   expect(response.status()).toBe(413)
  252 |   const body = await response.json()
  253 |   expect(body.error_code).toBe('IMAGE_TOO_LARGE')
  254 |   const saved = await page.request.get(`http://127.0.0.1:5101/api/analyses/${body.analysis_id}`)
  255 |   expect((await saved.json()).status).toBe('failed')
  256 | })
  257 | 
  258 | for (const [scenario, expectedMessage] of [
  259 |   ['MISSING_GEMINI_API_KEY', 'Gemini is selected, but its server-side credential is not configured.'],
  260 |   ['GEMINI_AUTHENTICATION_FAILED', 'Gemini rejected the backend credential or account access.'],
  261 |   ['GEMINI_RATE_LIMITED', 'Gemini rate limit or quota was reached. Try again later.'],
  262 |   ['GEMINI_TIMEOUT', 'The Gemini request timed out. Try again with a smaller image.'],
  263 |   ['GEMINI_NETWORK_ERROR', 'The backend could not reach Gemini. Check the backend network connection.'],
  264 |   ['INVALID_GEMINI_RESPONSE', 'Gemini returned an unexpected interpretation format.'],
  265 | ]) {
  266 |   test(`provider failure ${scenario} is saved and explained without secrets`, async ({ page }) => {
  267 |     await page.setExtraHTTPHeaders({ 'X-QA-Mock-Provider': scenario })
  268 |     await page.goto('/?view=new')
  269 |     const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  270 |     const { response, body } = await submitFile(page, { name: `${scenario}.png`, mimeType: 'image/png', buffer: bytes })
  271 |     expect(response.status()).not.toBe(201)
  272 |     expect(body.error_code).toBe(scenario)
  273 |     expect(JSON.stringify(body)).not.toContain('API_KEY=')
  274 |     await expect(page.getByRole('heading', { name: `${scenario}.png` })).toBeVisible()
  275 |     await expect(page.getByRole('alert')).toContainText(expectedMessage)
  276 |     const record = await page.request.get(`/api/analyses/${body.analysis_id}`)
  277 |     const detail = await record.json()
  278 |     expect(detail.status).toBe('failed')
  279 |     expect(detail.error_code).toBe(scenario)
  280 |     recordUploadResult({
  281 |       filename: `${scenario}.png`,
  282 |       size_bytes: bytes.length,
  283 |       detected_format: detail.mime_type,
  284 |       upload_success: false,
  285 |       http_status: response.status(),
  286 |       analysis_record_saved: true,
  287 |       original_image_retrieved: Boolean(detail.sketch.image_url),
  288 |       opencv_candidate_lines: detail.perception.lines.length,
  289 |       provider: detail.provider,
  290 |       provider_result: `documented mocked error ${scenario}`,
  291 |       review_status: detail.review_status,
  292 |     })
  293 |   })
  294 | }
  295 | 
  296 | test('empty proposal stays unapproved and visible as having no candidate elements', async ({ page }) => {
  297 |   await page.setExtraHTTPHeaders({ 'X-QA-Mock-Provider': 'EMPTY_PROPOSAL' })
  298 |   await page.goto('/?view=new')
  299 |   const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  300 |   const { response, body } = await submitFile(page, { name: 'empty-proposal.png', mimeType: 'image/png', buffer: bytes })
  301 |   expect(response.status()).toBe(201)
  302 |   expect(body.review_status).toBe('pending_review')
  303 |   expect(body.interpretation_proposal.joints).toEqual([])
  304 |   expect(body.interpretation_proposal.members).toEqual([])
  305 |   await expect(page.getByText('0 members')).toBeVisible()
  306 |   await expect(page.getByText('NOT SAVED')).toBeVisible()
  307 | })
  308 | 
  309 | test('geometry review saves, validates, explicitly reviews, solves, and reloads persisted results', async ({ page }) => {
  310 |   await page.goto('/?view=new')
  311 |   const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  312 |   const { response, body } = await submitFile(page, { name: 'workflow.png', mimeType: 'image/png', buffer: bytes })
  313 |   expect(response.status()).toBe(201)
  314 |   expect(body.review_status).toBe('pending_review')
  315 |   await expect(page.getByText('NOT SAVED')).toBeVisible()
  316 |   await expect(page.getByRole('button', { name: 'Mark reviewed' })).toHaveCount(0)
  317 |   const editButton = page.getByRole('button', { name: 'Correct interpretation' })
  318 |   await expect(editButton).toBeEnabled()
  319 |   expect(body.interpretation_proposal.proposal_only).toBe(true)
  320 | 
  321 |   await editButton.click()
  322 |   await expect(page.getByRole('heading', { name: 'Joints' })).toBeVisible()
  323 |   await page.getByLabel('Length unit').selectOption('m')
  324 |   await page.getByLabel('Force unit').selectOption('kN')
  325 | 
  326 |   const nodeRows = page.locator('.node-form-row')
  327 |   for (const [index, [x, y]] of [[0, 0], [4, 0], [2, 3]].entries()) {
  328 |     await nodeRows.nth(index).locator('input').nth(1).fill(String(x))
  329 |     await nodeRows.nth(index).locator('input').nth(2).fill(String(y))
  330 |   }
  331 |   const supportSection = page.locator('.form-collection').nth(2)
  332 |   await supportSection.getByLabel('Joint').nth(0).selectOption('J1')
  333 |   await supportSection.getByLabel('Joint').nth(1).selectOption('J2')
  334 |   await supportSection.getByLabel('Direction').selectOption('vertical')
  335 |   const loadSection = page.locator('.form-collection').nth(3)
  336 |   await loadSection.getByLabel('Joint').selectOption('J3')
  337 |   await loadSection.getByLabel('Fx kN').fill('0')
  338 |   await loadSection.getByLabel('Fy kN').fill('-10')
  339 |   await page.getByRole('checkbox', { name: /I replaced or verified every joint coordinate/ }).check()
  340 |   await page.getByRole('button', { name: 'Validate and save draft' }).click()
  341 |   await expect(page.locator('.draft-state').filter({ hasText: 'DRAFT SAVED' })).toBeVisible()
> 342 |   await expect(page.getByRole('button', { name: 'Mark reviewed' })).toBeEnabled()
      |                                                                     ^ Error: expect(locator).toBeEnabled() failed
  343 |   const savedBeforeReview = await page.request.get(`/api/analyses/${body.analysis_id}`)
  344 |   const unreviewedDetail = await savedBeforeReview.json()
  345 |   expect(unreviewedDetail.review_status).toBe('draft')
  346 |   expect(unreviewedDetail.interpretation_proposal.proposal_only).toBe(true)
  347 |   expect(unreviewedDetail.solver_results).toBeNull()
  348 | 
  349 |   await page.getByRole('button', { name: 'Mark reviewed' }).click()
  350 |   await expect(page.getByText('REVIEWED')).toBeVisible()
  351 |   page.once('dialog', (dialog) => dialog.accept())
  352 |   await page.getByRole('button', { name: 'Submit reviewed geometry to solver' }).click()
  353 |   await expect(page.getByText('SUBMITTED')).toBeVisible()
  354 |   await expect(page.getByText('Solver results')).toBeVisible()
  355 | 
  356 |   await page.reload()
  357 |   await expect(page.getByRole('heading', { name: 'workflow.png' })).toBeVisible()
  358 |   await expect(page.getByText('SUBMITTED')).toBeVisible()
  359 |   const persisted = await page.request.get(`/api/analyses/${body.analysis_id}`)
  360 |   const detail = await persisted.json()
  361 |   expect(detail.review_status).toBe('submitted')
  362 |   expect(detail.human_review.geometry.model.nodes).toHaveLength(3)
  363 |   expect(detail.solver_results.member_forces).toHaveProperty('M1')
  364 |   expect(detail.interpretation_proposal.proposal_only).toBe(true)
  365 | })
  366 | 
  367 | test('invalid geometry, missing units, and solver failures preserve the unapproved or reviewed draft', async ({ page }) => {
  368 |   const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  369 |   const created = await page.request.post('/api/analyses', {
  370 |     multipart: { provider: 'gemini', image: { name: 'validation.png', mimeType: 'image/png', buffer: bytes } },
  371 |   })
  372 |   const analysis = await created.json()
  373 |   expect(analysis.review_status).toBe('pending_review')
  374 |   const draftUrl = `/api/analyses/${analysis.analysis_id}/draft`
  375 |   const solveUrl = `/api/analyses/${analysis.analysis_id}/solve`
  376 | 
  377 |   const unconfirmed = await page.request.put(draftUrl, {
  378 |     data: { geometry: {}, coordinates_confirmed: false },
  379 |   })
  380 |   expect(unconfirmed.status()).toBe(422)
  381 |   expect((await unconfirmed.json()).error_code).toBe('COORDINATES_NOT_CONFIRMED')
  382 |   expect((await page.request.post(solveUrl)).status()).toBe(409)
  383 | 
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
```