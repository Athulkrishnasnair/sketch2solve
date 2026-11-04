import { expect, test } from '@playwright/test'
import { readFileSync, readdirSync, statSync, writeFileSync, existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const testDirectory = path.dirname(fileURLToPath(import.meta.url))
const repositoryDirectory = path.resolve(testDirectory, '../../..')
const evaluationDirectory = path.join(repositoryDirectory, 'backend/evaluation/sketches')
const evaluationImages = readdirSync(evaluationDirectory)
  .filter((name) => /\.(?:png|jpe?g)$/i.test(name))
  .sort()
const telemetry = new WeakMap()
const resultFile = path.join(process.env.QA_OUTPUT_DIR, 'upload-results.json')

function expectFailedRequest(page, urlPart) {
  telemetry.get(page).expectedFailedRequests.push(urlPart)
}

function expectHttpError(page, status) {
  telemetry.get(page).expectedHttpErrors.add(status)
}

function recordUploadResult(result) {
  const previous = existsSync(resultFile) ? JSON.parse(readFileSync(resultFile, 'utf8')) : []
  previous.push(result)
  writeFileSync(resultFile, `${JSON.stringify(previous, null, 2)}\n`)
}

async function submitFile(page, { name, mimeType, buffer }) {
  await page.locator('input[type="file"]').setInputFiles({ name, mimeType, buffer })
  await expect(page.getByRole('button', { name: 'Start analysis' })).toBeEnabled()
  const responsePromise = page.waitForResponse((response) =>
    response.request().method() === 'POST' && new URL(response.url()).pathname === '/api/analyses',
  )
  await page.getByRole('button', { name: 'Start analysis' }).click()
  const response = await responsePromise
  if (response.status() >= 400) expectHttpError(page, response.status())
  return { response, body: await response.json() }
}

test.beforeEach(async ({ page }) => {
  const events = {
    pageErrors: [],
    consoleErrors: [],
    failedRequests: [],
    expectedFailedRequests: [],
    expectedConsoleErrors: [],
    expectedHttpErrors: new Set(),
  }
  telemetry.set(page, events)
  page.on('pageerror', (error) => events.pageErrors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') events.consoleErrors.push(message.text())
  })
  page.on('requestfailed', (request) => events.failedRequests.push(request.url()))
})

test.afterEach(async ({ page }) => {
  const events = telemetry.get(page)
  expect(events.pageErrors, 'uncaught browser errors').toEqual([])
  const unexpectedConsoleErrors = events.consoleErrors.filter((message) =>
    !events.expectedConsoleErrors.some((expected) => message.includes(expected))
      && ![...events.expectedHttpErrors].some((status) =>
        message.includes(`status of ${status}`) || message.includes(`status code ${status}`),
      ),
  )
  expect(unexpectedConsoleErrors, 'unexpected browser console errors').toEqual([])
  const unexpectedFailures = events.failedRequests.filter((url) =>
    !events.expectedFailedRequests.some((expected) => url.includes(expected)),
  )
  expect(unexpectedFailures, 'unexpected failed network requests').toEqual([])
})

test('health endpoint, dashboard, and primary navigation load', async ({ page }) => {
  const health = await page.request.get('/api/health')
  expect(health.status()).toBe(200)
  expect(await health.json()).toMatchObject({ status: 'ok', application: 'Sketch2Solve' })

  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Sketch review/ })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible()

  const navigation = page.getByRole('navigation', { name: 'Main navigation' })
  await navigation.getByRole('button', { name: 'New analysis' }).click()
  await expect(page.getByRole('heading', { name: /Review a structure/ })).toBeVisible()
  await navigation.getByRole('button', { name: 'Analysis history' }).click()
  await expect(page.getByRole('heading', { name: 'Analysis history' })).toBeVisible()
})

for (const filename of evaluationImages) {
  test(`uploads evaluation sketch ${filename} through the UI`, async ({ page }) => {
    const filePath = path.join(evaluationDirectory, filename)
    const bytes = readFileSync(filePath)
    await page.goto('/?view=new')
    const { response, body } = await submitFile(page, {
      name: filename,
      mimeType: /\.png$/i.test(filename) ? 'image/png' : 'image/jpeg',
      buffer: bytes,
    })

    expect(response.status()).toBe(201)
    expect(body.status).toBe('pending_review')
    expect(body.review_status).toBe('pending_review')
    expect(body.interpretation_proposal.proposal_only).toBe(true)
    await expect(page.getByRole('heading', { name: filename })).toBeVisible()
    await expect(page.getByText('AI-proposed geometry')).toBeVisible()

    const detailResponse = await page.request.get(`/api/analyses/${body.analysis_id}`)
    expect(detailResponse.status()).toBe(200)
    const detail = await detailResponse.json()
    const originalResponse = await page.request.get(detail.sketch.image_url)
    expect(originalResponse.status()).toBe(200)
    expect(originalResponse.headers()['content-type']).toContain(detail.mime_type)
    expect(Buffer.from(await originalResponse.body())).toEqual(bytes)
    expect(detail.perception.lines.length).toBeGreaterThan(0)

    const originalImage = page.getByRole('img', { name: 'Original uploaded truss sketch' })
    await expect(originalImage).toBeVisible()
    await expect.poll(() => originalImage.evaluate((image) => image.naturalWidth)).toBeGreaterThan(0)

    recordUploadResult({
      filename,
      size_bytes: statSync(filePath).size,
      detected_format: detail.mime_type,
      upload_success: true,
      http_status: response.status(),
      analysis_record_saved: Boolean(detail.analysis_id),
      original_image_retrieved: originalResponse.status() === 200,
      opencv_candidate_lines: detail.perception.lines.length,
      provider: detail.provider,
      provider_result: 'mock proposal returned; not a live interpretation',
      review_status: detail.review_status,
    })
  })
}

