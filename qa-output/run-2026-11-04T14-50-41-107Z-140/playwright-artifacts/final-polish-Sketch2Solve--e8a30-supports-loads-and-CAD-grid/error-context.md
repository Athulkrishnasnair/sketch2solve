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

Locator: locator('.studio-right-pane .cad-svg').locator('.cad-load-arrow')
Expected: visible
Error: strict mode violation: locator('.studio-right-pane .cad-svg').locator('.cad-load-arrow') resolved to 2 elements:
    1) <line x1="0" x2="0" y2="0" stroke="#dc2626" data-v-0ea7f51c="" stroke-width="0.1008" class="cad-load-arrow" y1="-0.8400000000000001"></line> aka locator('.cad-load-arrow').first()
    2) <polygon fill="#dc2626" data-v-0ea7f51c="" class="cad-load-arrow" points="-0.12960000000000002,-0.23040000000000005 0.12960000000000002,-0.23040000000000005 0,0"></polygon> aka locator('polygon').nth(4)

Call log:
  - Expect "toBeVisible" locator('.studio-right-pane .cad-svg').locator('.cad-load-arrow') with timeout 8000ms
  - waiting for locator('.studio-right-pane .cad-svg').locator('.cad-load-arrow')

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
      - generic [ref=e74]: Design proposal formulated. Review proposed geometry before applying.
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
            - generic [ref=e90]:
              - textbox "Describe structural change or question (e.g. \"Add a diagonal between J1 and J3\", \"Move J2 up 0.5m\", \"Why unstable?\")..." [ref=e91]: Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top
              - generic [ref=e92]:
                - generic [ref=e93]: Enter ↵ to submit · Shift+Enter for newline
                - button "Generate" [ref=e94] [cursor=pointer]
            - generic [ref=e100]:
              - generic [ref=e101]:
                - generic [ref=e102]:
                  - generic [ref=e103]: CREATE
                  - 'generic "Proposal ID: 4049fb07008a4989a11233e2a6eb7304" [ref=e107]': "#4049fb07"
                  - generic [ref=e108]: rev 1 rev 2
                - generic [ref=e111]: Valid
              - paragraph [ref=e117]: Generated a statically determinate triangular truss with a 6.0 m span, 3.0 m height, pin support at left, roller support at right, and applied vertical load.
              - generic [ref=e118]: Topology Preview
              - generic [ref=e130]:
                - generic [ref=e131]:
                  - generic [ref=e132]: "3"
                  - generic [ref=e133]: Joints
                - generic [ref=e134]:
                  - generic [ref=e135]: "3"
                  - generic [ref=e136]: Members
                - generic [ref=e137]:
                  - generic [ref=e138]: "2"
                  - generic [ref=e139]: Supports
                - generic [ref=e140]:
                  - generic [ref=e141]: "1"
                  - generic [ref=e142]: Loads
                - generic [ref=e143]:
                  - generic [ref=e144]: 6.00 m
                  - generic [ref=e145]: Span
                - generic [ref=e146]:
                  - generic [ref=e147]: 3.00 m
                  - generic [ref=e148]: Height
              - generic [ref=e152]:
                - text: "Predicted:"
                - strong [ref=e153]: SQUARE_FULL_RANK
                - text: (6 eq vs 6 unk)
              - generic [ref=e154]:
                - button "Discard" [ref=e155] [cursor=pointer]
                - button "Apply & Open Editor" [ref=e159] [cursor=pointer]
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
              - generic [ref=e186]: "Previewing Proposal #4049fb"
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
  13  |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
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
  30  |     await expect(pinSymbol).toBeVisible()
  31  |     await expect(rollerSymbol).toBeVisible()
  32  | 
  33  |     // 4. Check load vector arrow and magnitude label exist
  34  |     const loadArrow = previewCanvas.locator('.cad-load-arrow')
  35  |     const loadLabel = previewCanvas.locator('.cad-load-label')
