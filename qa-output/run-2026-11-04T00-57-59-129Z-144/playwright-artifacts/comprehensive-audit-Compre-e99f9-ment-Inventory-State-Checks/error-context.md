# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: comprehensive-audit.spec.js >> Comprehensive Application Audit >> Audit 2: Complete Interactive Element Inventory & State Checks
- Location: tests/e2e/comprehensive-audit.spec.js:80:3

# Error details

```
TypeError: page.locator(...).toContainText is not a function
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
      - button "Analysis history 1" [ref=e36] [cursor=pointer]:
        - generic [ref=e42]: Analysis history
        - generic [ref=e43]: "1"
    - generic [ref=e49]:
      - strong [ref=e50]: Private by default
      - paragraph [ref=e51]: Runs stay in your local backend. Don’t expose this workspace publicly.
    - generic [ref=e52]: Backend API · localhost:5000
  - main [ref=e54]:
    - generic [ref=e55]:
      - status:
        - generic: Truss solved successfully — analysis results available.
      - generic [ref=e56]:
        - generic:
          - button "Back" [ref=e57] [cursor=pointer]
          - generic:
            - strong: Triangular Truss
            - generic:
              - text: "#1D99F5E2"
              - generic [ref=e61]: submitted
        - generic [ref=e62]:
          - button "Undo (Ctrl+Z)" [ref=e63] [cursor=pointer]
          - button "Redo (Ctrl+Y)" [disabled] [ref=e67]
          - generic [ref=e72]:
            - generic [ref=e73]: Length
            - combobox [ref=e74] [cursor=pointer]:
              - option "m" [selected]
              - option "mm"
              - option "ft"
            - generic [ref=e75]: Force
            - combobox [ref=e76] [cursor=pointer]:
              - option "kN" [selected]
              - option "N"
              - option "lbf"
          - generic [ref=e77] [cursor=pointer]:
            - checkbox "Coords Confirmed" [checked] [ref=e78]
            - generic [ref=e79]: Coords Confirmed
        - generic [ref=e80]:
          - button "Save *" [ref=e81] [cursor=pointer]
          - button "Mark Reviewed" [ref=e87] [cursor=pointer]
          - button "Solve" [disabled] [ref=e91]
          - button "Results *" [active] [ref=e95] [cursor=pointer]
          - button "Design with AI" [ref=e100] [cursor=pointer]
      - generic [ref=e105]:
        - generic [ref=e106]:
          - generic [ref=e107]:
            - button "Zoom In" [ref=e108] [cursor=pointer]
            - button "Zoom Out" [ref=e112] [cursor=pointer]
            - button "Fit Content" [ref=e116] [cursor=pointer]
            - button "Toggle Grid" [ref=e123] [cursor=pointer]
            - button "Snap to Grid" [ref=e126] [cursor=pointer]
            - button "AI Proposal Layer" [ref=e131] [cursor=pointer]
            - button "Toggle Analysis Results panel" [ref=e136] [cursor=pointer]
          - generic: "X: 0.000 m · Y: 0.000 m"
          - img [ref=e139]:
            - generic [ref=e141]: (0,0)
            - generic [ref=e144]:
              - generic [ref=e145]: M1
              - generic [ref=e147]:
                - generic [ref=e148] [cursor=pointer]
                - generic [ref=e149] [cursor=pointer]: M2
              - generic [ref=e150]:
                - generic [ref=e151] [cursor=pointer]
                - generic [ref=e152] [cursor=pointer]: M3
            - generic [ref=e160]: "L1: -10 kN"
            - generic [ref=e163]:
              - generic [ref=e164]:
                - generic [ref=e165] [cursor=pointer]
                - generic: J1
              - generic [ref=e166]:
                - generic [ref=e167] [cursor=pointer]
                - generic: J2
              - generic [ref=e168]:
                - generic [ref=e169] [cursor=pointer]
                - generic: J3
          - region "Analysis Results Panel" [ref=e170]:
            - generic [ref=e171]:
              - generic [ref=e172]:
                - generic [ref=e173]: RESULTS STALE
                - heading "Analysis Results" [level=3] [ref=e177]
                - generic [ref=e178]: m · kN
              - navigation [ref=e180]:
                - button "Summary & Matrix" [ref=e181] [cursor=pointer]
                - button "Member Forces (3)" [ref=e182] [cursor=pointer]
                - button "Support Reactions (2)" [ref=e183] [cursor=pointer]
                - button "Limitations" [ref=e184] [cursor=pointer]
              - generic [ref=e185]:
                - button "Labels On" [ref=e186] [cursor=pointer]
                - button "Expand panel height" [ref=e191] [cursor=pointer]
                - button "Close results panel" [ref=e197] [cursor=pointer]
            - generic [ref=e205]:
              - strong [ref=e206]: Geometry modified — results are stale.
              - text: The model was edited after the last solve. Re-run analysis to view updated member forces and reactions.
            - generic [ref=e209]:
              - generic [ref=e210]:
                - heading "Structural Counts" [level=4] [ref=e211]
                - generic [ref=e212]:
                  - generic [ref=e213]:
                    - generic [ref=e214]: Joints (N)
                    - generic [ref=e215]: "3"
                  - generic [ref=e216]:
                    - generic [ref=e217]: Members (M)
                    - generic [ref=e218]: "3"
                  - generic [ref=e219]:
                    - generic [ref=e220]: Equilibrium Equations (2N)
                    - generic [ref=e221]: "6"
                  - generic [ref=e222]:
                    - generic [ref=e223]: Unknowns (M + R)
                    - generic [ref=e224]: "6"
              - generic [ref=e225]:
                - heading "Equilibrium Matrix Diagnostics" [level=4] [ref=e226]
                - generic [ref=e227]:
                  - generic [ref=e228]:
                    - generic [ref=e229]: Matrix Shape
                    - generic [ref=e230]: 6 × 6
                  - generic [ref=e231]:
                    - generic [ref=e232]: Numerical Rank
                    - generic [ref=e233]: "6"
                  - generic [ref=e234]:
                    - generic [ref=e235]: Condition Number (κ)
                    - generic [ref=e236]: "4.07"
                  - generic [ref=e237]:
                    - generic [ref=e238]: Classification
                    - generic [ref=e239]: SQUARE_FULL_RANK
              - generic [ref=e240]:
                - heading "Equilibrium Verification" [level=4] [ref=e241]
                - generic [ref=e242]:
                  - generic [ref=e243]:
                    - generic [ref=e244]: Max Nodal Residual
                    - generic [ref=e245]: 0.00 kN
                  - generic [ref=e246]:
                    - generic [ref=e247]: Residual Tolerance
                    - generic [ref=e248]: 1.00e-9 kN
                  - generic [ref=e249]:
                    - generic [ref=e250]: Equilibrium Status
                    - generic [ref=e251]: Verified Closed
                  - generic [ref=e255]:
                    - generic [ref=e256]: External Loads
                    - generic [ref=e257]: 1 applied
        - complementary [ref=e258]:
          - generic [ref=e259]:
            - generic [ref=e260]:
              - generic [ref=e261]: Navigate
              - generic [ref=e262]:
                - button "Select" [ref=e263] [cursor=pointer]
                - button "Pan" [ref=e267] [cursor=pointer]
            - generic [ref=e273]:
              - generic [ref=e274]: Construction
              - generic [ref=e275]:
                - button "Joint" [ref=e276] [cursor=pointer]
                - button "Member" [ref=e279] [cursor=pointer]
                - button "Measure" [ref=e284] [cursor=pointer]
            - generic [ref=e291]:
              - generic [ref=e292]: Structural
              - generic [ref=e293]:
                - button "Pin" [ref=e294] [cursor=pointer]
                - button "Roller" [ref=e298] [cursor=pointer]
                - button "Load" [ref=e302] [cursor=pointer]
            - generic [ref=e305]:
              - generic [ref=e306]: Edit
              - button "Delete" [ref=e308] [cursor=pointer]
          - generic [ref=e313]:
            - generic [ref=e314]:
              - heading "Joint" [level=3] [ref=e315]
              - generic [ref=e316]: J1
            - generic [ref=e317]:
              - generic [ref=e318]:
                - generic [ref=e319]: Joint ID
                - textbox [ref=e320]: J1
              - generic [ref=e321]:
                - generic [ref=e322]:
                  - generic [ref=e323]: X (m)
                  - spinbutton [ref=e324]: "0.5"
                - generic [ref=e325]:
                  - generic [ref=e326]: Y (m)
                  - spinbutton [ref=e327]: "0"
              - generic [ref=e328]:
                - generic [ref=e329]: Support
                - combobox [ref=e330]:
                  - option "None (Free)"
                  - option "Pin (Fx & Fy)" [selected]
                  - option "Roller (Fy)"
              - generic [ref=e331]:
                - generic [ref=e332]: Point Load (kN)
                - generic [ref=e333]:
                  - spinbutton "Fx" [ref=e334]: "0"
                  - spinbutton "Fy" [ref=e335]: "0"
              - generic [ref=e336]:
                - generic [ref=e337]: Connected Members
                - generic [ref=e338]:
                  - 'button "M1: J1 → J2" [ref=e339] [cursor=pointer]'
                  - 'button "M3: J3 → J1" [ref=e343] [cursor=pointer]'
              - button "Delete Joint" [ref=e347] [cursor=pointer]
      - generic [ref=e351]:
        - generic [ref=e352]:
          - generic [ref=e353]: STALE — EDITING
          - generic [ref=e356]: Results stale — geometry was edited after last solve
          - generic "Unsaved changes" [ref=e357]
        - generic [ref=e358]: 3 joints · 3 members · 0.00, 0.00
```

