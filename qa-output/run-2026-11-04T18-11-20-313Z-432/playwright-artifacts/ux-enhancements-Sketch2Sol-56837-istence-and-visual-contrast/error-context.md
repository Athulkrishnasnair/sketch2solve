# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ux-enhancements.spec.js >> Sketch2Solve UX Enhancements & Branding Suite >> 3. Dark mode theme toggle, persistence, and visual contrast
- Location: tests/e2e/ux-enhancements.spec.js:119:3

# Error details

```
Test timeout of 90000ms exceeded.
```

```
Error: locator.click: Test timeout of 90000ms exceeded.
Call log:
  - waiting for locator('.btn-theme-toggle')
    - locator resolved to <button type="button" data-v-7a7a37b1="" title="Switch to Dark Theme" aria-label="Switch to Dark Theme" class="btn-topbar-tool btn-theme-toggle">…</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div data-v-65bffd5a="" data-v-7a7a37b1="" class="onboarding-overlay">…</div> intercepts pointer events
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div data-v-65bffd5a="" data-v-7a7a37b1="" class="onboarding-overlay">…</div> intercepts pointer events
    - retrying click action
      - waiting 100ms
    - waiting for element to be visible, enabled and stable
    - element is visible, enabled and stable
    - scrolling into view if needed

```

# Test source

```ts
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
  63  |     await page.goto('/')
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
> 129 |       await themeBtn.click()
      |                      ^ Error: locator.click: Test timeout of 90000ms exceeded.
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
  164 | 
  165 |     // 3. Capture editor in Light theme
  166 |     await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'light'))
  167 |     await page.screenshot({ path: path.resolve('qa-output/screenshots/06-editor-light-mode.png') })
  168 | 
  169 |     // 4. Switch to Dark theme in Editor and verify canvas colors
  170 |     await page.evaluate(() => {
  171 |       document.documentElement.setAttribute('data-theme', 'dark')
  172 |       localStorage.setItem('sketch2solve_theme', 'dark')
  173 |     })
  174 |     await page.waitForTimeout(300)
  175 | 
  176 |     const canvasBg = await page.evaluate(() => {
  177 |       const el = document.querySelector('.canvas-container')
  178 |       return el ? window.getComputedStyle(el).backgroundColor : ''
  179 |     })
  180 |     expect(canvasBg).toMatch(/rgb\(19,\s*21,\s*24\)/)
  181 | 
  182 |     // Capture editor in Dark theme
  183 |     await page.screenshot({ path: path.resolve('qa-output/screenshots/07-editor-dark-mode.png') })
  184 |   })
  185 | 
  186 |   test('5. Analysis History page layout and Dark theme adaptation', async ({ page }) => {
  187 |     await page.goto('/?view=history')
  188 |     await expect(page.locator('.history-page')).toBeVisible({ timeout: 10_000 })
  189 | 
  190 |     // Set to dark theme
  191 |     await page.evaluate(() => {
  192 |       document.documentElement.setAttribute('data-theme', 'dark')
  193 |       localStorage.setItem('sketch2solve_theme', 'dark')
  194 |     })
  195 |     await page.waitForTimeout(300)
  196 | 
  197 |     // Verify footer and headers render cleanly
  198 |     await expect(page.locator('.history-header')).toBeVisible()
  199 | 
  200 |     // Capture History Dark Mode
  201 |     await page.screenshot({ path: path.resolve('qa-output/screenshots/08-history-dark-mode.png') })
  202 |   })
  203 | 
  204 |   test('6. Official Branding & Asset Verification', async ({ page }) => {
  205 |     await page.goto('/')
  206 | 
  207 |     // 1. Sidebar Brand logo image
  208 |     const brandLogo = page.locator('.sidebar .brand-logo-img')
  209 |     await expect(brandLogo).toBeVisible()
  210 |     expect(await brandLogo.getAttribute('src')).toBe('/logo.png')
  211 | 
  212 |     // 2. Direct static asset availability (200 OK)
  213 |     const logoResp = await page.request.get('/logo.png')
  214 |     expect(logoResp.status()).toBe(200)
  215 | 
  216 |     const faviconResp = await page.request.get('/favicon.png')
  217 |     expect(faviconResp.status()).toBe(200)
  218 | 
  219 |     const favicon32Resp = await page.request.get('/favicon-32x32.png')
  220 |     expect(favicon32Resp.status()).toBe(200)
  221 |   })
  222 | })
  223 | 
  224 | 
```