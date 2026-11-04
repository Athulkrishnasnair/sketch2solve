# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> corrupt and unsupported uploads show clear messages and persist failed attempts
- Location: tests/e2e/application.spec.js:206:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('alert')
Expected substring: "Choose a JPEG, PNG, or WebP image."
Received string:    "!The saved image is not a supported format.UNSUPPORTED_IMAGE_TYPE · This attempt was saved to history. Retry only when you choose to submit another provider request."
Timeout: 8000ms

Call log:
  - Expect "toContainText" getByRole('alert') with timeout 8000ms
  - waiting for getByRole('alert')
    20 × locator resolved to <div role="alert" class="alert alert-error analysis-alert">…</div>
       - unexpected value "!The saved image is not a supported format.UNSUPPORTED_IMAGE_TYPE · This attempt was saved to history. Retry only when you choose to submit another provider request."

```

```yaml
- alert:
  - text: "!"
  - strong: The saved image is not a supported format.
  - paragraph: UNSUPPORTED_IMAGE_TYPE · This attempt was saved to history. Retry only when you choose to submit another provider request.
```

# Test source

```ts
  125 |       upload_success: true,
  126 |       http_status: response.status(),
  127 |       analysis_record_saved: Boolean(detail.analysis_id),
  128 |       original_image_retrieved: originalResponse.status() === 200,
  129 |       opencv_candidate_lines: detail.perception.lines.length,
  130 |       provider: detail.provider,
  131 |       provider_result: 'mock proposal returned; not a live interpretation',
  132 |       review_status: detail.review_status,
  133 |     })
  134 |   })
  135 | }
  136 | 
  137 | test('existing analysis details expose image, detection/proposal toggles, zoom, and review controls', async ({ page }) => {
  138 |   await page.goto('/?view=history')
  139 |   await expect(page.getByRole('button', { name: /test5\.png/ })).toBeVisible()
  140 |   await page.getByRole('button', { name: /test5\.png/ }).click()
  141 |   await expect(page.getByRole('heading', { name: 'test5.png' })).toBeVisible()
  142 | 
  143 |   await expect(page.getByRole('img', { name: 'Original uploaded truss sketch' })).toBeVisible()
  144 |   await expect(page.getByRole('img', { name: 'OpenCV candidate segments and endpoint clusters' })).toBeVisible()
  145 |   await expect(page.getByRole('img', { name: 'AI candidate joints, members, supports and loads' })).toBeVisible()
  146 |   await page.getByLabel('OpenCV detections').uncheck()
  147 |   await expect(page.getByRole('img', { name: 'OpenCV candidate segments and endpoint clusters' })).toHaveCount(0)
  148 |   await page.getByLabel('OpenCV detections').check()
  149 |   await page.getByLabel('AI proposal').uncheck()
  150 |   await expect(page.getByRole('img', { name: 'AI candidate joints, members, supports and loads' })).toHaveCount(0)
  151 |   await page.getByLabel('AI proposal').check()
  152 | 
  153 |   await page.getByRole('slider').fill('2')
  154 |   await expect(page.getByText('2.00×')).toBeVisible()
  155 |   await expect(page.getByRole('heading', { name: 'Geometry draft' })).toBeVisible()
  156 |   await expect(page.getByRole('button', { name: 'Correct interpretation' })).toBeEnabled()
  157 | })
  158 | 
  159 | test('history refreshes without breaking saved records', async ({ page }) => {
  160 |   await page.goto('/?view=history')
  161 |   await expect(page.getByRole('button', { name: /test1\.jpg/ })).toBeVisible()
  162 |   await page.getByRole('button', { name: 'Refresh history' }).click()
  163 |   await expect(page.getByRole('button', { name: /test1\.jpg/ })).toBeVisible()
  164 |   await expect(page.getByText(/saved records/)).toBeVisible()
  165 | })
  166 | 
  167 | test('history displays an understandable backend error', async ({ page }) => {
  168 |   expectHttpError(page, 503)
  169 |   await page.route('**/api/analyses?**', (route) => route.fulfill({
  170 |     status: 503,
  171 |     contentType: 'application/json',
  172 |     body: JSON.stringify({ error_code: 'ANALYSIS_HISTORY_UNAVAILABLE', message: 'History is temporarily unavailable.' }),
  173 |   }))
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
> 225 |   await expect(page.getByRole('alert')).toContainText('Choose a JPEG, PNG, or WebP image.')
      |                                         ^ Error: expect(locator).toContainText(expected) failed
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
```