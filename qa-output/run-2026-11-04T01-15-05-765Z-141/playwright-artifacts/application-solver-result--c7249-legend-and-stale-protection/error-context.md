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

Locator: locator('.analysis-results-panel')
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.analysis-results-panel') with timeout 8000ms
  - waiting for locator('.analysis-results-panel')

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
  - strong: Triangular Reference Truss
  - text: "#3E6CFE0C submitted"
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
  - checkbox "Coords Confirmed" [checked]
  - text: Coords Confirmed
  - button "Saved"
  - button "Mark Reviewed"
  - button "Solve" [disabled]
  - button "Results"
  - button "Design with AI"
  - toolbar "Canvas view controls":
    - button "Zoom in"
    - button "Zoom out"
    - button "Fit content to view"
    - separator
    - button "Toggle grid" [pressed]
    - button "Snap to grid" [pressed]
    - button "Toggle AI proposal layer" [pressed]
    - separator
    - button "Hide member force labels" [pressed]
    - button "Toggle Analysis Results panel"
  - text: "Forces Legend Tension (+) Compression (−) Zero-Force (0) Reaction (R) X: 1.147 m · Y: 3.748 m"
  - img: "(0,0) AB +3.33 kN AC -6.01 kN BC -6.01 kN Ry: +5.00 kN Ry: +5.00 kN L_C: -10 kN A B C"
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
    - heading "Model" [level=3]
    - text: TRUSS Joints
    - strong: "3"
    - text: Members
    - strong: "3"
    - text: Supports
    - strong: "2"
    - text: Loads
    - strong: "1"
    - paragraph: Select a joint or member to inspect and edit its properties.
    - button "Clear All Model Elements"
  - text: SOLVED Analysis complete — results available 3 joints · 3 members · 1.15, 3.75
```

```
Error: uncaught browser errors

expect(received).toEqual(expected) // deep equality

- Expected  - 1
+ Received  + 4

- Array []
+ Array [
+   "nextTick is not defined",
+   "nextTick is not defined",
+ ]
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
  30  |   await page.locator('input[type="file"]').setInputFiles({ name, mimeType, buffer })
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
> 60  |   expect(events.pageErrors, 'uncaught browser errors').toEqual([])
      |                                                        ^ Error: uncaught browser errors
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
```