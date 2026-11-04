# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ux-polish.spec.js >> Sketch2Solve UX Polish & Layout Architecture Verification >> 5. Truss Editor canvas interactions and zero browser scrollbars preserved
- Location: tests/e2e/ux-polish.spec.js:146:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.editor-toolbar')
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.editor-toolbar') with timeout 8000ms
  - waiting for locator('.editor-toolbar')

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
  - button "Back to analysis": Back
  - strong: Triangular Truss
  - text: "#E9E7BEDC draft"
  - button "Undo" [disabled]
  - button "Redo" [disabled]
  - text: Length
  - combobox:
    - option "m" [selected]
    - option "mm"
    - option "ft"
  - text: Force
  - combobox:
    - option "kN" [selected]
    - option "N"
    - option "lbf"
  - checkbox "Coords Confirmed" [checked]
  - text: Coords Confirmed
  - button "Saved"
  - button "Mark Reviewed"
  - button "Solve" [disabled]
  - button "Design with AI"
  - toolbar "Canvas view controls":
    - button "Zoom in"
    - button "Zoom out"
    - button "Fit content to view"
    - separator
    - button "Toggle grid" [pressed]
    - button "Snap to grid" [pressed]
    - button "Toggle AI proposal layer" [pressed]
  - text: "X: 0.000 m · Y: 0.000 m"
  - img: "(0,0) M1 M2 M3 L1: -10 kN J1 J2 J3"
  - complementary:
    - tablist "Sidebar navigation":
      - tab "Tools" [selected]
      - tab "Design with AI"
    - text: Navigate
    - button "Select"
    - button "Pan"
    - text: Construction
    - button "Joint"
    - button "Member"
    - button "Measure"
    - text: Structural
    - button "Pin"
    - button "Roller"
    - button "Load"
    - text: Edit
    - button "Delete"
    - heading "Model" [level=3]
    - text: TRUSS Joints
    - strong: "3"
    - text: Members
    - strong: "3"
    - text: Supports
    - strong: "2"
    - text: Loads
    - strong: "1"
    - paragraph: Select a joint or member to inspect and edit its properties.
    - button "Clear All Model Elements"
  - text: SOLVABLE Truss is statically determinate and in static equilibrium. 3 joints · 3 members · 0.00, 0.00
```

# Test source

```ts
  68  |       }
  69  |     })
  70  |     expect(documentScroll.overflow).toBe('hidden')
  71  |     expect(documentScroll.bodyOverflow).toBe('hidden')
  72  |     expect(documentScroll.windowScrollY).toBe(0)
  73  | 
  74  |     // 2. Verify sidebar and topbar are fixed and stable
  75  |     const topbar = page.locator('.topbar')
  76  |     await expect(topbar).toBeVisible()
  77  |     const sidebar = page.locator('.sidebar')
  78  |     await expect(sidebar).toBeVisible()
  79  | 
  80  |     // 3. Verify main content viewport exists and handles internal scrolling
  81  |     const viewport = page.locator('.main-content-viewport')
  82  |     await expect(viewport).toBeVisible()
  83  |     const viewportOverflow = await viewport.evaluate((el) => window.getComputedStyle(el).overflowY)
  84  |     expect(['auto', 'scroll']).toContain(viewportOverflow)
  85  | 
  86  |     // Capture dashboard screenshot
  87  |     await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '02-dashboard-clean.png') })
  88  |   })
  89  | 
  90  |   test('3. Compact Getting Started guide: 6-step walkthrough opens, navigates, and closes', async ({ page }) => {
  91  |     await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
  92  |     await page.goto('/')
  93  | 
  94  |     // Open guide via Dashboard button
  95  |     const guideBtn = page.locator('.dashboard-guide-btn')
  96  |     await expect(guideBtn).toBeVisible()
  97  |     await guideBtn.click()
  98  | 
  99  |     const guideModal = page.locator('.guide-overlay')
  100 |     await expect(guideModal).toBeVisible()
  101 |     await expect(page.locator('.step-badge')).toContainText('Step 1 of 6')
  102 |     await expect(page.locator('.step-title')).toContainText('Create a New Analysis')
  103 | 
  104 |     // Step dots should be 6
  105 |     const dots = page.locator('.step-dot')
  106 |     await expect(dots).toHaveCount(6)
  107 | 
  108 |     // Click Next
  109 |     await page.locator('.btn-guide-primary').click()
  110 |     await expect(page.locator('.step-badge')).toContainText('Step 2 of 6')
  111 |     await expect(page.locator('.step-title')).toContainText('Upload a Sketch or Describe with AI')
  112 | 
  113 |     // Click step 6 dot directly
  114 |     await dots.nth(5).click()
  115 |     await expect(page.locator('.step-badge')).toContainText('Step 6 of 6')
  116 |     await expect(page.locator('.step-title')).toContainText('Understand Results & Export')
  117 | 
  118 |     // Capture guide screenshot
  119 |     await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '03-getting-started-guide.png') })
  120 | 
  121 |     // Dismiss guide
  122 |     await page.locator('.btn-close-guide').click()
  123 |     await expect(guideModal).not.toBeVisible()
  124 |   })
  125 | 
  126 |   test('4. Developer messaging removed and official branding loaded', async ({ page }) => {
  127 |     await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
  128 |     await page.goto('/')
  129 | 
  130 |     // 1. "Private by default" must not exist anywhere
  131 |     await expect(page.locator('text=Private by default')).toHaveCount(0)
  132 |     await expect(page.locator('text=Don’t expose this workspace publicly')).toHaveCount(0)
  133 | 
  134 |     // 2. "Local review workspace" must not exist in footer
  135 |     await expect(page.locator('text=Sketch2Solve · Local review workspace')).toHaveCount(0)
  136 | 
  137 |     // 3. Official footer text present
  138 |     await expect(page.locator('.main-footer')).toContainText('Sketch2Solve · Structural Truss Engineering')
  139 | 
  140 |     // 4. Official brand logo present in sidebar
  141 |     const brandLogo = page.locator('.brand-logo-img')
  142 |     await expect(brandLogo).toBeVisible()
  143 |     expect(await brandLogo.getAttribute('src')).toBe('/logo.png')
  144 |   })
  145 | 
  146 |   test('5. Truss Editor canvas interactions and zero browser scrollbars preserved', async ({ page }) => {
  147 |     // 1. Enter editor via Design Studio
  148 |     await page.addInitScript(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
  149 |     await page.goto('/?view=design')
  150 |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  151 | 
  152 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  153 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  154 |     await page.locator('.studio-left-pane .btn-submit').click()
  155 | 
  156 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  157 |     await expect(proposalCard).toBeVisible({ timeout: 25_000 })
  158 |     await proposalCard.locator('.btn-apply').click()
  159 | 
  160 |     // 2. Editor workspace should be visible
  161 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  162 | 
  163 |     // Check window scroll is 0
  164 |     const scrollY = await page.evaluate(() => window.scrollY)
  165 |     expect(scrollY).toBe(0)
  166 | 
  167 |     // Check status bar and tools
> 168 |     await expect(page.locator('.editor-toolbar')).toBeVisible()
      |                                                   ^ Error: expect(locator).toBeVisible() failed
  169 |     await expect(page.locator('.editor-statusbar')).toBeVisible()
  170 | 
  171 |     // Capture editor screenshot
  172 |     await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '04-truss-editor.png') })
  173 |   })
  174 | })
  175 | 
  176 | 
```