import { test, expect } from '@playwright/test'
import path from 'node:path'

test.describe('Sketch2Solve Documentation Screenshots Capture', () => {
  const screenshotsDir = path.resolve(import.meta.dirname, '../../../docs/screenshots')

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Chief Engineer'))
  })

  test('Capture all 6 documentation screenshots', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })

    // ── 1. Dashboard ──────────────────────────────────────────────────────────
    await page.goto('/')
    await expect(page.locator('.dashboard-page')).toBeVisible({ timeout: 10_000 })
    await page.waitForTimeout(600)
    await page.screenshot({ path: path.join(screenshotsDir, '01-dashboard.png') })

    // ── 2. Sketch Upload & Interpretation Review ─────────────────────────────
    await page.goto('/?view=new')
    await expect(page.locator('.upload-card')).toBeVisible({ timeout: 10_000 })
    const fileChooserPromise = page.waitForEvent('filechooser')
    await page.locator('.dropzone').click()
    const fileChooser = await fileChooserPromise
    await fileChooser.setFiles(path.resolve(import.meta.dirname, '../../../backend/evaluation/sketches/test4.jpg'))
    await expect(page.locator('.upload-submit')).toBeEnabled()
    await page.locator('.upload-submit').click()

    // Wait for detail page (class: .detail-page)
    await expect(page.locator('.detail-page')).toBeVisible({ timeout: 25_000 })
    await page.waitForTimeout(800)
    await page.screenshot({ path: path.join(screenshotsDir, '02-sketch-upload-and-review.png') })

    // ── 3. Truss CAD Editor ───────────────────────────────────────────────────
    const editBtn = page.locator('button:has-text("Edit geometry")')
    await expect(editBtn).toBeVisible({ timeout: 5_000 })
    await editBtn.click()

    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(800)
    await page.screenshot({ path: path.join(screenshotsDir, '03-truss-editor.png') })

    // ── 4. Natural Language Design Studio ─────────────────────────────────────
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a symmetrical Pratt truss with 10 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 25_000 })
    await page.waitForTimeout(800)
    await page.screenshot({ path: path.join(screenshotsDir, '04-natural-language-design.png') })

    // ── 5. Solver Results Panel ───────────────────────────────────────────────
    await proposalCard.locator('.btn-apply').click()
    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Check Coordinates Confirmed checkbox if not checked
    const coordsCheckbox = page.locator('.confirm-checkbox input')
    if (await coordsCheckbox.isVisible({ timeout: 3_000 }).catch(() => false)) {
      if (!await coordsCheckbox.isChecked()) {
        await coordsCheckbox.check()
        await page.waitForTimeout(300)
      }
    }

    const reviewBtn = page.locator('.editor-topbar .btn-review')
    if (await reviewBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await reviewBtn.click()
      await page.waitForTimeout(600)
    }

    const solveBtn = page.locator('.editor-topbar .btn-solve')
    await expect(solveBtn).toBeEnabled({ timeout: 10_000 })
    await solveBtn.click()

    const confirmSubmitBtn = page.locator('.cdialog-confirm')
    await expect(confirmSubmitBtn).toBeVisible({ timeout: 5_000 })
    await confirmSubmitBtn.click()

    const resultsPanel = page.locator('.analysis-results-panel')
    await expect(resultsPanel).toBeVisible({ timeout: 15_000 })
    await page.waitForTimeout(800)
    await page.screenshot({ path: path.join(screenshotsDir, '05-solver-results.png') })

    // ── 6. AI Issue Resolution Assistant ─────────────────────────────────────
    // Close results panel
    const closeResultsBtn = page.locator('.analysis-results-panel .header-action-btn.btn-close')
    if (await closeResultsBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await closeResultsBtn.click()
      await page.waitForTimeout(500)
    }

    // Activate delete tool on desktop
    const deleteToolBtn = page.locator('button.tool-delete:visible, .tool-tile.tool-delete')
    if (await deleteToolBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await deleteToolBtn.click()
      await page.waitForTimeout(300)
      const nodeCircle = page.locator('svg.engineering-svg circle.truss-node-circle').first()
      if (await nodeCircle.isVisible().catch(() => false)) {
        await nodeCircle.click({ force: true })
        await page.waitForTimeout(800)
      }
    }

    const assistantCard = page.locator('.issue-resolution-assistant')
    if (await assistantCard.isVisible({ timeout: 5000 }).catch(() => false)) {
      const fixAiBtn = assistantCard.locator('.btn-fix-ai')
      if (await fixAiBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await fixAiBtn.click()
        await page.waitForTimeout(2500)
      }
    }
    await page.waitForTimeout(600)
    await page.screenshot({ path: path.join(screenshotsDir, '06-ai-issue-resolution.png') })
  })
})
