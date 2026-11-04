import { test, expect } from '@playwright/test'
import path from 'node:path'

test.describe('Sketch2Solve UX Polish & Layout Architecture Verification', () => {
  test.beforeEach(async ({ context }) => {
    // Clear localStorage for a fresh first-time visit
    await context.clearCookies()
  })

  test('1. First-time user onboarding modal prompts for name, saves to localStorage, and updates header', async ({ page }) => {
    // Navigate with empty storage to simulate a brand new user
    await page.goto('/')
    await page.evaluate(() => localStorage.clear())
    await page.reload()

    // 1. Verify Welcome modal appears
    const onboardingModal = page.locator('.onboarding-overlay')
    await expect(onboardingModal).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('.onboarding-title')).toContainText('Welcome to Sketch2Solve')
    await expect(page.locator('.onboarding-subtitle')).toContainText('What should we call you?')

    // Verify official logo inside onboarding modal
    const modalLogo = page.locator('.onboarding-logo')
    await expect(modalLogo).toBeVisible()
    const logoSrc = await modalLogo.getAttribute('src')
    expect(logoSrc).toBe('/logo.png')

    // Capture onboarding screenshot
    await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '01-onboarding-modal.png') })

    // 2. Submit name
    const input = page.locator('.name-input')
    await input.fill('Dr. Alex Reed, SE')
    await page.locator('.onboarding-form button[type="submit"]').click()

    // Modal should dismiss
    await expect(onboardingModal).not.toBeVisible()

    // Header profile should display saved name
    const profileBtn = page.locator('.user-profile-btn')
    await expect(profileBtn).toBeVisible()
    await expect(page.locator('.user-name-text')).toContainText('Dr. Alex Reed, SE')

    // LocalStorage should persist name
    const savedName = await page.evaluate(() => localStorage.getItem('sketch2solve_username'))
    expect(savedName).toBe('Dr. Alex Reed, SE')

    // Subsequent reload does NOT show modal
    await page.reload()
    await expect(page.locator('.onboarding-overlay')).not.toBeVisible()
    await expect(page.locator('.user-name-text')).toContainText('Dr. Alex Reed, SE')
  })

  test('2. Browser-level scrolling: Zero document scrollbars on Dashboard & internal scrolling', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
    await page.goto('/')

    await expect(page.locator('.dashboard-page')).toBeVisible()

    // 1. Verify document-level scroll is 0 / hidden
    const documentScroll = await page.evaluate(() => {
      const doc = document.documentElement
      return {
        hasScrollbar: doc.scrollHeight > doc.clientHeight,
        overflow: window.getComputedStyle(doc).overflow,
        bodyOverflow: window.getComputedStyle(document.body).overflow,
        windowScrollY: window.scrollY,
      }
    })
    expect(documentScroll.overflow).toBe('hidden')
    expect(documentScroll.bodyOverflow).toBe('hidden')
    expect(documentScroll.windowScrollY).toBe(0)

    // 2. Verify sidebar and topbar are fixed and stable
    const topbar = page.locator('.topbar')
    await expect(topbar).toBeVisible()
    const sidebar = page.locator('.sidebar')
    await expect(sidebar).toBeVisible()

    // 3. Verify main content viewport exists and handles internal scrolling
    const viewport = page.locator('.main-content-viewport')
    await expect(viewport).toBeVisible()
    const viewportOverflow = await viewport.evaluate((el) => window.getComputedStyle(el).overflowY)
    expect(['auto', 'scroll']).toContain(viewportOverflow)

    // Capture dashboard screenshot
    await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '02-dashboard-clean.png') })
  })

  test('3. Compact Getting Started guide: 6-step walkthrough opens, navigates, and closes', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
    await page.goto('/')

    // Open guide via Dashboard button
    const guideBtn = page.locator('.dashboard-guide-btn')
    await expect(guideBtn).toBeVisible()
    await guideBtn.click()

    const guideModal = page.locator('.guide-overlay')
    await expect(guideModal).toBeVisible()
    await expect(page.locator('.step-badge')).toContainText('Step 1 of 6')
    await expect(page.locator('.step-title')).toContainText('Create a New Analysis')

    // Step dots should be 6
    const dots = page.locator('.step-dot')
    await expect(dots).toHaveCount(6)

    // Click Next
    await page.locator('.btn-guide-primary').click()
    await expect(page.locator('.step-badge')).toContainText('Step 2 of 6')
    await expect(page.locator('.step-title')).toContainText('Upload a Sketch or Describe with AI')

    // Click step 6 dot directly
    await dots.nth(5).click()
    await expect(page.locator('.step-badge')).toContainText('Step 6 of 6')
    await expect(page.locator('.step-title')).toContainText('Understand Results & Export')

    // Capture guide screenshot
    await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '03-getting-started-guide.png') })

    // Dismiss guide
    await page.locator('.btn-close-guide').click()
    await expect(guideModal).not.toBeVisible()
  })

  test('4. Developer messaging removed and official branding loaded', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
    await page.goto('/')

    // 1. "Private by default" must not exist anywhere
    await expect(page.locator('text=Private by default')).toHaveCount(0)
    await expect(page.locator('text=Don’t expose this workspace publicly')).toHaveCount(0)

    // 2. "Local review workspace" must not exist in footer
    await expect(page.locator('text=Sketch2Solve · Local review workspace')).toHaveCount(0)

    // 3. Official footer text present
    await expect(page.locator('.main-footer')).toContainText('Sketch2Solve · Structural Truss Engineering')

    // 4. Official brand logo present in sidebar
    const brandLogo = page.locator('.brand-logo-img')
    await expect(brandLogo).toBeVisible()
    expect(await brandLogo.getAttribute('src')).toBe('/logo.png')
  })

  test('5. Truss Editor canvas interactions and zero browser scrollbars preserved', async ({ page }) => {
    // 1. Enter editor via Design Studio
    await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
    await page.goto('/?view=design')
    await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })

    const textarea = page.locator('.studio-left-pane .design-textarea')
    await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
    await page.locator('.studio-left-pane .btn-submit').click()

    const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
    await expect(proposalCard).toBeVisible({ timeout: 25_000 })
    await proposalCard.locator('.btn-apply').click()

    // 2. Editor workspace should be visible
    await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })

    // Check window scroll is 0
    const scrollY = await page.evaluate(() => window.scrollY)
    expect(scrollY).toBe(0)

    // Check status bar and tools
    await expect(page.locator('.editor-topbar')).toBeVisible()
    await expect(page.locator('.editor-statusbar')).toBeVisible()

    // Capture editor screenshot
    await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '04-truss-editor.png') })
  })
})

