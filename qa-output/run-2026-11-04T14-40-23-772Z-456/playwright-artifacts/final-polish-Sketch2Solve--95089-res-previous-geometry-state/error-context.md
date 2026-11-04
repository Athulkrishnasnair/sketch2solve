# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 8. Model mutation and Undo support restores previous geometry state
- Location: tests/e2e/final-polish.spec.js:212:3

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 1
Received: 4
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
        - generic [ref=e57]:
          - button "Back to analysis" [ref=e58] [cursor=pointer]: Back
          - generic:
            - strong: Triangular Truss
            - generic:
              - text: "#B71AB3FC"
              - generic [ref=e62]: draft
        - generic [ref=e63]:
          - button "Undo" [ref=e64] [cursor=pointer]
          - button "Redo" [disabled] [ref=e68]
          - generic [ref=e73]:
            - generic [ref=e74]: Length
            - combobox [ref=e75] [cursor=pointer]:
              - option "m" [selected]
              - option "mm"
              - option "ft"
            - generic [ref=e76]: Force
            - combobox [ref=e77] [cursor=pointer]:
              - option "kN" [selected]
              - option "N"
              - option "lbf"
          - generic [ref=e78] [cursor=pointer]:
            - checkbox "Coords Confirmed" [checked] [ref=e79]
            - generic [ref=e80]: Coords Confirmed
        - generic [ref=e81]:
          - button "Save *" [ref=e82] [cursor=pointer]
          - button "Mark Reviewed" [ref=e88] [cursor=pointer]
          - button "Solve" [disabled] [ref=e92]
          - button "Design with AI" [ref=e97] [cursor=pointer]
      - generic [ref=e102]:
        - generic [ref=e104]:
          - toolbar "Canvas view controls" [ref=e105]:
            - button "Zoom in" [ref=e106] [cursor=pointer]
            - button "Zoom out" [ref=e110] [cursor=pointer]
            - button "Fit content to view" [ref=e114] [cursor=pointer]
            - separator [ref=e120]
            - button "Toggle grid" [pressed] [ref=e121] [cursor=pointer]
            - button "Snap to grid" [pressed] [ref=e124] [cursor=pointer]
            - button "Toggle AI proposal layer" [pressed] [ref=e129] [cursor=pointer]
          - generic: "X: 1.447 m · Y: 2.686 m"
          - img [ref=e133]:
            - generic [ref=e135]: (0,0)
            - generic [ref=e138]:
              - generic [ref=e139]: M1
              - generic [ref=e141]:
                - generic [ref=e142] [cursor=pointer]
                - generic [ref=e143] [cursor=pointer]: M2
              - generic [ref=e144]:
                - generic [ref=e145] [cursor=pointer]
                - generic [ref=e146] [cursor=pointer]: M3
            - generic [ref=e154]: "L1: -10 kN"
            - generic [ref=e157]:
              - generic [ref=e158]:
                - generic [ref=e159] [cursor=pointer]
                - generic: J1
              - generic [ref=e160]:
                - generic [ref=e161] [cursor=pointer]
                - generic: J2
              - generic [ref=e162]:
                - generic [ref=e163] [cursor=pointer]
                - generic: J3
              - generic [ref=e164]:
                - generic [ref=e165] [cursor=pointer]
                - generic: J4
        - complementary [ref=e166]:
          - tablist "Sidebar navigation" [ref=e167]:
            - tab "Tools" [selected] [ref=e168] [cursor=pointer]
            - tab "Design with AI" [ref=e171] [cursor=pointer]
          - generic [ref=e176]:
            - generic [ref=e177]:
              - generic [ref=e178]:
                - generic [ref=e179]: Navigate
                - generic [ref=e180]:
                  - button "Select" [ref=e181] [cursor=pointer]
                  - button "Pan" [ref=e185] [cursor=pointer]
              - generic [ref=e191]:
                - generic [ref=e192]: Construction
                - generic [ref=e193]:
                  - button "Joint" [ref=e194] [cursor=pointer]
                  - button "Member" [ref=e197] [cursor=pointer]
                  - button "Measure" [ref=e202] [cursor=pointer]
              - generic [ref=e209]:
                - generic [ref=e210]: Structural
                - generic [ref=e211]:
                  - button "Pin" [ref=e212] [cursor=pointer]
                  - button "Roller" [ref=e216] [cursor=pointer]
                  - button "Load" [ref=e220] [cursor=pointer]
              - generic [ref=e223]:
                - generic [ref=e224]: Edit
                - button "Delete" [ref=e226] [cursor=pointer]
            - generic [ref=e231]:
              - generic [ref=e232]:
                - heading "Joint" [level=3] [ref=e233]
                - generic [ref=e234]: J4
              - generic [ref=e235]:
                - generic [ref=e236]:
                  - generic [ref=e237]: Joint ID
                  - textbox [ref=e238]: J4
                - generic [ref=e239]:
                  - generic [ref=e240]:
                    - generic [ref=e241]: X (m)
                    - spinbutton [ref=e242]: "1.5"
                  - generic [ref=e243]:
                    - generic [ref=e244]: Y (m)
                    - spinbutton [ref=e245]: "2.5"
                - generic [ref=e246]:
                  - generic [ref=e247]: Support
                  - combobox [ref=e248]:
                    - option "None (Free)" [selected]
                    - option "Pin (Fx & Fy)"
                    - option "Roller (Fy)"
                - generic [ref=e249]:
                  - generic [ref=e250]: Point Load (kN)
                  - generic [ref=e251]:
                    - spinbutton "Fx" [ref=e252]: "0"
                    - spinbutton "Fy" [ref=e253]: "0"
                - generic [ref=e254]:
                  - generic [ref=e255]: Connected Members
                  - generic [ref=e256]: No members attached
                - button "Delete Joint" [ref=e257] [cursor=pointer]
      - generic [ref=e261]:
        - generic [ref=e262]:
          - generic [ref=e263]: SOLVABLE
          - generic [ref=e267]: Truss is statically determinate and in static equilibrium.
          - generic "Unsaved changes" [ref=e268]
        - generic [ref=e269]: 4 joints · 3 members · 1.45, 2.69
