<script setup>
import { computed, ref, watch } from 'vue'
import { getAnalysisDraft, markAnalysisReviewed, saveAnalysisDraft, solveReviewedAnalysis } from '../api/analyses'

const props = defineProps({ analysis: { type: Object, required: true }, selectedElementId: { type: String, default: '' } })
const emit = defineEmits(['updated', 'select-element', 'editor'])
const editing = ref(false)
const geometry = ref(null)
const loadedGeometry = ref(null)
const coordinatesConfirmed = ref(false)
const busy = ref('')
const message = ref('')
const requestError = ref(null)

const proposal = computed(() => props.analysis.interpretation_proposal || null)
const savedGeometry = computed(() => props.analysis.human_review?.geometry || null)
const validationIssues = computed(() => requestError.value?.validation_issues || props.analysis.validation?.issues || [])
const activeNodes = computed(() => savedGeometry.value?.model?.nodes || geometry.value?.model?.nodes || [])
const bounds = computed(() => {
  const points = activeNodes.value.filter((node) => Number.isFinite(Number(node.x)) && Number.isFinite(Number(node.y)))
  if (!points.length) return '0 0 1 1'
  const xs = points.map((point) => Number(point.x))
  const ys = points.map((point) => Number(point.y))
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const span = Math.max(maxX - minX, maxY - minY, 1)
  const pad = span * 0.12
  return `${minX - pad} ${minY - pad} ${(maxX - minX) + pad * 2} ${(maxY - minY) + pad * 2}`
})
const nodeRadius = computed(() => {
  const points = activeNodes.value.filter((node) => Number.isFinite(Number(node.x)) && Number.isFinite(Number(node.y)))
  if (!points.length) return 0.02
  const xs = points.map((point) => Number(point.x))
  const ys = points.map((point) => Number(point.y))
  const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys), 1)
  return Math.max(span * 0.018, 0.001)
})
const reviewed = computed(() => props.analysis.review_status === 'reviewed')
const submitted = computed(() => props.analysis.review_status === 'submitted')

function makeDraft() {
  const source = savedGeometry.value
  if (source) return JSON.parse(JSON.stringify(source))
  const candidate = proposal.value || {}
  return {
    schema_version: '1.0',
    metadata: {
      name: props.analysis.sketch?.original_filename || 'Reviewed sketch',
      source: 'human_review',
      units: { length: '', force: '' },
    },
    model: {
      nodes: (candidate.joints || []).map(({ id, x, y }) => ({ id, x, y })),
      members: (candidate.members || []).map((member) => ({ id: member.id, node_i: member.joint_i || '', node_j: member.joint_j || '' })),
      // Support attachment and constraints are intentionally left for the reviewer to specify.
      supports: (candidate.supports || []).map((support) => ({
        id: support.id,
        node: '',
        type: ['pin', 'roller'].includes(String(support.possible_type).toLowerCase()) ? String(support.possible_type).toLowerCase() : '',
        ...(String(support.possible_type).toLowerCase() === 'roller' ? { direction: '' } : {}),
      })),
      // Loads are entered as explicit global components; no direction or magnitude is inferred.
      loads: (candidate.loads || []).map((load) => ({ id: load.id, node: '', fx: '', fy: '' })),
    },
  }
}

async function beginEditing() {
  busy.value = 'load'
  coordinatesConfirmed.value = false
  requestError.value = null
  message.value = ''
  try {
    const saved = await getAnalysisDraft(props.analysis.analysis_id)
    geometry.value = saved.draft ? JSON.parse(JSON.stringify(saved.draft)) : makeDraft()
    loadedGeometry.value = JSON.stringify(geometry.value)
    editing.value = true
  } catch (error) {
    requestError.value = error.body || { message: error.message }
  } finally {
    busy.value = ''
  }
}

function cancelEditing() {
  if (editing.value && JSON.stringify(geometry.value) !== loadedGeometry.value
      && !window.confirm('Discard your unsaved geometry changes?')) return
  editing.value = false
  geometry.value = null
  loadedGeometry.value = null
  coordinatesConfirmed.value = false
  requestError.value = null
  message.value = ''
}

function nextId(prefix, collection) {
  const ids = new Set(collection.map((item) => item.id))
  let index = 1
  while (ids.has(`${prefix}${index}`)) index += 1
  return `${prefix}${index}`
}

