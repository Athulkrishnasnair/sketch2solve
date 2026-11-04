# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: final-polish.spec.js >> Sketch2Solve Final Polish and Verification >> 9. Revision conflict handling rejects stale proposals gracefully
- Location: tests/e2e/final-polish.spec.js:244:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.sidebar-design-pane').locator('.design-error-notice')
Expected: visible
Timeout: 8000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.sidebar-design-pane').locator('.design-error-notice') with timeout 8000ms
  - waiting for locator('.sidebar-design-pane').locator('.design-error-notice')

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
  - button "Back to analysis": Back
  - strong: Triangular Truss
  - text: "#61683DF9 draft"
  - button "Undo"
  - button "Redo" [disabled]
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
  - button "Design with AI"
  - toolbar "Canvas view controls":
    - button "Zoom in"
    - button "Zoom out"
    - button "Fit content to view"
    - separator
    - button "Toggle grid" [pressed]
    - button "Snap to grid" [pressed]
    - button "Toggle AI proposal layer" [pressed]
  - text: "X: 2.452 m · Y: 3.188 m"
  - img: "(0,0) M1 M2 M3 L1: -10 kN J1 J2 J3"
  - complementary:
    - tablist "Sidebar navigation":
      - tab "Tools"
      - tab "Design with AI" [selected]
    - text: "Rev 2 Selected:"
    - strong: J4
    - text: (node) Unsaved canvas edits included
    - radiogroup "Design Intent":
      - button "Auto"
      - button "Create"
      - button "Modify"
      - button "Explain"
    - textbox "Instruct modification for joint J4 (e.g. \"Move JJ4 upwards by 0.5m\", \"Add pin support\")...": Add a vertical strut
    - text: Enter ↵ to submit · Shift+Enter for newline
    - button "Generate"
    - button "Move J4 up by 0.5 m"
    - button "Add pin support at J4"
    - button "Add roller support at J4"
    - button "Apply 10 kN downward load at J4"
  - text: SOLVABLE Truss is statically determinate and in static equilibrium. 3 joints · 3 members · 2.45, 3.19
```

# Test source

```ts
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
  234 |     expect(afterJointCount).toBe(initialJointCount + 1)
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
> 279 |     await expect(errorNotice).toBeVisible()
      |                               ^ Error: expect(locator).toBeVisible() failed
  280 |     await expect(errorNotice).toContainText(/Revision conflict|stale|modified/i)
  281 |   })
  282 | })
  283 | 
```