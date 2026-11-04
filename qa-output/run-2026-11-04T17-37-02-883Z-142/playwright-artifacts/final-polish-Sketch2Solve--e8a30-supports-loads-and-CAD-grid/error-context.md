# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 1. Natural Language Design geometry preview accurately renders geometry, supports, loads, and CAD grid
- Location: tests/e2e/final-polish.spec.js:6:3

# Error details

```
Test timeout of 90000ms exceeded.
```

```
Error: expect(locator).toHaveCount(expected) failed

Locator:  locator('.studio-right-pane .cad-svg').locator('.cad-member')
Expected: 15
Received: 3

Call log:
  - Expect "toHaveCount" locator('.studio-right-pane .cad-svg').locator('.cad-member') with timeout 8000ms
  - waiting for locator('.studio-right-pane .cad-svg').locator('.cad-member')
    5 × locator resolved to 3 elements
      - unexpected value "3"
  - Test timeout of 90000ms exceeded.

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - complementary [ref=e4]:
    - link "Sketch2Solve STRUCTURE REVIEW" [ref=e5] [cursor=pointer]:
      - /url: /
      - generic [ref=e13]:
        - strong [ref=e14]: Sketch2Solve
        - generic [ref=e15]: STRUCTURE REVIEW
    - generic [ref=e16]: Local workspace
    - navigation "Main navigation" [ref=e18]:
      - button "Dashboard" [ref=e19] [cursor=pointer]
      - button "Natural Language Design" [ref=e26] [cursor=pointer]
      - button "New analysis" [ref=e32] [cursor=pointer]
      - button "Analysis history 0" [ref=e36] [cursor=pointer]:
        - generic [ref=e42]: Analysis history
        - generic [ref=e43]: "0"
    - generic [ref=e49]:
      - strong [ref=e50]: Private by default
      - paragraph [ref=e51]: Runs stay in your local backend. Don’t expose this workspace publicly.
    - generic [ref=e52]: Backend API · localhost:5000
  - main [ref=e54]:
    - generic [ref=e55]:
      - generic [ref=e56]:
        - generic [ref=e57]: Workspace
        - generic [ref=e58]: /
        - strong [ref=e59]: Natural Language Design
      - generic [ref=e60]:
        - generic [ref=e61]: LOCAL ONLY
        - generic [aria-hidden] [ref=e63]: S
    - generic [ref=e64]:
      - generic [ref=e65]:
        - generic [ref=e66]:
          - generic [ref=e67]: CONVERSATIONAL TRUSS WORKBENCH
          - heading "Natural Language Design Studio" [level=1] [ref=e68]
          - paragraph [ref=e69]: Synthesize new structural geometries, modify canvas snapshots, and inspect determinacy using deterministic engineering rules.
        - generic [ref=e71]:
          - generic [ref=e72]: "Target Structure:"
          - combobox "Target Structure:" [ref=e73] [cursor=pointer]:
            - option "＋ New Truss Design (Blank Canvas)" [selected]
      - generic [ref=e74]:
        - generic [ref=e75]:
          - generic [ref=e76]:
            - generic [ref=e77]:
              - generic [ref=e78]:
                - generic "Model revision 1" [ref=e80]: Rev 1
                - radiogroup "Design Intent" [ref=e85]:
                  - button "Auto" [ref=e86] [cursor=pointer]
                  - button "Create" [ref=e87] [cursor=pointer]
                  - button "Modify" [ref=e88] [cursor=pointer]
                  - button "Explain" [ref=e89] [cursor=pointer]
              - generic [ref=e91]:
                - generic [ref=e92]:
                  - generic [ref=e93]:
                    - generic [ref=e94]: CREATE
                    - 'generic "Proposal ID: b9b209669c804a1ebdd1df6b33a6f9d2" [ref=e98]': "#b9b20966"
                    - generic [ref=e99]: rev 1 rev 2
                  - generic [ref=e102]: Valid
                - paragraph [ref=e108]: Generated a statically determinate triangular truss with a 6.0 m span, 3.0 m height, pin support at left, roller support at right, and applied vertical load.
                - generic [ref=e109]: Topology Preview
                - generic [ref=e121]:
                  - generic [ref=e122]:
                    - generic [ref=e123]: "3"
                    - generic [ref=e124]: Joints
                  - generic [ref=e125]:
                    - generic [ref=e126]: "3"
                    - generic [ref=e127]: Members
                  - generic [ref=e128]:
                    - generic [ref=e129]: "2"
                    - generic [ref=e130]: Supports
                  - generic [ref=e131]:
                    - generic [ref=e132]: "1"
                    - generic [ref=e133]: Loads
                  - generic [ref=e134]:
                    - generic [ref=e135]: 6.00 m
                    - generic [ref=e136]: Span
                  - generic [ref=e137]:
                    - generic [ref=e138]: 3.00 m
                    - generic [ref=e139]: Height
                - generic [ref=e143]:
                  - text: "Predicted:"
                  - strong [ref=e144]: SQUARE_FULL_RANK
                  - text: (6 eq vs 6 unk)
                - generic [ref=e145]:
                  - button "Discard" [ref=e146] [cursor=pointer]
                  - button "Apply & Open Editor" [ref=e150] [cursor=pointer]
            - generic [ref=e153]:
              - textbox "Describe structural change or question (e.g. \"Add a diagonal between J1 and J3\", \"Move J2 up 0.5m\", \"Why unstable?\")..." [active] [ref=e154]: Build a Warren truss with 4 panels and a 10 m span
              - generic [ref=e155]:
                - generic [ref=e156]: Enter ↵ to submit · Shift+Enter for newline
                - button "Generate" [ref=e157] [cursor=pointer]
          - generic [ref=e162]:
            - strong [ref=e167]: CAD Design Conventions
            - list [ref=e168]:
              - listitem [ref=e169]:
                - strong [ref=e170]: "CREATE:"
                - text: Specify span, height, panel count, and support conditions (e.g.
                - emphasis [ref=e171]: "\"Warren truss, 6 m span, 4 panels\""
                - text: ).
              - listitem [ref=e172]:
                - strong [ref=e173]: "MODIFY:"
                - text: Reference existing joint/member IDs (e.g.
                - emphasis [ref=e174]: "\"Add diagonal between J1 and J3\""
                - text: ","
                - emphasis [ref=e175]: "\"Move J2 up 0.5 m\""
                - text: ).
              - listitem [ref=e176]:
                - strong [ref=e177]: "EXPLAIN:"
                - text: Ask about determinacy, stability, or support reactions (e.g.
                - emphasis [ref=e178]: "\"Why is this unstable?\""
                - text: ).
              - listitem [ref=e179]:
                - strong [ref=e180]: "SAFETY GATE:"
                - text: AI proposals are strictly non-destructive previews until explicitly approved.
        - generic [ref=e181]:
          - generic [ref=e182]:
            - generic [ref=e183]:
              - strong [ref=e185]: Structural Geometry Preview
              - generic [ref=e186]: "Previewing Proposal #b9b209"
            - generic [ref=e187]:
              - generic [ref=e188]:
                - text: "Span:"
                - strong [ref=e189]: 6.00 m
              - generic [ref=e190]:
                - text: "Height:"
                - strong [ref=e191]: 3.00 m
              - generic [ref=e192]:
                - text: "Joints:"
                - strong [ref=e193]: "3"
              - generic [ref=e194]:
                - text: "Members:"
                - strong [ref=e195]: "3"
          - generic [ref=e196]:
            - img [ref=e197]:
              - generic [ref=e209]: 10 kN
              - generic [ref=e213]:
                - generic [ref=e214]: J1
                - generic [ref=e216]: J2
                - generic [ref=e218]: J3
            - generic [ref=e220]:
              - generic [ref=e221]: Existing Member
              - generic [ref=e223]: Proposed Addition
              - generic [ref=e225]: Proposed Deletion
              - generic [ref=e227]: Support Constraint
    - generic [ref=e229]:
      - generic [ref=e230]: Sketch2Solve · Local review workspace
      - generic [ref=e231]: Interpretation is a starting point, not a structural check.
```