test('existing analysis details expose image, detection/proposal toggles, zoom, and review controls', async ({ page }) => {
  await page.goto('/?view=history')
  await expect(page.getByRole('button', { name: /test5\.png/ })).toBeVisible()
  await page.getByRole('button', { name: /test5\.png/ }).click()
  await expect(page.getByRole('heading', { name: 'test5.png' })).toBeVisible()

  await expect(page.getByRole('img', { name: 'Original uploaded truss sketch' })).toBeVisible()
  await expect(page.getByRole('img', { name: 'OpenCV candidate segments and endpoint clusters' })).toBeVisible()
  await expect(page.getByRole('img', { name: 'AI candidate joints, members, supports and loads' })).toBeVisible()
  await page.getByLabel('OpenCV detections').uncheck()
  await expect(page.getByRole('img', { name: 'OpenCV candidate segments and endpoint clusters' })).toHaveCount(0)
  await page.getByLabel('OpenCV detections').check()
  await page.getByLabel('AI proposal').uncheck()
  await expect(page.getByRole('img', { name: 'AI candidate joints, members, supports and loads' })).toHaveCount(0)
  await page.getByLabel('AI proposal').check()

  await page.getByRole('slider').fill('2')
  await expect(page.getByText('2.00×')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Geometry draft' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Correct interpretation' })).toBeEnabled()
})

test('history refreshes without breaking saved records', async ({ page }) => {
  await page.goto('/?view=history')
  await expect(page.getByRole('button', { name: /test1\.jpg/ })).toBeVisible()
  await page.getByRole('button', { name: 'Refresh history' }).click()
  await expect(page.getByRole('button', { name: /test1\.jpg/ })).toBeVisible()
  await expect(page.getByText(/saved records/)).toBeVisible()
})

test('history displays an understandable backend error', async ({ page }) => {
  expectHttpError(page, 503)
  await page.route('**/api/analyses?**', (route) => route.fulfill({
    status: 503,
    contentType: 'application/json',
    body: JSON.stringify({ error_code: 'ANALYSIS_HISTORY_UNAVAILABLE', message: 'History is temporarily unavailable.' }),
  }))
  await page.goto('/?view=history')
  await expect(page.getByRole('alert')).toContainText('History could not be loaded')
  await expect(page.getByRole('alert')).toContainText('History is temporarily unavailable.')
})

test('valid WebP uploads and misleading extension is resolved from image bytes', async ({ page }) => {
  await page.goto('/?view=new')
  const webpDataUrl = await page.evaluate(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 32
    canvas.height = 24
    const context = canvas.getContext('2d')
    context.fillStyle = '#222'
    context.beginPath()
    context.moveTo(2, 22)
    context.lineTo(16, 2)
    context.lineTo(30, 22)
    context.stroke()
    return canvas.toDataURL('image/webp')
  })
  const webp = Buffer.from(webpDataUrl.split(',')[1], 'base64')
  const webpResult = await submitFile(page, { name: 'browser-generated.webp', mimeType: 'image/webp', buffer: webp })
  expect(webpResult.response.status()).toBe(201)
  expect(webpResult.body.mime_type).toBe('image/webp')

  await page.goto('/?view=new')
  const png = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  const mislabeled = await submitFile(page, { name: 'misleading.jpg', mimeType: 'image/jpeg', buffer: png })
  expect(mislabeled.response.status()).toBe(201)
  expect(mislabeled.body.mime_type).toBe('image/png')
})

test('corrupt and unsupported uploads show clear messages and persist failed attempts', async ({ page }) => {
  await page.goto('/?view=new')
  const corrupt = Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    Buffer.alloc(20),
  ])
  const corrupted = await submitFile(page, { name: 'corrupted.png', mimeType: 'image/png', buffer: corrupt })
  expect(corrupted.response.status()).toBe(422)
  expect(corrupted.body.error_code).toBe('INVALID_IMAGE')
  await expect(page.getByRole('alert')).toContainText('could not be read as a supported sketch image')

  await page.goto('/?view=new')
  const unsupported = await submitFile(page, {
    name: 'unsupported.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('not an image'),
  })
  expect(unsupported.response.status()).toBe(415)
  expect(unsupported.body.error_code).toBe('UNSUPPORTED_IMAGE_TYPE')
  await expect(page.getByRole('alert')).toContainText(/Choose a JPEG, PNG, or WebP image|The saved image is not a supported format/)

  for (const body of [corrupted.body, unsupported.body]) {
    const saved = await page.request.get(`/api/analyses/${body.analysis_id}`)
    expect(saved.status()).toBe(200)
    expect((await saved.json()).status).toBe('failed')
  }
})

