import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const editorFile = readFileSync(new URL('../../src/pages/TrussEditorPage.vue', import.meta.url), 'utf8')
const appFile = readFileSync(new URL('../../src/App.vue', import.meta.url), 'utf8')
const detailFile = readFileSync(new URL('../../src/pages/AnalysisDetailPage.vue', import.meta.url), 'utf8')

test('dedicated editor route and view are configured in App.vue', () => {
  assert.match(appFile, /import TrussEditorPage from '\.\/pages\/TrussEditorPage\.vue'/)
  assert.match(appFile, /TrussEditorPage v-else-if="view === 'editor'"/)
  assert.match(appFile, /function openEditor\(id\)/)
  assert.match(appFile, /view\.value = 'editor'/)
  assert.match(appFile, /url\.searchParams\.set\('view', 'editor'\)/)
})

test('analysis detail page provides a prominent edit geometry button', () => {
  assert.match(detailFile, /emit\('editor', analysis\.analysis_id\)/)
  assert.match(detailFile, /Edit geometry/)
})

test('truss editor defines complete toolset with icons and keyboard handling', () => {
  const tools = ['select', 'pan', 'joint', 'member', 'pin', 'roller', 'load', 'measure']
  for (const tool of tools) {
    assert.ok(editorFile.includes(`activeTool = '${tool}'`), `Tool '${tool}' is defined in editor`)
  }
  assert.match(editorFile, /showGrid/)
  assert.match(editorFile, /snapToGrid/)
  assert.match(editorFile, /snapInterval/)
  assert.match(editorFile, /function toScreen\(wx, wy\)/)
  assert.match(editorFile, /function toWorld\(sx, sy\)/)
  assert.match(editorFile, /pan\.value\.y - wy \* scale\.value/, 'World Y points upward on canvas')
})

test('live preview recalculation engine is debounced and protects against stale responses', () => {
  assert.match(editorFile, /previewAnalysisGeometry\(/)
  assert.match(editorFile, /previewDebounceTimer = setTimeout\(runPreview, 250\)/)
  assert.match(editorFile, /const seq = \+\+previewSeq/)
  assert.match(editorFile, /if \(seq === previewSeq\) \{[\s\S]*?previewResult\.value = result/)
})

test('undo and redo history is maintained for geometry edits', () => {
  assert.match(editorFile, /function pushHistory\(\)/)
  assert.match(editorFile, /function undo\(\)/)
  assert.match(editorFile, /function redo\(\)/)
  assert.match(editorFile, /historyStack\.value/)
})

test('safety gating: draft save requires coordinate confirmation; solve requires reviewed state', () => {
  assert.match(editorFile, /if \(!coordinatesConfirmed\.value\)/)
  assert.match(editorFile, /saveAnalysisDraft\(props\.analysisId, payload, true\)/)
  assert.match(editorFile, /if \(reviewStatus\.value !== 'reviewed'\)/)
  assert.match(editorFile, /solveReviewedAnalysis\(props\.analysisId\)/)
})

test('AI assistant panel is on-demand and requires explicit user action to apply suggestions', () => {
  assert.match(editorFile, /showAiAssistant/)
  assert.match(editorFile, /function openAiAssistant\(\)/)
  assert.match(editorFile, /function applySuggestion\(sugg\)/)
  assert.match(editorFile, /sugg\.action\(\)/)
})

