# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: responsive-layout.spec.js >> Sketch2Solve Responsive Layout & Visual Polish Verification >> 2. Desktop 1440px: Analysis History typography, hierarchy, and table alignment
- Location: tests/e2e/responsive-layout.spec.js:43:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.history-summary-bar')
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.history-summary-bar') with timeout 8000ms
  - waiting for locator('.history-summary-bar')

```

```yaml
- complementary:
  - link "Sketch2Solve STRUCTURE REVIEW":
    - /url: /
    - strong: Sketch2Solve
    - text: STRUCTURE REVIEW
  - text: Local workspace
  - navigation "Main navigation":
    - button "Dashboard"
    - button "Natural Language Design"
    - button "New analysis"
    - button "Analysis history 0"
  - strong: Getting Started
  - paragraph: 6-step structural engineering workflow guide.
  - button "Open guide →"
  - text: Backend API · localhost:5000
- main:
  - text: Workspace /
  - strong: Analysis history
  - button "Open Getting Started Guide": Guide
  - button "C Chief Engineer"
  - text: SAVED WORK
  - heading "Analysis history" [level=1]
  - paragraph: Saved sketch interpretations and solver runs, newest first.
  - button "Refresh history"
  - button "＋ New analysis"
  - strong: Your history is clear
  - paragraph: Upload a sketch to create your first saved analysis.
  - button "Upload a sketch"
  - text: Sketch2Solve · Structural Truss Engineering Deterministic analysis and verification.
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test'
  2   | import path from 'node:path'
  3   | 
  4   | test.describe('Sketch2Solve Responsive Layout & Visual Polish Verification', () => {
  5   |   const outputDir = process.env.QA_OUTPUT_DIR || path.join(process.cwd(), 'qa-output')
  6   | 
  7   |   test.beforeEach(async ({ page }) => {
  8   |     // Set username so onboarding modal is bypassed for layout checks
  9   |     await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Chief Engineer'))
  10  |   })
  11  | 
  12  |   test('1. Desktop 1440px: Full-viewport application shell without floating rounded-card box', async ({ page }) => {
  13  |     await page.setViewportSize({ width: 1440, height: 900 })
  14  |     await page.goto('/')
  15  |     await expect(page.locator('.dashboard-page')).toBeVisible({ timeout: 10_000 })
  16  | 
  17  |     // Verify app-frame fills viewport
  18  |     const frameBox = await page.locator('.app-frame').boundingBox()
  19  |     expect(frameBox.width).toBe(1440)
  20  |     expect(frameBox.height).toBe(900)
  21  | 
  22  |     // Verify CSS: margin 0, border-radius 0, no box-shadow
  23  |     const frameStyles = await page.locator('.app-frame').evaluate((el) => {
  24  |       const s = window.getComputedStyle(el)
  25  |       return {
  26  |         margin: s.margin,
  27  |         borderRadius: s.borderRadius,
  28  |         boxShadow: s.boxShadow,
  29  |       }
  30  |     })
  31  |     expect(frameStyles.margin).toBe('0px')
  32  |     expect(frameStyles.borderRadius).toBe('0px')
  33  |     expect(frameStyles.boxShadow).toBe('none')
  34  | 
  35  |     // Verify zero window scroll
  36  |     const scrollY = await page.evaluate(() => window.scrollY)
  37  |     expect(scrollY).toBe(0)
  38  | 
  39  |     // Capture desktop dashboard screenshot
  40  |     await page.screenshot({ path: path.join(outputDir, '01-desktop-dashboard-1440px.png') })
  41  |   })
  42  | 
  43  |   test('2. Desktop 1440px: Analysis History typography, hierarchy, and table alignment', async ({ page }) => {
  44  |     await page.setViewportSize({ width: 1440, height: 900 })
  45  |     await page.goto('/?view=history')
  46  |     await expect(page.locator('.history-page')).toBeVisible({ timeout: 10_000 })
  47  | 
  48  |     // Verify typography hierarchy
  49  |     await expect(page.locator('.history-heading .eyebrow')).toHaveText('SAVED WORK')
  50  |     await expect(page.locator('.history-title')).toHaveText('Analysis history')
  51  |     await expect(page.locator('.history-subtitle')).toBeVisible()
  52  | 
  53  |     // Verify summary bar structure (not running together)
  54  |     const summaryBar = page.locator('.history-summary-bar')
> 55  |     await expect(summaryBar).toBeVisible()
      |                              ^ Error: expect(locator).toBeVisible() failed
  56  |     const summaryCount = page.locator('.history-summary-count')
  57  |     await expect(summaryCount).toBeVisible()
  58  |     await expect(page.locator('.count-text')).toHaveText('saved records')
  59  |     const summaryNote = page.locator('.history-summary-note')
  60  |     await expect(summaryNote).toBeVisible()
  61  |     await expect(summaryNote).toContainText('Analysis results are stored in this local workspace.')
  62  | 
  63  |     // Verify table structure and alignment
  64  |     await expect(page.locator('.history-table-container')).toBeVisible()
  65  |     await expect(page.locator('.history-header')).toBeVisible()
  66  |     const rows = page.locator('.history-row')
  67  |     const count = await rows.count()
  68  |     if (count > 0) {
  69  |       await expect(rows.first().locator('.item-filename')).toBeVisible()
  70  |       await expect(rows.first().locator('.provider-cell')).toBeVisible()
  71  |       await expect(rows.first().locator('.date-cell')).toBeVisible()
  72  |       await expect(rows.first().locator('.status-badge')).toBeVisible()
  73  |     }
  74  | 
  75  |     // Capture desktop history screenshot
  76  |     await page.screenshot({ path: path.join(outputDir, '02-desktop-history-1440px.png') })
  77  |   })
  78  | 
  79  |   test('3. Desktop 1440px: Natural Language Design Studio geometry preview visibility', async ({ page }) => {
  80  |     await page.setViewportSize({ width: 1440, height: 900 })
  81  |     await page.goto('/?view=design')
  82  |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  83  | 
  84  |     // Verify split-pane grid
  85  |     const workspace = page.locator('.studio-workspace')
  86  |     await expect(workspace).toBeVisible()
  87  | 
  88  |     // Verify Structural Geometry Preview panel
  89  |     const rightPane = page.locator('.studio-right-pane')
  90  |     await expect(rightPane).toBeVisible()
  91  |     await expect(page.locator('.canvas-title')).toContainText('Structural Geometry Preview')
  92  | 
  93  |     // Verify canvas viewport is visible and receives ample space (>= 480px)
  94  |     const viewport = page.locator('.canvas-viewport')
  95  |     await expect(viewport).toBeVisible()
  96  |     const viewportBox = await viewport.boundingBox()
  97  |     expect(viewportBox.width).toBeGreaterThan(400)
  98  |     expect(viewportBox.height).toBeGreaterThanOrEqual(480)
  99  | 
  100 |     // Capture desktop design studio screenshot
  101 |     await page.screenshot({ path: path.join(outputDir, '03-desktop-design-1440px.png') })
  102 |   })
  103 | 
  104 |   test('4. Tablet viewports (1024px and 768px): Proper adaptation without cramped navigation', async ({ page }) => {
  105 |     // 1024px Tablet Landscape
  106 |     await page.setViewportSize({ width: 1024, height: 768 })
  107 |     await page.goto('/')
  108 |     await expect(page.locator('.dashboard-page')).toBeVisible()
  109 |     await expect(page.locator('.sidebar')).toBeVisible()
  110 |     const sidebarWidth1024 = await page.locator('.sidebar').evaluate((el) => el.getBoundingClientRect().width)
  111 |     expect(sidebarWidth1024).toBeLessThanOrEqual(210)
  112 | 
  113 |     // 768px Tablet Portrait
  114 |     await page.setViewportSize({ width: 768, height: 1024 })
  115 |     await page.goto('/')
  116 |     await expect(page.locator('.dashboard-page')).toBeVisible()
  117 |     // At 768px, mobile topbar toggle is available
  118 |     await expect(page.locator('.btn-mobile-nav-toggle')).toBeVisible()
  119 |   })
  120 | 
  121 |   test('5. Mobile 390px: Clean collapsible navigation drawer, legible labels, touch targets, and responsive pages', async ({ page }) => {
  122 |     await page.setViewportSize({ width: 390, height: 844 })
  123 |     await page.goto('/')
  124 |     await expect(page.locator('.dashboard-page')).toBeVisible({ timeout: 10_000 })
  125 | 
  126 |     // 1. Desktop sidebar should be hidden
  127 |     await expect(page.locator('.sidebar')).not.toBeVisible()
  128 | 
  129 |     // 2. Mobile toggle and brand logo should be visible in topbar
  130 |     const toggleBtn = page.locator('.btn-mobile-nav-toggle')
  131 |     await expect(toggleBtn).toBeVisible()
  132 |     await expect(page.locator('.mobile-header-brand')).toBeVisible()
  133 | 
  134 |     // Check touch target height (>= 36px)
  135 |     const toggleBox = await toggleBtn.boundingBox()
  136 |     expect(toggleBox.height).toBeGreaterThanOrEqual(36)
  137 | 
  138 |     // Capture mobile dashboard screenshot
  139 |     await page.screenshot({ path: path.join(outputDir, '04-mobile-dashboard-390px.png') })
  140 | 
  141 |     // 3. Open mobile drawer
  142 |     await toggleBtn.click()
  143 |     const drawer = page.locator('.mobile-drawer')
  144 |     await expect(drawer).toBeVisible()
  145 | 
  146 |     // Check mobile nav items are readable and vertical
  147 |     const mobileNavItems = drawer.locator('.nav-item')
  148 |     await expect(mobileNavItems).toHaveCount(4)
  149 |     await expect(mobileNavItems.nth(0)).toContainText('Dashboard')
  150 |     await expect(mobileNavItems.nth(1)).toContainText('Natural Language Design')
  151 |     await expect(mobileNavItems.nth(2)).toContainText('New analysis')
  152 |     await expect(mobileNavItems.nth(3)).toContainText('Analysis history')
  153 | 
  154 |     // Touch target of mobile nav item >= 40px
  155 |     const navItemBox = await mobileNavItems.nth(0).boundingBox()
```