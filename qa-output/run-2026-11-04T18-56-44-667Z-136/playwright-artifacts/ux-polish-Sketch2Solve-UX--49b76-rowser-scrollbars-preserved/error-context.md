# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ux-polish.spec.js >> Sketch2Solve UX Polish & Layout Architecture Verification >> 5. Truss Editor canvas interactions and zero browser scrollbars preserved
- Location: tests/e2e/ux-polish.spec.js:150:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.truss-editor')
Expected: visible
Timeout: 15000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.truss-editor') with timeout 15000ms
  - waiting for locator('.truss-editor')

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
  - strong: Dashboard
  - button "Open Getting Started Guide": Guide
  - button "E Engineer"
  - text: LOCAL ENGINEERING WORKSPACE
  - heading "Sketch review, with evidence in view." [level=1]:
    - text: Sketch review,
    - emphasis: with evidence in view.
  - paragraph: Compare visual detections and model interpretations, then decide what belongs in a structural model.
  - button "＋ New analysis"
  - button "Create with AI"
  - button "Guide"
  - button "Browse all history ↗"
  - text: ▤ Saved analyses
  - strong: "0"
  - text: from local history ◉ Review boundary
  - strong: Human checked
  - text: AI proposals stay unapproved ∑ Solver access
  - strong: After review
  - text: explicit submission only SAVED WORK
  - heading "Recent sketches 0" [level=2]
  - button "View history ↗"
  - strong: Your review space is ready
  - paragraph: Upload a truss sketch to create the first saved analysis.
  - button "Start with a sketch →"
  - text: Sketch2Solve · Structural Truss Engineering Deterministic analysis and verification.
- dialog "Welcome to Sketch2Solve":
  - img "Sketch2Solve Logo"
  - heading "Welcome to Sketch2Solve" [level=2]
  - paragraph: What should we call you?
  - text: Your Name or Engineering Callout
  - textbox "Your Name or Engineering Callout":
    - /placeholder: e.g. Jane Doe, PE
  - button "Continue" [disabled]
