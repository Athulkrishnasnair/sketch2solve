# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: application.spec.js >> Conversational natural-language truss design workflows across dashboard, sidebar studio, and editor
- Location: tests/e2e/application.spec.js:784:1

# Error details

```
Test timeout of 45000ms exceeded.
```

```
Error: unexpected browser console errors

expect(received).toEqual(expected) // deep equality

- Expected  - 1
+ Received  + 3

- Array []
+ Array [
+   "Failed to load resource: the server responded with a status of 400 (BAD REQUEST)",
+ ]
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
        - generic [ref=e57]:
          - button "Back" [ref=e58] [cursor=pointer]
          - generic:
            - strong: Triangular Truss
            - generic:
              - text: "#CB6F4FC5"
              - generic [ref=e62]: draft
        - generic [ref=e63]:
          - button "Undo (Ctrl+Z)" [disabled] [ref=e64]
          - button "Redo (Ctrl+Y)" [disabled] [ref=e68]
          - generic [ref=e73]:
            - generic [ref=e74]: Length
            - combobox [ref=e75] [cursor=pointer]:
              - option "m" [selected]
              - option "mm"
              - option "ft"
            - generic [ref=e76]: Force
            - combobox [ref=e77] [cursor=pointer]:
              - option "kN" [selected]
              - option "N"
              - option "lbf"
          - generic [ref=e78] [cursor=pointer]:
            - checkbox "Coords Confirmed" [checked] [ref=e79]
            - generic [ref=e80]: Coords Confirmed
        - generic [ref=e81]:
          - button "Saved" [ref=e82] [cursor=pointer]
          - button "Mark Reviewed" [ref=e88] [cursor=pointer]
          - button "Solve" [disabled] [ref=e92]
          - button "Design with AI" [ref=e97] [cursor=pointer]
      - generic [ref=e102]:
        - generic [ref=e103]:
          - generic [ref=e104]:
            - button "Zoom In" [ref=e105] [cursor=pointer]
            - button "Zoom Out" [ref=e109] [cursor=pointer]
            - button "Fit Content" [ref=e113] [cursor=pointer]
            - button "Toggle Grid" [ref=e120] [cursor=pointer]
            - button "Snap to Grid" [ref=e123] [cursor=pointer]
            - button "AI Proposal Layer" [ref=e128] [cursor=pointer]
          - generic: "X: 5.933 m · Y: -0.616 m"
          - img [ref=e132]:
            - generic [ref=e134]: (0,0)
            - generic [ref=e137]:
              - generic [ref=e138]: M1
              - generic [ref=e140]:
                - generic [ref=e141] [cursor=pointer]
                - generic [ref=e142] [cursor=pointer]: M2
              - generic [ref=e143]:
                - generic [ref=e144] [cursor=pointer]
                - generic [ref=e145] [cursor=pointer]: M3
            - generic [ref=e153]: "L1: -10 kN"
            - generic [ref=e156]:
              - generic [ref=e157]:
                - generic [ref=e158] [cursor=pointer]
                - generic: J1
              - generic [ref=e159]:
                - generic [ref=e160] [cursor=pointer]
                - generic: J2
              - generic [ref=e161]:
                - generic [ref=e162] [cursor=pointer]
                - generic: J3
            - generic [ref=e163]: +M4
          - generic [ref=e165]:
            - generic [ref=e166]:
              - generic [ref=e167]:
                - strong [ref=e171]: Design with AI
                - generic [ref=e172]: Context Aware
              - button "Close Assistant" [ref=e173] [cursor=pointer]: ✕
            - generic [ref=e174]:
              - generic [ref=e175]:
                - generic "Model revision 1" [ref=e177]: Rev 1
                - radiogroup "Design Intent" [ref=e182]:
                  - button "Auto" [ref=e183] [cursor=pointer]
                  - button "Create" [ref=e184] [cursor=pointer]
                  - button "Modify" [ref=e185] [cursor=pointer]
                  - button "Explain" [ref=e186] [cursor=pointer]
              - generic [ref=e187]:
                - textbox "Describe structural change or question (e.g. \"Add a diagonal between J1 and J3\", \"Move J2 up 0.5m\", \"Why unstable?\")..." [ref=e188]: Add a diagonal between J1 and J3
                - generic [ref=e189]:
                  - generic [ref=e190]: Enter ↵ to submit · Shift+Enter for newline
                  - button "Generate" [ref=e191] [cursor=pointer]
              - generic [ref=e197]:
                - generic [ref=e198]:
                  - generic [ref=e199]:
                    - generic [ref=e200]: MODIFY
                    - 'generic "Proposal ID: 8c4a8ee3debd40b08f95b75c48fb45bf" [ref=e205]': "#8c4a8ee3"
                    - generic [ref=e206]: rev 1 rev 2
                  - generic [ref=e209]: Invalid
                - paragraph [ref=e214]: Added member M4 connecting joint J1 and joint J3. All other geometry remains unchanged.
                - generic [ref=e215]:
                  - generic [ref=e216]: Proposed Topology Changes (1)
                  - generic [ref=e217]: Add Member M4 (J1 ↔ J3)
                - generic [ref=e222]:
                  - generic [ref=e223]:
                    - generic [ref=e224]: "3"
                    - generic [ref=e225]: Joints
                  - generic [ref=e226]:
                    - generic [ref=e227]: "3"
                    - generic [ref=e228]: Members
                  - generic [ref=e229]:
                    - generic [ref=e230]: "2"
                    - generic [ref=e231]: Supports
                  - generic [ref=e232]:
                    - generic [ref=e233]: "1"
                    - generic [ref=e234]: Loads
                  - generic [ref=e235]:
                    - generic [ref=e236]: 6.00 m
                    - generic [ref=e237]: Span
                  - generic [ref=e238]:
                    - generic [ref=e239]: 3.00 m
                    - generic [ref=e240]: Height
                - generic [ref=e244]:
                  - text: "Predicted:"
                  - strong [ref=e245]: SQUARE_FULL_RANK
                  - text: (6 eq vs 6 unk)
                - generic [ref=e246]:
                  - button "Discard" [ref=e247] [cursor=pointer]
                  - button "Apply Changes" [disabled] [ref=e251]
        - complementary [ref=e254]:
          - generic [ref=e255]:
            - generic [ref=e256]:
              - generic [ref=e257]: Navigate
              - generic [ref=e258]:
                - button "Select" [ref=e259] [cursor=pointer]
                - button "Pan" [ref=e263] [cursor=pointer]
            - generic [ref=e269]:
              - generic [ref=e270]: Construction
              - generic [ref=e271]:
                - button "Joint" [ref=e272] [cursor=pointer]
                - button "Member" [ref=e275] [cursor=pointer]
                - button "Measure" [ref=e280] [cursor=pointer]
            - generic [ref=e287]:
              - generic [ref=e288]: Structural
              - generic [ref=e289]:
                - button "Pin" [ref=e290] [cursor=pointer]
                - button "Roller" [ref=e294] [cursor=pointer]
                - button "Load" [ref=e298] [cursor=pointer]
            - generic [ref=e301]:
              - generic [ref=e302]: Edit
              - button "Delete" [ref=e304] [cursor=pointer]
          - generic [ref=e309]:
            - generic [ref=e310]:
              - heading "Model" [level=3] [ref=e311]
              - generic [ref=e312]: TRUSS
            - generic [ref=e313]:
              - generic [ref=e314]:
                - text: Joints
                - strong [ref=e315]: "3"
              - generic [ref=e316]:
                - text: Members
                - strong [ref=e317]: "3"
              - generic [ref=e318]:
                - text: Supports
                - strong [ref=e319]: "2"
              - generic [ref=e320]:
                - text: Loads
                - strong [ref=e321]: "1"
            - paragraph [ref=e322]: Select a joint or member to inspect and edit its properties.
            - button "Clear All Model Elements" [ref=e323] [cursor=pointer]
      - generic [ref=e327]:
        - generic [ref=e328]:
          - generic [ref=e329]: SOLVABLE
          - generic [ref=e333]: Truss is statically determinate and in static equilibrium.
        - generic [ref=e334]: 3 joints · 3 members · 5.93, -0.62
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
  60  |   expect(events.pageErrors, 'uncaught browser errors').toEqual([])
  61  |   const unexpectedConsoleErrors = events.consoleErrors.filter((message) =>
  62  |     !events.expectedConsoleErrors.some((expected) => message.includes(expected))
  63  |       && ![...events.expectedHttpErrors].some((status) =>
  64  |         message.includes(`status of ${status}`) || message.includes(`status code ${status}`),
  65  |       ),
  66  |   )
> 67  |   expect(unexpectedConsoleErrors, 'unexpected browser console errors').toEqual([])
      |                                                                        ^ Error: unexpected browser console errors
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
  161 |   await expect(page.getByRole('button', { name: /test1\.jpg/ })).toBeVisible()
  162 |   await page.getByRole('button', { name: 'Refresh history' }).click()
  163 |   await expect(page.getByRole('button', { name: /test1\.jpg/ })).toBeVisible()
  164 |   await expect(page.getByText(/saved records/)).toBeVisible()
  165 | })
  166 | 
  167 | test('history displays an understandable backend error', async ({ page }) => {
```