# Test source

```ts
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
  267 |     // Select the select tool first
  268 |     await page.locator('.tool-tile[title*="Select"]').click()
  269 |     const firstJoint = page.locator('.truss-joints-group circle.truss-joint-node').first()
  270 |     await firstJoint.click()
  271 |     const inspector = page.locator('.editor-sidebar .inspector-section')
  272 |     await expect(inspector).toBeVisible()
  273 |     const xInput = inspector.locator('input[type="number"], input[inputmode="decimal"]').first()
  274 |     const curVal = await xInput.inputValue()
  275 |     await xInput.fill(String(Number(curVal) + 0.5))
  276 |     await xInput.dispatchEvent('change')
  277 | 
  278 |     // Reopen results panel to verify stale banner
  279 |     await page.locator('.editor-topbar .btn-results').click()
  280 |     await expect(resultsPanel).toBeVisible()
  281 | 
  282 |     // Verify stale banner and pill
  283 |     const isStale = await resultsPanel.locator('.banner-stale').isVisible()
> 284 |     const statusStale = await page.locator('.editor-statusbar').toContainText('Results stale').then(() => true).catch(() => false)
      |                                                                 ^ TypeError: page.locator(...).toContainText is not a function
  285 |     auditLog.push({
  286 |       page: 'TrussEditor',
  287 |       element: 'stale results detection',
  288 |       staleBannerVisible: isStale,
  289 |       statusBarShowsStale: statusStale,
  290 |     })
  291 | 
  292 |     console.log('--- INTERACTIVE ELEMENT AUDIT LOG ---')
  293 |     console.log(JSON.stringify(auditLog, null, 2))
  294 |     console.log('--- CONSOLE MESSAGES ---')
  295 |     console.log(JSON.stringify(consoleMessages, null, 2))
  296 |     console.log('--- FAILED REQUESTS ---')
  297 |     console.log(JSON.stringify(failedRequests, null, 2))
  298 |   })
  299 | 
  300 |   // 3. Audit Natural Language Design Studio Workflows
  301 |   test('Audit 3: Design Studio CREATE, MODIFY, EXPLAIN & Target Selection', async ({ page }) => {
  302 |     const studioAudit = {}
  303 | 
  304 |     await page.goto('/?view=design')
  305 |     await expect(page.locator('.design-studio-page')).toBeVisible()
  306 | 
  307 |     // 1. Selector for target analyses
  308 |     const select = page.locator('#analysis-select')
  309 |     await expect(select).toBeVisible()
  310 |     const optionsCount = await select.locator('option').count()
  311 |     studioAudit.targetSelector = { optionsCount }
  312 | 
  313 |     // 2. Intent Tabs
  314 |     const intentTabs = ['Auto', 'Create', 'Modify', 'Explain']
  315 |     for (const intent of intentTabs) {
  316 |       const btn = page.locator(`.intent-btn:has-text("${intent}")`)
  317 |       studioAudit[`intentTab_${intent}`] = await btn.count() > 0
  318 |     }
  319 | 
  320 |     // 3. Test CREATE Intent
  321 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  322 |     await textarea.fill('Create a Warren truss with 4 panels and 10 m span')
  323 |     await page.locator('.studio-left-pane .btn-submit').click()
  324 | 
  325 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  326 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  327 |     studioAudit.createProposal = {
  328 |       intent: await proposalCard.locator('.intent-pill').textContent(),
  329 |       valid: await proposalCard.locator('.validation-pill').textContent(),
  330 |       cadSvgRendered: await page.locator('.studio-right-pane .cad-svg').isVisible(),
  331 |     }
  332 | 
  333 |     // 4. Test Discard
  334 |     await proposalCard.locator('.btn-discard').click()
  335 |     studioAudit.proposalDiscarded = (await page.locator('.studio-left-pane .design-proposal-card').count()) === 0
  336 | 
  337 |     // 5. Test EXPLAIN Intent
  338 |     await page.locator('.intent-btn:has-text("Explain")').click()
  339 |     await textarea.fill('Explain how truss equilibrium works')
  340 |     await page.locator('.studio-left-pane .btn-submit').click()
  341 |     const explainCard = page.locator('.studio-left-pane .design-proposal-card')
  342 |     await expect(explainCard).toBeVisible({ timeout: 10_000 })
  343 |     studioAudit.explainProposal = {
  344 |       intent: await explainCard.locator('.intent-pill').textContent(),
  345 |       hasExplanation: (await explainCard.locator('.card-explanation').textContent())?.length > 10,
  346 |     }
  347 | 
  348 |     console.log('--- DESIGN STUDIO AUDIT ---')
  349 |     console.log(JSON.stringify(studioAudit, null, 2))
  350 |   })
  351 | })
  352 | 
  353 | 
```