import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const component = readFileSync(new URL('../../src/components/GeometryReview.vue', import.meta.url), 'utf8')
const script = component.match(/<script setup>([\s\S]*?)<\/script>/)?.[1] || ''
const templateStart = component.indexOf('<template>') + '<template>'.length
const template = component.slice(templateStart, component.lastIndexOf('</template>'))

test('pending proposals can open the editor; entry is disabled only during draft loading', () => {
  const button = template.match(/<button\b[^>]*@click="beginEditing"[^>]*>[\s\S]*?<\/button>/)?.[0]
  assert.ok(button, 'the geometry editor entry control exists')
  assert.match(button, /:disabled="busy === 'load'"/)
  assert.doesNotMatch(button, /reviewed|pending_review|proposal_only/)
})

test('saving a draft does not review or solve it', () => {
  const saveHandler = script.match(/async function saveDraft\(\) \{([\s\S]*?)\n\}/)?.[1]
  assert.ok(saveHandler, 'the draft save handler exists')
  assert.match(saveHandler, /saveAnalysisDraft\(/)
  assert.doesNotMatch(saveHandler, /markAnalysisReviewed\(|solveReviewedAnalysis\(/)
  assert.match(saveHandler, /still unapproved/)
})

test('review and solver actions require their explicit prior workflow states', () => {
  assert.match(template, /v-if="savedGeometry && !reviewed && !submitted"[^>]*@click="markReviewed"/)
  assert.match(template, /v-if="reviewed && !submitted"[^>]*@click="solveReviewed"/)
  assert.match(script, /coordinatesConfirmed\.value/)
  assert.match(script, /saveAnalysisDraft\(props\.analysis\.analysis_id, payload, coordinatesConfirmed\.value\)/)
})
