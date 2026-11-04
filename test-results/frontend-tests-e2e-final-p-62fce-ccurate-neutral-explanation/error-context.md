# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/e2e/final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 3. New Analysis evidence-card copy provides accurate, neutral explanation
- Location: frontend/tests/e2e/final-polish.spec.js:154:3

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/?view=new", waiting until "load"

```

# Test source

```ts
  55  |           id: el.id,
  56  |           class: el.getAttribute('class') || '',
  57  |           fill: cs.fill,
  58  |           stroke: cs.stroke,
  59  |           strokeWidth: cs.strokeWidth,
  60  |           w: rect.width,
  61  |           h: rect.height,
  62  |         })
  63  |       }
  64  |       return results
  65  |     })
  66  | 
  67  |     // Assert that every joint label is small (< 50px) and has stroke = none
  68  |     const jointLabels = elementsInfo.filter(el => el.class.includes('cad-joint-label'))
  69  |     expect(jointLabels.length).toBe(3)
  70  |     for (const lbl of jointLabels) {
  71  |       expect(lbl.w).toBeLessThan(50)
  72  |       expect(lbl.h).toBeLessThan(50)
  73  |       expect(lbl.stroke).toBe('none')
  74  |     }
  75  | 
  76  |     // Assert that no structural element has enormous glyph dimensions (> 150px)
  77  |     const oversizedElements = elementsInfo.filter(el =>
  78  |       ['text', 'path', 'polygon', 'circle'].includes(el.tag) &&
  79  |       !el.class.includes('cad-member') &&
  80  |       el.w > 150
  81  |     )
  82  |     expect(oversizedElements).toHaveLength(0)
  83  | 
  84  |     // 7. Test larger multi-member truss (Warren truss with 4 panels)
  85  |     await textarea.fill('Build a Warren truss with 4 panels and a 10 m span')
  86  |     await page.locator('.studio-left-pane .btn-submit').click()
  87  |     await expect(page.locator('.studio-left-pane .design-proposal-card')).toBeVisible({ timeout: 10_000 })
  88  | 
  89  |     const warrenMembers = previewCanvas.locator('.cad-member')
  90  |     await expect(warrenMembers).toHaveCount(15)
  91  |     const warrenJoints = previewCanvas.locator('.cad-joint')
  92  |     await expect(warrenJoints).toHaveCount(9)
  93  | 
  94  |     // Verify all Warren labels are clean and small
  95  |     const warrenLabels = await previewCanvas.evaluate(svg => {
  96  |       return Array.from(svg.querySelectorAll('.cad-joint-label')).map(el => {
  97  |         const r = el.getBoundingClientRect()
  98  |         return { w: r.width, h: r.height, stroke: window.getComputedStyle(el).stroke }
  99  |       })
  100 |     })
  101 |     expect(warrenLabels.length).toBe(9)
  102 |     for (const lbl of warrenLabels) {
  103 |       expect(lbl.w).toBeLessThan(50)
  104 |       expect(lbl.h).toBeLessThan(50)
  105 |       expect(lbl.stroke).toBe('none')
  106 |     }
  107 | 
  108 |     // 8. Test different container aspect ratios (wide 1600x900 and narrow 800x700)
  109 |     await page.setViewportSize({ width: 1600, height: 900 })
  110 |     await page.waitForTimeout(300)
  111 |     let canvasBox = await previewCanvas.boundingBox()
  112 |     expect(canvasBox.width).toBeGreaterThan(600)
  113 | 
  114 |     await page.setViewportSize({ width: 850, height: 700 })
  115 |     await page.waitForTimeout(300)
  116 |     canvasBox = await previewCanvas.boundingBox()
  117 |     expect(canvasBox.width).toBeGreaterThan(400)
  118 | 
  119 |     // Restore standard viewport
  120 |     await page.setViewportSize({ width: 1280, height: 800 })
  121 |   })
  122 | 
  123 |   test('2. Analysis History pagination footer adheres to design standards', async ({ page }) => {
  124 |     // 1. Ensure a record exists by creating one via Design Studio first
  125 |     await page.goto('/?view=design')
  126 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  127 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  128 |     await page.locator('.studio-left-pane .btn-submit').click()
  129 | 
  130 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  131 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  132 |     await proposalCard.locator('.btn-apply').click()
  133 | 
  134 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  135 | 
  136 |     // 2. Now navigate to History page
  137 |     await page.goto('/?view=history')
  138 |     await expect(page.locator('.history-page')).toBeVisible({ timeout: 10_000 })
  139 | 
  140 |     // Check pagination footer exists with consistent design tokens
  141 |     const footer = page.locator('.history-pagination-footer')
  142 |     await expect(footer).toBeVisible()
  143 | 
  144 |     const paginationInfo = footer.locator('.pagination-info')
  145 |     await expect(paginationInfo).toBeVisible()
  146 |     await expect(paginationInfo).toContainText(/Showing \d+ of \d+ saved runs/)
  147 | 
  148 |     // Verify either Load More button is visible or All saved runs loaded is visible
  149 |     const hasLoadMore = await footer.locator('.btn-load-more').isVisible()
  150 |     const hasComplete = await footer.locator('.pagination-complete').isVisible()
  151 |     expect(hasLoadMore || hasComplete).toBe(true)
  152 |   })
  153 | 
  154 |   test('3. New Analysis evidence-card copy provides accurate, neutral explanation', async ({ page }) => {
> 155 |     await page.goto('/?view=new')
      |                ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
  156 |     await expect(page.locator('.upload-card')).toBeVisible({ timeout: 10_000 })
  157 | 
  158 |     const step2 = page.locator('.workflow-step').nth(1)
  159 |     await expect(step2).toBeVisible()
  160 |     await expect(step2.locator('p')).toHaveText(
  161 |       'The selected AI provider interprets the sketch and proposes candidate joints, members, supports and loads for human review.'
  162 |     )
  163 |   })
  164 | 
  165 |   test('4. Issue Resolution Assistant docks in bottom-right corner and closes when highlighting is cleared', async ({ page }) => {
  166 |     // Navigate into the editor with a sample model
  167 |     await page.goto('/?view=design')
  168 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  169 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  170 |     await page.locator('.studio-left-pane .btn-submit').click()
  171 | 
  172 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  173 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  174 |     await proposalCard.locator('.btn-apply').click()
  175 | 
  176 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  177 | 
  178 |     // Assistant card is docked at bottom-right
  179 |     const assistantCard = page.locator('.contextual-action-card')
  180 |     if (await assistantCard.isVisible()) {
  181 |       const box = await assistantCard.boundingBox()
  182 |       expect(box).toBeTruthy()
  183 | 
  184 |       // Verify close/clear button closes it
  185 |       const closeBtn = assistantCard.locator('.card-close-btn')
  186 |       await closeBtn.click()
  187 |       await expect(assistantCard).not.toBeVisible()
  188 | 
  189 |       // Toggle highlight using floating canvas control re-opens it
  190 |       const alertBtn = page.locator('.canvas-floating-controls button[title*="Highlight detected issues"], .canvas-floating-controls button[aria-label*="Highlight detected issues"]')
  191 |       if (await alertBtn.isVisible()) {
  192 |         await alertBtn.click()
  193 |         await expect(assistantCard).toBeVisible()
  194 |       }
  195 |     }
  196 |   })
  197 | 
  198 |   test('5. Right sidebar tabbed workspace cleanly toggles between Tools and Design with AI', async ({ page }) => {
  199 |     await page.goto('/?view=design')
  200 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  201 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  202 |     await page.locator('.studio-left-pane .btn-submit').click()
  203 | 
  204 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  205 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  206 |     await proposalCard.locator('.btn-apply').click()
  207 | 
  208 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  209 | 
  210 |     // Verify tabs exist in sidebar
  211 |     const tabsNav = page.locator('.sidebar-tabs-nav')
  212 |     await expect(tabsNav).toBeVisible()
  213 | 
  214 |     const toolsTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' })
  215 |     const designTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' })
  216 |     await expect(toolsTab).toBeVisible()
  217 |     await expect(designTab).toBeVisible()
  218 | 
  219 |     // Initially Tools tab is active
  220 |     await expect(toolsTab).toHaveClass(/active/)
  221 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  222 |     await expect(page.locator('.sidebar-design-pane')).not.toBeVisible()
  223 | 
  224 |     // Click Design with AI tab
  225 |     await designTab.click()
  226 |     await expect(designTab).toHaveClass(/active/)
  227 |     await expect(page.locator('.sidebar-design-pane')).toBeVisible()
  228 |     await expect(page.locator('.sidebar-tools-pane')).not.toBeVisible()
  229 | 
  230 |     // Topbar btn-ai switches back to Tools tab or toggles
  231 |     const topbarAiBtn = page.locator('.editor-topbar .btn-ai')
  232 |     await expect(topbarAiBtn).toHaveClass(/active/)
  233 |     await topbarAiBtn.click()
  234 |     await expect(toolsTab).toHaveClass(/active/)
  235 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  236 |   })
  237 | 
  238 |   test('6. Construction and Structural tools use 3-column grid with uniform 48px tile height', async ({ page }) => {
  239 |     await page.goto('/?view=design')
  240 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  241 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  242 |     await page.locator('.studio-left-pane .btn-submit').click()
  243 | 
  244 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  245 |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  246 |     await proposalCard.locator('.btn-apply').click()
  247 | 
  248 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 20_000 })
  249 | 
  250 |     // Verify 3-column grid for Construction
  251 |     const constructionGrid = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tools-grid-3')
  252 |     await expect(constructionGrid).toBeVisible()
  253 |     await expect(constructionGrid.locator('.tool-tile')).toHaveCount(3)
  254 | 
  255 |     // Verify 3-column grid for Structural
```