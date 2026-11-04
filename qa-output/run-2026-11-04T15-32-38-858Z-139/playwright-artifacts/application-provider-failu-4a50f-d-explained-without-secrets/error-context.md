# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> provider failure MISSING_GEMINI_API_KEY is saved and explained without secrets
- Location: tests/e2e/application.spec.js:266:3

# Error details

```
Test timeout of 45000ms exceeded.
```

```
Error: apiRequestContext.get: Test timeout of 45000ms exceeded.
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
      - button "Natural Language Design" [ref=e26] [cursor=pointer]
      - button "New analysis" [ref=e32] [cursor=pointer]
      - button "Analysis history 1" [ref=e36] [cursor=pointer]:
        - generic [ref=e42]: Analysis history
        - generic [ref=e43]: "1"
    - generic [ref=e49]:
      - strong [ref=e50]: Private by default
      - paragraph [ref=e51]: Runs stay in your local backend. Don’t expose this workspace publicly.
    - generic [ref=e52]: Backend API · localhost:5000
  - main [ref=e54]:
    - generic [ref=e55]:
      - generic [ref=e56]:
        - generic [ref=e57]: Workspace
        - generic [ref=e58]: /
        - strong [ref=e59]: Analysis review
      - generic [ref=e60]:
        - generic [ref=e61]: LOCAL ONLY
        - generic [aria-hidden] [ref=e63]: S
    - generic [ref=e64]:
      - generic [ref=e65]:
        - button "← Analysis history" [ref=e66] [cursor=pointer]
        - generic [ref=e67]: "ANALYSIS #2D92ECDD"
      - generic [ref=e68]:
        - generic [ref=e69]:
          - generic [ref=e70]: ANALYSIS REVIEW
          - heading "MISSING_GEMINI_API_KEY.png" [level=1] [ref=e71]
          - generic [ref=e72]:
            - generic [ref=e73]: Nov 4, 2026, 3:33 PM
            - generic [ref=e75]: 1024 × 515 px
            - generic [ref=e77]: gemini · gemini-3.1-flash-lite
        - generic [ref=e78]:
          - button "Edit geometry" [ref=e79] [cursor=pointer]
          - generic [ref=e82]: Failed
      - alert [ref=e84]:
        - generic [ref=e85]: "!"
        - generic [ref=e86]:
          - strong [ref=e87]: Gemini is selected, but its server-side credential is not configured.
          - paragraph [ref=e88]: MISSING_GEMINI_API_KEY · This attempt was saved to history. Retry only when you choose to submit another provider request.
        - button "Retry analysis" [ref=e89] [cursor=pointer]
      - generic [ref=e90]:
        - generic [ref=e91]:
          - generic [ref=e92]:
            - generic [ref=e93]: SIDE-BY-SIDE EVIDENCE
            - heading "Compare the readings" [level=2] [ref=e94]
          - generic [ref=e95]: Pending review
        - generic "Visualization controls" [ref=e97]:
          - generic [ref=e98] [cursor=pointer]:
            - checkbox "OpenCV detections" [checked] [ref=e99]
            - text: OpenCV detections
          - generic [ref=e100] [cursor=pointer]:
            - checkbox "Endpoint clusters" [ref=e101]
            - text: Endpoint clusters
          - generic [ref=e102] [cursor=pointer]:
            - checkbox "AI proposal" [checked] [ref=e103]
            - text: AI proposal
          - generic [ref=e104] [cursor=pointer]:
            - checkbox "Element IDs" [ref=e105]
            - text: Element IDs
          - generic [ref=e106] [cursor=pointer]:
            - text: Zoom
            - slider "Zoom 1.00×" [ref=e107]: "1"
            - generic [ref=e108]: 1.00×
        - generic [ref=e109]:
          - article [ref=e110]:
            - generic [ref=e111]:
              - generic [ref=e112]:
                - generic [ref=e113]: A
                - generic [ref=e114]:
                  - strong [ref=e115]: Original sketch
                  - generic [ref=e116]: Uploaded source
              - link "Open original image" [ref=e117] [cursor=pointer]:
                - /url: http://127.0.0.1:5175/api/analyses/2d92ecdd760b4d8cb4111291e9bc3000/image
                - text: ↗
            - img "Original uploaded truss sketch" [ref=e119]
            - generic [ref=e120]:
              - generic [ref=e121]: image/png
              - generic [ref=e122]: 1024 × 515 px
          - article [ref=e123]:
            - generic [ref=e124]:
              - generic [ref=e125]:
                - generic [ref=e126]: B
                - generic [ref=e127]:
                  - strong [ref=e128]: OpenCV detections
                  - generic [ref=e129]: Visual evidence only
              - generic [ref=e130]: 76 segments
            - generic [ref=e131]:
              - img "Sketch under OpenCV detections" [ref=e132]
              - img "OpenCV candidate segments and endpoint clusters" [ref=e133]:
                - button [ref=e134]
                - button [ref=e135]
                - button [ref=e136]
                - button [ref=e137]
                - button [ref=e138]
                - button [ref=e139]
                - button [ref=e140]
                - button [ref=e141]
                - button
                - button
                - button
                - button [ref=e142]
                - button
                - button [ref=e143]
                - button [ref=e144]
                - button [ref=e145]
                - button
                - button [ref=e146]
                - button
                - button [ref=e147]
                - button [ref=e148]
                - button
                - button
                - button [ref=e149]
                - button
                - button [ref=e150]
                - button [ref=e151]
                - button [ref=e152]
                - button [ref=e153]
                - button
                - button
                - button [ref=e154]
                - button
                - button [ref=e155]
                - button
                - button [ref=e156]
                - button
                - button
                - button [ref=e157]
                - button [ref=e158]
                - button [ref=e159]
                - button [ref=e160]
                - button [ref=e161]
                - button [ref=e162]
                - button
                - button
                - button [ref=e163]
                - button [ref=e164]
                - button [ref=e165]
                - button [ref=e166]
                - button [ref=e167]
                - button
                - button [ref=e168]
                - button
                - button
                - button [ref=e169]
                - button
                - button
                - button [ref=e170]
                - button [ref=e171]
                - button
                - button [ref=e172]
                - button [ref=e173]
                - button
                - button [ref=e174]
                - button [ref=e175]
                - button [ref=e176]
                - button [ref=e177]
                - button [ref=e178]
                - button [ref=e179]
                - button [ref=e180]
                - button [ref=e181]
                - button
                - button [ref=e182]
                - button [ref=e183]
                - button [ref=e184]
            - generic [ref=e185]:
              - generic [ref=e186]: Candidate line
              - generic [ref=e188]: Endpoint cluster
          - article [ref=e190]:
            - generic [ref=e192]:
              - generic [ref=e193]: C
              - generic [ref=e194]:
                - strong [ref=e195]: AI-proposed geometry
                - generic [ref=e196]: No proposal available
            - generic [ref=e197]:
              - img "Sketch under AI-proposed geometry" [ref=e198]
              - generic [ref=e199]: Interpretation did not complete.
            - generic [ref=e200]:
              - generic [ref=e201]: Proposed member
              - generic [ref=e203]: Proposed joint
      - generic [ref=e205]:
        - generic [ref=e206]:
          - generic [ref=e208]:
            - generic [ref=e209]: MODEL OUTPUT
            - heading "Interpretation proposal" [level=2] [ref=e210]
          - generic [ref=e211]: No candidate interpretation is available for this run.
        - generic [ref=e212]:
          - generic [ref=e213]:
            - generic [ref=e214]:
              - generic [ref=e215]: CHECKS & DIAGNOSTICS
              - heading "Validation state" [level=2] [ref=e216]
            - generic [ref=e217]: NOT RUN
          - paragraph [ref=e218]: Candidate geometry has not been converted into a solver model. Nothing is approved or solved from this proposal.
      - generic [ref=e219]:
        - generic [ref=e220]: i
        - generic [ref=e221]:
          - strong [ref=e222]: Engineering review boundary
          - paragraph [ref=e223]: Model validation checks the request schema and references; solver diagnostics are numerical checks. Neither establishes physical stability, code compliance, or engineering suitability. Review all dimensions and loads.
        - generic [ref=e224]: Pending review
    - generic [ref=e226]:
      - generic [ref=e227]: Sketch2Solve · Local review workspace
      - generic [ref=e228]: Interpretation is a starting point, not a structural check.
```

