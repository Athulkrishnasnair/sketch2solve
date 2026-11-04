# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> geometry review saves, validates, explicitly reviews, solves, and reloads persisted results
- Location: tests/e2e/application.spec.js:309:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('DRAFT SAVED')
Expected: visible
Error: strict mode violation: getByText('DRAFT SAVED') resolved to 3 elements:
    1) <span class="review-state">…</span> aka getByText('Draft saved').first()
    2) <span class="draft-state">DRAFT SAVED</span> aka getByText('DRAFT SAVED', { exact: true })
    3) <span class="review-status-label">…</span> aka getByText('Draft saved').nth(2)

Call log:
  - Expect "toBeVisible" getByText('DRAFT SAVED') with timeout 8000ms
  - waiting for getByText('DRAFT SAVED')

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
        - generic [ref=e61]: "ANALYSIS #0C3A37E1"
      - generic [ref=e62]:
        - generic [ref=e63]:
          - generic [ref=e64]: ANALYSIS REVIEW
          - heading "workflow.png" [level=1] [ref=e65]
          - generic [ref=e66]:
            - generic [ref=e67]: Nov 2, 2026, 4:47 PM
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
          - generic [ref=e83]: Draft saved
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
                - /url: http://127.0.0.1:5174/api/analyses/0c3a37e1646d4290ab26e6f7b6e710ad/image
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
            - generic [ref=e241]: valid
          - generic [ref=e242]: No validation issues were saved.
      - generic [ref=e243]:
        - generic [ref=e244]:
          - generic [ref=e245]:
            - generic [ref=e246]: HUMAN-CORRECTED MODEL
            - heading "Geometry draft" [level=2] [ref=e247]
          - generic [ref=e248]:
            - button "Open Interactive Editor ↗" [ref=e249] [cursor=pointer]
            - generic [ref=e250]: DRAFT SAVED
        - paragraph [ref=e251]: AI output remains preserved above. Draft coordinates use physical length units and are separate from the AI's image-pixel coordinates. No unit or load value is inferred.
        - generic [ref=e252]:
          - generic [ref=e253]:
            - generic [ref=e254]:
              - strong [ref=e255]: Saved reviewer geometry
              - generic [ref=e256]: m · kN
            - generic [ref=e257]: 3 joints · 3 members
          - generic "Human geometry preview in its own model coordinate system" [ref=e258]:
            - img "Human-corrected draft geometry, drawn independently of the sketch image" [ref=e259]:
              - generic [ref=e260] [cursor=pointer]
              - generic [ref=e261] [cursor=pointer]
              - generic [ref=e262] [cursor=pointer]
              - generic [ref=e263] [cursor=pointer]
              - generic [ref=e264] [cursor=pointer]
            - generic [ref=e265]: Reviewer geometry preview · model units · not overlaid on image pixels
          - generic [ref=e266]:
            - button "J1 Joint · 0, 0 m" [ref=e267] [cursor=pointer]:
              - strong [ref=e268]: J1
              - generic [ref=e269]: Joint · 0, 0 m
            - button "J2 Joint · 4, 0 m" [ref=e270] [cursor=pointer]:
              - strong [ref=e271]: J2
              - generic [ref=e272]: Joint · 4, 0 m
            - button "J3 Joint · 2, 3 m" [ref=e273] [cursor=pointer]:
              - strong [ref=e274]: J3
              - generic [ref=e275]: Joint · 2, 3 m
            - button "M1 Member · J1 ↔ J2" [ref=e276] [cursor=pointer]:
              - strong [ref=e277]: M1
              - generic [ref=e278]: Member · J1 ↔ J2
            - button "M2 Member · J1 ↔ J3" [ref=e279] [cursor=pointer]:
              - strong [ref=e280]: M2
              - generic [ref=e281]: Member · J1 ↔ J3
            - button "M3 Member · J2 ↔ J3" [ref=e282] [cursor=pointer]:
              - strong [ref=e283]: M3
              - generic [ref=e284]: Member · J2 ↔ J3
            - button "S1 pin support · J1" [ref=e285] [cursor=pointer]:
              - strong [ref=e286]: S1
              - generic [ref=e287]: pin support · J1
            - button "S2 roller support · J2 · vertical" [ref=e288] [cursor=pointer]:
              - strong [ref=e289]: S2
              - generic [ref=e290]: roller support · J2 · vertical
            - button "L1 Load · J3 · Fx 0, Fy -10 kN" [ref=e291] [cursor=pointer]:
              - strong [ref=e292]: L1
              - generic [ref=e293]: Load · J3 · Fx 0, Fy -10 kN
        - generic [ref=e294]:
          - button "Edit saved draft" [ref=e295] [cursor=pointer]
          - button "Mark reviewed" [disabled] [ref=e296]
      - generic [ref=e297]:
        - generic [ref=e298]: i
        - generic [ref=e299]:
          - strong [ref=e300]: Engineering review boundary
          - paragraph [ref=e301]: Model validation checks the request schema and references; solver diagnostics are numerical checks. Neither establishes physical stability, code compliance, or engineering suitability. Review all dimensions and loads.
        - generic [ref=e302]: Draft saved
    - generic [ref=e304]:
      - generic [ref=e305]: Sketch2Solve · Local review workspace
      - generic [ref=e306]: Interpretation is a starting point, not a structural check.
```

# Test source

```ts
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
  274 |     await expect(page.getByRole('heading', { name: 'test3.png' })).toBeVisible()
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
> 341 |   await expect(page.getByText('DRAFT SAVED')).toBeVisible()
      |                                               ^ Error: expect(locator).toBeVisible() failed
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
```