test('oversized UI upload is blocked and backend limit returns a recorded 413', async ({ page }) => {
  await page.goto('/?view=new')
  const oversized = Buffer.alloc(10 * 1024 * 1024 + 1)
  await page.locator('input[type="file"]').setInputFiles({
    name: 'over-limit.jpg',
    mimeType: 'image/jpeg',
    buffer: oversized,
  })
  await expect(page.getByRole('alert')).toContainText('larger than the 10 MiB upload limit')
  await expect(page.getByRole('button', { name: 'Start analysis' })).toBeDisabled()

  const response = await page.request.post('http://127.0.0.1:5101/api/analyses', {
    multipart: {
      provider: 'gemini',
      image: { name: 'over-limit.jpg', mimeType: 'image/jpeg', buffer: oversized },
    },
  })
  expect(response.status()).toBe(413)
  const body = await response.json()
  expect(body.error_code).toBe('IMAGE_TOO_LARGE')
  const saved = await page.request.get(`http://127.0.0.1:5101/api/analyses/${body.analysis_id}`)
  expect((await saved.json()).status).toBe('failed')
})

for (const [scenario, expectedMessage] of [
  ['MISSING_GEMINI_API_KEY', 'Gemini is selected, but its server-side credential is not configured.'],
  ['GEMINI_AUTHENTICATION_FAILED', 'Gemini rejected the backend credential or account access.'],
  ['GEMINI_RATE_LIMITED', 'Gemini rate limit or quota was reached. Try again later.'],
  ['GEMINI_TIMEOUT', 'The Gemini request timed out. Try again with a smaller image.'],
  ['GEMINI_NETWORK_ERROR', 'The backend could not reach Gemini. Check the backend network connection.'],
  ['INVALID_GEMINI_RESPONSE', 'Gemini returned an unexpected interpretation format.'],
]) {
  test(`provider failure ${scenario} is saved and explained without secrets`, async ({ page }) => {
    await page.setExtraHTTPHeaders({ 'X-QA-Mock-Provider': scenario })
    await page.goto('/?view=new')
    const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
    const { response, body } = await submitFile(page, { name: `${scenario}.png`, mimeType: 'image/png', buffer: bytes })
    expect(response.status()).not.toBe(201)
    expect(body.error_code).toBe(scenario)
    expect(JSON.stringify(body)).not.toContain('API_KEY=')
    await expect(page.getByRole('heading', { name: `${scenario}.png` })).toBeVisible()
    await expect(page.getByRole('alert')).toContainText(expectedMessage)
    const record = await page.request.get(`/api/analyses/${body.analysis_id}`)
    const detail = await record.json()
    expect(detail.status).toBe('failed')
    expect(detail.error_code).toBe(scenario)
    recordUploadResult({
      filename: `${scenario}.png`,
      size_bytes: bytes.length,
      detected_format: detail.mime_type,
      upload_success: false,
      http_status: response.status(),
      analysis_record_saved: true,
      original_image_retrieved: Boolean(detail.sketch.image_url),
      opencv_candidate_lines: detail.perception.lines.length,
      provider: detail.provider,
      provider_result: `documented mocked error ${scenario}`,
      review_status: detail.review_status,
    })
  })
}

test('empty proposal stays unapproved and visible as having no candidate elements', async ({ page }) => {
  await page.setExtraHTTPHeaders({ 'X-QA-Mock-Provider': 'EMPTY_PROPOSAL' })
  await page.goto('/?view=new')
  const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  const { response, body } = await submitFile(page, { name: 'empty-proposal.png', mimeType: 'image/png', buffer: bytes })
  expect(response.status()).toBe(201)
  expect(body.review_status).toBe('pending_review')
  expect(body.interpretation_proposal.joints).toEqual([])
  expect(body.interpretation_proposal.members).toEqual([])
  await expect(page.getByText('0 members')).toBeVisible()
  await expect(page.getByText('NOT SAVED')).toBeVisible()
})

