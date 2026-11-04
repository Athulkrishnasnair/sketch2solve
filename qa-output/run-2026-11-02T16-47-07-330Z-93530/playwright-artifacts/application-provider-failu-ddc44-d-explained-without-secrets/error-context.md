# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> provider failure GEMINI_AUTHENTICATION_FAILED is saved and explained without secrets
- Location: tests/e2e/application.spec.js:266:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: 'test3.png' })
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('heading', { name: 'test3.png' }) with timeout 8000ms
  - waiting for getByRole('heading', { name: 'test3.png' })

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
    - button "Analysis history 1"
  - strong: Private by default
  - paragraph: Runs stay in your local backend. Don’t expose this workspace publicly.
  - text: Backend API · localhost:5000
- main:
  - text: Workspace /
  - strong: Analysis review
  - text: LOCAL ONLY
  - button "← Analysis history"
  - text: "ANALYSIS #F1E05254 ANALYSIS REVIEW"
  - heading "GEMINI_AUTHENTICATION_FAILED.png" [level=1]
  - text: Nov 2, 2026, 4:47 PM 1024 × 515 px gemini · gemini-3.1-flash-lite
  - button "Edit geometry":
    - img
    - text: Edit geometry
  - text: Failed
  - alert:
    - text: "!"
    - strong: Gemini rejected the backend credential or account access.
    - paragraph: GEMINI_AUTHENTICATION_FAILED · This attempt was saved to history. Retry only when you choose to submit another provider request.
    - button "Retry analysis"
  - text: SIDE-BY-SIDE EVIDENCE
  - heading "Compare the readings" [level=2]
  - text: Pending review
  - checkbox "OpenCV detections" [checked]
  - text: OpenCV detections
  - checkbox "Endpoint clusters"
  - text: Endpoint clusters
  - checkbox "AI proposal" [checked]
  - text: AI proposal
  - checkbox "Element IDs"
  - text: Element IDs Zoom
  - slider "Zoom 1.00×": "1"
  - text: 1.00×
  - article:
    - text: A
    - strong: Original sketch
    - text: Uploaded source
    - link "Open original image":
      - /url: http://127.0.0.1:5174/api/analyses/f1e05254d68843cb8e9fdc27502daa09/image
      - text: ↗
    - img "Original uploaded truss sketch"
    - text: image/png 1024 × 515 px
  - article:
    - text: B
    - strong: OpenCV detections
    - text: Visual evidence only 76 segments
    - img "Sketch under OpenCV detections"
    - img "OpenCV candidate segments and endpoint clusters":
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
      - button
    - text: Candidate line Endpoint cluster
  - article:
    - text: C
    - strong: AI-proposed geometry
    - text: No proposal available
    - img "Sketch under AI-proposed geometry"
    - text: Interpretation did not complete. Proposed member Proposed joint
  - text: MODEL OUTPUT
  - heading "Interpretation proposal" [level=2]
  - text: No candidate interpretation is available for this run. CHECKS & DIAGNOSTICS
  - heading "Validation state" [level=2]
  - text: NOT RUN
  - paragraph: Candidate geometry has not been converted into a solver model. Nothing is approved or solved from this proposal.
  - text: i
  - strong: Engineering review boundary
  - paragraph: Model validation checks the request schema and references; solver diagnostics are numerical checks. Neither establishes physical stability, code compliance, or engineering suitability. Review all dimensions and loads.
  - text: Pending review Sketch2Solve · Local review workspace Interpretation is a starting point, not a structural check.
```

# Test source

```ts
  174 |   await page.goto('/?view=history')
  175 |   await expect(page.getByRole('alert')).toContainText('History could not be loaded')
  176 |   await expect(page.getByRole('alert')).toContainText('History is temporarily unavailable.')
  177 | })
  178 | 
  179 | test('valid WebP uploads and misleading extension is resolved from image bytes', async ({ page }) => {
  180 |   await page.goto('/?view=new')
  181 |   const webpDataUrl = await page.evaluate(() => {
  182 |     const canvas = document.createElement('canvas')
  183 |     canvas.width = 32
  184 |     canvas.height = 24
  185 |     const context = canvas.getContext('2d')
  186 |     context.fillStyle = '#222'
  187 |     context.beginPath()
  188 |     context.moveTo(2, 22)
  189 |     context.lineTo(16, 2)
  190 |     context.lineTo(30, 22)
  191 |     context.stroke()
  192 |     return canvas.toDataURL('image/webp')
  193 |   })
  194 |   const webp = Buffer.from(webpDataUrl.split(',')[1], 'base64')
  195 |   const webpResult = await submitFile(page, { name: 'browser-generated.webp', mimeType: 'image/webp', buffer: webp })
  196 |   expect(webpResult.response.status()).toBe(201)
  197 |   expect(webpResult.body.mime_type).toBe('image/webp')
  198 | 
  199 |   await page.goto('/?view=new')
  200 |   const png = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  201 |   const mislabeled = await submitFile(page, { name: 'misleading.jpg', mimeType: 'image/jpeg', buffer: png })
  202 |   expect(mislabeled.response.status()).toBe(201)
  203 |   expect(mislabeled.body.mime_type).toBe('image/png')
  204 | })
  205 | 
  206 | test('corrupt and unsupported uploads show clear messages and persist failed attempts', async ({ page }) => {
  207 |   await page.goto('/?view=new')
  208 |   const corrupt = Buffer.concat([
  209 |     Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
  210 |     Buffer.alloc(20),
  211 |   ])
  212 |   const corrupted = await submitFile(page, { name: 'corrupted.png', mimeType: 'image/png', buffer: corrupt })
  213 |   expect(corrupted.response.status()).toBe(422)
  214 |   expect(corrupted.body.error_code).toBe('INVALID_IMAGE')
  215 |   await expect(page.getByRole('alert')).toContainText('could not be read as a supported sketch image')
  216 | 
  217 |   await page.goto('/?view=new')
  218 |   const unsupported = await submitFile(page, {
  219 |     name: 'unsupported.txt',
  220 |     mimeType: 'text/plain',
  221 |     buffer: Buffer.from('not an image'),
  222 |   })
  223 |   expect(unsupported.response.status()).toBe(415)
  224 |   expect(unsupported.body.error_code).toBe('UNSUPPORTED_IMAGE_TYPE')
  225 |   await expect(page.getByRole('alert')).toContainText('Choose a JPEG, PNG, or WebP image.')
  226 | 
  227 |   for (const body of [corrupted.body, unsupported.body]) {
  228 |     const saved = await page.request.get(`/api/analyses/${body.analysis_id}`)
  229 |     expect(saved.status()).toBe(200)
  230 |     expect((await saved.json()).status).toBe('failed')
  231 |   }
  232 | })
  233 | 
  234 | test('oversized UI upload is blocked and backend limit returns a recorded 413', async ({ page }) => {
  235 |   await page.goto('/?view=new')
  236 |   const oversized = Buffer.alloc(10 * 1024 * 1024 + 1)
  237 |   await page.locator('input[type="file"]').setInputFiles({
  238 |     name: 'over-limit.jpg',
  239 |     mimeType: 'image/jpeg',
  240 |     buffer: oversized,
  241 |   })
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
> 274 |     await expect(page.getByRole('heading', { name: 'test3.png' })).toBeVisible()
      |                                                                    ^ Error: expect(locator).toBeVisible() failed
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
  341 |   await expect(page.getByText('DRAFT SAVED')).toBeVisible()
  342 |   await expect(page.getByRole('button', { name: 'Mark reviewed' })).toBeEnabled()
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
```