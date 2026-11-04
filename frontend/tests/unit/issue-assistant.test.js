import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const assistantComponentFile = readFileSync(
  new URL('../../src/components/IssueResolutionAssistant.vue', import.meta.url),
  'utf8'
)
const editorFile = readFileSync(
  new URL('../../src/pages/TrussEditorPage.vue', import.meta.url),
  'utf8'
)
const apiFile = readFileSync(
  new URL('../../src/api/analyses.js', import.meta.url),
  'utf8'
)
const cssFile = readFileSync(
  new URL('../../src/styles/truss-editor.css', import.meta.url),
  'utf8'
)

test('API contract: resolveGeometryIssue calls /api/ai/assistant with geometry, issue, and diagnostics', () => {
  assert.match(apiFile, /export function resolveGeometryIssue\(geometry, issue, diagnostics = null\)/)
  assert.match(apiFile, /request\('\/api\/ai\/assistant',/)
  assert.match(apiFile, /method: 'POST'/)
  assert.match(apiFile, /geometry,\s*issue,\s*diagnostics/)
})

test('Contextual issue action card UI adheres to design tokens and specifications', () => {
  // Check sparkle icon & 'Fix with AI' button
  assert.match(assistantComponentFile, /Sparkles/)
  assert.match(assistantComponentFile, /Fix with AI/)

  // Check classification badge and affected element tags
  assert.match(assistantComponentFile, /classification-pill/)
  assert.match(assistantComponentFile, /elem-pill/)
  assert.match(assistantComponentFile, /affected-pills-row/)

  // Check navigation controls for multiple issues
  assert.match(assistantComponentFile, /prevIssue/)
  assert.match(assistantComponentFile, /nextIssue/)
  assert.match(assistantComponentFile, /totalIssues/)

  // Check uncertainty explanation for component-level diagnostics
  assert.match(assistantComponentFile, /uncertainty-callout/)
  assert.match(assistantComponentFile, /localization_precision === 'component_level'/)

  // Check clear highlight & minimize controls
  assert.match(assistantComponentFile, /btn-clear-highlight/)
  assert.match(assistantComponentFile, /assistant-minimized-pill/)
  assert.match(assistantComponentFile, /toggleDismiss/)
})

test('AI resolution workflow displays root cause explanation, rationale, and structured proposed fixes', () => {
  assert.match(assistantComponentFile, /resolution\.root_cause_explanation/)
  assert.match(assistantComponentFile, /resolution\.engineering_rationale/)
  assert.match(assistantComponentFile, /resolution\.proposed_fixes/)
  assert.match(assistantComponentFile, /fix\.affected_elements/)
  assert.match(assistantComponentFile, /handleApplyFix/)
  assert.match(assistantComponentFile, /handleCancelFix/)
  assert.match(assistantComponentFile, /Apply Suggested Fix/)
  assert.match(assistantComponentFile, /Cancel/)
})

test('Safety gating: model is not modified on cancel, and suggestions require explicit Apply click', () => {
  // Cancel clears resolution without applying
  assert.match(assistantComponentFile, /function handleCancelFix\(\) \{[\s\S]*?resolution\.value = null/)
  // Only handleApplyFix emits apply-fix
  assert.match(assistantComponentFile, /emit\('apply-fix', fix\)/)
})

test('Editor integration: TrussEditorPage compiles activeIssues with precise classifications', () => {
  assert.match(editorFile, /import IssueResolutionAssistant from '\.\.\/components\/IssueResolutionAssistant\.vue'/)
  assert.match(editorFile, /const activeIssues = computed\(\(\) => \{/)
  assert.match(editorFile, /validationErrors\.value/)
  assert.match(editorFile, /validationWarnings\.value/)
  assert.match(editorFile, /solvability\.value/)
  assert.match(editorFile, /INSUFFICIENT_SUPPORTS/)
  assert.match(editorFile, /UNDERDETERMINED/)
  // Differentiates strength from stability (HIGH_AXIAL_FORCE)
  assert.match(editorFile, /HIGH_AXIAL_FORCE/)
})

test('Editor integration: autofocuses canvas on selected issue and positions card near affected geometry', () => {
  assert.match(editorFile, /function focusOnIssue\(issue\)/)
  assert.match(editorFile, /const contextualCardPosition = computed\(\(\) => \{/)
  assert.match(editorFile, /toScreen\(wx, wy\)/)
})

test('Editor integration: on-canvas issue highlighting, muting, and visual preview layer', () => {
  // SVG highlighting for error, mechanism, warning, and muting
  assert.match(editorFile, /issue-highlight-error/)
  assert.match(editorFile, /issue-highlight-mechanism/)
  assert.match(editorFile, /is-muted/)
  assert.match(editorFile, /joint-issue-pulse-ring/)

  // AI Proposed modifications in separate distinct preview styling
  assert.match(editorFile, /ai-proposed-member-line/)
  assert.match(editorFile, /ai-proposed-support-ring/)

  // Clear highlight toggle
  assert.match(editorFile, /toggleHighlightMode/)
  assert.match(editorFile, /handleClearHighlight/)
})

test('CSS styling defines distinct colors: red for error, amber for warning/mechanism, blue for AI modifications', () => {
  assert.match(cssFile, /\.truss-member-line\.issue-highlight-error\s*\{[^}]*stroke:\s*#dc2626/)
  assert.match(cssFile, /\.truss-member-line\.issue-highlight-mechanism\s*\{[^}]*stroke:\s*#d97706/)
  assert.match(cssFile, /\.ai-proposed-member-line\s*\{[^}]*stroke:\s*#0284c7/)
  assert.match(cssFile, /\.truss-member-line\.is-muted/)
  assert.match(cssFile, /@keyframes issue-error-pulse/)
  assert.match(cssFile, /@keyframes joint-ring-pulse-red/)
})

test('Scrolling and interaction isolation: independent scroll container, sticky action footer, and event propagation stopping', () => {
  // Independent scroll container and sticky footer in template
  assert.match(assistantComponentFile, /card-content-scroll/)
  assert.match(assistantComponentFile, /card-footer/)
  assert.match(assistantComponentFile, /scrollContainer/)

  // Wheel and pointer isolation
  assert.match(assistantComponentFile, /handleCardWheel/)
  assert.match(assistantComponentFile, /@wheel\.stop="handleCardWheel"/)
  assert.match(assistantComponentFile, /@pointerdown\.stop/)

  // Defensive isolation in TrussEditorPage canvas handlers
  assert.match(editorFile, /if \(e\.target[\s\S]*?closest\('\.contextual-action-card/)

  // Viewport-aware max-height and overscroll containment
  assert.match(assistantComponentFile, /overscroll-behavior:\s*contain/)
  assert.match(assistantComponentFile, /max-height:\s*min\(480px/)
})
