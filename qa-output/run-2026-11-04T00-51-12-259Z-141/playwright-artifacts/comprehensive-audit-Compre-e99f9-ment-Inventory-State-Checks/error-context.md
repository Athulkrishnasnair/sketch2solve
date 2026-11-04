# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: comprehensive-audit.spec.js >> Comprehensive Application Audit >> Audit 2: Complete Interactive Element Inventory & State Checks
- Location: tests/e2e/comprehensive-audit.spec.js:80:3

# Error details

```
Error: locator.isEnabled: Error: strict mode violation: locator('.dashboard-primary') resolved to 2 elements:
    1) <button type="button" data-v-ec0fe1c5="" class="dashboard-primary">…</button> aka getByRole('button', { name: '＋ New analysis' })
    2) <button type="button" data-v-ec0fe1c5="" class="dashboard-primary">…</button> aka getByRole('button', { name: 'Start with a sketch →' })

Call log:
  - waiting for locator('.dashboard-primary')

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
        - strong [ref=e59]: Dashboard
      - generic [ref=e60]:
        - generic [ref=e61]: LOCAL ONLY
        - generic [aria-hidden] [ref=e63]: S
    - generic [ref=e64]:
      - generic [ref=e65]:
        - generic [ref=e66]:
          - generic [ref=e67]: LOCAL ENGINEERING WORKSPACE
          - heading [level=1] [ref=e68]:
            - text: Sketch review,
            - emphasis [ref=e69]: with evidence in view.
          - paragraph [ref=e70]: Compare visual detections and model interpretations, then decide what belongs in a structural model.
          - generic [ref=e71]:
            - button "＋ New analysis" [ref=e72] [cursor=pointer]:
              - generic [ref=e73]: ＋
              - text: New analysis
            - button "Create with AI" [ref=e74] [cursor=pointer]
            - button "Browse all history ↗" [ref=e78] [cursor=pointer]
        - generic [ref=e89]: IMAGE-SPACE EVIDENCE
      - generic [ref=e90]:
        - generic [ref=e91]:
          - generic [ref=e92]: ▤
          - generic [ref=e93]:
            - generic [ref=e94]: Saved analyses
            - strong [ref=e95]: "0"
          - generic [ref=e96]: from local history
        - generic [ref=e97]:
          - generic [ref=e98]: ◉
          - generic [ref=e99]:
            - generic [ref=e100]: Review boundary
            - strong [ref=e101]: Human checked
          - generic [ref=e102]: AI proposals stay unapproved
        - generic [ref=e103]:
          - generic [ref=e104]: ∑
          - generic [ref=e105]:
            - generic [ref=e106]: Solver access
            - strong [ref=e107]: After review
          - generic [ref=e108]: explicit submission only
      - generic [ref=e109]:
        - generic [ref=e110]:
          - generic [ref=e111]:
            - generic [ref=e112]: SAVED WORK
            - heading "Recent sketches 0" [level=2] [ref=e113]:
              - text: Recent sketches
              - generic [ref=e114]: "0"
          - button "View history ↗" [ref=e115] [cursor=pointer]
        - generic [ref=e116]:
          - generic [ref=e123]:
            - strong [ref=e124]: Your review space is ready
            - paragraph [ref=e125]: Upload a truss sketch to create the first saved analysis.
          - button "Start with a sketch →" [ref=e126] [cursor=pointer]:
            - text: Start with a sketch
            - generic [ref=e127]: →
    - generic [ref=e128]:
      - generic [ref=e129]: Sketch2Solve · Local review workspace
      - generic [ref=e130]: Interpretation is a starting point, not a structural check.
```

# Test source

