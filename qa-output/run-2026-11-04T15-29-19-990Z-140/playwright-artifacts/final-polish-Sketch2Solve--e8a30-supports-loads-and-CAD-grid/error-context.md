# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 1. Natural Language Design geometry preview accurately renders geometry, supports, loads, and CAD grid
- Location: tests/e2e/final-polish.spec.js:4:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.studio-left-pane .design-proposal-card')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.studio-left-pane .design-proposal-card') with timeout 10000ms
  - waiting for locator('.studio-left-pane .design-proposal-card')

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
  - strong: Private by default
  - paragraph: Runs stay in your local backend. Don’t expose this workspace publicly.
  - text: Backend API · localhost:5000
- main:
  - text: Workspace /
  - strong: Natural Language Design
  - text: LOCAL ONLY CONVERSATIONAL TRUSS WORKBENCH
  - heading "Natural Language Design Studio" [level=1]
  - paragraph: Synthesize new structural geometries, modify canvas snapshots, and inspect determinacy using deterministic engineering rules.
  - text: "Target Structure:"
  - combobox "Target Structure:" [disabled]:
    - option "＋ New Truss Design (Blank Canvas)" [selected]
  - text: Rev 1
  - radiogroup "Design Intent":
    - button "Auto"
    - button "Create"
    - button "Modify"
    - button "Explain"
  - textbox "Describe structural change or question (e.g. \"Add a diagonal between J1 and J3\", \"Move J2 up 0.5m\", \"Why unstable?\")..." [disabled]: Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top
  - text: Enter ↵ to submit · Shift+Enter for newline
  - button "Analyzing..." [disabled]
  - button "Add a diagonal between J1 and J3" [disabled]
  - button "Move J2 up by 0.5 m" [disabled]
  - button "Add 10 kN downward load at top" [disabled]
  - button "Why is this structure unstable?" [disabled]
  - strong: CAD Design Conventions
  - list:
    - listitem:
      - strong: "CREATE:"
      - text: Specify span, height, panel count, and support conditions (e.g.
      - emphasis: "\"Warren truss, 6 m span, 4 panels\""
      - text: ).
    - listitem:
      - strong: "MODIFY:"
      - text: Reference existing joint/member IDs (e.g.
      - emphasis: "\"Add diagonal between J1 and J3\""
      - text: ","
      - emphasis: "\"Move J2 up 0.5 m\""
      - text: ).
    - listitem:
      - strong: "EXPLAIN:"
      - text: Ask about determinacy, stability, or support reactions (e.g.
      - emphasis: "\"Why is this unstable?\""
      - text: ).
    - listitem:
      - strong: "SAFETY GATE:"
      - text: AI proposals are strictly non-destructive previews until explicitly approved.
  - strong: Structural Geometry Preview
  - strong: Ready to Design
  - paragraph: Type a prompt on the left to synthesize a new truss structure, or select an existing analysis above.
  - text: Existing Member Proposed Addition Proposed Deletion Support Constraint Sketch2Solve · Local review workspace Interpretation is a starting point, not a structural check.
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test'
  2   | 
  3   | test.describe('Sketch2Solve Final Polish and Verification', () => {
  4   |   test('1. Natural Language Design geometry preview accurately renders geometry, supports, loads, and CAD grid', async ({ page }) => {
  5   |     await page.goto('/?view=design')
  6   |     await expect(page.locator('.design-studio-page')).toBeVisible({ timeout: 10_000 })
  7   | 
  8   |     const textarea = page.locator('.studio-left-pane .design-textarea')
  9   |     await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
  10  |     await page.locator('.studio-left-pane .btn-submit').click()
  11  | 
  12  |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
> 13  |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
      |                                ^ Error: expect(locator).toBeVisible() failed
  14  | 
  15  |     // Inspect large geometry preview on the right
  16  |     const previewCanvas = page.locator('.studio-right-pane .cad-svg')
  17  |     await expect(previewCanvas).toBeVisible()
  18  | 
  19  |     // 1. Check straight structural lines exist
  20  |     const memberLines = previewCanvas.locator('.cad-member')
  21  |     await expect(memberLines).toHaveCount(3)
  22  | 
  23  |     // 2. Check joints and labels exist
  24  |     const joints = previewCanvas.locator('.cad-joint')
  25  |     await expect(joints).toHaveCount(3)
  26  | 
  27  |     // 3. Check pin and roller support symbols exist
  28  |     const pinSymbol = previewCanvas.locator('.cad-support.pin')
  29  |     const rollerSymbol = previewCanvas.locator('.cad-support.roller')
  30  |     await expect(pinSymbol.first()).toBeVisible()
  31  |     await expect(rollerSymbol.first()).toBeVisible()
  32  | 
  33  |     // 4. Check load vector arrow and magnitude label exist
  34  |     const loadArrow = previewCanvas.locator('.cad-load-arrow')
  35  |     const loadLabel = previewCanvas.locator('.cad-load-label')
  36  |     await expect(loadArrow.first()).toBeAttached()
  37  |     await expect(loadLabel.first()).toBeVisible()
  38  |     await expect(loadLabel.first()).toContainText('10')
  39  | 
  40  |     // 5. Check CAD grid pattern exists
  41  |     const gridPattern = previewCanvas.locator('#cad-grid-pattern')
  42  |     await expect(gridPattern).toBeAttached()
  43  | 
  44  |     // 6. Verify NO oversized glyphs or dark filled shapes exist
  45  |     const elementsInfo = await previewCanvas.evaluate(svg => {
  46  |       const results = []
  47  |       const all = svg.querySelectorAll('*')
  48  |       for (const el of all) {
  49  |         const cs = window.getComputedStyle(el)
  50  |         const rect = el.getBoundingClientRect()
  51  |         results.push({
  52  |           tag: el.tagName,
  53  |           id: el.id,
  54  |           class: el.getAttribute('class') || '',
  55  |           fill: cs.fill,
  56  |           stroke: cs.stroke,
  57  |           strokeWidth: cs.strokeWidth,
  58  |           w: rect.width,
  59  |           h: rect.height,
  60  |         })
  61  |       }
  62  |       return results
  63  |     })
  64  | 
  65  |     // Assert that every joint label is small (< 50px) and has stroke = none
  66  |     const jointLabels = elementsInfo.filter(el => el.class.includes('cad-joint-label'))
  67  |     expect(jointLabels.length).toBe(3)
  68  |     for (const lbl of jointLabels) {
  69  |       expect(lbl.w).toBeLessThan(50)
  70  |       expect(lbl.h).toBeLessThan(50)
  71  |       expect(lbl.stroke).toBe('none')
  72  |     }
  73  | 
  74  |     // Assert that no structural element has enormous glyph dimensions (> 150px)
  75  |     const oversizedElements = elementsInfo.filter(el =>
  76  |       ['text', 'path', 'polygon', 'circle'].includes(el.tag) &&
  77  |       !el.class.includes('cad-member') &&
  78  |       el.w > 150
  79  |     )
  80  |     expect(oversizedElements).toHaveLength(0)
  81  | 
  82  |     // 7. Test larger multi-member truss (Warren truss with 4 panels)
  83  |     await textarea.fill('Build a Warren truss with 4 panels and a 10 m span')
  84  |     await page.locator('.studio-left-pane .btn-submit').click()
  85  |     await expect(page.locator('.studio-left-pane .design-proposal-card')).toBeVisible({ timeout: 10_000 })
  86  | 
  87  |     const warrenMembers = previewCanvas.locator('.cad-member')
  88  |     await expect(warrenMembers).toHaveCount(15)
  89  |     const warrenJoints = previewCanvas.locator('.cad-joint')
  90  |     await expect(warrenJoints).toHaveCount(9)
  91  | 
  92  |     // Verify all Warren labels are clean and small
  93  |     const warrenLabels = await previewCanvas.evaluate(svg => {
  94  |       return Array.from(svg.querySelectorAll('.cad-joint-label')).map(el => {
  95  |         const r = el.getBoundingClientRect()
  96  |         return { w: r.width, h: r.height, stroke: window.getComputedStyle(el).stroke }
  97  |       })
  98  |     })
  99  |     expect(warrenLabels.length).toBe(9)
  100 |     for (const lbl of warrenLabels) {
  101 |       expect(lbl.w).toBeLessThan(50)
  102 |       expect(lbl.h).toBeLessThan(50)
  103 |       expect(lbl.stroke).toBe('none')
  104 |     }
  105 | 
  106 |     // 8. Test different container aspect ratios (wide 1600x900 and narrow 800x700)
  107 |     await page.setViewportSize({ width: 1600, height: 900 })
  108 |     await page.waitForTimeout(300)
  109 |     let canvasBox = await previewCanvas.boundingBox()
  110 |     expect(canvasBox.width).toBeGreaterThan(600)
  111 | 
  112 |     await page.setViewportSize({ width: 850, height: 700 })
  113 |     await page.waitForTimeout(300)
```