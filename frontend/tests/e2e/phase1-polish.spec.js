import { readFileSync } from 'node:fs'
import path from 'node:path'
import { test, expect } from '@playwright/test'

const configDirectory = import.meta.dirname
const evaluationDirectory = path.resolve(configDirectory, '../../../backend/evaluation/sketches')

test.describe('Phase 1 Polish Verification', () => {
  test('1. Dashboard: semantic selectors and buttons retain existing behavior', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.dashboard-welcome')).toBeVisible()

    // 1. Verify semantic classes exist and are distinct
    const headerNewBtn = page.locator('.btn-new-analysis')
    await expect(headerNewBtn).toBeVisible()
    await expect(headerNewBtn).toHaveClass(/dashboard-primary/)
    await expect(headerNewBtn).toHaveText(/New analysis/)

    // 2. Verify AI Workbench button still functions
    const aiBtn = page.locator('.dashboard-ai-btn')
    await expect(aiBtn).toBeVisible()
    await aiBtn.click()
    const workbench = page.locator('.dashboard-ai-workbench')
    await expect(workbench).toBeVisible()

    // Close workbench
    await page.locator('.btn-close-workbench').click()
    await expect(workbench).not.toBeVisible()

    // 3. Click New Analysis button to navigate to upload page
    await headerNewBtn.click()
    await expect(page.locator('.dropzone')).toBeVisible()
  })

  test('2. Accessibility: canvas floating controls and header actions have explicit accessible names', async ({ page }) => {
    // Create a new analysis via design studio to jump into the editor
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible()

    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 10_000 })
    await proposalCard.locator('.btn-apply').click()

    // In editor workspace
    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })

    // Verify accessible names on canvas toolbar
    const controls = page.locator('.canvas-floating-controls')
    await expect(controls).toBeVisible()
    await expect(controls).toHaveAttribute('role', 'toolbar')
    await expect(controls).toHaveAttribute('aria-label', 'Canvas view controls')

    await expect(controls.locator('button[aria-label="Zoom in"]')).toBeVisible()
    await expect(controls.locator('button[aria-label="Zoom out"]')).toBeVisible()
    await expect(controls.locator('button[aria-label="Fit content to view"]')).toBeVisible()
    await expect(controls.locator('button[aria-label="Toggle grid"]')).toBeVisible()
    await expect(controls.locator('button[aria-label="Snap to grid"]')).toBeVisible()
    await expect(controls.locator('button[aria-label="Toggle AI proposal layer"]')).toBeVisible()

    // Verify topbar accessible names
    await expect(page.locator('.editor-topbar button[aria-label="Return to Dashboard"], .editor-topbar .back-btn[aria-label]')).toBeVisible()
    await expect(page.locator('.editor-topbar button[aria-label="Undo"]')).toBeVisible()
    await expect(page.locator('.editor-topbar button[aria-label="Redo"]')).toBeVisible()
  })

  test('3. P1 Fix: AnalysisResultsPanel viewport management, lower joints clickability, expand/minimize states, and pan/zoom', async ({ page }) => {
    // 1. Create a determinate triangular truss with J1 at (0,0), J2 at (4,0), J3 at (2,3)
    await page.goto('/?view=design')
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 10_000 })
    await proposalCard.locator('.btn-apply').click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })

    // 2. Mark reviewed and solve
    const reviewBtn = page.locator('.btn-review')
    await expect(reviewBtn).toBeEnabled()
    await reviewBtn.click()

    const solveBtn = page.locator('.btn-solve')
    await expect(solveBtn).toBeEnabled({ timeout: 5_000 })
    await solveBtn.click()

    // Confirm dialog
    const confirmDialog = page.locator('.cdialog-panel')
    await expect(confirmDialog).toBeVisible()
    await confirmDialog.locator('.cdialog-confirm').click()

    // 3. Results panel opens
    const resultsPanel = page.locator('.analysis-results-panel')
    await expect(resultsPanel).toBeVisible({ timeout: 10_000 })
    await expect(resultsPanel.locator('.badge-solved')).toBeVisible()

    // Verify editor-canvas-column layout
    const column = page.locator('.editor-canvas-column')
    await expect(column).toBeVisible()
    const canvasContainer = page.locator('.canvas-container')
    await expect(canvasContainer).toBeVisible()

    // 4. LOWER JOINTS REMAIN FULLY CLICKABLE WHILE RESULTS PANEL IS OPEN
    // Select tool
    await page.locator('.tool-tile[title*="Select"]').click()

    // Joint 1 (J1) is at the bottom left (Y=0), the lowest part of the truss
    const jointNodes = page.locator('.truss-joints-group circle.truss-joint-node')
    await expect(jointNodes).toHaveCount(3)

    // Click the first joint (bottom joint)
    const firstJoint = jointNodes.first()
    await expect(firstJoint).toBeVisible()
    await firstJoint.click()

    // Inspector opens and displays the selected joint properties
    const inspector = page.locator('.editor-sidebar .inspector-section')
    await expect(inspector).toBeVisible()
    await expect(inspector.locator('.element-badge')).toBeVisible()

    // 5. EXPAND PANEL: test expanded state
    const expandBtn = resultsPanel.locator('.btn-expand')
    await expect(expandBtn).toBeVisible()
    await expandBtn.click()
    await expect(resultsPanel).toHaveClass(/is-expanded/)
    await page.waitForTimeout(300)

    // Lower joints must remain clickable in expanded state
    const secondJoint = jointNodes.nth(1) // J2 at bottom right (Y=0)
    await expect(secondJoint).toBeVisible()
    await secondJoint.click()
    await expect(inspector.locator('.element-badge')).toBeVisible()

    // 6. MINIMIZE PANEL: test minimized state
    const minimizeBtn = resultsPanel.locator('.btn-minimize')
    await expect(minimizeBtn).toBeVisible()
    await minimizeBtn.click()
    await expect(resultsPanel).toHaveClass(/is-minimized/)
    await page.waitForTimeout(300)

    // Lower joints remain selectable after minimizing the panel
    await firstJoint.click()
    await expect(inspector.locator('.element-badge')).toBeVisible()

    // 7. RESTORE FROM MINIMIZED: clicking a tab in panel restores it
    const summaryTab = resultsPanel.locator('.tab-btn:has-text("Summary & Matrix")')
    await summaryTab.click()
    await expect(resultsPanel).not.toHaveClass(/is-minimized/)

    // 8. PAN AND ZOOM REMAIN FULLY FUNCTIONAL
    // Zoom in using floating toolbar
    const zoomInBtn = page.locator('.canvas-floating-controls button[aria-label="Zoom in"]')
    await zoomInBtn.click()
    await zoomInBtn.click()

    // Fit content
    const fitBtn = page.locator('.canvas-floating-controls button[aria-label="Fit content to view"]')
    await fitBtn.click()

    // Pan canvas with mouse drag
    const panTool = page.locator('.tool-tile[title*="Pan"]')
    await panTool.click()
    const canvasBBox = await canvasContainer.boundingBox()
    await page.mouse.move(canvasBBox.x + 200, canvasBBox.y + 150)
    await page.mouse.down()
    await page.mouse.move(canvasBBox.x + 260, canvasBBox.y + 190)
    await page.mouse.up()

    // 9. RESULTS PANEL CONTROLS REMAIN FULLY INTERACTIVE
    // Switch to Member Forces tab
    await resultsPanel.locator('.tab-btn:has-text("Member Forces")').click()
    await expect(resultsPanel.locator('.results-table')).toBeVisible()

    // Toggle force labels button inside panel header
    const toggleLabelsBtn = resultsPanel.locator('.btn-force-labels')
    await expect(toggleLabelsBtn).toBeVisible()
    await toggleLabelsBtn.click()
    await expect(page.locator('.member-force-label')).toHaveCount(0)
    await toggleLabelsBtn.click()
    await expect(page.locator('.member-force-label')).toHaveCount(3)

    // Switch to Support Reactions tab
    await resultsPanel.locator('.tab-btn:has-text("Support Reactions")').click()
    await expect(resultsPanel.locator('.results-table')).toBeVisible()

    // Switch to Limitations tab
    await resultsPanel.locator('.tab-btn:has-text("Limitations")').click()
    await expect(resultsPanel.locator('.warning-block')).toBeVisible()
  })
})