```

# Test source

```ts
  52  |   })
  53  | 
  54  |   test('2. Browser-level scrolling: Zero document scrollbars on Dashboard & internal scrolling', async ({ page }) => {
  55  |     // Set user so onboarding doesn't block
  56  |     await page.goto('/')
  57  |     await page.evaluate(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
  58  |     await page.reload()
  59  | 
  60  |     await expect(page.locator('.dashboard-page')).toBeVisible()
  61  | 
  62  |     // 1. Verify document-level scroll is 0 / hidden
  63  |     const documentScroll = await page.evaluate(() => {
  64  |       const doc = document.documentElement
  65  |       return {
  66  |         hasScrollbar: doc.scrollHeight > doc.clientHeight,
  67  |         overflow: window.getComputedStyle(doc).overflow,
  68  |         bodyOverflow: window.getComputedStyle(document.body).overflow,
  69  |         windowScrollY: window.scrollY,
  70  |       }
  71  |     })
  72  |     expect(documentScroll.overflow).toBe('hidden')
  73  |     expect(documentScroll.bodyOverflow).toBe('hidden')
  74  |     expect(documentScroll.windowScrollY).toBe(0)
  75  | 
  76  |     // 2. Verify sidebar and topbar are fixed and stable
  77  |     const topbar = page.locator('.topbar')
  78  |     await expect(topbar).toBeVisible()
  79  |     const sidebar = page.locator('.sidebar')
  80  |     await expect(sidebar).toBeVisible()
  81  | 
  82  |     // 3. Verify main content viewport exists and handles internal scrolling
  83  |     const viewport = page.locator('.main-content-viewport')
  84  |     await expect(viewport).toBeVisible()
  85  |     const viewportOverflow = await viewport.evaluate((el) => window.getComputedStyle(el).overflowY)
  86  |     expect(['auto', 'scroll']).toContain(viewportOverflow)
  87  | 
  88  |     // Capture dashboard screenshot
  89  |     await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '02-dashboard-clean.png') })
  90  |   })
  91  | 
  92  |   test('3. Compact Getting Started guide: 6-step walkthrough opens, navigates, and closes', async ({ page }) => {
  93  |     await page.goto('/')
  94  |     await page.evaluate(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
  95  |     await page.reload()
  96  | 
  97  |     // Open guide via Dashboard button
  98  |     const guideBtn = page.locator('.dashboard-guide-btn')
  99  |     await expect(guideBtn).toBeVisible()
  100 |     await guideBtn.click()
  101 | 
  102 |     const guideModal = page.locator('.guide-overlay')
  103 |     await expect(guideModal).toBeVisible()
  104 |     await expect(page.locator('.step-badge')).toContainText('Step 1 of 6')
  105 |     await expect(page.locator('.step-title')).toContainText('Create a New Analysis')
  106 | 
  107 |     // Step dots should be 6
  108 |     const dots = page.locator('.step-dot')
  109 |     await expect(dots).toHaveCount(6)
  110 | 
  111 |     // Click Next
  112 |     await page.locator('.btn-guide-primary').click()
  113 |     await expect(page.locator('.step-badge')).toContainText('Step 2 of 6')
  114 |     await expect(page.locator('.step-title')).toContainText('Upload a Sketch or Describe with AI')
  115 | 
  116 |     // Click step 6 dot directly
  117 |     await dots.nth(5).click()
  118 |     await expect(page.locator('.step-badge')).toContainText('Step 6 of 6')
  119 |     await expect(page.locator('.step-title')).toContainText('Understand Results & Export')
  120 | 
  121 |     // Capture guide screenshot
  122 |     await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '03-getting-started-guide.png') })
  123 | 
  124 |     // Dismiss guide
  125 |     await page.locator('.btn-close-guide').click()
  126 |     await expect(guideModal).not.toBeVisible()
  127 |   })
  128 | 
  129 |   test('4. Developer messaging removed and official branding loaded', async ({ page }) => {
  130 |     await page.goto('/')
  131 |     await page.evaluate(() => localStorage.setItem('sketch2solve_username', 'Engineer Sarah'))
  132 |     await page.reload()
  133 | 
  134 |     // 1. "Private by default" must not exist anywhere
  135 |     await expect(page.locator('text=Private by default')).toHaveCount(0)
  136 |     await expect(page.locator('text=Don’t expose this workspace publicly')).toHaveCount(0)
  137 | 
  138 |     // 2. "Local review workspace" must not exist in footer
  139 |     await expect(page.locator('text=Sketch2Solve · Local review workspace')).toHaveCount(0)
  140 | 
  141 |     // 3. Official footer text present
  142 |     await expect(page.locator('.main-footer')).toContainText('Sketch2Solve · Structural Truss Engineering')
  143 | 
  144 |     // 4. Official brand logo present in sidebar
  145 |     const brandLogo = page.locator('.brand-logo-img')
  146 |     await expect(brandLogo).toBeVisible()
  147 |     expect(await brandLogo.getAttribute('src')).toBe('/logo.png')
  148 |   })
  149 | 
  150 |   test('5. Truss Editor canvas interactions and zero browser scrollbars preserved', async ({ page }) => {
  151 |     await page.goto('/?view=editor')
> 152 |     await expect(page.locator('.truss-editor')).toBeVisible({ timeout: 15_000 })
      |                                                 ^ Error: expect(locator).toBeVisible() failed
  153 | 
  154 |     // Check editor canvas and SVG viewport
  155 |     const canvasViewport = page.locator('.editor-canvas-container')
  156 |     await expect(canvasViewport).toBeVisible()
  157 | 
  158 |     // Check window scroll is 0
  159 |     const scrollY = await page.evaluate(() => window.scrollY)
  160 |     expect(scrollY).toBe(0)
  161 | 
  162 |     // Check status bar and tools
  163 |     await expect(page.locator('.editor-toolbar')).toBeVisible()
  164 |     await expect(page.locator('.editor-statusbar')).toBeVisible()
  165 | 
  166 |     // Capture editor screenshot
  167 |     await page.screenshot({ path: path.join(process.env.QA_OUTPUT_DIR || '.', '04-truss-editor.png') })
  168 |   })
  169 | })
  170 | 
  171 | 
```