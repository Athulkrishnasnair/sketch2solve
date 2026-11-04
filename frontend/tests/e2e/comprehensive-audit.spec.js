import { readFileSync } from 'node:fs'
import path from 'node:path'
import { test, expect } from '@playwright/test'

const configDirectory = import.meta.dirname
const evaluationDirectory = path.resolve(configDirectory, '../../../backend/evaluation/sketches')

const VIEWPORTS = {
  desktop: { width: 1920, height: 1080 },
  laptop: { width: 1366, height: 768 },
  tablet: { width: 768, height: 1024 },
  mobile: { width: 375, height: 667 },
}

test.describe('Comprehensive Application Audit', () => {
  // 1. Audit Viewports, Layout Overflow & Responsiveness across all main pages
  test('Audit 1: Layout Overflow and Responsiveness across all viewports', async ({ page }) => {
    const pagesToTest = [
      { name: 'Dashboard', url: '/' },
      { name: 'Natural Language Design Studio', url: '/?view=design' },
      { name: 'New Analysis', url: '/?view=new' },
      { name: 'Analysis History', url: '/?view=history' },
    ]

    const overflowFindings = []

    for (const [vpName, vpSize] of Object.entries(VIEWPORTS)) {
      await page.setViewportSize(vpSize)
      for (const p of pagesToTest) {
        await page.goto(p.url, { waitUntil: 'networkidle' })
        const metrics = await page.evaluate(() => {
          const doc = document.documentElement
          const body = document.body
          const scrollW = Math.max(doc.scrollWidth, body.scrollWidth)
          const clientW = window.innerWidth
          const hasHorizontalOverflow = scrollW > clientW + 1 // 1px threshold for subpixel

          // Check if any element specifically overflows the viewport
          const overflowingElements = []
          const allEls = document.querySelectorAll('*')
          for (const el of allEls) {
            const rect = el.getBoundingClientRect()
            if (rect.right > clientW + 2) {
              overflowingElements.push({
                tag: el.tagName,
                className: el.className?.toString?.() || '',
                id: el.id,
                right: rect.right,
                width: rect.width,
              })
              if (overflowingElements.length >= 5) break
            }
          }

          return {
            scrollW,
            clientW,
            hasHorizontalOverflow,
            overflowingElements,
          }
        })

        if (metrics.hasHorizontalOverflow) {
          overflowFindings.push({
            viewport: vpName,
            page: p.name,
            scrollW: metrics.scrollW,
            clientW: metrics.clientW,
            elements: metrics.overflowingElements,
          })
        }
      }
    }

    console.log('--- OVERFLOW FINDINGS ---')
    console.log(JSON.stringify(overflowFindings, null, 2))
  })

  // 2. Interactive Element Inventory & Functional Audit
  test('Audit 2: Complete Interactive Element Inventory & State Checks', async ({ page }) => {
    const auditLog = []
    const consoleMessages = []
    const failedRequests = []

    page.on('console', (msg) => {
      consoleMessages.push({ type: msg.type(), text: msg.text() })
    })
    page.on('requestfailed', (req) => {
      failedRequests.push({ url: req.url(), method: req.method(), failure: req.failure()?.errorText })
    })

    // --- DASHBOARD ---
    await page.goto('/')
    await expect(page.locator('.dashboard-welcome')).toBeVisible()

    // 1. New Analysis Button
    const newBtn = page.locator('.dashboard-actions .dashboard-primary')
    auditLog.push({
      page: 'Dashboard',
      element: 'button.dashboard-primary',
      label: '＋ New analysis',
      hasHandler: await newBtn.count() > 0,
      enabled: await newBtn.isEnabled(),
    })

    // 2. Create with AI Button (toggle)
    const createAiBtn = page.locator('.dashboard-ai-btn')
    await expect(createAiBtn).toBeVisible()
    await createAiBtn.click()
    const workbenchVisible = await page.locator('.dashboard-ai-workbench').isVisible()
    auditLog.push({
      page: 'Dashboard',
      element: 'button.dashboard-ai-btn',
      label: 'Create with AI',
      hasHandler: true,
      togglesWorkbench: workbenchVisible,
    })

    // 3. Close Workbench Button
    const closeWorkbenchBtn = page.locator('.btn-close-workbench')
    await closeWorkbenchBtn.click()
    const workbenchClosed = !(await page.locator('.dashboard-ai-workbench').isVisible())
    auditLog.push({
      page: 'Dashboard',
      element: 'button.btn-close-workbench',
      label: '✕',
      hasHandler: true,
      closesWorkbench: workbenchClosed,
    })

    // 4. History Links
    const historyLink = page.locator('.dashboard-actions .dashboard-link')
    auditLog.push({
      page: 'Dashboard',
      element: 'button.dashboard-link',
      label: 'Browse all history ↗',
      hasHandler: await historyLink.count() > 0,
      enabled: await historyLink.isEnabled(),
    })

    // 5. Workbench Prompt Submission & Examples
    await createAiBtn.click()
    const exampleChips = page.locator('.workbench-chip')
    const chipCount = await exampleChips.count()
    auditLog.push({
      page: 'Dashboard',
      element: '.workbench-chip',
      count: chipCount,
      label: 'Example Prompt Chips',
      hasHandler: chipCount > 0,
    })

    // Submit first chip
    await exampleChips.first().click()
    const proposalCard = page.locator('.dashboard-ai-workbench .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 10_000 })
    auditLog.push({
      page: 'Dashboard',
      element: '.design-proposal-card',
      label: 'Generated Proposal Card',
      rendered: true,
      hasApply: await proposalCard.locator('.btn-apply').isVisible(),
      hasDiscard: await proposalCard.locator('.btn-discard').isVisible(),
    })

    // Apply proposal to create record and enter editor
    await proposalCard.locator('.btn-apply').click()
    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })

    // --- TRUSS EDITOR ---
    // Test all topbar buttons
    const backBtn = page.locator('.editor-topbar .back-btn')
    const undoBtn = page.locator('.editor-topbar button[title="Undo (Ctrl+Z)"]')
    const redoBtn = page.locator('.editor-topbar button[title="Redo (Ctrl+Y)"]')
    const saveBtn = page.locator('.editor-topbar .btn-save')
    const reviewBtn = page.locator('.editor-topbar .btn-review')
    const solveBtn = page.locator('.editor-topbar .btn-solve')
    const designAiBtn = page.locator('.editor-topbar .btn-ai')

    auditLog.push({
      page: 'TrussEditor',
      element: 'topbar buttons',
      back: { visible: await backBtn.isVisible(), enabled: await backBtn.isEnabled() },
      undo: { visible: await undoBtn.isVisible(), enabled: await undoBtn.isEnabled() },
      redo: { visible: await redoBtn.isVisible(), enabled: await redoBtn.isEnabled() },
      save: { visible: await saveBtn.isVisible(), enabled: await saveBtn.isEnabled() },
      review: { visible: await reviewBtn.isVisible(), enabled: await reviewBtn.isEnabled() },
      solve: { visible: await solveBtn.isVisible(), enabled: await solveBtn.isEnabled() },
      designAi: { visible: await designAiBtn.isVisible(), enabled: await designAiBtn.isEnabled() },
    })

    // Test tool palette buttons
    const tools = ['select', 'pan', 'joint', 'member', 'measure', 'pin', 'roller', 'load', 'delete']
    const toolResults = {}
    for (const tool of tools) {
      const tile = page.locator(`.tool-tile[class*="tool-${tool}"], .tool-tile:has-text("${tool}"), button[title*="${tool}"]`).first()
      if (await tile.count() > 0) {
        await tile.click()
        const isActive = await tile.evaluate((el) => el.classList.contains('active'))
        toolResults[tool] = { exists: true, activates: isActive }
      } else {
        toolResults[tool] = { exists: false }
      }
    }
    auditLog.push({ page: 'TrussEditor', element: 'tool palette', tools: toolResults })

    // Test canvas controls
    const zoomInBtn = page.locator('.canvas-floating-controls button[title="Zoom In"]')
    const zoomOutBtn = page.locator('.canvas-floating-controls button[title="Zoom Out"]')
    const fitViewBtn = page.locator('.canvas-floating-controls button[title="Fit Content"]')
    const gridToggle = page.locator('.canvas-floating-controls button[title="Toggle Grid"]')
    const snapToggle = page.locator('.canvas-floating-controls button[title="Snap to Grid"]')
    const aiLayerToggle = page.locator('.canvas-floating-controls button[title="AI Proposal Layer"]')

    auditLog.push({
      page: 'TrussEditor',
      element: 'floating canvas toolbar',
      zoomIn: await zoomInBtn.isVisible(),
      zoomOut: await zoomOutBtn.isVisible(),
      fitView: await fitViewBtn.isVisible(),
      gridToggle: await gridToggle.isVisible(),
      snapToggle: await snapToggle.isVisible(),
      aiLayerToggle: await aiLayerToggle.isVisible(),
    })

    // Test solver submission on the created triangular truss
    // Verify review and solve workflow
    await reviewBtn.click()
    await expect(solveBtn).toBeEnabled({ timeout: 5_000 })
    await solveBtn.click()

    // Handle ConfirmDialog
    const confirmDialog = page.locator('.cdialog-panel')
    await expect(confirmDialog).toBeVisible()
    await confirmDialog.locator('.cdialog-confirm').click()

    // Results panel appears
    const resultsPanel = page.locator('.analysis-results-panel')
    await expect(resultsPanel).toBeVisible({ timeout: 10_000 })

    // Audit Results Panel Tabs
    const tabs = ['Summary & Matrix', 'Member Forces', 'Support Reactions', 'Limitations']
    const tabAudit = {}
    for (const tab of tabs) {
      const tabBtn = resultsPanel.getByRole('button', { name: new RegExp(tab, 'i') })
      const exists = await tabBtn.count() > 0
      if (exists) {
        await tabBtn.click()
        tabAudit[tab] = { clickable: true }
      } else {
        tabAudit[tab] = { clickable: false }
      }
    }
    auditLog.push({ page: 'ResultsPanel', element: 'tabs', tabs: tabAudit })

    // Test Stale Results Protection: Move a joint
    // Close results panel before interacting with canvas geometry
    const closeResultsBtn = resultsPanel.locator('.btn-panel-action[title*="Close"], button[aria-label="Close"]').first()
    if (await closeResultsBtn.count() > 0) {
      await closeResultsBtn.click()
    } else {
      await page.locator('.editor-topbar .btn-results').click()
    }
    await expect(resultsPanel).not.toBeVisible()

    // Drag or update via inspector
    // Select the select tool first
    await page.locator('.tool-tile[title*="Select"]').click()
    const firstJoint = page.locator('.truss-joints-group circle.truss-joint-node').first()
    await firstJoint.click()
    const inspector = page.locator('.editor-sidebar .inspector-section')
    await expect(inspector).toBeVisible()
    const xInput = inspector.locator('input[type="number"], input[inputmode="decimal"]').first()
    const curVal = await xInput.inputValue()
    await xInput.fill(String(Number(curVal) + 0.5))
    await xInput.dispatchEvent('change')

    // Reopen results panel to verify stale banner
    await page.locator('.editor-topbar .btn-results').click()
    await expect(resultsPanel).toBeVisible()

    // Verify stale banner and pill
    const isStale = await resultsPanel.locator('.banner-stale').isVisible()
    const statusText = (await page.locator('.editor-statusbar').textContent()) || ''
    const statusStale = statusText.includes('Results stale')
    auditLog.push({
      page: 'TrussEditor',
      element: 'stale results detection',
      staleBannerVisible: isStale,
      statusBarShowsStale: statusStale,
    })

    console.log('--- INTERACTIVE ELEMENT AUDIT LOG ---')
    console.log(JSON.stringify(auditLog, null, 2))
    console.log('--- CONSOLE MESSAGES ---')
    console.log(JSON.stringify(consoleMessages, null, 2))
    console.log('--- FAILED REQUESTS ---')
    console.log(JSON.stringify(failedRequests, null, 2))
  })

  // 3. Audit Natural Language Design Studio Workflows
  test('Audit 3: Design Studio CREATE, MODIFY, EXPLAIN & Target Selection', async ({ page }) => {
    const studioAudit = {}

    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible()

    // 1. Selector for target analyses
    const select = page.locator('#analysis-select')
    await expect(select).toBeVisible()
    const optionsCount = await select.locator('option').count()
    studioAudit.targetSelector = { optionsCount }

    // 2. Intent Tabs
    const intentTabs = ['Auto', 'Create', 'Modify', 'Explain']
    for (const intent of intentTabs) {
      const btn = page.locator(`.intent-btn:has-text("${intent}")`)
      studioAudit[`intentTab_${intent}`] = await btn.count() > 0
    }

    // 3. Test CREATE Intent
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a Warren truss with 4 panels and 10 m span')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 10_000 })
    studioAudit.createProposal = {
      intent: await proposalCard.locator('.intent-pill').textContent(),
      valid: await proposalCard.locator('.validation-pill').textContent(),
      cadSvgRendered: await page.locator('.studio-right-pane .cad-svg').isVisible(),
    }

    // 4. Test Discard
    await proposalCard.locator('.btn-discard').click()
    studioAudit.proposalDiscarded = (await page.locator('.studio-left-pane .design-proposal-card').count()) === 0

    // 5. Test EXPLAIN Intent
    await page.locator('.intent-btn:has-text("Explain")').click()
    await textarea.fill('Explain how truss equilibrium works')
    await page.locator('.studio-left-pane .btn-submit').click()
    const explainCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(explainCard).toBeVisible({ timeout: 10_000 })
    studioAudit.explainProposal = {
      intent: await explainCard.locator('.intent-pill').textContent(),
      hasExplanation: (await explainCard.locator('.card-explanation').textContent())?.length > 10,
    }

    console.log('--- DESIGN STUDIO AUDIT ---')
    console.log(JSON.stringify(studioAudit, null, 2))
  })
})

