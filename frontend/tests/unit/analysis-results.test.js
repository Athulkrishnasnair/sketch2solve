import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const resultsComponentFile = readFileSync(
  new URL('../../src/components/AnalysisResultsPanel.vue', import.meta.url),
  'utf8'
)
const editorFile = readFileSync(
  new URL('../../src/pages/TrussEditorPage.vue', import.meta.url),
  'utf8'
)
const cssFile = readFileSync(
  new URL('../../src/styles/truss-editor.css', import.meta.url),
  'utf8'
)

test('Analysis Results Panel: renders overall solver status, counts, equations, and matrix diagnostics', () => {
  // Status badge
  assert.match(resultsComponentFile, /badge-solved/)
  assert.match(resultsComponentFile, /badge-stale/)
  assert.match(resultsComponentFile, /SOLVED/)

  // Structural counts & equation counts
  assert.match(resultsComponentFile, /Joints \(N\)/)
  assert.match(resultsComponentFile, /Members \(M\)/)
  assert.match(resultsComponentFile, /Equilibrium Equations \(2N\)/)
  assert.match(resultsComponentFile, /Unknowns \(M \+ R\)/)

  // Matrix diagnostics: shape, rank, condition number
  assert.match(resultsComponentFile, /Matrix Shape/)
  assert.match(resultsComponentFile, /matrixShapeStr/)
  assert.match(resultsComponentFile, /Numerical Rank/)
  assert.match(resultsComponentFile, /numericalRank/)
  assert.match(resultsComponentFile, /Condition Number \(κ\)/)
  assert.match(resultsComponentFile, /conditionNumber/)
})

test('Analysis Results Panel: support reactions table with horizontal and vertical components', () => {
  assert.match(resultsComponentFile, /Support Reactions/)
  assert.match(resultsComponentFile, /Horizontal Reaction Fx/)
  assert.match(resultsComponentFile, /Vertical Reaction Fy/)
  assert.match(resultsComponentFile, /Resultant Magnitude R/)
  assert.match(resultsComponentFile, /reactionRows/)
  assert.match(resultsComponentFile, /r\.fxDisplay/)
  assert.match(resultsComponentFile, /r\.fyDisplay/)
  assert.match(resultsComponentFile, /r\.magnitudeDisplay/)
})

test('Analysis Results Panel: axial force for every member with tension and compression classifications', () => {
  assert.match(resultsComponentFile, /Member Forces/)
  assert.match(resultsComponentFile, /Axial Force/)
  assert.match(resultsComponentFile, /Classification/)
  assert.match(resultsComponentFile, /memberRows/)
  assert.match(resultsComponentFile, /row\.forceDisplay/)
  assert.match(resultsComponentFile, /pill-tension/)
  assert.match(resultsComponentFile, /pill-compression/)
  assert.match(resultsComponentFile, /pill-zero/)
  assert.match(resultsComponentFile, /Tension \(\+\)/)
  assert.match(resultsComponentFile, /Compression \(−\)/)
  assert.match(resultsComponentFile, /Zero-force \(0\)/)
})

test('Analysis Results Panel: equilibrium residual verification and engineering limitations disclaimer', () => {
  // Max residual & tolerance
  assert.match(resultsComponentFile, /Max Nodal Residual/)
  assert.match(resultsComponentFile, /maxResidual/)
  assert.match(resultsComponentFile, /Residual Tolerance/)
  assert.match(resultsComponentFile, /residualTolerance/)
  assert.match(resultsComponentFile, /Verified Closed/)

  // Caveats and limitations disclaimer
  assert.match(resultsComponentFile, /Engineering Solver Disclaimer/)
  assert.match(resultsComponentFile, /warningText/)
  assert.match(resultsComponentFile, /Key Engineering Assumptions/)
  assert.match(resultsComponentFile, /Planar Ideal Pin-Jointed System/)
  assert.match(resultsComponentFile, /Small Displacement Theory/)
  assert.match(resultsComponentFile, /Elastic & Buckling Limits Unchecked/)
})

test('Zero-load case: explains unloaded model without treating zero forces as a failure', () => {
  assert.match(resultsComponentFile, /isUnloaded/)
  assert.match(resultsComponentFile, /banner-unloaded/)
  assert.match(resultsComponentFile, /Model is unloaded \(Zero external forces applied\)/)
  assert.match(resultsComponentFile, /Static equilibrium is satisfied trivially/)
  assert.match(resultsComponentFile, /exact analytical result, not a solver failure/)
  assert.match(resultsComponentFile, /Apply a point load to any joint using the Load tool/)
})

test('Canvas visualization: member force labels, tension/compression styling, and legend', () => {
  // Member force label on truss
  assert.match(editorFile, /v-if="showForceLabels && !resultsStale && memberForceText\(member\.id\)"/)
  assert.match(editorFile, /member-force-label/)

  // Reaction vectors on canvas
  assert.match(editorFile, /truss-reactions-group/)
  assert.match(editorFile, /calculatedReactions/)
  assert.match(editorFile, /reaction-vector-line/)
  assert.match(editorFile, /reaction-arrowhead/)
  assert.match(editorFile, /reaction-vector-label/)

  // Forces color legend
  assert.match(editorFile, /canvas-forces-legend/)
  assert.match(editorFile, /swatch-tension/)
  assert.match(editorFile, /swatch-compression/)
  assert.match(editorFile, /swatch-zero/)
  assert.match(editorFile, /swatch-reaction/)

  // CSS definitions for reactions and legend
  assert.match(cssFile, /\.reaction-vector-line/)
  assert.match(cssFile, /\.reaction-arrowhead/)
  assert.match(cssFile, /\.canvas-forces-legend/)
  assert.match(cssFile, /\.swatch-tension/)
  assert.match(cssFile, /\.swatch-compression/)
})

test('Interaction and stale results protection: loading state, toast, and re-solve guard', () => {
  // Loading state on Solve button
  assert.match(editorFile, /btn-solve/)
  assert.match(editorFile, /solving \? 'Solving…' : 'Solve'/)

  // Reveal results panel on solve
  assert.match(editorFile, /persistedSolverData\.value = res/)
  assert.match(editorFile, /showResultsPanel\.value = true/)
  assert.match(editorFile, /Truss solved successfully — analysis results available/)

  // Stale detection when geometry modified
  assert.match(editorFile, /if \(persistedSolverData\.value\) {\s*resultsStale\.value = true/)
  assert.match(editorFile, /Results stale — geometry was edited after last solve/)

  // Stale banner and re-solve action in results panel
  assert.match(resultsComponentFile, /banner-stale/)
  assert.match(resultsComponentFile, /Geometry modified — results are stale/)
  assert.match(resultsComponentFile, /btn-re-solve/)
  assert.match(resultsComponentFile, /Re-solve Now/)
})

test('Member selection and inspection in sidebar inspector', () => {
  assert.match(editorFile, /handleSelectMemberFromResults/)
  assert.match(resultsComponentFile, /handleRowClick/)
  assert.match(editorFile, /member-analysis-group/)
  assert.match(editorFile, /member-stale-badge/)
})
