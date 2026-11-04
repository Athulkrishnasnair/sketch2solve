# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> contextual on-canvas issue highlighting, floating action card, and AI repair workflow
- Location: tests/e2e/application.spec.js:469:1

# Error details

```
Test timeout of 45000ms exceeded.
```

```
Error: locator.setInputFiles: Test timeout of 45000ms exceeded.
Call log:
  - waiting for locator('input[type="file"]')

```

# Test source

```ts
  1   | import { expect, test } from '@playwright/test'
  2   | import { readFileSync, readdirSync, statSync, writeFileSync, existsSync } from 'node:fs'
  3   | import path from 'node:path'
  4   | import { fileURLToPath } from 'node:url'
  5   | 
  6   | const testDirectory = path.dirname(fileURLToPath(import.meta.url))
  7   | const repositoryDirectory = path.resolve(testDirectory, '../../..')
  8   | const evaluationDirectory = path.join(repositoryDirectory, 'backend/evaluation/sketches')
  9   | const evaluationImages = readdirSync(evaluationDirectory)
  10  |   .filter((name) => /\.(?:png|jpe?g)$/i.test(name))
  11  |   .sort()
  12  | const telemetry = new WeakMap()
  13  | const resultFile = path.join(process.env.QA_OUTPUT_DIR, 'upload-results.json')
  14  | 
  15  | function expectFailedRequest(page, urlPart) {
  16  |   telemetry.get(page).expectedFailedRequests.push(urlPart)
  17  | }
  18  | 
  19  | function expectHttpError(page, status) {
  20  |   telemetry.get(page).expectedHttpErrors.add(status)
  21  | }
  22  | 
  23  | function recordUploadResult(result) {
  24  |   const previous = existsSync(resultFile) ? JSON.parse(readFileSync(resultFile, 'utf8')) : []
  25  |   previous.push(result)
  26  |   writeFileSync(resultFile, `${JSON.stringify(previous, null, 2)}\n`)
  27  | }
  28  | 
  29  | async function submitFile(page, { name, mimeType, buffer }) {
> 30  |   await page.locator('input[type="file"]').setInputFiles({ name, mimeType, buffer })
      |   ^ Error: locator.setInputFiles: Test timeout of 45000ms exceeded.
  31  |   await expect(page.getByRole('button', { name: 'Start analysis' })).toBeEnabled()
  32  |   const responsePromise = page.waitForResponse((response) =>
  33  |     response.request().method() === 'POST' && new URL(response.url()).pathname === '/api/analyses',
  34  |   )
  35  |   await page.getByRole('button', { name: 'Start analysis' }).click()
  36  |   const response = await responsePromise
  37  |   if (response.status() >= 400) expectHttpError(page, response.status())
  38  |   return { response, body: await response.json() }
  39  | }
  40  | 
  41  | test.beforeEach(async ({ page }) => {
  42  |   const events = {
  43  |     pageErrors: [],
  44  |     consoleErrors: [],
  45  |     failedRequests: [],
  46  |     expectedFailedRequests: [],
  47  |     expectedConsoleErrors: [],
  48  |     expectedHttpErrors: new Set(),
  49  |   }
  50  |   telemetry.set(page, events)
  51  |   page.on('pageerror', (error) => events.pageErrors.push(error.message))
  52  |   page.on('console', (message) => {
  53  |     if (message.type() === 'error') events.consoleErrors.push(message.text())
  54  |   })
  55  |   page.on('requestfailed', (request) => events.failedRequests.push(request.url()))
  56  | })
  57  | 
  58  | test.afterEach(async ({ page }) => {
  59  |   const events = telemetry.get(page)
  60  |   expect(events.pageErrors, 'uncaught browser errors').toEqual([])
  61  |   const unexpectedConsoleErrors = events.consoleErrors.filter((message) =>
  62  |     !events.expectedConsoleErrors.some((expected) => message.includes(expected))
  63  |       && ![...events.expectedHttpErrors].some((status) =>
  64  |         message.includes(`status of ${status}`) || message.includes(`status code ${status}`),
  65  |       ),
  66  |   )
  67  |   expect(unexpectedConsoleErrors, 'unexpected browser console errors').toEqual([])
  68  |   const unexpectedFailures = events.failedRequests.filter((url) =>
  69  |     !events.expectedFailedRequests.some((expected) => url.includes(expected)),
  70  |   )
  71  |   expect(unexpectedFailures, 'unexpected failed network requests').toEqual([])
  72  | })
  73  | 
  74  | test('health endpoint, dashboard, and primary navigation load', async ({ page }) => {
  75  |   const health = await page.request.get('/api/health')
  76  |   expect(health.status()).toBe(200)
  77  |   expect(await health.json()).toMatchObject({ status: 'ok', application: 'Sketch2Solve' })
  78  | 
  79  |   await page.goto('/')
  80  |   await expect(page.getByRole('heading', { name: /Sketch review/ })).toBeVisible()
  81  |   await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible()
  82  | 
  83  |   const navigation = page.getByRole('navigation', { name: 'Main navigation' })
  84  |   await navigation.getByRole('button', { name: 'New analysis' }).click()
  85  |   await expect(page.getByRole('heading', { name: /Review a structure/ })).toBeVisible()
  86  |   await navigation.getByRole('button', { name: 'Analysis history' }).click()
  87  |   await expect(page.getByRole('heading', { name: 'Analysis history' })).toBeVisible()
  88  | })
  89  | 
  90  | for (const filename of evaluationImages) {
  91  |   test(`uploads evaluation sketch ${filename} through the UI`, async ({ page }) => {
  92  |     const filePath = path.join(evaluationDirectory, filename)
  93  |     const bytes = readFileSync(filePath)
  94  |     await page.goto('/?view=new')
  95  |     const { response, body } = await submitFile(page, {
  96  |       name: filename,
  97  |       mimeType: /\.png$/i.test(filename) ? 'image/png' : 'image/jpeg',
  98  |       buffer: bytes,
  99  |     })
  100 | 
  101 |     expect(response.status()).toBe(201)
  102 |     expect(body.status).toBe('pending_review')
  103 |     expect(body.review_status).toBe('pending_review')
  104 |     expect(body.interpretation_proposal.proposal_only).toBe(true)
  105 |     await expect(page.getByRole('heading', { name: filename })).toBeVisible()
  106 |     await expect(page.getByText('AI-proposed geometry')).toBeVisible()
  107 | 
  108 |     const detailResponse = await page.request.get(`/api/analyses/${body.analysis_id}`)
  109 |     expect(detailResponse.status()).toBe(200)
  110 |     const detail = await detailResponse.json()
  111 |     const originalResponse = await page.request.get(detail.sketch.image_url)
  112 |     expect(originalResponse.status()).toBe(200)
  113 |     expect(originalResponse.headers()['content-type']).toContain(detail.mime_type)
  114 |     expect(Buffer.from(await originalResponse.body())).toEqual(bytes)
  115 |     expect(detail.perception.lines.length).toBeGreaterThan(0)
  116 | 
  117 |     const originalImage = page.getByRole('img', { name: 'Original uploaded truss sketch' })
  118 |     await expect(originalImage).toBeVisible()
  119 |     await expect.poll(() => originalImage.evaluate((image) => image.naturalWidth)).toBeGreaterThan(0)
  120 | 
  121 |     recordUploadResult({
  122 |       filename,
  123 |       size_bytes: statSync(filePath).size,
  124 |       detected_format: detail.mime_type,
  125 |       upload_success: true,
  126 |       http_status: response.status(),
  127 |       analysis_record_saved: Boolean(detail.analysis_id),
  128 |       original_image_retrieved: originalResponse.status() === 200,
  129 |       opencv_candidate_lines: detail.perception.lines.length,
  130 |       provider: detail.provider,
```