```

# Test source

```ts
  134 |     await designTab.click()
  135 |     await expect(designTab).toHaveClass(/active/)
  136 |     await expect(page.locator('.sidebar-design-pane')).toBeVisible()
  137 |     await expect(page.locator('.sidebar-tools-pane')).not.toBeVisible()
  138 | 
  139 |     // Topbar btn-ai switches back to Tools tab or toggles
  140 |     const topbarAiBtn = page.locator('.editor-topbar .btn-ai')
  141 |     await expect(topbarAiBtn).toHaveClass(/active/)
  142 |     await topbarAiBtn.click()
  143 |     await expect(toolsTab).toHaveClass(/active/)
  144 |     await expect(page.locator('.sidebar-tools-pane')).toBeVisible()
  145 |   })
  146 | 
  147 |   test('6. Construction and Structural tools use 3-column grid with uniform 48px tile height', async ({ page }) => {
  148 |     await page.goto('/?view=design')
  149 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  150 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  151 |     await page.locator('.studio-left-pane .btn-submit').click()
  152 | 
  153 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  154 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  155 |     await proposalCard.locator('.btn-apply').click()
  156 | 
  157 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  158 | 
  159 |     // Verify 3-column grid for Construction
  160 |     const constructionGrid = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tools-grid-3')
  161 |     await expect(constructionGrid).toBeVisible()
  162 |     await expect(constructionGrid.locator('.tool-tile')).toHaveCount(3)
  163 | 
  164 |     // Verify 3-column grid for Structural
  165 |     const structuralGrid = page.locator('.toolbox-group').filter({ hasText: 'Structural' }).locator('.tools-grid-3')
  166 |     await expect(structuralGrid).toBeVisible()
  167 |     await expect(structuralGrid.locator('.tool-tile')).toHaveCount(3)
  168 | 
  169 |     // Verify 1-column grid for Edit
  170 |     const editGrid = page.locator('.toolbox-group').filter({ hasText: 'Edit' }).locator('.tools-grid-1')
  171 |     await expect(editGrid).toBeVisible()
  172 |     await expect(editGrid.locator('.tool-tile')).toHaveCount(1)
  173 | 
  174 |     // Check height of tiles
  175 |     const tile = constructionGrid.locator('.tool-tile').first()
  176 |     const box = await tile.boundingBox()
  177 |     expect(box?.height).toBeGreaterThanOrEqual(47)
  178 |   })
  179 | 
  180 |   test('7. Sequential AI proposal generation, application, and model mutation', async ({ page }) => {
  181 |     await page.goto('/?view=design')
  182 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  183 |     await textarea.fill('Create a triangular truss with a 6 m span and 3 m height with a pin at left, roller at right, and 10 kN downward load at top')
  184 |     await page.locator('.studio-left-pane .btn-submit').click()
  185 | 
  186 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  187 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  188 |     await proposalCard.locator('.btn-apply').click()
  189 | 
  190 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  191 | 
  192 |     // Switch to Design with AI tab in the editor
  193 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  194 |     const sidebarDesignPane = page.locator('.sidebar-design-pane')
  195 |     await expect(sidebarDesignPane).toBeVisible()
  196 | 
  197 |     // Formulate sequential modification
  198 |     const promptInput = sidebarDesignPane.locator('textarea')
  199 |     await promptInput.fill('Add a vertical strut from the apex to the bottom chord')
  200 |     await sidebarDesignPane.locator('.btn-submit').click()
  201 | 
  202 |     const modProposal = sidebarDesignPane.locator('.design-proposal-card')
  203 |     await expect(modProposal).toBeVisible({ timeout: 10_000 })
  204 | 
  205 |     // Apply the proposal
  206 |     await modProposal.locator('.btn-apply').click()
  207 | 
  208 |     // Verify toast notification and success
  209 |     await expect(page.locator('.editor-toast')).toBeVisible()
  210 |   })
  211 | 
  212 |   test('8. Model mutation and Undo support restores previous geometry state', async ({ page }) => {
  213 |     await page.goto('/?view=design')
  214 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  215 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  216 |     await page.locator('.studio-left-pane .btn-submit').click()
  217 | 
  218 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  219 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  220 |     await proposalCard.locator('.btn-apply').click()
  221 | 
  222 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  223 | 
  224 |     const initialJointCount = await page.locator('.truss-joint-node').count()
  225 | 
  226 |     // Add a joint using the joint tool
  227 |     const jointTool = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tool-tile').filter({ hasText: 'Joint' })
  228 |     await jointTool.click()
  229 | 
  230 |     const canvas = page.locator('.engineering-svg')
  231 |     await canvas.click({ position: { x: 200, y: 200 } })
  232 | 
  233 |     const afterJointCount = await page.locator('.truss-joint-node').count()
> 234 |     expect(afterJointCount).toBe(initialJointCount + 1)
      |                             ^ Error: expect(received).toBe(expected) // Object.is equality
  235 | 
  236 |     // Click Undo
  237 |     const undoBtn = page.locator('.editor-topbar button[aria-label="Undo"]')
  238 |     await undoBtn.click()
  239 | 
  240 |     const revertedJointCount = await page.locator('.truss-joint-node').count()
  241 |     expect(revertedJointCount).toBe(initialJointCount)
  242 |   })
  243 | 
  244 |   test('9. Revision conflict handling rejects stale proposals gracefully', async ({ page }) => {
  245 |     await page.goto('/?view=design')
  246 |     const textarea = page.locator('.studio-left-pane .design-textarea')
  247 |     await textarea.fill('Create a triangular truss with 6 m span and 3 m height')
  248 |     await page.locator('.studio-left-pane .btn-submit').click()
  249 | 
  250 |     const proposalCard = page.locator('.studio-left-pane .design-proposal-card')
  251 |     await expect(proposalCard).toBeVisible({ timeout: 10_000 })
  252 |     await proposalCard.locator('.btn-apply').click()
  253 | 
  254 |     await expect(page.locator('.truss-editor-workspace')).toBeVisible({ timeout: 10_000 })
  255 | 
  256 |     // Switch to Design with AI tab
  257 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  258 |     const sidebarDesignPane = page.locator('.sidebar-design-pane')
  259 | 
  260 |     const promptInput = sidebarDesignPane.locator('textarea')
  261 |     await promptInput.fill('Add a vertical strut')
  262 |     await sidebarDesignPane.locator('.btn-submit').click()
  263 | 
  264 |     const modProposal = sidebarDesignPane.locator('.design-proposal-card')
  265 |     await expect(modProposal).toBeVisible({ timeout: 10_000 })
  266 | 
  267 |     // Now modify the canvas geometry behind the proposal's back (e.g. switch to Tools and add a joint)
  268 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Tools' }).click()
  269 |     const jointTool = page.locator('.toolbox-group').filter({ hasText: 'Construction' }).locator('.tool-tile').filter({ hasText: 'Joint' })
  270 |     await jointTool.click()
  271 |     await page.locator('.engineering-svg').click({ position: { x: 300, y: 150 } })
  272 | 
  273 |     // Switch back to Design with AI tab and attempt to apply the stale proposal
  274 |     await page.locator('.sidebar-tab-btn').filter({ hasText: 'Design with AI' }).click()
  275 |     await modProposal.locator('.btn-apply').click()
  276 | 
  277 |     // Verify conflict error message is displayed
  278 |     const errorNotice = sidebarDesignPane.locator('.design-error-notice')
  279 |     await expect(errorNotice).toBeVisible()
  280 |     await expect(errorNotice).toContainText(/Revision conflict|stale|modified/i)
  281 |   })
  282 | })
  283 | 
```