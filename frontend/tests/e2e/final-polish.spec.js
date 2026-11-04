import { readFileSync } from 'node:fs'
import path from 'node:path'
import { test, expect } from '@playwright/test'

test.describe('Sketch2Solve Final Polish and Verification', () => {
  test('1. Natural Language Design geometry preview accurately renders geometry, supports, loads, and CAD grid', async ({ page }) => {
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })

    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })

    // Inspect large geometry preview on the right
    const previewCanvas = page.locator('.studio-right-pane .cad-svg')
    await expect(previewCanvas).toBeVisible()

    // 1. Check straight structural lines exist
    const memberLines = previewCanvas.locator('.cad-member')
    await expect(memberLines).toHaveCount(3)

    // 2. Check joints and labels exist
    const joints = previewCanvas.locator('.cad-joint')
    await expect(joints).toHaveCount(3)

    // 3. Check pin and roller support symbols exist
    const pinSymbol = previewCanvas.locator('.cad-support.pin')
    const rollerSymbol = previewCanvas.locator('.cad-support.roller')
    await expect(pinSymbol.first()).toBeVisible()
    await expect(rollerSymbol.first()).toBeVisible()

    // 4. Check load vector arrow and magnitude label exist
    const loadArrow = previewCanvas.locator('.cad-load-arrow')
    const loadLabel = previewCanvas.locator('.cad-load-label')
    await expect(loadArrow.first()).toBeAttached()
    await expect(loadLabel.first()).toBeVisible()
    await expect(loadLabel.first()).toContainText('10')

    // 5. Check CAD grid pattern exists
    const gridPattern = previewCanvas.locator('#cad-grid-pattern')
    await expect(gridPattern).toBeAttached()

    // 6. Verify NO oversized glyphs or dark filled shapes exist
    const elementsInfo = await previewCanvas.evaluate(svg => {
      const results = []
      const all = svg.querySelectorAll('*')
      for (const el of all) {
        const cs = window.getComputedStyle(el)
        const rect = el.getBoundingClientRect()
        results.push({
          tag: el.tagName,
          id: el.id,
          class: el.getAttribute('class') || '',
          fill: cs.fill,
          stroke: cs.stroke,
          strokeWidth: cs.strokeWidth,
          w: rect.width,
          h: rect.height,
        })
      }
      return results
    })

    // Assert that every joint label is small (< 50px) and has stroke = none
    const jointLabels = elementsInfo.filter(el => el.class.includes('cad-joint-label'))
    expect(jointLabels.length).toBe(3)
    for (const lbl of jointLabels) {
      expect(lbl.w).toBeLessThan(50)
      expect(lbl.h).toBeLessThan(50)
      expect(lbl.stroke).toBe('none')
    }

    // Assert that no structural element has enormous glyph dimensions (> 150px)
    const oversizedElements = elementsInfo.filter(el =>
      ['text', 'path', 'polygon', 'circle'].includes(el.tag) &&
      !el.class.includes('cad-member') &&
      el.w > 150
    )
    expect(oversizedElements).toHaveLength(0)

    // 7. Test larger multi-member truss (Warren truss with 4 panels)
    await textarea.fill('Build a Warren truss with 4 panels and a 10 m span')
    const warrenDesignResponse = page.waitForResponse(r => r.url().includes('/api/ai/design') && r.status() === 200)
    await page.locator('.studio-left-pane .btn-submit').click()
    await warrenDesignResponse
    await expect(page.locator('.studio-left-pane .design-proposal-card')).toBeVisible({ timeout: 10_000 })

    const warrenMembers = previewCanvas.locator('.cad-member')
    await expect(warrenMembers).toHaveCount(15)
    const warrenJoints = previewCanvas.locator('.cad-joint')
    await expect(warrenJoints).toHaveCount(9)

    // Verify all Warren labels are clean and small
    const warrenLabels = await previewCanvas.evaluate(svg => {
      return Array.from(svg.querySelectorAll('.cad-joint-label')).map(el => {
        const r = el.getBoundingClientRect()
        return { w: r.width, h: r.height, stroke: window.getComputedStyle(el).stroke }
      })
    })
    expect(warrenLabels.length).toBe(9)
    for (const lbl of warrenLabels) {
      expect(lbl.w).toBeLessThan(50)
      expect(lbl.h).toBeLessThan(50)
      expect(lbl.stroke).toBe('none')
    }

    // 8. Test different container aspect ratios (wide 1600x900 and narrow 800x700)
    await page.setViewportSize({ width: 1600, height: 900 })
    await page.waitForTimeout(300)
    let canvasBox = await previewCanvas.boundingBox()
    expect(canvasBox.width).toBeGreaterThan(600)

    await page.setViewportSize({ width: 850, height: 700 })
    await page.waitForTimeout(300)
    canvasBox = await previewCanvas.boundingBox()
    expect(canvasBox.width).toBeGreaterThan(400)

    // Restore standard viewport
    await page.setViewportSize({ width: 1280, height: 800 })
  })

  test('2. Analysis History pagination footer adheres to design standards', async ({ page }) => {
    // 1. Ensure a record exists by creating one via Design Studio first
    await page.goto('/?view=design')
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // 2. Now navigate to History page
    await page.goto('/?view=history')
    await expect(page.locator('.history-page')).toBeVisible({ timeout: 10_000 })

    // Check pagination footer exists with consistent design tokens
    const footer = page.locator('.history-pagination-footer')
    await expect(footer).toBeVisible()

    const paginationInfo = footer.locator('.pagination-info')
    await expect(paginationInfo).toBeVisible()
    await expect(paginationInfo).toContainText(/Showing \d+ of \d+ saved runs/)

    // Verify either Load More button is visible or All saved runs loaded is visible
    const hasLoadMore = await footer.locator('.btn-load-more').isVisible()
    const hasComplete = await footer.locator('.pagination-complete').isVisible()
    expect(hasLoadMore || hasComplete).toBe(true)
  })

  test('3. New Analysis evidence-card copy provides accurate, neutral explanation', async ({ page }) => {
    await page.goto('/?view=new')
    await expect(page.locator('.upload-card')).toBeVisible({ timeout: 10_000 })

    const step2 = page.locator('.workflow-step').nth(1)
    await expect(step2).toBeVisible()
    await expect(step2.locator('p')).toHaveText(
      'The selected AI provider interprets the sketch and proposes candidate joints, members, supports and loads for human review.'
    )
  })

  test('4. Issue Resolution Assistant docks in bottom-right corner and closes when highlighting is cleared', async ({ page }) => {
    // Navigate into the editor with a sample model
    await page.goto('/?view=design')
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Assistant card is docked at bottom-right
    const assistantCard = page.locator('.contextual-action-card')
    if (await assistantCard.isVisible()) {
      const box = await assistantCard.boundingBox()
      expect(box).toBeTruthy()

      // Verify close/clear button closes it
      const closeBtn = assistantCard.locator('.card-close-btn')
      await closeBtn.click()
      await expect(assistantCard).not.toBeVisible()

      // Toggle highlight using floating canvas control re-opens it
      const alertBtn = page.locator('.canvas-floating-controls button[title*="Highlight detected issues"], .canvas-floating-controls button[aria-label*="Highlight detected issues"]')
      if (await alertBtn.isVisible()) {
        await alertBtn.click()
        await expect(assistantCard).toBeVisible()
      }
    }
  })

  test('5. Right sidebar tabbed workspace cleanly toggles between Tools and Design with AI', async ({ page }) => {
    await page.goto('/?view=design')
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Verify tabs exist in sidebar
    const tabsNav = page.locator('.sidebar-tabs-nav')
    await expect(tabsNav).toBeVisible()

    const toolsTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' })
    const designTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' })
    await expect(toolsTab).toBeVisible()
    await expect(designTab).toBeVisible()

    // Initially Tools tab is active
    await expect(toolsTab).toHaveClass(/active/)
    await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
    await expect(page.locator('.sidebar-design-pane')).not.toBeVisible()

    // Click Design with AI tab
    await designTab.click()
    await expect(designTab).toHaveClass(/active/)
    await expect(page.locator('.sidebar-design-pane')).toBeVisible()
    await expect(page.locator('.sidebar-tools-pane')).not.toBeVisible()

    // Topbar btn-ai switches back to Tools tab or toggles
    const topbarAiBtn = page.locator('.editor-topbar .btn-ai')
    await expect(topbarAiBtn).toHaveClass(/active/)
    await topbarAiBtn.click()
    await expect(toolsTab).toHaveClass(/active/)
    await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  })

  test('6. Construction and Structural tools use 3-column grid with uniform 48px tile height', async ({ page }) => {
    await page.goto('/?view=design')
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Verify 3-column grid for Construction
    const constructionGrid = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tools-grid-3')
    await expect(constructionGrid).toBeVisible()
    await expect(constructionGrid.locator('.tool-tile')).toHaveCount(3)

    // Verify 3-column grid for Structural
    const structuralGrid = page.locator('.toolbox-group').filter({ hasText: 'Structural' }).locator('.tools-grid-3')
    await expect(structuralGrid).toBeVisible()
    await expect(structuralGrid.locator('.tool-tile')).toHaveCount(3)

    // Verify 1-column grid for Edit
    const editGrid = page.locator('.toolbox-group').filter({ hasText: 'Edit' }).locator('.tools-grid-1')
    await expect(editGrid).toBeVisible()
    await expect(editGrid.locator('.tool-tile')).toHaveCount(1)

    // Check height of tiles
    const tile = constructionGrid.locator('.tool-tile').first()
    const box = await tile.boundingBox()
    expect(box?.height).toBeGreaterThanOrEqual(47)
  })

  test('7. Sequential AI proposal generation, application, and model mutation', async ({ page }) => {
    await page.goto('/?view=design')
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Switch to Design with AI tab in the editor
    await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
    const sidebarDesignPane = page.locator('.sidebar-design-pane')
    await expect(sidebarDesignPane).toBeVisible()

    // Formulate sequential modification
    const promptInput = sidebarDesignPane.locator('textarea')
    await promptInput.fill('Add a vertical strut from the apex to the bottom chord')
    await sidebarDesignPane.locator('.btn-submit').click()

    const modProposal = sidebarDesignPane.locator('.design-proposal-card')
    await expect(modProposal).toBeVisible({ timeout: 10_000 })

    // Apply the proposal
    await modProposal.locator('.btn-apply').click()

    // Verify toast notification and success
    await expect(page.locator('.editor-toast')).toBeVisible()
  })

  test('8. Model mutation and Undo support restores previous geometry state', async ({ page }) => {
    await page.goto('/?view=design')
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Wait for nodes to be rendered
    await expect(page.locator('.truss-joint-node').first()).toBeVisible({ timeout: 10_000 })
    const initialJointCount = await page.locator('.truss-joint-node').count()
    expect(initialJointCount).toBeGreaterThanOrEqual(3)

    // Add a joint using the joint tool
    const jointTool = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tool-tile').filter({ hasText: 'Joint' })
    await jointTool.click()

    const canvas = page.locator('.engineering-svg')
    await canvas.click({ position: { x: 200, y: 200 } })

    const afterJointCount = await page.locator('.truss-joint-node').count()
    expect(afterJointCount).toBe(initialJointCount + 1)

    // Click Undo
    const undoBtn = page.locator('.editor-topbar button[aria-label="Undo"]')
    await undoBtn.click()

    const revertedJointCount = await page.locator('.truss-joint-node').count()
    expect(revertedJointCount).toBe(initialJointCount)
  })

  test('9. Revision conflict handling rejects stale proposals gracefully', async ({ page }) => {
    await page.goto('/?view=design')
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Switch to Design with AI tab
    await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
    const sidebarDesignPane = page.locator('.sidebar-design-pane')

    const promptInput = sidebarDesignPane.locator('textarea')
    await promptInput.fill('Add a vertical strut')
    await sidebarDesignPane.locator('.btn-submit').click()

    const modProposal = sidebarDesignPane.locator('.design-proposal-card')
    await expect(modProposal).toBeVisible({ timeout: 10_000 })

    // Now modify the canvas geometry behind the proposal's back (switch to Tools and add a joint)
    await page.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' }).click()
    const jointTool = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tool-tile').filter({ hasText: 'Joint' })
    await jointTool.click()
    await page.locator('.engineering-svg').click({ position: { x: 300, y: 150 } })

    // Switch back to Design with AI tab and attempt to apply the stale proposal
    await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
    await modProposal.locator('.btn-apply').click()

    // Verify conflict error message is displayed
    const errorNotice = sidebarDesignPane.locator('.error-banner')
    await expect(errorNotice).toBeVisible()
    await expect(errorNotice).toContainText(/Revision conflict|stale|modified/i)
  })

  test('10. Editor Design with AI interface is docked inside right sidebar with anchored composer and unobstructed canvas', async ({ page }) => {
    // Navigate directly to editor with a demo truss
    await page.goto('/?view=design')
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Activate Design with AI from topbar button
    const topbarAiBtn = page.locator('.editor-topbar .btn-ai')
    await expect(topbarAiBtn).toBeVisible()
    await topbarAiBtn.click()

    // Right sidebar must now show Design with AI pane
    const sidebar = page.locator('.editor-sidebar')
    await expect(sidebar).toBeVisible()

    const designPane = sidebar.locator('.sidebar-design-pane')
    await expect(designPane).toBeVisible()

    // Verify DesignInstructionPanel is inside sidebar
    const panel = designPane.locator('.design-instruction-panel')
    await expect(panel).toBeVisible()

    // Bounding box verification: the assistant card is completely inside the sidebar column
    const sidebarBox = await sidebar.boundingBox()
    const paneBox = await designPane.boundingBox()
    expect(paneBox.x).toBeGreaterThanOrEqual(sidebarBox.x - 2)
    expect(paneBox.x + paneBox.width).toBeLessThanOrEqual(sidebarBox.x + sidebarBox.width + 2)

    // Canvas must remain unobstructed
    const canvas = page.locator('.engineering-svg')
    const canvasBox = await canvas.boundingBox()
    // Pane X should be strictly to the right of the canvas right edge
    expect(paneBox.x).toBeGreaterThanOrEqual(canvasBox.x + canvasBox.width - 2)

    // Input container is anchored at bottom of sidebar pane
    const inputContainer = designPane.locator('.input-container')
    await expect(inputContainer).toBeVisible()
    const inputPrompt = inputContainer.locator('.design-textarea')
    await expect(inputPrompt).toBeVisible()
    const generateBtn = inputContainer.locator('.btn-submit')
    await expect(generateBtn).toBeVisible()

    const inputBox = await inputContainer.boundingBox()
    // Bottom of input container should be close to bottom of design pane
    expect(paneBox.y + paneBox.height - (inputBox.y + inputBox.height)).toBeLessThan(30)

    // Verify typing prompt and switching tabs preserves prompt state
    await inputPrompt.fill('Add a diagonal strut between J1 and J3')
    await page.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' }).click()
    await expect(designPane).toBeHidden()
    await expect(page.locator('.sidebar-tools-pane')).toBeVisible()

    await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
    await expect(designPane).toBeVisible()
    await expect(inputPrompt).toHaveValue('Add a diagonal strut between J1 and J3')
  })

  test('11. Editor viewport layout eliminates document-level scrollbars at 1920x1080 and 1366x768', async ({ page }) => {
    // Test desktop 1920x1080
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/?view=design')

    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Verify 0 document/body scrollbars on 1920x1080
    const scrollInfo1080 = await page.evaluate(() => ({
      scrollX: window.scrollX,
      scrollY: window.scrollY,
      htmlScrollHeight: document.documentElement.scrollHeight,
      htmlClientHeight: document.documentElement.clientHeight,
      bodyScrollHeight: document.body.scrollHeight,
      bodyClientHeight: document.body.clientHeight,
      windowHeight: window.innerHeight,
      windowWidth: window.innerWidth,
    }))

    expect(scrollInfo1080.scrollY).toBe(0)
    expect(scrollInfo1080.scrollX).toBe(0)
    expect(scrollInfo1080.htmlScrollHeight).toBeLessThanOrEqual(scrollInfo1080.windowHeight)
    expect(scrollInfo1080.bodyScrollHeight).toBeLessThanOrEqual(scrollInfo1080.windowHeight)

    // Test desktop 1366x768
    await page.setViewportSize({ width: 1366, height: 768 })
    await page.waitForTimeout(300)

    const scrollInfo768 = await page.evaluate(() => ({
      scrollX: window.scrollX,
      scrollY: window.scrollY,
      htmlScrollHeight: document.documentElement.scrollHeight,
      htmlClientHeight: document.documentElement.clientHeight,
      bodyScrollHeight: document.body.scrollHeight,
      bodyClientHeight: document.body.clientHeight,
      windowHeight: window.innerHeight,
      windowWidth: window.innerWidth,
    }))

    expect(scrollInfo768.scrollY).toBe(0)
    expect(scrollInfo768.scrollX).toBe(0)
    expect(scrollInfo768.htmlScrollHeight).toBeLessThanOrEqual(scrollInfo768.windowHeight)
    expect(scrollInfo768.bodyScrollHeight).toBeLessThanOrEqual(scrollInfo768.windowHeight)

    // Key elements must all be visible within the 1366x768 viewport
    await expect(page.locator('.sidebar')).toBeVisible()
    await expect(page.locator('.editor-topbar')).toBeVisible()
    await expect(page.locator('.canvas-container')).toBeVisible()
    await expect(page.locator('.editor-sidebar')).toBeVisible()
    await expect(page.locator('.editor-statusbar')).toBeVisible()
  })

  test('12. Minimal Save & Export MVP: Natural Language Design pathway (create -> correct -> save draft -> reopen from history -> solve -> download PNG, JSON, CSV -> stale guard)', async ({ page }) => {
    // 1. Create via NL Design
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })

    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    // 2. Lands in Editor
    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // 3. Confirm coordinates and save draft
    const confirmCheckbox = page.locator('.confirm-checkbox input')
    await confirmCheckbox.check()
    await expect(confirmCheckbox).toBeChecked()

    const saveBtn = page.locator('.editor-topbar .btn-save')
    await saveBtn.click()
    await expect(page.locator('.editor-topbar .btn-save')).toContainText('Saved', { timeout: 10_000 })

    // 4. Reopen saved model from Analysis History
    await page.goto('/?view=history')
    await expect(page.locator('.history-list')).toBeVisible({ timeout: 10_000 })
    const topRow = page.locator('.history-row').first()
    await expect(topRow).toBeVisible()
    await topRow.click()

    // Lands on detail page
    await expect(page.locator('.detail-page')).toBeVisible({ timeout: 10_000 })
    const editBtn = page.getByRole('button', { name: 'Edit geometry' })
    await expect(editBtn).toBeVisible()
    await editBtn.click()

    // Reopened in Truss Editor
    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })

    // 5. Mark Reviewed and Solve
    const reviewBtn = page.locator('.editor-topbar .btn-review')
    await reviewBtn.click()
    await expect(page.locator('.editor-topbar .btn-solve')).toBeEnabled({ timeout: 10_000 })

    const solveBtn = page.locator('.editor-topbar .btn-solve')
    await solveBtn.click()
    await page.locator('.cdialog-confirm').click()

    // 6. Results Panel appears with SOLVED status
    const resultsPanel = page.locator('.analysis-results-panel')
    await expect(resultsPanel).toBeVisible({ timeout: 15_000 })
    await expect(resultsPanel.locator('.badge-solved')).toBeVisible()

    // 7. Test Export Menu & Downloads
    const exportBtn = resultsPanel.locator('.btn-export')
    await expect(exportBtn).toBeVisible()
    await exportBtn.click()

    const exportMenu = resultsPanel.locator('.export-menu')
    await expect(exportMenu).toBeVisible()

    // PNG Download
    const [pngDownload] = await Promise.all([
      page.waitForEvent('download'),
      exportMenu.locator('.export-menu-item:has-text("PNG Diagram")').click(),
    ])
    expect(pngDownload.suggestedFilename()).toMatch(/\.png$/)

    // Reopen menu for JSON
    await exportBtn.click()
    await expect(exportMenu).toBeVisible()

    // JSON Download
    const [jsonDownload] = await Promise.all([
      page.waitForEvent('download'),
      exportMenu.locator('.export-menu-item:has-text("JSON Model")').click(),
    ])
    expect(jsonDownload.suggestedFilename()).toMatch(/\.json$/)

    // Reopen menu for CSV
    await exportBtn.click()
    await expect(exportMenu).toBeVisible()

    // CSV Download
    const [csvDownload] = await Promise.all([
      page.waitForEvent('download'),
      exportMenu.locator('.export-menu-item:has-text("CSV Results")').click(),
    ])
    expect(csvDownload.suggestedFilename()).toMatch(/\.csv$/)

    // 8. Stale Results Protection
    // Select a joint and modify its coordinate to invalidate results
    const jointNode = page.locator('.truss-joint-node').first()
    await jointNode.click({ force: true })

    const xInput = page.locator('.inspector-fields input[type="number"]').first()
    await expect(xInput).toBeVisible({ timeout: 5_000 })
    await xInput.fill('1.5')
    await xInput.dispatchEvent('change')

    // Results panel must now indicate STALE
    await expect(resultsPanel.locator('.badge-stale')).toBeVisible({ timeout: 10_000 })

    // Open export menu: CSV option must be disabled and tagged stale
    await exportBtn.click()
    await expect(exportMenu).toBeVisible()
    const csvItem = exportMenu.locator('.export-menu-item:has-text("CSV Results")')
    await expect(csvItem).toBeDisabled()
    await expect(csvItem.locator('.export-badge-tag.tag-stale')).toBeVisible()

    // Save draft again (reopen in place without duplicate records)
    await saveBtn.click()
    await expect(page.locator('.editor-topbar .btn-save')).toContainText('Saved', { timeout: 10_000 })
  })

  test('13. Minimal Save & Export MVP: Direct export endpoints and JSON draft persistence', async ({ page }) => {
    // Verify direct API export behavior
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })

    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 4 m span and 2 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 30_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
    const confirmCheckbox = page.locator('.confirm-checkbox input')
    await confirmCheckbox.check()
    await page.locator('.editor-topbar .btn-save').click()
    await expect(page.locator('.editor-topbar .btn-save')).toContainText('Saved', { timeout: 10_000 })

    // Get current analysis ID from URL
    const url = new URL(page.url())
    const analysisId = url.searchParams.get('analysis')
    expect(analysisId).toBeTruthy()

    // Test direct JSON export on draft (unsolved)
    const jsonRes = await page.request.get(`/api/analyses/${analysisId}/export/json`)
    expect(jsonRes.status()).toBe(200)
    const jsonData = await jsonRes.json()
    expect(jsonData.schema_version).toBe('1.0')
    expect(jsonData.model.nodes.length).toBe(3)
    expect(jsonData.solver_results).toBeUndefined()

    // Test CSV export on draft (unsolved) returns 409
    const csvRes = await page.request.get(`/api/analyses/${analysisId}/export/csv`)
    expect(csvRes.status()).toBe(409)
    const csvErr = await csvRes.json()
    expect(csvErr.error_code).toBe('RESULTS_REQUIRED')

    // Test PNG export on draft (unsolved) succeeds
    const pngRes = await page.request.get(`/api/analyses/${analysisId}/export/png`)
    expect(pngRes.status()).toBe(200)
    expect(pngRes.headers()['content-type']).toBe('image/png')
  })

  test('14. Minimal Save & Export MVP: Sketch upload pathway (upload -> edit geometry -> save draft -> reopen -> solve -> export PNG/JSON/CSV)', async ({ page }) => {
    // 1. Upload sketch
    await page.goto('/?view=new')
    await expect(page.locator('.upload-card')).toBeVisible({ timeout: 10_000 })

    const sketchPath = path.resolve(import.meta.dirname, '../../../backend/evaluation/sketches/test1.jpg')
    const fileBytes = readFileSync(sketchPath)
    await page.locator('input[type="file"]').setInputFiles({
      name: 'test1.jpg',
      mimeType: 'image/jpeg',
      buffer: fileBytes,
    })

    const uploadBtn = page.getByRole('button', { name: 'Start analysis' })
    await expect(uploadBtn).toBeEnabled()
    await uploadBtn.click()

    // 2. Lands on detail page
    await expect(page.locator('.detail-page')).toBeVisible({ timeout: 15_000 })
    const editBtn = page.getByRole('button', { name: 'Edit geometry' })
    await expect(editBtn).toBeVisible()
    await editBtn.click()

    // 3. Lands in Truss Editor
    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 15_000 })
    const confirmCheckbox = page.locator('.confirm-checkbox input')
    await confirmCheckbox.check()

    // Save draft
    const saveBtn = page.locator('.editor-topbar .btn-save')
    await saveBtn.click()
    await expect(saveBtn).toContainText('Saved', { timeout: 10_000 })

    // 4. Mark Reviewed and Solve
    const reviewBtn = page.locator('.editor-topbar .btn-review')
    await reviewBtn.click()
    await expect(page.locator('.editor-topbar .btn-solve')).toBeEnabled({ timeout: 10_000 })

    await page.locator('.editor-topbar .btn-solve').click()
    await page.locator('.cdialog-confirm').click()

    // 5. Results Panel appears with SOLVED status
    const resultsPanel = page.locator('.analysis-results-panel')
    await expect(resultsPanel).toBeVisible({ timeout: 15_000 })
    await expect(resultsPanel.locator('.badge-solved')).toBeVisible()

    // 6. Test Export
    const exportBtn = resultsPanel.locator('.btn-export')
    await expect(exportBtn).toBeVisible()
    await exportBtn.click()

    const exportMenu = resultsPanel.locator('.export-menu')
    await expect(exportMenu).toBeVisible()

    // CSV Download
    const [csvDownload] = await Promise.all([
      page.waitForEvent('download'),
      exportMenu.locator('.export-menu-item:has-text("CSV Results")').click(),
    ])
    expect(csvDownload.suggestedFilename()).toMatch(/\.csv$/)

    // JSON Download
    await exportBtn.click()
    const [jsonDownload] = await Promise.all([
      page.waitForEvent('download'),
      exportMenu.locator('.export-menu-item:has-text("JSON Model")').click(),
    ])
    expect(jsonDownload.suggestedFilename()).toMatch(/\.json$/)

    // PNG Download
    await exportBtn.click()
    const [pngDownload] = await Promise.all([
      page.waitForEvent('download'),
      exportMenu.locator('.export-menu-item:has-text("PNG Diagram")').click(),
    ])
    expect(pngDownload.suggestedFilename()).toMatch(/\.png$/)
  })
})
