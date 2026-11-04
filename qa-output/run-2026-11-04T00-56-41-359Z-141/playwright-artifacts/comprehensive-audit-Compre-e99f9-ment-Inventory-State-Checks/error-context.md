# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: comprehensive-audit.spec.js >> Comprehensive Application Audit >> Audit 2: Complete Interactive Element Inventory & State Checks
- Location: tests/e2e/comprehensive-audit.spec.js:80:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.editor-sidebar .sidebar-inspector')
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.editor-sidebar .sidebar-inspector') with timeout 8000ms
  - waiting for locator('.editor-sidebar .sidebar-inspector')

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
    - button "Analysis history 1"
  - strong: Private by default
  - paragraph: Runs stay in your local backend. Don’t expose this workspace publicly.
  - text: Backend API · localhost:5000
- main:
  - button "Back"
  - strong: Triangular Truss
  - text: "#EE3F389C submitted"
  - button "Undo (Ctrl+Z)"
  - button "Redo (Ctrl+Y)" [disabled]
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
  - button "Save *"
  - button "Mark Reviewed"
  - button "Solve" [disabled]
  - button "Results *"
  - button "Design with AI"
  - button "Zoom In"
  - button "Zoom Out"
  - button "Fit Content"
  - button "Toggle Grid"
  - button "Snap to Grid"
  - button "AI Proposal Layer"
  - button "Clear issue highlighting"
  - button "Toggle Analysis Results panel"
  - text: "X: 0.000 m · Y: 0.000 m"
  - img: "(0,0) M2 L1: -10 kN J2 J3"
  - region "Contextual Issue Resolution":
    - text: Under-constrained 1 / 2
    - button "Previous issue" [disabled]
    - button "Next issue"
    - button "Clear issue highlighting"
    - button "Minimize"
    - strong: INSUFFICIENT SUPPORTS
    - paragraph: The structure has 1 support constraint (at least 3 non-parallel constraints are required for stable planar equilibrium).
    - text: Joint J2 Support S2
    - button "Diagnostics info"
    - button "Fix with AI"
  - complementary:
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
    - strong: "2"
    - text: Members
    - strong: "1"
    - text: Supports
    - strong: "1"
    - text: Loads
    - strong: "1"
    - paragraph: Select a joint or member to inspect and edit its properties.
    - button "Clear All Model Elements"
  - text: STALE — EDITING Results stale — geometry was edited after last solve 2 joints · 1 members · 0.00, 0.00
  - button "Clear Highlight"
```

# Test source

```ts
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
  204 |     }
  205 |     auditLog.push({ page: 'TrussEditor', element: 'tool palette', tools: toolResults })
  206 | 
  207 |     // Test canvas controls
  208 |     const zoomInBtn = page.locator('.canvas-floating-toolbar button[title="Zoom In"]')
  209 |     const zoomOutBtn = page.locator('.canvas-floating-toolbar button[title="Zoom Out"]')
  210 |     const fitViewBtn = page.locator('.canvas-floating-toolbar button[title="Fit Content"]')
  211 |     const gridToggle = page.locator('.canvas-floating-toolbar button[title="Toggle Grid"]')
  212 |     const snapToggle = page.locator('.canvas-floating-toolbar button[title="Snap to Grid"]')
  213 |     const aiLayerToggle = page.locator('.canvas-floating-toolbar button[title="AI Proposal Layer"]')
  214 | 
  215 |     auditLog.push({
  216 |       page: 'TrussEditor',
  217 |       element: 'floating canvas toolbar',
  218 |       zoomIn: await zoomInBtn.isVisible(),
  219 |       zoomOut: await zoomOutBtn.isVisible(),
  220 |       fitView: await fitViewBtn.isVisible(),
  221 |       gridToggle: await gridToggle.isVisible(),
  222 |       snapToggle: await snapToggle.isVisible(),
  223 |       aiLayerToggle: await aiLayerToggle.isVisible(),
  224 |     })
  225 | 
  226 |     // Test solver submission on the created triangular truss
  227 |     // Verify review and solve workflow
  228 |     await reviewBtn.click()
  229 |     await expect(solveBtn).toBeEnabled({ timeout: 5_000 })
  230 |     await solveBtn.click()
  231 | 
  232 |     // Handle ConfirmDialog
  233 |     const confirmDialog = page.locator('.cdialog-panel')
  234 |     await expect(confirmDialog).toBeVisible()
  235 |     await confirmDialog.locator('.cdialog-confirm').click()
  236 | 
  237 |     // Results panel appears
  238 |     const resultsPanel = page.locator('.analysis-results-panel')
  239 |     await expect(resultsPanel).toBeVisible({ timeout: 10_000 })
  240 | 
  241 |     // Audit Results Panel Tabs
  242 |     const tabs = ['Summary & Matrix', 'Member Forces', 'Support Reactions', 'Limitations']
  243 |     const tabAudit = {}
  244 |     for (const tab of tabs) {
  245 |       const tabBtn = resultsPanel.getByRole('button', { name: new RegExp(tab, 'i') })
  246 |       const exists = await tabBtn.count() > 0
  247 |       if (exists) {
  248 |         await tabBtn.click()
  249 |         tabAudit[tab] = { clickable: true }
  250 |       } else {
  251 |         tabAudit[tab] = { clickable: false }
  252 |       }
  253 |     }
  254 |     auditLog.push({ page: 'ResultsPanel', element: 'tabs', tabs: tabAudit })
  255 | 
  256 |     // Test Stale Results Protection: Move a joint
  257 |     // Close results panel before interacting with canvas geometry
  258 |     const closeResultsBtn = resultsPanel.locator('.btn-panel-action[title*="Close"], button[aria-label="Close"]').first()
  259 |     if (await closeResultsBtn.count() > 0) {
  260 |       await closeResultsBtn.click()
  261 |     } else {
  262 |       await page.locator('.editor-topbar .btn-results').click()
  263 |     }
  264 |     await expect(resultsPanel).not.toBeVisible()
  265 | 
  266 |     // Drag or update via inspector
  267 |     const firstJoint = page.locator('.truss-joints-group circle.truss-joint-node').first()
  268 |     await firstJoint.click()
  269 |     const inspector = page.locator('.editor-sidebar .sidebar-inspector')
