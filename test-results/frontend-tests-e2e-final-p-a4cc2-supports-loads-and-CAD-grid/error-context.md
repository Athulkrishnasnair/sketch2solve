# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: frontend/tests/e2e/final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 1. Natural Language Design geometry preview accurately renders geometry, supports, loads, and CAD grid
- Location: frontend/tests/e2e/final-polish.spec.js:6:3

# Error details

```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
Call log:
  - navigating to "/?view=design", waiting until "load"

```

# Test source

```ts
  1   | import { readFileSync } from 'node:fs'
  2   | import path from 'node:path'
  3   | import { test, expect } from '@playwright/test'
  4   | 
  5   | test.describe('Sketch2Solve Final Polish and Verification', () => {
  6   |   test('1. Natural Language Design geometry preview accurately renders geometry, supports, loads, and CAD grid', async ({ page }) => {
> 7   |     await page.goto('/?view=design')
      |                ^ Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
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
```