function addNode() { geometry.value.model.nodes.push({ id: nextId('J', geometry.value.model.nodes), x: '', y: '' }) }
function addMember() { geometry.value.model.members.push({ id: nextId('M', geometry.value.model.members), node_i: '', node_j: '' }) }
function addSupport() { geometry.value.model.supports.push({ id: nextId('S', geometry.value.model.supports), node: '', type: '' }) }
function addLoad() { geometry.value.model.loads.push({ id: nextId('L', geometry.value.model.loads), node: '', fx: '', fy: '' }) }
function removeAt(collection, index) { collection.splice(index, 1) }

function toNumber(value) {
  if (value === '' || value === null || value === undefined) return ''
  const number = Number(value)
  return Number.isFinite(number) ? number : value
}

async function saveDraft() {
  if (!geometry.value || busy.value) return
  busy.value = 'save'
  message.value = ''
  requestError.value = null
  const payload = JSON.parse(JSON.stringify(geometry.value))
  for (const node of payload.model.nodes) { node.x = toNumber(node.x); node.y = toNumber(node.y) }
  for (const load of payload.model.loads) { load.fx = toNumber(load.fx); load.fy = toNumber(load.fy) }
  try {
    await saveAnalysisDraft(props.analysis.analysis_id, payload, coordinatesConfirmed.value)
    editing.value = false
    loadedGeometry.value = null
    message.value = 'Draft saved and schema validation passed. It is still unapproved.'
    emit('updated')
  } catch (error) {
    requestError.value = error.body || { message: error.message }
  } finally {
    busy.value = ''
  }
}

async function markReviewed() {
  if (busy.value) return
  busy.value = 'review'
  message.value = ''
  requestError.value = null
  try {
    await markAnalysisReviewed(props.analysis.analysis_id)
    message.value = 'Draft passed server validation and is marked reviewed.'
    emit('updated')
  } catch (error) {
    requestError.value = error.body || { message: error.message }
  } finally {
    busy.value = ''
  }
}

async function solveReviewed() {
  if (busy.value || !window.confirm('Submit this reviewed geometry to the deterministic solver? The AI proposal will remain unchanged.')) return
  busy.value = 'solve'
  message.value = ''
  requestError.value = null
  try {
    await solveReviewedAnalysis(props.analysis.analysis_id)
    message.value = 'Reviewed geometry was submitted. Solver output is saved with this analysis.'
    emit('updated')
  } catch (error) {
    requestError.value = error.body || { message: error.message }
  } finally {
    busy.value = ''
  }
}

watch(() => props.analysis.analysis_id, () => cancelEditing())
</script>