> 270 |     await expect(inspector).toBeVisible()
      |                             ^ Error: expect(locator).toBeVisible() failed
  271 |     const xInput = inspector.locator('input[type="number"], input[inputmode="decimal"]').first()
  272 |     const curVal = await xInput.inputValue()
  273 |     await xInput.fill(String(Number(curVal) + 0.5))
  274 |     await xInput.dispatchEvent('change')
  275 | 
  276 |     // Reopen results panel to verify stale banner
  277 |     await page.locator('.editor-topbar .btn-results').click()
  278 |     await expect(resultsPanel).toBeVisible()
  279 | 
  280 |     // Verify stale banner and pill
  281 |     const isStale = await resultsPanel.locator('.banner-stale').isVisible()
  282 |     const statusStale = await page.locator('.editor-statusbar').toContainText('Results stale').then(() => true).catch(() => false)
  283 |     auditLog.push({
  284 |       page: 'TrussEditor',
  285 |       element: 'stale results detection',
  286 |       staleBannerVisible: isStale,
  287 |       statusBarShowsStale: statusStale,
  288 |     })
  289 | 
  290 |     console.log('--- INTERACTIVE ELEMENT AUDIT LOG ---')
  291 |     console.log(JSON.stringify(auditLog, null, 2))
  292 |     console.log('--- CONSOLE MESSAGES ---')
  293 |     console.log(JSON.stringify(consoleMessages, null, 2))
  294 |     console.log('--- FAILED REQUESTS ---')
  295 |     console.log(JSON.stringify(failedRequests, null, 2))
  296 |   })
  297 | 
  298 |   // 3. Audit Natural Language Design Studio Workflows
  299 |   test('Audit 3: Design Studio CREATE, MODIFY, EXPLAIN & Target Selection', async ({ page }) => {
  300 |     const studioAudit = {}
  301 | 
  302 |     await page.goto('/?view=design')
  303 |     await expect(page.locator('.design-studio-page')).toBeVisible()
  304 | 
  305 |     // 1. Selector for target analyses
  306 |     const select = page.locator('#analysis-select')
  307 |     await expect(select).toBeVisible()
  308 |     const optionsCount = await select.locator('option').count()
  309 |     studioAudit.targetSelector = { optionsCount }
  310 | 
  311 |     // 2. Intent Tabs
  312 |     const intentTabs = ['Auto', 'Create', 'Modify', 'Explain']
  313 |     for (const intent of intentTabs) {
  314 |       const btn = page.locator(`.intent-btn:has-text("${intent}")`)
  315 |       studioAudit[`intentTab_${intent}`] = await btn.count() > 0
  316 |     }
  317 | 
  318 |     // 3. Test CREATE Intent
  319 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  320 |     await textarea.fill('Create a Warren truss with 4 panels and 10 m span')
  321 |     await page.locator('.studio-left-pane .btn-submit').click()
  322 | 
  323 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  324 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  325 |     studioAudit.createProposal = {
  326 |       intent: await proposalCard.locator('.intent-pill').textContent(),
  327 |       valid: await proposalCard.locator('.validation-pill').textContent(),
  328 |       cadSvgRendered: await page.locator('.studio-right-pane .cad-svg').isVisible(),
  329 |     }
  330 | 
  331 |     // 4. Test Discard
  332 |     await proposalCard.locator('.btn-discard').click()
  333 |     studioAudit.proposalDiscarded = (await page.locator('.studio-left-pane .design-proposal-card').count()) === 0
  334 | 
  335 |     // 5. Test EXPLAIN Intent
  336 |     await page.locator('.intent-btn:has-text("Explain")').click()
  337 |     await textarea.fill('Explain how truss equilibrium works')
  338 |     await page.locator('.studio-left-pane .btn-submit').click()
  339 |     const explainCard = page.locator('.studio-left-pane .design-proposal-card')
  340 |     await expect(explainCard).toBeVisible({ timeout: 10_000 })
  341 |     studioAudit.explainProposal = {
  342 |       intent: await explainCard.locator('.intent-pill').textContent(),
  343 |       hasExplanation: (await explainCard.locator('.card-explanation').textContent())?.length > 10,
  344 |     }
  345 | 
  346 |     console.log('--- DESIGN STUDIO AUDIT ---')
  347 |     console.log(JSON.stringify(studioAudit, null, 2))
  348 |   })
  349 | })
  350 | 
  351 | 
```