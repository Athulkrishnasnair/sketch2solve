import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const apiFile = readFileSync(
  new URL('../../src/api/analyses.js', import.meta.url),
  'utf8'
)
const appFile = readFileSync(
  new URL('../../src/App.vue', import.meta.url),
  'utf8'
)
const dashboardFile = readFileSync(
  new URL('../../src/pages/DashboardPage.vue', import.meta.url),
  'utf8'
)
const designStudioFile = readFileSync(
  new URL('../../src/pages/DesignStudioPage.vue', import.meta.url),
  'utf8'
)
const editorFile = readFileSync(
  new URL('../../src/pages/TrussEditorPage.vue', import.meta.url),
  'utf8'
)
const proposalCardFile = readFileSync(
  new URL('../../src/components/DesignProposalCard.vue', import.meta.url),
  'utf8'
)
const instructionPanelFile = readFileSync(
  new URL('../../src/components/DesignInstructionPanel.vue', import.meta.url),
  'utf8'
)
const cssFile = readFileSync(
  new URL('../../src/styles/truss-editor.css', import.meta.url),
  'utf8'
)

// --- 1. Shared API Client Tests ---
test('Shared API Client: exposes designTruss, applyDesignProposal, and rejectDesignProposal', () => {
  assert.match(apiFile, /export function designTruss\(\{ message, intent = 'auto', context = \{\}, provider = null \}\)/)
  assert.match(apiFile, /request\('\/api\/ai\/design',/)
  assert.match(apiFile, /export function applyDesignProposal\(\{ proposal_id, analysis_id = null, base_revision = null, proposed_model, create_record = false \}\)/)
  assert.match(apiFile, /request\('\/api\/ai\/design\/apply',/)
  assert.match(apiFile, /export function rejectDesignProposal\(\{ proposal_id, analysis_id = null, base_revision = null \}\)/)
  assert.match(apiFile, /request\('\/api\/ai\/design\/reject',/)
})

// --- 2. Entry Point A: Dashboard Create with AI ---
test('Dashboard: prominent "Create with AI" action and in-place natural language workspace', () => {
  assert.match(dashboardFile, /Create with AI/)
  assert.match(dashboardFile, /dashboard-ai-btn/)
  assert.match(dashboardFile, /dashboard-ai-workbench/)
  assert.match(dashboardFile, /createPrompt/)
  assert.match(dashboardFile, /examplePrompts/)
  assert.match(dashboardFile, /submitCreateAi/)
  assert.match(dashboardFile, /handleApplyCreatedProposal/)
  assert.match(dashboardFile, /DesignProposalCard/)
  // Verify example prompts cover triangular, warren, and roof trusses
  assert.match(dashboardFile, /triangular truss/)
  assert.match(dashboardFile, /Warren truss/)
})

// --- 3. Entry Point B: Sidebar & Dedicated Design Studio ---
test('Sidebar navigation: includes "Natural Language Design" entry in App.vue', () => {
  assert.match(appFile, /Natural Language Design/)
  assert.match(appFile, /view === 'design'/)
  assert.match(appFile, /DesignStudioPage/)
  assert.match(appFile, /navigate\('design'\)/)
})

test('Design Studio Workspace: split-pane layout with controls, CAD canvas, and analysis selector', () => {
  assert.match(designStudioFile, /DesignInstructionPanel/)
  assert.match(designStudioFile, /DesignProposalCard/)
  assert.match(designStudioFile, /selectedAnalysisId/)
  assert.match(designStudioFile, /studio-left-pane/)
  assert.match(designStudioFile, /studio-right-pane/)
  assert.match(designStudioFile, /cad-svg/)
  assert.match(designStudioFile, /proposed-addition/)
  assert.match(designStudioFile, /proposed-removal/)
})

// --- 4. Entry Point C: Truss Editor Contextual Design Assistant ---
test('Truss Editor: accessible "Design with AI" toolbar action and contextual assistant panel', () => {
  assert.match(editorFile, /Design with AI/)
  assert.match(editorFile, /showDesignAssistant/)
  assert.match(editorFile, /editor-design-assistant-card/)
  assert.match(editorFile, /DesignInstructionPanel/)
})

test('Truss Editor Context: sends actual canvas snapshot, revision, selected elements, diagnostics, and solver results', () => {
  assert.match(editorFile, /const currentSnapshot = JSON\.parse\(JSON\.stringify\(geometry\.value\)\)/)
  assert.match(editorFile, /model_revision: designModelRevision\.value/)
  assert.match(editorFile, /selected_element: selectedElement\.value/)
  assert.match(editorFile, /diagnostics: previewResult\.value\?\.solvability/)
  assert.match(editorFile, /solver_results:/)
  assert.match(editorFile, /!resultsStale\.value && hasSolvedResults\.value/)
})

// --- 5. On-Canvas Visual Highlighting ---
test('Canvas Overlay: renders added members dashed cyan (#0284c7) and deleted members dashed red (#ef4444)', () => {
  assert.match(editorFile, /design-preview-member-added/)
  assert.match(editorFile, /design-preview-member-deleted/)
  assert.match(editorFile, /design-preview-joint/)
  assert.match(cssFile, /\.design-preview-member-added\s*\{[^}]*#0284c7/)
  assert.match(cssFile, /\.design-preview-member-added\s*\{[^}]*stroke-dasharray:\s*6\s*4/)
  assert.match(cssFile, /\.design-preview-member-deleted\s*\{[^}]*#ef4444/)
  assert.match(cssFile, /\.design-preview-joint\.added\s*\{[^}]*#0284c7/)
  assert.match(cssFile, /\.design-preview-joint\.modified\s*\{[^}]*#f59e0b/)
})

// --- 6. Approval Workflow & Safety Gating ---
test('Approval Workflow: proposals require explicit user action to apply or reject', () => {
  // Model is not optimistically mutated on submit
  assert.doesNotMatch(editorFile, /geometry\.value = res\.proposed_model/)
  // Apply calls API and pushes history
  assert.match(editorFile, /applyDesignProposal\(/)
  assert.match(editorFile, /pushHistory\(\)/)
  assert.match(editorFile, /designModelRevision\.value = res\.model_revision/)
  // Invalidation of previous solver results
  assert.match(editorFile, /resultsStale\.value = true/)
  // Reject calls API without mutating model
  assert.match(editorFile, /rejectDesignProposal\(/)
})

test('Revision Conflict Handling: handles HTTP 409 stale revision gracefully', () => {
  assert.match(editorFile, /err\.status === 409/)
  assert.match(editorFile, /Revision conflict/)
  assert.match(designStudioFile, /err\.status === 409/)
  assert.match(designStudioFile, /Revision conflict/)
})

// --- 7. Engineering Response Design ---
test('Engineering Response Design: structured engineering cards with operations, stats, and mini preview', () => {
  assert.match(proposalCardFile, /intent-pill/)
  assert.match(proposalCardFile, /operations-section/)
  assert.match(proposalCardFile, /metrics-grid/)
  assert.match(proposalCardFile, /mini-preview-svg/)
  assert.match(proposalCardFile, /diagnostics-bar/)
  assert.match(proposalCardFile, /btn-apply/)
  assert.match(proposalCardFile, /btn-discard/)
  // Avoids generic chatbot avatar or bubbles
  assert.doesNotMatch(proposalCardFile, /chat-bubble/)
  assert.doesNotMatch(proposalCardFile, /avatar-robot/)
})

test('Keyboard & Interaction Isolation: Enter submits, Shift+Enter newlines, and wheel/clicks isolated from canvas', () => {
  assert.match(instructionPanelFile, /handleKeydown/)
  assert.match(instructionPanelFile, /e\.key === 'Enter' && !e\.shiftKey/)
  assert.match(editorFile, /@wheel\.stop/)
  assert.match(editorFile, /@pointerdown\.stop/)
})
