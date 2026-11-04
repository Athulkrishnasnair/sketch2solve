import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '../../..')

const analysesApiFile = fs.readFileSync(path.join(rootDir, 'frontend/src/api/analyses.js'), 'utf8')
const resultsPanelFile = fs.readFileSync(path.join(rootDir, 'frontend/src/components/AnalysisResultsPanel.vue'), 'utf8')
const editorPageFile = fs.readFileSync(path.join(rootDir, 'frontend/src/pages/TrussEditorPage.vue'), 'utf8')

test('API Client: exportAnalysisUrl and downloadAnalysisExport are defined', () => {
  assert.match(analysesApiFile, /export function exportAnalysisUrl\(analysisId, format = 'json'\)/)
  assert.match(analysesApiFile, /export async function downloadAnalysisExport\(analysisId, format = 'json'\)/)
  assert.match(analysesApiFile, /apiUrl\(`\/api\/analyses\/\$\{encodeURIComponent\(analysisId\)\}\/export\//)
})

test('API Client: saveAnalysisDraft supports reopen parameter', () => {
  assert.match(analysesApiFile, /export function saveAnalysisDraft\(analysisId, draft, coordinatesConfirmed, reopen = false\)/)
  assert.match(analysesApiFile, /const query = reopen \? '\?reopen=true' : ''/)
})

test('Analysis Results Panel: provides Export button with PNG, JSON, and CSV downloads', () => {
  assert.match(resultsPanelFile, /btn-export/)
  assert.match(resultsPanelFile, /showExportMenu/)
  assert.match(resultsPanelFile, /handleExport\('png'\)/)
  assert.match(resultsPanelFile, /handleExport\('json'\)/)
  assert.match(resultsPanelFile, /handleExport\('csv'\)/)
  assert.match(resultsPanelFile, /PNG Diagram/)
  assert.match(resultsPanelFile, /JSON Model/)
  assert.match(resultsPanelFile, /CSV Results/)
})

test('Analysis Results Panel: indicates when results are stale or model is unsolved on CSV export', () => {
  assert.match(resultsPanelFile, /isStale \|\| !hasResults/)
  assert.match(resultsPanelFile, /tag-stale/)
  assert.match(resultsPanelFile, /tag-unsolved/)
  assert.match(resultsPanelFile, /Requires fresh solve/)
})

test('Truss Editor: passes analysis-id to AnalysisResultsPanel and supports draft reopening', () => {
  assert.match(editorPageFile, /:analysis-id="analysisId"/)
  assert.match(editorPageFile, /saveAnalysisDraft\(props\.analysisId, payload, true, true\)/)
})

