import { test, expect } from '@playwright/test'
import path from 'node:path'

test.describe('Sketch2Solve Responsive Layout & Visual Polish Verification', () => {
  const outputDir = process.env.QA_OUTPUT_DIR || path.join(process.cwd(), 'qa-output')

  test.beforeEach(async ({ page }) => {
    // Set username so onboarding modal is bypassed for layout checks
    await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Chief Engineer'))
  })

  test('1. Setup & Editor: Synthesize initial truss analysis and verify editor canvas', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })

    // Submit a triangular truss prompt
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 25_000 })
    await proposalCard.locator('.btn-apply').click()

    // Enter Truss Editor
    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Verify editor topbar and status bar
    await expect(page.locator('.editor-topbar')).toBeVisible()
    await expect(page.locator('.editor-statusbar')).toBeVisible()
  })

  test('2. Desktop 1440px: Full-viewport application shell without floating rounded-card box', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/')
    await expect(page.locator('.dashboard-page')).toBeVisible({ timeout: 10_000 })

    // Verify app-frame fills viewport
    const frameBox = await page.locator('.app-frame').boundingBox()
    expect(frameBox.width).toBe(1440)
    expect(frameBox.height).toBe(900)

    // Verify CSS: margin 0, border-radius 0, no box-shadow
    const frameStyles = await page.locator('.app-frame').evaluate((el) => {
      const s = window.getComputedStyle(el)
      return {
        margin: s.margin,
        borderRadius: s.borderRadius,
        boxShadow: s.boxShadow,
      }
    })
    expect(frameStyles.margin).toBe('0px')
    expect(frameStyles.borderRadius).toBe('0px')
    expect(frameStyles.boxShadow).toBe('none')

    // Verify zero window scroll
    const scrollY = await page.evaluate(() => window.scrollY)
    expect(scrollY).toBe(0)

    // Capture desktop dashboard screenshot
    await page.screenshot({ path: path.join(outputDir, '01-desktop-dashboard-1440px.png') })
  })

  test('3. Desktop 1440px: Analysis History typography, hierarchy, and table alignment', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/?view=history')
    await expect(page.locator('.history-page')).toBeVisible({ timeout: 10_000 })

    // Verify typography hierarchy
    await expect(page.locator('.history-heading .eyebrow')).toHaveText('SAVED WORK')
    await expect(page.locator('.history-title')).toHaveText('Analysis history')
    await expect(page.locator('.history-subtitle')).toBeVisible()

    // Verify summary bar structure (not running together)
    const summaryBar = page.locator('.history-summary-bar')
    await expect(summaryBar).toBeVisible()
    const summaryCount = page.locator('.history-summary-count')
    await expect(summaryCount).toBeVisible()
    await expect(page.locator('.count-text')).toHaveText('saved records')
    const summaryNote = page.locator('.history-summary-note')
    await expect(summaryNote).toBeVisible()
    await expect(summaryNote).toContainText('Analysis results are stored in this local workspace.')

    // Verify table structure and alignment
    await expect(page.locator('.history-table-container')).toBeVisible()
    await expect(page.locator('.history-header')).toBeVisible()
    const rows = page.locator('.history-row')
    await expect(rows.first()).toBeVisible({ timeout: 5_000 })
    await expect(rows.first().locator('.item-filename')).toBeVisible()
    await expect(rows.first().locator('.provider-cell')).toBeVisible()
    await expect(rows.first().locator('.date-cell')).toBeVisible()
    await expect(rows.first().locator('.status-badge')).toBeVisible()

    // Capture desktop history screenshot
    await page.screenshot({ path: path.join(outputDir, '02-desktop-history-1440px.png') })
  })

  test('4. Desktop 1440px: Natural Language Design Studio geometry preview visibility', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })

    // Verify split-pane grid
    const workspace = page.locator('.studio-workspace')
    await expect(workspace).toBeVisible()

    // Verify Structural Geometry Preview panel
    const rightPane = page.locator('.studio-right-pane')
    await expect(rightPane).toBeVisible()
    await expect(page.locator('.canvas-title')).toContainText('Structural Geometry Preview')

    // Verify canvas viewport is visible and receives ample space (>= 480px)
    const viewport = page.locator('.canvas-viewport')
    await expect(viewport).toBeVisible()
    const viewportBox = await viewport.boundingBox()
    expect(viewportBox.width).toBeGreaterThan(400)
    expect(viewportBox.height).toBeGreaterThanOrEqual(480)

    // Capture desktop design studio screenshot
    await page.screenshot({ path: path.join(outputDir, '03-desktop-design-1440px.png') })
  })

  test('5. Tablet viewports (1024px and 768px): Proper adaptation without cramped navigation', async ({ page }) => {
    // 1024px Tablet Landscape
    await page.setViewportSize({ width: 1024, height: 768 })
    await page.goto('/')
    await expect(page.locator('.dashboard-page')).toBeVisible()
    await expect(page.locator('.sidebar')).toBeVisible()
    const sidebarWidth1024 = await page.locator('.sidebar').evaluate((el) => el.getBoundingClientRect().width)
    expect(sidebarWidth1024).toBeLessThanOrEqual(210)

    // 768px Tablet Portrait
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/')
    await expect(page.locator('.dashboard-page')).toBeVisible()
    // At 768px, mobile topbar toggle is available
    await expect(page.locator('.btn-mobile-nav-toggle')).toBeVisible()
  })

  test('6. Mobile 390px: Clean collapsible navigation drawer, legible labels, touch targets, and responsive pages', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')
    await expect(page.locator('.dashboard-page')).toBeVisible({ timeout: 10_000 })

    // 1. Desktop sidebar should be hidden
    await expect(page.locator('.sidebar')).not.toBeVisible()

    // 2. Mobile toggle and brand logo should be visible in topbar
    const toggleBtn = page.locator('.btn-mobile-nav-toggle')
    await expect(toggleBtn).toBeVisible()
    await expect(page.locator('.mobile-header-brand')).toBeVisible()

    // Check touch target height (>= 36px)
    const toggleBox = await toggleBtn.boundingBox()
    expect(toggleBox.height).toBeGreaterThanOrEqual(36)

    // Capture mobile dashboard screenshot
    await page.screenshot({ path: path.join(outputDir, '04-mobile-dashboard-390px.png') })

    // 3. Open mobile drawer
    await toggleBtn.click()
    const drawer = page.locator('.mobile-drawer')
    await expect(drawer).toBeVisible()

    // Check mobile nav items are readable and vertical
    const mobileNavItems = drawer.locator('.nav-item')
    await expect(mobileNavItems).toHaveCount(4)
    await expect(mobileNavItems.nth(0)).toContainText('Dashboard')
    await expect(mobileNavItems.nth(1)).toContainText('Natural Language Design')
    await expect(mobileNavItems.nth(2)).toContainText('New analysis')
    await expect(mobileNavItems.nth(3)).toContainText('Analysis history')

    // Touch target of mobile nav item >= 40px
    const navItemBox = await mobileNavItems.nth(0).boundingBox()
    expect(navItemBox.height).toBeGreaterThanOrEqual(40)

    // 4. Navigate to Analysis History via mobile drawer
    await mobileNavItems.nth(3).click()
    await expect(page.locator('.history-page')).toBeVisible({ timeout: 10_000 })
    await expect(drawer).not.toBeVisible()

    // Capture mobile history screenshot
    await page.screenshot({ path: path.join(outputDir, '05-mobile-history-390px.png') })

    // 5. Navigate to Natural Language Design
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })

    // Structural Geometry Preview should remain visible and sized on mobile
    const mobilePreview = page.locator('.canvas-viewport')
    await expect(mobilePreview).toBeVisible()
    const mobilePreviewBox = await mobilePreview.boundingBox()
    expect(mobilePreviewBox.height).toBeGreaterThanOrEqual(280)

    // Capture mobile design studio screenshot
    await page.screenshot({ path: path.join(outputDir, '06-mobile-design-390px.png') })
  })

  test('7. Natural Language Design: Clean textarea rendering, placeholder, and no undefined text', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })

    const textarea = page.locator('.studio-left-pane .design-textarea')
    await expect(textarea).toBeVisible()

    // 1. Initial state: textarea must be empty, no literal 'undefined'
    const initialVal = await textarea.inputValue()
    expect(initialVal).not.toContain('undefined')

    const placeholder = await textarea.getAttribute('placeholder')
    expect(placeholder).toBeTruthy()
    expect(placeholder).not.toContain('undefined')

    // 2. Submit ambiguous prompt to trigger clarification chips
    await textarea.fill('truss')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 25_000 })

    // If clarification questions appear, verify no 'undefined' in question text or options
    const clarificationSection = proposalCard.locator('.clarification-section')
    if (await clarificationSection.isVisible()) {
      const promptText = await clarificationSection.locator('.cq-prompt').first().textContent()
      expect(promptText).not.toContain('undefined')

      // Click the first clarification chip
      const firstChip = clarificationSection.locator('.cq-chip').first()
      const chipLabel = (await firstChip.textContent() || '').trim()
      await firstChip.click()

      // Textarea must be populated with the clean answer, never "undefined:"
      const populatedVal = await textarea.inputValue()
      expect(populatedVal).not.toContain('undefined')
      expect(populatedVal).toContain(chipLabel)
    }

    // Capture screenshot of clean textarea
    await page.screenshot({ path: path.join(outputDir, '07-nl-design-textarea-clean.png') })
  })

  test('8. Mobile Truss Editor 390px: Full viewport width canvas, floating tool dock, and responsive results', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })

    // Select existing analysis to open in editor
    const select = page.locator('#analysis-select')
    await expect(select).toBeVisible({ timeout: 10_000 })
    await expect(async () => {
      const count = await select.locator('option').count()
      expect(count).toBeGreaterThan(1)
    }).toPass({ timeout: 10_000 })
    await select.selectOption({ index: 1 })

    // Open analysis in editor
    const openEditorBtn = page.locator('.btn-open-editor')
    await expect(openEditorBtn).toBeVisible({ timeout: 10_000 })
    await openEditorBtn.click()

    // Editor workspace must be visible
    const editor = page.locator('.truss-editor-workspace')
    await expect(editor).toBeVisible({ timeout: 20_000 })

    // 1. App-frame and canvas must use full 390px available viewport
    const appFrameBox = await page.locator('.app-frame.in-editor-frame').boundingBox()
    expect(appFrameBox.width).toBe(390)

    const canvasBox = await page.locator('.canvas-container').boundingBox()
    expect(canvasBox.width).toBe(390)
    expect(canvasBox.height).toBeGreaterThan(250)

    // 2. Mobile floating construction toolbar must be visible
    const mobileToolBar = page.locator('.mobile-construction-bar')
    await expect(mobileToolBar).toBeVisible()

    // Verify tools: Select, Joint, Member, etc.
    const jointBtn = mobileToolBar.locator('button:has-text("Joint")')
    await expect(jointBtn).toBeVisible()
    await jointBtn.click()
    await expect(jointBtn).toHaveClass(/active/)

    // Capture mobile full-canvas screenshot
    await page.screenshot({ path: path.join(outputDir, '08-mobile-truss-editor-full-canvas.png') })

    // 3. Mark reviewed and Solve to test Analysis Results panel
    const reviewBtn = page.locator('.editor-topbar .btn-review')
    if (await reviewBtn.isEnabled()) {
      await reviewBtn.click()
      await page.waitForTimeout(500)
    }

    const solveBtn = page.locator('.editor-topbar .btn-solve')
    if (await solveBtn.isEnabled()) {
      await solveBtn.click()
      // Confirm solver modal
      const confirmSubmitBtn = page.locator('.cdialog-confirm')
      await expect(confirmSubmitBtn).toBeVisible({ timeout: 5_000 })
      await confirmSubmitBtn.click()

      const resultsPanel = page.locator('.analysis-results-panel')
      await expect(resultsPanel).toBeVisible({ timeout: 15_000 })

      // Panel must occupy full 390px width without horizontal viewport overflow
      const resultsBox = await resultsPanel.boundingBox()
      expect(resultsBox.width).toBe(390)

      // Capture mobile results panel screenshot
      await page.screenshot({ path: path.join(outputDir, '09-mobile-truss-editor-results.png') })
    }
  })
})