test('geometry review saves, validates, explicitly reviews, solves, and reloads persisted results', async ({ page }) => {
  await page.goto('/?view=new')
  const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  const { response, body } = await submitFile(page, { name: 'workflow.png', mimeType: 'image/png', buffer: bytes })
  expect(response.status()).toBe(201)
  expect(body.review_status).toBe('pending_review')
  await expect(page.getByText('NOT SAVED')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Mark reviewed' })).toHaveCount(0)
  const editButton = page.getByRole('button', { name: 'Correct interpretation' })
  await expect(editButton).toBeEnabled()
  expect(body.interpretation_proposal.proposal_only).toBe(true)

  await editButton.click()
  await expect(page.getByRole('heading', { name: 'Joints' })).toBeVisible()
  await page.getByLabel('Length unit').selectOption('m')
  await page.getByLabel('Force unit').selectOption('kN')

  const nodeRows = page.locator('.node-form-row')
  for (const [index, [x, y]] of [[0, 0], [4, 0], [2, 3]].entries()) {
    await nodeRows.nth(index).locator('input').nth(1).fill(String(x))
    await nodeRows.nth(index).locator('input').nth(2).fill(String(y))
  }
  const supportSection = page.locator('.form-collection').nth(2)
  await supportSection.getByLabel('Joint').nth(0).selectOption('J1')
  await supportSection.getByLabel('Joint').nth(1).selectOption('J2')
  await supportSection.getByLabel('Direction').selectOption('vertical')
  const loadSection = page.locator('.form-collection').nth(3)
  await loadSection.getByLabel('Joint').selectOption('J3')
  await loadSection.getByLabel('Fx kN').fill('0')
  await loadSection.getByLabel('Fy kN').fill('-10')
  await page.getByRole('checkbox', { name: /I replaced or verified every joint coordinate/ }).check()
  await page.getByRole('button', { name: 'Validate and save draft' }).click()
  await expect(page.locator('.draft-state').filter({ hasText: 'DRAFT SAVED' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Mark reviewed' })).toBeEnabled()
  const savedBeforeReview = await page.request.get(`/api/analyses/${body.analysis_id}`)
  const unreviewedDetail = await savedBeforeReview.json()
  expect(unreviewedDetail.review_status).toBe('draft')
  expect(unreviewedDetail.interpretation_proposal.proposal_only).toBe(true)
  expect(unreviewedDetail.solver_results).toBeNull()

  await page.getByRole('button', { name: 'Mark reviewed' }).click()
  await expect(page.locator('.draft-state').filter({ hasText: 'REVIEWED' })).toBeVisible()
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'Submit reviewed geometry to solver' }).click()
  await expect(page.locator('.draft-state').filter({ hasText: 'SUBMITTED' })).toBeVisible()
  await expect(page.getByText('Solver results')).toBeVisible()

  await page.reload()
  await expect(page.getByRole('heading', { name: 'workflow.png' })).toBeVisible()
  await expect(page.locator('.draft-state').filter({ hasText: 'SUBMITTED' })).toBeVisible()
  const persisted = await page.request.get(`/api/analyses/${body.analysis_id}`)
  const detail = await persisted.json()
  expect(detail.review_status).toBe('submitted')
  expect(detail.human_review.geometry.model.nodes).toHaveLength(3)
  expect(detail.solver_results.member_forces).toHaveProperty('M1')
  expect(detail.interpretation_proposal.proposal_only).toBe(true)
})

test('invalid geometry, missing units, and solver failures preserve the unapproved or reviewed draft', async ({ page }) => {
  const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  const created = await page.request.post('/api/analyses', {
    multipart: { provider: 'gemini', image: { name: 'validation.png', mimeType: 'image/png', buffer: bytes } },
  })
  const analysis = await created.json()
  expect(analysis.review_status).toBe('pending_review')
  const draftUrl = `/api/analyses/${analysis.analysis_id}/draft`
  const solveUrl = `/api/analyses/${analysis.analysis_id}/solve`

  const unconfirmed = await page.request.put(draftUrl, {
    data: { geometry: {}, coordinates_confirmed: false },
  })
  expect(unconfirmed.status()).toBe(422)
  expect((await unconfirmed.json()).error_code).toBe('COORDINATES_NOT_CONFIRMED')
  expect((await page.request.post(solveUrl)).status()).toBe(409)

  const invalidGeometry = {
    schema_version: '1.0',
    metadata: { name: 'invalid', source: 'human_review', units: { length: 'm', force: 'N' } },
    model: {
      nodes: [{ id: 'A', x: 0, y: 0 }, { id: 'B', x: 1, y: 0 }],
      members: [{ id: 'M1', node_i: 'A', node_j: 'missing' }],
      supports: [],
      loads: [],
    },
  }
  const invalid = await page.request.put(draftUrl, {
    data: { geometry: invalidGeometry, coordinates_confirmed: true },
  })
  expect(invalid.status()).toBe(422)
  expect((await invalid.json()).error_code).toBe('VALIDATION_FAILED')

  const singular = {
    schema_version: '1.0',
    metadata: { name: 'singular', source: 'human_review', units: { length: 'm', force: 'N' } },
    model: {
      nodes: [
        { id: 'A', x: 0, y: 0 },
        { id: 'B', x: 4, y: 0 },
        { id: 'C', x: 2, y: 3 },
      ],
      members: [
        { id: 'M1', node_i: 'A', node_j: 'B' },
        { id: 'M2', node_i: 'A', node_j: 'C' },
        { id: 'M3', node_i: 'A', node_j: 'C' },
      ],
      supports: [
        { id: 'S1', node: 'A', type: 'pin' },
        { id: 'S2', node: 'B', type: 'roller', direction: 'vertical' },
      ],
      loads: [{ id: 'L1', node: 'C', fx: 0, fy: -10 }],
    },
  }
  const missingUnits = structuredClone(singular)
  missingUnits.metadata.units.length = ''
  const noUnits = await page.request.put(draftUrl, {
    data: { geometry: missingUnits, coordinates_confirmed: true },
  })
  expect(noUnits.status()).toBe(422)
  expect((await noUnits.json()).error_code).toBe('VALIDATION_FAILED')

  expect((await page.request.put(draftUrl, {
    data: { geometry: singular, coordinates_confirmed: true },
  })).status()).toBe(200)
  expect((await page.request.post(`/api/analyses/${analysis.analysis_id}/review`)).status()).toBe(200)
  const failedSolve = await page.request.post(solveUrl)
  expect(failedSolve.status()).toBe(422)

  const retained = await page.request.get(`/api/analyses/${analysis.analysis_id}`)
  const detail = await retained.json()
  expect(detail.review_status).toBe('reviewed')
  expect(detail.human_review.geometry).toEqual(singular)
  expect(detail.solver_results).toBeNull()
  expect(detail.diagnostics).not.toBeNull()
})

test('a missing stored image is explained while geometry remains available', async ({ page }) => {
  const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  const created = await page.request.post('/api/analyses', {
    multipart: { provider: 'gemini', image: { name: 'missing-image.png', mimeType: 'image/png', buffer: bytes } },
  })
  const body = await created.json()
  expectHttpError(page, 404)
  await page.route(`**/api/analyses/${body.analysis_id}/image`, (route) => route.fulfill({
    status: 404,
    contentType: 'application/json',
    body: JSON.stringify({ error_code: 'ANALYSIS_NOT_FOUND', message: 'Image unavailable.' }),
  }))
  await page.goto(`/?analysis=${body.analysis_id}`)
  await expect(page.getByText('The original sketch file is unavailable.')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Geometry draft' })).toBeVisible()
})

test('network failure displays the local backend connection message', async ({ page }) => {
  expectFailedRequest(page, '/api/analyses?')
  telemetry.get(page).expectedConsoleErrors = ['net::ERR_FAILED']
  await page.route('**/api/analyses?**', (route) => route.abort())
  await page.goto('/?view=history')
  await expect(page.getByRole('alert')).toContainText('Could not reach the local Sketch2Solve backend.')
})

test('contextual on-canvas issue highlighting, floating action card, and AI repair workflow', async ({ page }) => {
  await page.goto('/?view=new')
  const bytes = readFileSync(path.join(evaluationDirectory, 'test4.jpg'))
  const { response, body } = await submitFile(page, { name: 'canvas_repair.jpg', mimeType: 'image/jpeg', buffer: bytes })
  expect(response.status()).toBe(201)

  // Navigate to interactive editor view
  await page.goto(`/?analysis=${body.analysis_id}&view=editor`)
  await expect(page.locator('.truss-editor-workspace')).toBeVisible()

  // Wait for canvas and initial preview calculation
  await expect(page.locator('.engineering-svg')).toBeVisible()

  // Verify contextual action card appears near affected geometry
  const actionCard = page.locator('.contextual-action-card')
  await expect(actionCard).toBeVisible({ timeout: 10_000 })
  await expect(actionCard.locator('.classification-pill')).toBeVisible()
  await expect(actionCard.getByRole('button', { name: 'Fix with AI' })).toBeVisible()

  // Verify affected elements highlighting on canvas
  const affectedHighlights = page.locator('.issue-highlight-error, .issue-highlight-mechanism, .issue-highlight-warning, .joint-issue-pulse-ring')
  const highlightCount = await affectedHighlights.count()
  expect(highlightCount).toBeGreaterThan(0)

  // Test clearing highlight
  await page.locator('.btn-clear-highlight').click()
  await expect(actionCard).not.toBeVisible()

  // Test re-enabling highlight via status bar toggle
  await page.locator('.status-warnings-toggle').click()
  await expect(actionCard).toBeVisible()

  // Click 'Fix with AI'
  await actionCard.getByRole('button', { name: 'Fix with AI' }).click()

  // Verify root cause explanation and repair actions appear
  await expect(page.locator('.explanation-quote')).toBeVisible({ timeout: 8_000 })
  await expect(page.locator('.btn-apply-fix')).toBeVisible()
  await expect(page.locator('.btn-cancel-fix')).toBeVisible()

  // Verify AI proposed modification preview rendered on canvas (distinct blue styling)
  const proposedPreview = page.locator('.ai-fix-preview-group')
  await expect(proposedPreview).toBeVisible()

  // Apply suggested fix
  await page.locator('.btn-apply-fix').click()

  // Verify toast notification and revalidation update
  await expect(page.locator('.editor-toast')).toBeVisible()
})

test('issue resolution assistant independent scrolling, mouse-wheel isolation, and sticky footer', async ({ page }) => {
  await page.goto('/?view=new')
  const bytes = readFileSync(path.join(evaluationDirectory, 'test4.jpg'))
  const { response, body } = await submitFile(page, { name: 'card_scroll_test.jpg', mimeType: 'image/jpeg', buffer: bytes })
  expect(response.status()).toBe(201)

  // Navigate to interactive editor view
  await page.goto(`/?analysis=${body.analysis_id}&view=editor`)
  await expect(page.locator('.truss-editor-workspace')).toBeVisible()
  await expect(page.locator('.engineering-svg')).toBeVisible()

  // Verify contextual action card appears
  const actionCard = page.locator('.contextual-action-card')
  await expect(actionCard).toBeVisible({ timeout: 10_000 })

  // Click 'Fix with AI' to generate extensive resolution content (root cause, rationale, proposed fixes, alternatives)
  await actionCard.getByRole('button', { name: 'Fix with AI' }).click()
  await expect(page.locator('.explanation-quote')).toBeVisible({ timeout: 8_000 })

  // 1. Verify card content area has overflowed and is independently scrollable
  const scrollArea = page.locator('.card-content-scroll')
  await expect(scrollArea).toBeVisible()
  const scrollMetrics = await scrollArea.evaluate((el) => ({
    scrollHeight: el.scrollHeight,
    clientHeight: el.clientHeight,
    scrollTop: el.scrollTop,
  }))
  expect(scrollMetrics.scrollHeight).toBeGreaterThan(scrollMetrics.clientHeight)

  // 2. Verify sticky footer with Apply and Cancel actions remains visible and accessible
  const applyButton = page.locator('.btn-apply-fix')
  const cancelButton = page.locator('.btn-cancel-fix')
  await expect(applyButton).toBeVisible()
  await expect(cancelButton).toBeVisible()

  // 3. Record initial canvas element screen coordinate
  const firstJoint = page.locator('.truss-joint-node').first()
  const initialJointCx = await firstJoint.getAttribute('cx')

  // 4. Scroll inside the card using mouse wheel
  const cardBox = await scrollArea.boundingBox()
  expect(cardBox).not.toBeNull()
  await page.mouse.move(cardBox.x + cardBox.width / 2, cardBox.y + cardBox.height / 2)
  await page.mouse.wheel(0, 150)
  await page.waitForTimeout(200)

  // 5. Confirm the card scroll position changed
  const scrolledPosition = await scrollArea.evaluate((el) => el.scrollTop)
  expect(scrolledPosition).toBeGreaterThan(0)

  // 6. Confirm canvas zoom/scale remains unchanged
  const postCardScrollCx = await firstJoint.getAttribute('cx')
  expect(postCardScrollCx).toBe(initialJointCx)

  // 7. Scroll over the canvas outside the card (hover over open canvas SVG)
  const canvasSvg = page.locator('.engineering-svg')
  await canvasSvg.hover({ position: { x: 200, y: 200 } })
  await page.mouse.wheel(0, -200)
  await page.waitForTimeout(300)

  // 8. Confirm canvas zoom DID change when scrolled outside the card
  const postCanvasZoomCx = await firstJoint.getAttribute('cx')
  expect(postCanvasZoomCx).not.toBe(initialJointCx)

  // 9. Verify cancellation works without modifying original model
  await cancelButton.click()
  await expect(page.locator('.explanation-quote')).not.toBeVisible()
  await expect(actionCard.getByRole('button', { name: 'Fix with AI' })).toBeVisible()

  // 10. Re-open resolution and verify Apply Suggested Fix operates cleanly from sticky footer
  await actionCard.getByRole('button', { name: 'Fix with AI' }).click()
  await expect(page.locator('.explanation-quote')).toBeVisible({ timeout: 8_000 })
  await applyButton.click()
  await expect(page.locator('.editor-toast')).toBeVisible()
})

test('solver-result experience: triangular reference model verification, results panel, on-canvas forces, reactions, legend, and stale protection', async ({ page }) => {
  await page.goto('/?view=new')
  const bytes = readFileSync(path.join(evaluationDirectory, 'test3.png'))
  const { response, body } = await submitFile(page, { name: 'reference_triangle.png', mimeType: 'image/png', buffer: bytes })
  expect(response.status()).toBe(201)

  // 1. Establish the known triangular reference model:
  // A=(0,0), B=(4,0), C=(2,3), Pin at A, vertical Roller at B, 10 kN downward load at C
  const triangleModel = {
    schema_version: '1.0',
    metadata: {
      name: 'Triangular Reference Truss',
      units: { length: 'm', force: 'kN' },
    },
    model: {
      nodes: [
        { id: 'A', x: 0.0, y: 0.0 },
        { id: 'B', x: 4.0, y: 0.0 },
        { id: 'C', x: 2.0, y: 3.0 },
      ],
      members: [
        { id: 'AB', node_i: 'A', node_j: 'B' },
        { id: 'AC', node_i: 'A', node_j: 'C' },
        { id: 'BC', node_i: 'B', node_j: 'C' },
      ],
      supports: [
        { id: 'S_A', node: 'A', type: 'pin' },
        { id: 'S_B', node: 'B', type: 'roller', direction: 'vertical' },
      ],
      loads: [
        { id: 'L_C', node: 'C', fx: 0.0, fy: -10.0 },
      ],
    },
  }

  // Persist draft and mark reviewed
  const draftRes = await page.request.put(`/api/analyses/${body.analysis_id}/draft`, {
    data: { geometry: triangleModel, coordinates_confirmed: true },
  })
  expect(draftRes.status()).toBe(200)

  const reviewRes = await page.request.post(`/api/analyses/${body.analysis_id}/review`)
  expect(reviewRes.status()).toBe(200)

  // Open the interactive geometry editor
  await page.goto(`/?analysis=${body.analysis_id}&view=editor`)
  await expect(page.locator('.truss-editor-workspace')).toBeVisible()
  await expect(page.locator('.engineering-svg')).toBeVisible()

  // 2. Solve button interaction: loading state, confirm dialog, and execution
  const solveButton = page.locator('.btn-solve')
  await expect(solveButton).toBeEnabled()
  await solveButton.click()

  // Confirm in dialog
  const confirmDialog = page.locator('.cdialog-panel')
  await expect(confirmDialog).toBeVisible()
  await confirmDialog.locator('.cdialog-confirm').click()

  // 3. Clear transition to expanded Analysis Results view
  const resultsPanel = page.locator('.analysis-results-panel')
  await expect(resultsPanel).toBeVisible({ timeout: 10_000 })
  await expect(resultsPanel.locator('.badge-solved')).toHaveText(/SOLVED/)

  // 4. Verify structural counts and matrix diagnostics
  await expect(resultsPanel.getByText('Summary & Matrix')).toBeVisible()
  await expect(resultsPanel.locator('.summary-grid')).toContainText('Joints (N)')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('3')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('Members (M)')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('3')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('Equilibrium Equations (2N)')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('6')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('Unknowns (M + R)')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('6')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('Matrix Shape')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('6 × 6')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('Numerical Rank')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('6')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('Condition Number (κ)')
  await expect(resultsPanel.locator('.summary-grid')).toContainText('4.38')

  // 5. Verify analytical support reactions: 5 kN upward at each support
  await resultsPanel.getByRole('button', { name: /Support Reactions/ }).click()
  const reactionsTable = resultsPanel.locator('.results-table')
  await expect(reactionsTable).toBeVisible()
  // S_A: Rx ~ 0.000 kN, Ry = +5.000 kN, Magnitude = 5.000 kN
  await expect(reactionsTable).toContainText('S_A')
  await expect(reactionsTable).toContainText('+5.000 kN')
  // S_B: Ry = +5.000 kN, Magnitude = 5.000 kN
  await expect(reactionsTable).toContainText('S_B')

  // 6. Verify analytical member forces:
  // Base member AB: +3.333333 kN tension
  // Inclined members AC and BC: -6.009252 kN compression
  await resultsPanel.getByRole('button', { name: /Member Forces/ }).click()
  const memberTable = resultsPanel.locator('.results-table')
  await expect(memberTable).toBeVisible()
  await expect(memberTable).toContainText('+3.333 kN')
  await expect(memberTable).toContainText('Tension (+)')
  await expect(memberTable).toContainText('-6.009 kN')
  await expect(memberTable).toContainText('Compression (−)')

  // 7. Verify limitations & equilibrium residual
  await resultsPanel.getByRole('button', { name: 'Limitations' }).click()
  await expect(resultsPanel.locator('.warning-block')).toContainText('A numerical solution does not establish physical stability')
  await expect(resultsPanel.locator('.assumptions-list')).toContainText('Planar Ideal Pin-Jointed System')

  // 8. Close results panel to clearly inspect full canvas visualization
  await resultsPanel.locator('.btn-close').click()
  await expect(resultsPanel).not.toBeVisible()

  // Verify member force labels directly on truss
  const forceLabels = page.locator('.member-force-label')
  await expect(forceLabels).toHaveCount(3)
  await expect(page.locator('.member-force-label.tension')).toContainText('+3.33 kN')
  await expect(page.locator('.member-force-label.compression').first()).toContainText('-6.01 kN')

  // 9. Verify Support reaction arrows and labels on canvas
  const reactionLines = page.locator('.reaction-vector-line')
  await expect(reactionLines).toHaveCount(2)
  const reactionHeads = page.locator('.reaction-arrowhead')
  await expect(reactionHeads.first()).toBeVisible()
  const reactionLabels = page.locator('.reaction-vector-label')
  await expect(reactionLabels.first()).toBeVisible()
  await expect(reactionLabels.first()).toContainText('+5.00 kN')

  // 10. Verify Canvas color legend
  const legend = page.locator('.canvas-forces-legend')
  await expect(legend).toBeVisible()
  await expect(legend).toContainText('Tension (+)')
  await expect(legend).toContainText('Compression (−)')
  await expect(legend).toContainText('Reaction (R)')

  // 11. Test Force Labels Toggle
  const toggleLabelsBtn = page.locator('.canvas-floating-controls button[title*="force labels"]')
  await expect(toggleLabelsBtn).toBeVisible()
  await toggleLabelsBtn.click()
  await expect(page.locator('.member-force-label')).toHaveCount(0)
  await toggleLabelsBtn.click()
  await expect(page.locator('.member-force-label')).toHaveCount(3)

  // Re-open results panel using topbar Results button
  await page.locator('.btn-results').click()
  await expect(resultsPanel).toBeVisible()

  // 12. Member selection to inspect detailed result in sidebar
  await resultsPanel.getByRole('button', { name: /Member Forces/ }).click()
  await resultsPanel.locator('.member-table-row').first().click()
  await expect(page.locator('.editor-sidebar .member-analysis-group')).toBeVisible()
  await expect(page.locator('.editor-sidebar .force-display')).toContainText('+3.33 kN')

  // 13. Stale results prevention: editing geometry invalidates results display
  // Delete the selected member from inspector
  await page.locator('.inspector-fields .delete-btn').click()

  // Confirm results are marked stale and protected from presentation
  await expect(resultsPanel.locator('.banner-stale')).toBeVisible()
  await expect(resultsPanel.locator('.badge-stale')).toHaveText(/RESULTS STALE/)
  await expect(page.locator('.member-force-label')).toHaveCount(0)
  await expect(page.locator('.reaction-vector-line')).toHaveCount(0)
  await expect(page.locator('.editor-statusbar')).toContainText('Results stale')

  // 14. Zero-load case verification on a separate unloaded analysis
  await page.goto('/?view=new')
  const { response: res2, body: body2 } = await submitFile(page, { name: 'unloaded_triangle.png', mimeType: 'image/png', buffer: bytes })
  expect(res2.status()).toBe(201)

  const unloadedModel = JSON.parse(JSON.stringify(triangleModel))
  unloadedModel.model.loads = []
  const draft2 = await page.request.put(`/api/analyses/${body2.analysis_id}/draft`, {
    data: { geometry: unloadedModel, coordinates_confirmed: true },
  })
  expect(draft2.status()).toBe(200)
  const rev2 = await page.request.post(`/api/analyses/${body2.analysis_id}/review`)
  expect(rev2.status()).toBe(200)

  await page.goto(`/?analysis=${body2.analysis_id}&view=editor`)
  await expect(page.locator('.truss-editor-workspace')).toBeVisible()

  // Solve the unloaded model
  await page.locator('.btn-solve').click()
  await page.locator('.cdialog-panel').locator('.cdialog-confirm').click()
  const unloadedPanel = page.locator('.analysis-results-panel')
  await expect(unloadedPanel).toBeVisible({ timeout: 10_000 })
  await expect(unloadedPanel.locator('.banner-unloaded')).toBeVisible()
  await expect(unloadedPanel.locator('.banner-unloaded')).toContainText('Model is unloaded (Zero external forces applied)')
})

test('Conversational natural-language truss design workflows across dashboard, sidebar studio, and editor', async ({ page }) => {
  // 1. Dashboard Entry Point: Create with AI
  await page.goto('/')
  await expect(page.locator('.dashboard-welcome')).toBeVisible()

  // Open in-place AI workbench on dashboard
  const createAiBtn = page.locator('.dashboard-ai-btn')
  await expect(createAiBtn).toBeVisible()
  await createAiBtn.click()

  const workbench = page.locator('.dashboard-ai-workbench')
  await expect(workbench).toBeVisible()
  await expect(workbench.locator('.workbench-chips')).toBeVisible()

  // Submit via example prompt chip
  await workbench.locator('.workbench-chip').first().click()

  // Verify proposed model card generated
  const proposalCard = workbench.locator('.design-proposal-card')
  await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  await expect(proposalCard.locator('.intent-pill')).toContainText('CREATE')
  await expect(proposalCard.locator('.validation-pill.valid')).toBeVisible()
  await expect(proposalCard.locator('.metric-item')).toHaveCount(6)

  // Explicit approval: Apply & Open Editor
  await proposalCard.locator('.btn-apply').click()

  // Verify transition to Truss Editor with new analysis loaded
  await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  await expect(page.locator('.truss-members-group line.truss-member-line')).toHaveCount(3)

  // 2. Editor Entry Point: Contextual Design Assistant
  const designAiBtn = page.locator('.editor-topbar .btn-ai')
  await expect(designAiBtn).toBeVisible()
  await designAiBtn.click()

  const editorAssistant = page.locator('.editor-design-assistant-card')
  await expect(editorAssistant).toBeVisible()

  // Enter out-of-scope prompt and verify guardrail notice
  expectFailedRequest(page, '/api/ai/design')
  expectHttpError(page, 400)
  const textarea = editorAssistant.locator('.design-textarea')
  await textarea.fill('Write a python script to scrape data')
  await editorAssistant.locator('.btn-submit').click()
  await expect(editorAssistant.locator('.error-banner')).toBeVisible({ timeout: 8_000 })
  await expect(editorAssistant.locator('.error-banner')).toContainText('I can help create, modify or explain truss structures')

  // Clear and submit valid modify instruction
  await editorAssistant.locator('.error-dismiss').click()
  await textarea.fill('Move joint J3 up by 1 m')
  await editorAssistant.locator('.btn-submit').click()

  // Verify proposed modification card and on-canvas overlay
  const modifyCard = editorAssistant.locator('.design-proposal-card')
  await expect(modifyCard).toBeVisible({ timeout: 10_000 })
  await expect(modifyCard.locator('.intent-pill')).toContainText('MODIFY')
  await expect(modifyCard.locator('.op-card')).toContainText('Move Joint J3')

  // Verify on-canvas preview marker
  const previewMarker = page.locator('.design-proposal-canvas-layer .design-preview-joint')
  await expect(previewMarker).toBeVisible()

  // Explicit approval: Apply Changes
  await modifyCard.locator('.btn-apply').click()
  await expect(editorAssistant.locator('.design-proposal-card')).toHaveCount(0)

  // 3. Sidebar Entry Point: Natural Language Design Studio
  const sidebarNav = page.locator('.primary-nav button:has-text("Natural Language Design")')
  await expect(sidebarNav).toBeVisible()
  await sidebarNav.click()

  await expect(page.locator('.design-studio-page')).toBeVisible()
  await expect(page.locator('.studio-header h1')).toHaveText('Natural Language Design Studio')
  await expect(page.locator('.studio-left-pane')).toBeVisible()
  await expect(page.locator('.studio-right-pane')).toBeVisible()

  // Test Studio synthesis
  const studioTextarea = page.locator('.studio-left-pane .design-textarea')
  await studioTextarea.fill('Warren truss with 4 panels and 10 m span')
  await page.locator('.studio-left-pane .btn-submit').click()

  const studioProposal = page.locator('.studio-left-pane .design-proposal-card')
  await expect(studioProposal).toBeVisible({ timeout: 10_000 })
  await expect(studioProposal.locator('.intent-pill')).toContainText('CREATE')
  await expect(page.locator('.studio-right-pane .cad-svg')).toBeVisible()
})