> 36  |     await expect(loadArrow).toBeVisible()
      |                             ^ Error: expect(locator).toBeVisible() failed
  37  |     await expect(loadLabel).toBeVisible()
  38  |     await expect(loadLabel).toContainText('10')
  39  | 
  40  |     // 5. Check CAD grid pattern exists
  41  |     const gridPattern = previewCanvas.locator('#cad-grid-pattern')
  42  |     await expect(gridPattern).toBeAttached()
  43  |   })
  44  | 
  45  |   test('2. Analysis History pagination footer adheres to design standards', async ({ page }) => {
  46  |     // 1. Ensure a record exists by creating one via Design Studio first
  47  |     await page.goto('/?view=design')
  48  |     const textarea = page.locator('.studio-left-pane .design-textarea')
  49  |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  50  |     await page.locator('.studio-left-pane .btn-submit').click()
  51  | 
  52  |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  53  |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  54  |     await proposalCard.locator('.btn-apply').click()
  55  | 
  56  |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  57  | 
  58  |     // 2. Now navigate to History page
  59  |     await page.goto('/?view=history')
  60  |     await expect(page.locator('.history-page')).toBeVisible({ timeout: 10_000 })
  61  | 
  62  |     // Check pagination footer exists with consistent design tokens
  63  |     const footer = page.locator('.history-pagination-footer')
  64  |     await expect(footer).toBeVisible()
  65  | 
  66  |     const paginationInfo = footer.locator('.pagination-info')
  67  |     await expect(paginationInfo).toBeVisible()
  68  |     await expect(paginationInfo).toContainText(/Showing \d+ of \d+ saved runs/)
  69  | 
  70  |     // Verify either Load More button is visible or All saved runs loaded is visible
  71  |     const hasLoadMore = await footer.locator('.btn-load-more').isVisible()
  72  |     const hasComplete = await footer.locator('.pagination-complete').isVisible()
  73  |     expect(hasLoadMore || hasComplete).toBe(true)
  74  |   })
  75  | 
  76  |   test('3. New Analysis evidence-card copy provides accurate, neutral explanation', async ({ page }) => {
  77  |     await page.goto('/?view=new')
  78  |     await expect(page.locator('.upload-card')).toBeVisible({ timeout: 10_000 })
  79  | 
  80  |     const step2 = page.locator('.workflow-step').nth(1)
  81  |     await expect(step2).toBeVisible()
  82  |     await expect(step2.locator('p')).toHaveText(
  83  |       'The selected AI provider interprets the sketch and proposes candidate joints, members, supports and loads for human review.'
  84  |     )
  85  |   })
  86  | 
  87  |   test('4. Issue Resolution Assistant is hidden by default and docks in bottom-right corner when opened', async ({ page }) => {
  88  |     // Navigate into the editor with a sample model
  89  |     await page.goto('/?view=design')
  90  |     const textarea = page.locator('.studio-left-pane .design-textarea')
  91  |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  92  |     await page.locator('.studio-left-pane .btn-submit').click()
  93  | 
  94  |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  95  |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  96  |     await proposalCard.locator('.btn-apply').click()
  97  | 
  98  |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  99  | 
  100 |     // Verify IssueResolutionAssistant card is NOT visible initially
  101 |     const assistantCard = page.locator('.contextual-action-card')
  102 |     await expect(assistantCard).not.toBeVisible()
  103 | 
  104 |     // Toggle highlight using floating canvas control
  105 |     const alertBtn = page.locator('.canvas-floating-controls button[title*="Highlight detected issues"], .canvas-floating-controls button[aria-label*="Highlight detected issues"]')
  106 |     if (await alertBtn.isVisible()) {
  107 |       await alertBtn.click()
  108 |       // Now assistant card should be visible and docked at bottom-right
  109 |       await expect(assistantCard).toBeVisible()
  110 |       const box = await assistantCard.boundingBox()
  111 |       expect(box).toBeTruthy()
  112 | 
  113 |       // Verify close/clear button closes it
  114 |       const closeBtn = assistantCard.locator('.card-close-btn')
  115 |       await closeBtn.click()
  116 |       await expect(assistantCard).not.toBeVisible()
  117 |     }
  118 |   })
  119 | 
  120 |   test('5. Right sidebar tabbed workspace cleanly toggles between Tools and Design with AI', async ({ page }) => {
  121 |     await page.goto('/?view=design')
  122 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  123 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  124 |     await page.locator('.studio-left-pane .btn-submit').click()
  125 | 
  126 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  127 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  128 |     await proposalCard.locator('.btn-apply').click()
  129 | 
  130 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  131 | 
  132 |     // Verify tabs exist in sidebar
  133 |     const tabsNav = page.locator('.sidebar-tabs-nav')
  134 |     await expect(tabsNav).toBeVisible()
  135 | 
  136 |     const toolsTab = tabsNav.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' })
```