# Test source

```ts
  1   | import { readFileSync } from 'node:fs'
  2   | import path from 'node:path'
  3   | import { test, expect } from '@playwright/test'
  4   | 
  5   | test.describe('Sketch2Solve Final Polish and Verification', () => {
  6   |   test('1. Natural Language Design geometry preview accurately renders geometry, supports, loads, and CAD grid', async ({ page }) => {
  7   |     await page.goto('/?view=design')
  8   |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  9   | 
  10  |     const textarea = page.locator('.studio-left-pane .design-textarea')
  11  |     await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
  12  |     await page.locator('.studio-left-pane .btn-submit').click()
  13  | 
  14  |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  15  |     await expect(proposalCard).toBeVisible({ timeout: 30_000 })
  16  | 
  17  |     // Inspect large geometry preview on the right
  18  |     const previewCanvas = page.locator('.studio-right-pane .cad-svg')
  19  |     await expect(previewCanvas).toBeVisible()
  20  | 
  21  |     // 1. Check straight structural lines exist
  22  |     const memberLines = previewCanvas.locator('.cad-member')
  23  |     await expect(memberLines).toHaveCount(3)
  24  | 
  25  |     // 2. Check joints and labels exist
  26  |     const joints = previewCanvas.locator('.cad-joint')
  27  |     await expect(joints).toHaveCount(3)
  28  | 
  29  |     // 3. Check pin and roller support symbols exist
  30  |     const pinSymbol = previewCanvas.locator('.cad-support.pin')
  31  |     const rollerSymbol = previewCanvas.locator('.cad-support.roller')
  32  |     await expect(pinSymbol.first()).toBeVisible()
  33  |     await expect(rollerSymbol.first()).toBeVisible()
  34  | 
  35  |     // 4. Check load vector arrow and magnitude label exist
  36  |     const loadArrow = previewCanvas.locator('.cad-load-arrow')
  37  |     const loadLabel = previewCanvas.locator('.cad-load-label')
  38  |     await expect(loadArrow.first()).toBeAttached()
  39  |     await expect(loadLabel.first()).toBeVisible()
  40  |     await expect(loadLabel.first()).toContainText('10')
  41  | 
  42  |     // 5. Check CAD grid pattern exists
  43  |     const gridPattern = previewCanvas.locator('#cad-grid-pattern')
  44  |     await expect(gridPattern).toBeAttached()
  45  | 
  46  |     // 6. Verify NO oversized glyphs or dark filled shapes exist
  47  |     const elementsInfo = await previewCanvas.evaluate(svg => {
  48  |       const results = []
  49  |       const all = svg.querySelectorAll('*')
  50  |       for (const el of all) {
  51  |         const cs = window.getComputedStyle(el)
  52  |         const rect = el.getBoundingClientRect()
  53  |         results.push({
  54  |           tag: el.tagName,
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
> 90  |     await expect(warrenMembers).toHaveCount(15)
      |                                 ^ Error: expect(locator).toHaveCount(expected) failed
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
  155 |     await page.goto('/?view=new')
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
```