```ts
  3   | import { test, expect } from '@playwright/test'
  4   | 
  5   | const configDirectory = import.meta.dirname
  6   | const evaluationDirectory = path.resolve(configDirectory, '../../../backend/evaluation/sketches')
  7   | 
  8   | const VIEWPORTS = {
  9   |   desktop: { width: 1920, height: 1080 },
  10  |   laptop: { width: 1366, height: 768 },
  11  |   tablet: { width: 768, height: 1024 },
  12  |   mobile: { width: 375, height: 667 },
  13  | }
  14  | 
  15  | test.describe('Comprehensive Application Audit', () => {
  16  |   // 1. Audit Viewports, Layout Overflow & Responsiveness across all main pages
  17  |   test('Audit 1: Layout Overflow and Responsiveness across all viewports', async ({ page }) => {
  18  |     const pagesToTest = [
  19  |       { name: 'Dashboard', url: '/' },
  20  |       { name: 'Natural Language Design Studio', url: '/?view=design' },
  21  |       { name: 'New Analysis', url: '/?view=new' },
  22  |       { name: 'Analysis History', url: '/?view=history' },
  23  |     ]
  24  | 
  25  |     const overflowFindings = []
  26  | 
  27  |     for (const [vpName, vpSize] of Object.entries(VIEWPORTS)) {
  28  |       await page.setViewportSize(vpSize)
  29  |       for (const p of pagesToTest) {
  30  |         await page.goto(p.url, { waitUntil: 'networkidle' })
  31  |         const metrics = await page.evaluate(() => {
  32  |           const doc = document.documentElement
  33  |           const body = document.body
  34  |           const scrollW = Math.max(doc.scrollWidth, body.scrollWidth)
  35  |           const clientW = window.innerWidth
  36  |           const hasHorizontalOverflow = scrollW > clientW + 1 // 1px threshold for subpixel
  37  | 
  38  |           // Check if any element specifically overflows the viewport
  39  |           const overflowingElements = []
  40  |           const allEls = document.querySelectorAll('*')
  41  |           for (const el of allEls) {
  42  |             const rect = el.getBoundingClientRect()
  43  |             if (rect.right > clientW + 2) {
  44  |               overflowingElements.push({
  45  |                 tag: el.tagName,
  46  |                 className: el.className?.toString?.() || '',
  47  |                 id: el.id,
  48  |                 right: rect.right,
  49  |                 width: rect.width,
  50  |               })
  51  |               if (overflowingElements.length >= 5) break
  52  |             }
  53  |           }
  54  | 
  55  |           return {
  56  |             scrollW,
  57  |             clientW,
  58  |             hasHorizontalOverflow,
  59  |             overflowingElements,
  60  |           }
  61  |         })
  62  | 
  63  |         if (metrics.hasHorizontalOverflow) {
  64  |           overflowFindings.push({
  65  |             viewport: vpName,
  66  |             page: p.name,
  67  |             scrollW: metrics.scrollW,
  68  |             clientW: metrics.clientW,
  69  |             elements: metrics.overflowingElements,
  70  |           })
  71  |         }
  72  |       }
  73  |     }
  74  | 
  75  |     console.log('--- OVERFLOW FINDINGS ---')
  76  |     console.log(JSON.stringify(overflowFindings, null, 2))
  77  |   })
  78  | 
  79  |   // 2. Interactive Element Inventory & Functional Audit
  80  |   test('Audit 2: Complete Interactive Element Inventory & State Checks', async ({ page }) => {
  81  |     const auditLog = []
  82  |     const consoleMessages = []
  83  |     const failedRequests = []
  84  | 
  85  |     page.on('console', (msg) => {
  86  |       consoleMessages.push({ type: msg.type(), text: msg.text() })
  87  |     })
  88  |     page.on('requestfailed', (req) => {
  89  |       failedRequests.push({ url: req.url(), method: req.method(), failure: req.failure()?.errorText })
  90  |     })
  91  | 
  92  |     // --- DASHBOARD ---
  93  |     await page.goto('/')
  94  |     await expect(page.locator('.dashboard-welcome')).toBeVisible()
  95  | 
  96  |     // 1. New Analysis Button
  97  |     const newBtn = page.locator('.dashboard-primary')
  98  |     auditLog.push({
  99  |       page: 'Dashboard',
  100 |       element: 'button.dashboard-primary',
  101 |       label: '＋ New analysis',
  102 |       hasHandler: await newBtn.count() > 0,
> 103 |       enabled: await newBtn.isEnabled(),
      |                             ^ Error: locator.isEnabled: Error: strict mode violation: locator('.dashboard-primary') resolved to 2 elements:
  104 |     })
  105 | 
  106 |     // 2. Create with AI Button (toggle)
  107 |     const createAiBtn = page.locator('.dashboard-ai-btn')
  108 |     await expect(createAiBtn).toBeVisible()
  109 |     await createAiBtn.click()
  110 |     const workbenchVisible = await page.locator('.dashboard-ai-workbench').isVisible()
  111 |     auditLog.push({
  112 |       page: 'Dashboard',
  113 |       element: 'button.dashboard-ai-btn',
  114 |       label: 'Create with AI',
  115 |       hasHandler: true,
  116 |       togglesWorkbench: workbenchVisible,
  117 |     })
  118 | 
  119 |     // 3. Close Workbench Button
  120 |     const closeWorkbenchBtn = page.locator('.btn-close-workbench')
  121 |     await closeWorkbenchBtn.click()
  122 |     const workbenchClosed = !(await page.locator('.dashboard-ai-workbench').isVisible())
  123 |     auditLog.push({
  124 |       page: 'Dashboard',
  125 |       element: 'button.btn-close-workbench',
  126 |       label: '✕',
  127 |       hasHandler: true,
  128 |       closesWorkbench: workbenchClosed,
  129 |     })
  130 | 
  131 |     // 4. History Links
  132 |     const historyLink = page.locator('.dashboard-actions .dashboard-link')
  133 |     auditLog.push({
  134 |       page: 'Dashboard',
  135 |       element: 'button.dashboard-link',
  136 |       label: 'Browse all history ↗',
  137 |       hasHandler: await historyLink.count() > 0,
  138 |       enabled: await historyLink.isEnabled(),
  139 |     })
  140 | 
  141 |     // 5. Workbench Prompt Submission & Examples
  142 |     await createAiBtn.click()
  143 |     const exampleChips = page.locator('.workbench-chip')
  144 |     const chipCount = await exampleChips.count()
  145 |     auditLog.push({
  146 |       page: 'Dashboard',
  147 |       element: '.workbench-chip',
  148 |       count: chipCount,
  149 |       label: 'Example Prompt Chips',
  150 |       hasHandler: chipCount > 0,
  151 |     })
  152 | 
  153 |     // Submit first chip
  154 |     await exampleChips.first().click()
  155 |     const proposalCard = page.locator('.dashboard-ai-workbench .design-proposal-card')
  156 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  157 |     auditLog.push({
  158 |       page: 'Dashboard',
  159 |       element: '.design-proposal-card',
  160 |       label: 'Generated Proposal Card',
  161 |       rendered: true,
  162 |       hasApply: await proposalCard.locator('.btn-apply').isVisible(),
  163 |       hasDiscard: await proposalCard.locator('.btn-reject').isVisible(),
  164 |     })
  165 | 
  166 |     // Apply proposal to create record and enter editor
  167 |     await proposalCard.locator('.btn-apply').click()
  168 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  169 | 
  170 |     // --- TRUSS EDITOR ---
  171 |     // Test all topbar buttons
  172 |     const backBtn = page.locator('.editor-topbar .back-btn')
  173 |     const undoBtn = page.locator('.editor-topbar button[title="Undo (Ctrl+Z)"]')
  174 |     const redoBtn = page.locator('.editor-topbar button[title="Redo (Ctrl+Y)"]')
  175 |     const saveBtn = page.locator('.editor-topbar .btn-save')
  176 |     const reviewBtn = page.locator('.editor-topbar .btn-review')
  177 |     const solveBtn = page.locator('.editor-topbar .btn-solve')
  178 |     const designAiBtn = page.locator('.editor-topbar .btn-ai')
  179 | 
  180 |     auditLog.push({
  181 |       page: 'TrussEditor',
  182 |       element: 'topbar buttons',
  183 |       back: { visible: await backBtn.isVisible(), enabled: await backBtn.isEnabled() },
  184 |       undo: { visible: await undoBtn.isVisible(), enabled: await undoBtn.isEnabled() },
  185 |       redo: { visible: await redoBtn.isVisible(), enabled: await redoBtn.isEnabled() },
  186 |       save: { visible: await saveBtn.isVisible(), enabled: await saveBtn.isEnabled() },
  187 |       review: { visible: await reviewBtn.isVisible(), enabled: await reviewBtn.isEnabled() },
  188 |       solve: { visible: await solveBtn.isVisible(), enabled: await solveBtn.isEnabled() },
  189 |       designAi: { visible: await designAiBtn.isVisible(), enabled: await designAiBtn.isEnabled() },
  190 |     })
  191 | 
  192 |     // Test tool palette buttons
  193 |     const tools = ['select', 'pan', 'joint', 'member', 'measure', 'pin', 'roller', 'load', 'delete']
  194 |     const toolResults = {}
  195 |     for (const tool of tools) {
  196 |       const tile = page.locator(`.tool-tile[class*="tool-${tool}"], .tool-tile:has-text("${tool}"), button[title*="${tool}"]`).first()
  197 |       if (await tile.count() > 0) {
  198 |         await tile.click()
  199 |         const isActive = await tile.evaluate((el) => el.classList.contains('active'))
  200 |         toolResults[tool] = { exists: true, activates: isActive }
  201 |       } else {
  202 |         toolResults[tool] = { exists: false }
  203 |       }
```