<template>
  <section class="geometry-review card-surface">
    <div class="review-editor-heading">
      <div><div class="eyebrow">HUMAN-CORRECTED MODEL</div><h2>Geometry draft</h2></div>
      <div style="display: flex; align-items: center; gap: 10px;">
        <button class="button button-primary" type="button" @click="emit('editor', props.analysis.analysis_id)">
          Open Interactive Editor ↗
        </button>
        <span class="draft-state" :class="{ reviewed, submitted }">{{ submitted ? 'SUBMITTED' : reviewed ? 'REVIEWED' : savedGeometry ? 'DRAFT SAVED' : 'NOT SAVED' }}</span>
      </div>
    </div>
    <p class="editor-intro">AI output remains preserved above. Draft coordinates use physical length units and are separate from the AI's image-pixel coordinates. No unit or load value is inferred.</p>

    <div v-if="requestError" class="editor-error" role="alert">
      <strong>{{ requestError.message || 'The draft could not be saved.' }}</strong>
      <ul v-if="validationIssues.length"><li v-for="(issue, index) in validationIssues" :key="`${issue.path}-${index}`"><b>{{ issue.path || issue.code }}</b> — {{ issue.message }}</li></ul>
    </div>
    <p v-if="message" class="editor-success" role="status">{{ message }}</p>

    <div v-if="savedGeometry" class="draft-snapshot">
      <div class="draft-snapshot-head"><div><strong>Saved reviewer geometry</strong><small>{{ savedGeometry.metadata?.units?.length }} · {{ savedGeometry.metadata?.units?.force }}</small></div><span>{{ savedGeometry.model?.nodes?.length || 0 }} joints · {{ savedGeometry.model?.members?.length || 0 }} members</span></div>
      <div v-if="savedGeometry.model?.nodes?.length" class="draft-preview" aria-label="Human geometry preview in its own model coordinate system">
        <svg :viewBox="bounds" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Human-corrected draft geometry, drawn independently of the sketch image">
          <line v-for="member in savedGeometry.model.members || []" :key="`draft-member-${member.id}`" :x1="savedGeometry.model.nodes.find((node) => node.id === member.node_i)?.x" :y1="savedGeometry.model.nodes.find((node) => node.id === member.node_i)?.y" :x2="savedGeometry.model.nodes.find((node) => node.id === member.node_j)?.x" :y2="savedGeometry.model.nodes.find((node) => node.id === member.node_j)?.y" :class="['draft-preview-member', { selected: selectedElementId === member.id }]" @click="emit('select-element', member.id)" />
          <circle v-for="node in savedGeometry.model.nodes || []" :key="`draft-node-${node.id}`" :cx="node.x" :cy="node.y" :r="nodeRadius" :class="['draft-preview-node', { selected: selectedElementId === node.id }]" @click="emit('select-element', node.id)" />
        </svg>
        <small>Reviewer geometry preview · model units · not overlaid on image pixels</small>
      </div>
      <div class="saved-element-grid">
        <div v-for="node in savedGeometry.model.nodes || []" :key="`saved-node-${node.id}`" :class="['saved-element', { selected: selectedElementId === node.id }]" role="button" tabindex="0" @click="emit('select-element', node.id)" @keydown.enter="emit('select-element', node.id)"><strong>{{ node.id }}</strong><span>Joint · {{ node.x }}, {{ node.y }} {{ savedGeometry.metadata?.units?.length }}</span></div>
        <div v-for="member in savedGeometry.model.members || []" :key="`saved-member-${member.id}`" :class="['saved-element', { selected: selectedElementId === member.id }]" role="button" tabindex="0" @click="emit('select-element', member.id)" @keydown.enter="emit('select-element', member.id)"><strong>{{ member.id }}</strong><span>Member · {{ member.node_i }} ↔ {{ member.node_j }}</span></div>
        <div v-for="support in savedGeometry.model.supports || []" :key="`saved-support-${support.id}`" :class="['saved-element', { selected: selectedElementId === support.id }]" role="button" tabindex="0" @click="emit('select-element', support.id)" @keydown.enter="emit('select-element', support.id)"><strong>{{ support.id }}</strong><span>{{ support.type }} support · {{ support.node }}<template v-if="support.direction"> · {{ support.direction }}</template></span></div>
        <div v-for="load in savedGeometry.model.loads || []" :key="`saved-load-${load.id}`" :class="['saved-element', { selected: selectedElementId === load.id }]" role="button" tabindex="0" @click="emit('select-element', load.id)" @keydown.enter="emit('select-element', load.id)"><strong>{{ load.id }}</strong><span>Load · {{ load.node }} · Fx {{ load.fx }}, Fy {{ load.fy }} {{ savedGeometry.metadata?.units?.force }}</span></div>
      </div>
    </div>

    <div v-if="editing && geometry" class="geometry-form">
      <div class="units-form-row">
        <label>Length unit<select v-model="geometry.metadata.units.length"><option value="">Choose unit</option><option value="m">m</option><option value="mm">mm</option><option value="ft">ft</option></select></label>
        <label>Force unit<select v-model="geometry.metadata.units.force"><option value="">Choose unit</option><option value="N">N</option><option value="kN">kN</option><option value="lbf">lbf</option></select></label>
      </div>
      <p v-if="!savedGeometry" class="coordinate-warning">The prefilled joint values came from image pixels. Replace them with confirmed physical coordinates in the selected length unit before saving. Use positive x to the right and positive y upward for solver coordinates.</p>
      <p v-else class="coordinate-warning">Confirm saved joint coordinates are physical lengths in the selected unit. Solver coordinates use positive x to the right and positive y upward.</p>

      <section class="form-collection"><header><h3>Joints</h3><button type="button" class="small-action" @click="addNode">＋ Add joint</button></header>
        <div v-for="(node, index) in geometry.model.nodes" :key="`edit-node-${index}`" class="geometry-form-row node-form-row">
          <label>ID<input v-model="node.id" autocomplete="off" /></label><label>x <small>{{ geometry.metadata.units.length || 'unit' }}</small><input v-model="node.x" inputmode="decimal" /></label><label>y <small>{{ geometry.metadata.units.length || 'unit' }}</small><input v-model="node.y" inputmode="decimal" /></label><button type="button" class="remove-action" :aria-label="`Remove joint ${node.id}`" @click="removeAt(geometry.model.nodes, index)">×</button>
        </div>
      </section>

      <section class="form-collection"><header><h3>Members</h3><button type="button" class="small-action" @click="addMember">＋ Add member</button></header>
        <div v-for="(member, index) in geometry.model.members" :key="`edit-member-${index}`" class="geometry-form-row">
          <label>ID<input v-model="member.id" autocomplete="off" /></label><label>Joint i<select v-model="member.node_i"><option value="">Choose joint</option><option v-for="node in geometry.model.nodes" :key="node.id" :value="node.id">{{ node.id }}</option></select></label><label>Joint j<select v-model="member.node_j"><option value="">Choose joint</option><option v-for="node in geometry.model.nodes" :key="node.id" :value="node.id">{{ node.id }}</option></select></label><button type="button" class="remove-action" :aria-label="`Remove member ${member.id}`" @click="removeAt(geometry.model.members, index)">×</button>
        </div>
      </section>

      <section class="form-collection"><header><h3>Supports</h3><button type="button" class="small-action" @click="addSupport">＋ Add support</button></header>
        <div v-for="(support, index) in geometry.model.supports" :key="`edit-support-${index}`" class="geometry-form-row">
          <label>ID<input v-model="support.id" autocomplete="off" /></label><label>Joint<select v-model="support.node"><option value="">Choose joint</option><option v-for="node in geometry.model.nodes" :key="node.id" :value="node.id">{{ node.id }}</option></select></label><label>Type<select v-model="support.type"><option value="">Choose type</option><option value="pin">Pin</option><option value="roller">Roller</option></select></label><label v-if="support.type === 'roller'">Direction<select v-model="support.direction"><option value="">Choose direction</option><option value="horizontal">Horizontal</option><option value="vertical">Vertical</option></select></label><button type="button" class="remove-action" :aria-label="`Remove support ${support.id}`" @click="removeAt(geometry.model.supports, index)">×</button>
        </div>
      </section>

      <section class="form-collection"><header><h3>Loads</h3><button type="button" class="small-action" @click="addLoad">＋ Add load</button></header><p class="form-hint">Enter explicit global components. Positive x points right and positive y points up.</p>
        <div v-for="(load, index) in geometry.model.loads" :key="`edit-load-${index}`" class="geometry-form-row load-form-row">
          <label>ID<input v-model="load.id" autocomplete="off" /></label><label>Joint<select v-model="load.node"><option value="">Choose joint</option><option v-for="node in geometry.model.nodes" :key="node.id" :value="node.id">{{ node.id }}</option></select></label><label>Fx <small>{{ geometry.metadata.units.force || 'unit' }}</small><input v-model="load.fx" inputmode="decimal" /></label><label>Fy <small>{{ geometry.metadata.units.force || 'unit' }}</small><input v-model="load.fy" inputmode="decimal" /></label><button type="button" class="remove-action" :aria-label="`Remove load ${load.id}`" @click="removeAt(geometry.model.loads, index)">×</button>
        </div>
      </section>

      <label class="coordinate-confirmation"><input v-model="coordinatesConfirmed" type="checkbox" /><span>I replaced or verified every joint coordinate as a physical length in the selected unit. I checked loads and support constraints against the drawing.</span></label>
      <div class="editor-actions"><button type="button" class="button button-secondary" @click="cancelEditing">Cancel edits</button><button type="button" class="button button-primary" :disabled="busy || !coordinatesConfirmed" @click="saveDraft">{{ busy === 'save' ? 'Validating…' : 'Validate and save draft' }}</button></div>
    </div>

    <div v-else class="review-actions">
      <button v-if="!submitted" type="button" class="button button-secondary" :disabled="busy === 'load'" @click="beginEditing">{{ busy === 'load' ? 'Loading draft…' : savedGeometry ? 'Edit saved draft' : 'Correct interpretation' }}</button>
      <button v-if="savedGeometry && !reviewed && !submitted" type="button" class="button button-primary" :disabled="busy" @click="markReviewed">{{ busy === 'review' ? 'Checking…' : 'Mark reviewed' }}</button>
      <button v-if="reviewed && !submitted" type="button" class="button button-primary" :disabled="busy" @click="solveReviewed">{{ busy === 'solve' ? 'Solving…' : 'Submit reviewed geometry to solver' }}</button>
      <span v-if="submitted" class="submitted-note">Submitted geometry and results are saved with this sketch.</span>
    </div>
    <p v-if="analysis.solver_results" class="solver-caveat">A numerical solution does not establish physical stability, code compliance, or engineering suitability. Check diagnostics and units.</p>
  </section>
</template>
