# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ux-enhancements.spec.js >> Sketch2Solve UX Enhancements & Branding Suite >> 2. Interactive Getting Started Guide walkthrough across 9 steps
- Location: tests/e2e/ux-enhancements.spec.js:62:3

# Error details

```
Test timeout of 90000ms exceeded.
```

```
Error: page.goto: Test timeout of 90000ms exceeded.
Call log:
  - navigating to "http://127.0.0.1:5175/", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test'
  2   | import path from 'node:path'
  3   | 
  4   | test.describe('Sketch2Solve UX Enhancements & Branding Suite', () => {
  5   |   test('1. First-time onboarding, name persistence, and profile renaming', async ({ page }) => {
  6   |     // 1. Visit with fresh storage
  7   |     await page.goto('/')
  8   |     await page.evaluate(() => {
  9   |       localStorage.clear()
  10  |     })
  11  |     await page.reload()
  12  | 
  13  |     // 2. Verify onboarding modal appears with question & official logo
  14  |     const onboardingOverlay = page.locator('.onboarding-overlay')
  15  |     await expect(onboardingOverlay).toBeVisible({ timeout: 8_000 })
  16  |     await expect(page.locator('.onboarding-title')).toContainText('Welcome to Sketch2Solve')
  17  |     await expect(page.locator('.input-label')).toContainText('What should we call you?')
  18  | 
  19  |     const logoImg = page.locator('.onboarding-logo')
  20  |     await expect(logoImg).toBeVisible()
  21  |     expect(await logoImg.getAttribute('src')).toBe('/logo.png')
  22  | 
  23  |     // Capture screenshot: Onboarding Modal
  24  |     await page.screenshot({ path: path.resolve('qa-output/screenshots/01-onboarding-modal.png') })
  25  | 
  26  |     // 3. Fill in name and submit
  27  |     const nameInput = page.locator('#name-input')
  28  |     await nameInput.fill('Dr. Evelyn Reed')
  29  |     await page.locator('.btn-continue').click()
  30  | 
  31  |     // 4. Modal should close and header should display name
  32  |     await expect(onboardingOverlay).not.toBeVisible()
  33  |     const userNameText = page.locator('.user-name-text')
  34  |     await expect(userNameText).toHaveText('Dr. Evelyn Reed')
  35  | 
  36  |     // 5. Reload: name persists and onboarding does NOT re-appear
  37  |     await page.reload()
  38  |     await expect(page.locator('.onboarding-overlay')).not.toBeVisible()
  39  |     await expect(page.locator('.user-name-text')).toHaveText('Dr. Evelyn Reed')
  40  | 
  41  |     // Capture screenshot: Dashboard Returning User
  42  |     await page.screenshot({ path: path.resolve('qa-output/screenshots/02-dashboard-returning-user.png') })
  43  | 
  44  |     // 6. Test Profile Menu & Rename
  45  |     await page.locator('.user-profile-btn').click()
  46  |     const userMenu = page.locator('.user-dropdown-menu')
  47  |     await expect(userMenu).toBeVisible()
  48  |     await expect(page.locator('.menu-username')).toHaveText('Dr. Evelyn Reed')
  49  | 
  50  |     // Click "Change name"
  51  |     await page.locator('.menu-item', { hasText: 'Change name' }).click()
  52  |     await expect(page.locator('.onboarding-overlay')).toBeVisible()
  53  |     await expect(page.locator('.onboarding-title')).toContainText('Update Your Profile')
  54  | 
  55  |     await page.locator('#name-input').fill('Evelyn R.')
  56  |     await page.locator('.btn-continue').click()
  57  | 
  58  |     await expect(page.locator('.onboarding-overlay')).not.toBeVisible()
  59  |     await expect(page.locator('.user-name-text')).toHaveText('Evelyn R.')
  60  |   })
  61  | 
  62  |   test('2. Interactive Getting Started Guide walkthrough across 9 steps', async ({ page }) => {
> 63  |     await page.goto('/')
      |                ^ Error: page.goto: Test timeout of 90000ms exceeded.
  64  | 
  65  |     // Launch guide from sidebar
  66  |     const guideNavBtn = page.locator('.nav-guide-btn')
  67  |     await expect(guideNavBtn).toBeVisible()
  68  |     await guideNavBtn.click()
  69  | 
  70  |     const guideContainer = page.locator('.guide-container')
  71  |     await expect(guideContainer).toBeVisible()
  72  | 
  73  |     // Step 1: Workspace & Dashboard
  74  |     await expect(page.locator('.step-title')).toContainText('1. Workspace & Dashboard')
  75  |     await expect(page.locator('.step-indicator')).toContainText('Step 1 of 9')
  76  | 
  77  |     // Capture screenshot: Guide Step 1
  78  |     await page.screenshot({ path: path.resolve('qa-output/screenshots/03-getting-started-step1.png') })
  79  | 
  80  |     // Click Next -> Step 2
  81  |     await page.locator('.btn-next').click()
  82  |     await expect(page.locator('.step-title')).toContainText('2. Uploading a Sketch')
  83  |     await expect(page.locator('.step-indicator')).toContainText('Step 2 of 9')
  84  | 
  85  |     // Click step dot 4 directly
  86  |     const stepDots = page.locator('.step-dot')
  87  |     await stepDots.nth(3).click()
  88  |     await expect(page.locator('.step-title')).toContainText('4. Correcting Joints & Members')
  89  | 
  90  |     // Capture screenshot: Guide Step 4
  91  |     await page.screenshot({ path: path.resolve('qa-output/screenshots/04-getting-started-step4.png') })
  92  | 
  93  |     // Click step dot 9 directly (final step)
  94  |     await stepDots.nth(8).click()
  95  |     await expect(page.locator('.step-title')).toContainText('9. Saving & Multi-Format Export')
  96  |     const finishBtn = page.locator('.btn-next')
  97  |     await expect(finishBtn).toContainText('Finish Tour')
  98  | 
  99  |     // Click Finish Tour
  100 |     await finishBtn.click()
  101 |     await expect(guideContainer).not.toBeVisible()
  102 | 
  103 |     // Verify localStorage completion
  104 |     const isCompleted = await page.evaluate(() => localStorage.getItem('sketch2solve_guide_completed'))
  105 |     expect(isCompleted).toBe('true')
  106 | 
  107 |     // Can be restarted from dashboard button
  108 |     const dashboardGuideBtn = page.locator('.dashboard-guide-btn')
  109 |     await expect(dashboardGuideBtn).toBeVisible()
  110 |     await dashboardGuideBtn.click()
  111 |     await expect(page.locator('.guide-container')).toBeVisible()
  112 |     await expect(page.locator('.step-title')).toContainText('1. Workspace & Dashboard')
  113 | 
  114 |     // Close with X button
  115 |     await page.locator('.guide-header .btn-icon[title="Close guide"]').click()
  116 |     await expect(page.locator('.guide-container')).not.toBeVisible()
  117 |   })
  118 | 
  119 |   test('3. Dark mode theme toggle, persistence, and visual contrast', async ({ page }) => {
  120 |     await page.goto('/')
  121 | 
  122 |     // Verify initial theme (or toggle to light first)
  123 |     const html = page.locator('html')
  124 |     const themeBtn = page.locator('.btn-theme-toggle')
  125 |     await expect(themeBtn).toBeVisible()
  126 | 
  127 |     const currentTheme = await html.getAttribute('data-theme')
  128 |     if (currentTheme !== 'dark') {
  129 |       await themeBtn.click()
  130 |     }
  131 |     await expect(html).toHaveAttribute('data-theme', 'dark')
  132 | 
  133 |     // Verify dark mode styling on dashboard
  134 |     const bodyBg = await page.evaluate(() => window.getComputedStyle(document.body).backgroundColor)
  135 |     expect(bodyBg).toMatch(/rgb\(15,\s*17,\s*21\)/)
  136 | 
  137 |     // Capture screenshot: Dashboard Dark Mode
  138 |     await page.screenshot({ path: path.resolve('qa-output/screenshots/05-dashboard-dark-mode.png') })
  139 | 
  140 |     // Reload: dark theme persists
  141 |     await page.reload()
  142 |     await expect(html).toHaveAttribute('data-theme', 'dark')
  143 | 
  144 |     // Toggle back to light
  145 |     await page.locator('.btn-theme-toggle').click()
  146 |     await expect(html).toHaveAttribute('data-theme', 'light')
  147 |     const lightBg = await page.evaluate(() => window.getComputedStyle(document.body).backgroundColor)
  148 |     expect(lightBg).toMatch(/rgb\(181,\s*185,\s*194\)/)
  149 |   })
  150 | 
  151 |   test('4. Truss Editor visual verification in Light and Dark themes', async ({ page }) => {
  152 |     // 1. Create a quick truss via Design Studio
  153 |     await page.goto('/?view=design')
  154 |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  155 | 
  156 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  157 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  158 |     await page.locator('.studio-left-pane .btn-submit').click()
  159 |     await expect(page.locator('.studio-left-pane .design-proposal-card')).toBeVisible({ timeout: 15_000 })
  160 | 
  161 |     // 2. Apply and open editor
  162 |     await page.locator('.btn-apply-editor').click()
  163 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
```