# Test source

```ts
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
  225 |   await expect(page.getByRole('alert')).toContainText(/Choose a JPEG, PNG, or WebP image|The saved image is not a supported format/)
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
  274 |     await expect(page.getByRole('heading', { name: `${scenario}.png` })).toBeVisible()
  275 |     await expect(page.getByRole('alert')).toContainText(expectedMessage)
> 276 |     const record = await page.request.get(`/api/analyses/${body.analysis_id}`)
      |                                       ^ Error: apiRequestContext.get: Test timeout of 45000ms exceeded.
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
  342 |   await expect(page.getByRole('button', { name: 'Mark reviewed' })).toBeEnabled()
  343 |   const savedBeforeReview = await page.request.get(`/api/analyses/${body.analysis_id}`)
  344 |   const unreviewedDetail = await savedBeforeReview.json()
  345 |   expect(unreviewedDetail.review_status).toBe('draft')
  346 |   expect(unreviewedDetail.interpretation_proposal.proposal_only).toBe(true)
  347 |   expect(unreviewedDetail.solver_results).toBeNull()
  348 | 
  349 |   await page.getByRole('button', { name: 'Mark reviewed' }).click()
  350 |   await expect(page.locator('.draft-state').filter({ hasText: 'REVIEWED' })).toBeVisible()
  351 |   page.once('dialog', (dialog) => dialog.accept())
  352 |   await page.getByRole('button', { name: 'Submit reviewed geometry to solver' }).click()
  353 |   await expect(page.locator('.draft-state').filter({ hasText: 'SUBMITTED' })).toBeVisible()
  354 |   await expect(page.getByText('Solver results')).toBeVisible()
  355 | 
  356 |   await page.reload()
  357 |   await expect(page.getByRole('heading', { name: 'workflow.png' })).toBeVisible()
  358 |   await expect(page.locator('.draft-state').filter({ hasText: 'SUBMITTED' })).toBeVisible()
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
```