<script setup>
import { computed, ref, watch } from 'vue'
import { apiUrl, createAnalysis, getAnalysis, getAnalysisImage } from '../api/analyses'
import GeometryReview from '../components/GeometryReview.vue'

const props = defineProps({ analysisId: { type: String, required: true } })
const emit = defineEmits(['history', 'created', 'editor'])
const analysis = ref(null)
const loading = ref(true)
const error = ref('')
const uploading = ref(false)
const showOpenCv = ref(true)
const showProposal = ref(true)
const showEndpoints = ref(false)
const showIds = ref(false)
const zoom = ref(1)
const selectedElementId = ref('')
const imageUnavailable = ref(false)
let requestSequence = 0

const activeImageUrl = computed(() => apiUrl(analysis.value?.sketch?.image_url || analysis.value?.image_url))
const imageWidth = computed(() => analysis.value?.sketch?.image_width || analysis.value?.image_width || 0)
const imageHeight = computed(() => analysis.value?.sketch?.image_height || analysis.value?.image_height || 0)
const stageStyle = computed(() => imageWidth.value && imageHeight.value ? { aspectRatio: `${imageWidth.value} / ${imageHeight.value}` } : {})
const perception = computed(() => analysis.value?.perception || null)
const proposal = computed(() => analysis.value?.interpretation_proposal || null)
const jointsById = computed(() => Object.fromEntries((proposal.value?.joints || []).map((joint) => [joint.id, joint])))
const proposalLoads = computed(() => (proposal.value?.loads || []).map((load) => {
  const direction = String(load.direction || '').toLowerCase().replace(/[ _-]/g, '')
  const vectors = { down: [0, 20], downward: [0, 20], south: [0, 20], up: [0, -20], upward: [0, -20], north: [0, -20], right: [20, 0], rightward: [20, 0], east: [20, 0], left: [-20, 0], leftward: [-20, 0], west: [-20, 0], northeast: [14, -14], northwest: [-14, -14], southeast: [14, 14], southwest: [-14, 14] }
  const vector = vectors[direction]
  return vector ? { ...load, dx: vector[0], dy: vector[1] } : null
}).filter(Boolean))
const validationIssues = computed(() => analysis.value?.validation?.issues || analysis.value?.validation?.errors || [])
const validationWarnings = computed(() => analysis.value?.validation?.warnings || [])
const solverMemberForces = computed(() => Object.entries(analysis.value?.solver_results?.member_forces || {}))
const solverReactions = computed(() => Object.entries(analysis.value?.solver_results?.support_reactions || {}).flatMap(([supportId, axes]) => Object.entries(axes || {}).map(([axis, value]) => [supportId, axis, value])))

watch(() => props.analysisId, loadAnalysis, { immediate: true })
watch(activeImageUrl, () => { imageUnavailable.value = false })

function formatDate(value) {
  if (!value) return 'Date unavailable'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function displayStatus(status) {
  return ({ pending_review: 'Pending review', reviewed: 'Reviewed', failed: 'Failed', solved: 'Solved', pending: 'Processing', draft: 'Draft saved', submitted: 'Submitted to solver' })[status] || status || 'Unknown'
}

function statusClass(status) {
  if (status === 'failed') return 'status-failed'
  if (status === 'reviewed' || status === 'solved') return 'status-complete'
  return 'status-pending'
}

function humanizeError(code, message) {
  const messages = {
    MISSING_GEMINI_API_KEY: 'Gemini is selected, but its server-side credential is not configured.',
    MISSING_MODEL_API_KEY: 'Meta is selected, but its server-side credential is not configured.',
    INVALID_IMAGE: 'The uploaded file could not be read as a supported sketch image.',
    IMAGE_TOO_LARGE: 'The image exceeds the 10 MiB upload limit.',
    UNSUPPORTED_IMAGE_TYPE: 'The saved image is not a supported format.',
    GEMINI_API_ERROR: 'Gemini could not complete the interpretation request.',
    MUSE_API_ERROR: 'Meta Muse Spark could not complete the interpretation request.',
    GEMINI_AUTHENTICATION_FAILED: 'Gemini rejected the backend credential or account access.',
    MUSE_AUTHENTICATION_FAILED: 'Meta rejected the backend credential or account access.',
    GEMINI_INVALID_MODEL: 'Gemini did not recognize the configured model. Check GEMINI_MODEL.',
    MUSE_INVALID_MODEL: 'Meta did not recognize the configured model.',
    GEMINI_RATE_LIMITED: 'Gemini rate limit or quota was reached. Try again later.',
    MUSE_RATE_LIMITED: 'Meta rate limit or quota was reached. Try again later.',
    GEMINI_NETWORK_ERROR: 'The backend could not reach Gemini. Check the backend network connection.',
    MUSE_NETWORK_ERROR: 'The backend could not reach Meta. Check the backend network connection.',
    GEMINI_TIMEOUT: 'The Gemini request timed out. Try again with a smaller image.',
    MUSE_TIMEOUT: 'The Meta request timed out. Try again with a smaller image.',
    INVALID_GEMINI_RESPONSE: 'Gemini returned an unexpected interpretation format.',
    INVALID_MUSE_RESPONSE: 'Meta returned an unexpected interpretation format.',
    ANALYSIS_HISTORY_UNAVAILABLE: 'The backend could not save or retrieve this analysis.',
  }
  return messages[code] || message || 'The analysis could not be completed.'
}

async function loadAnalysis() {
  const sequence = ++requestSequence
  loading.value = true
  error.value = ''
  analysis.value = null
  try {
    const result = await getAnalysis(props.analysisId)
    if (sequence === requestSequence) analysis.value = result
  } catch (cause) {
    if (sequence === requestSequence) error.value = cause.message
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

async function retryAnalysis() {
  if (!analysis.value?.sketch?.image_url || uploading.value) return
  uploading.value = true
  error.value = ''
  try {
    const blob = await getAnalysisImage(analysis.value.sketch.image_url)
    const filename = analysis.value.sketch.original_filename || 'sketch.png'
    const file = new File([blob], filename, { type: blob.type || analysis.value.sketch.mime_type })
    const result = await createAnalysis(file, analysis.value.provider === 'meta' ? 'meta' : 'gemini')
    emit('created', result.analysis_id)
  } catch (cause) {
    error.value = humanizeError(cause.body?.error_code, cause.message)
    if (cause.body?.analysis_id) emit('created', cause.body.analysis_id)
  } finally {
    uploading.value = false
  }
}

function issueMessage(issue) {
  const messages = {
    MISSING_FIELD: 'A required value is missing.',
    INVALID_TYPE: 'A value has an unexpected type.',
    UNKNOWN_NODE_REFERENCE: 'A member, support, or load refers to a node that was not found.',
    ZERO_LENGTH_MEMBER: 'A member has endpoints at the same location.',
    INVALID_SUPPORT: 'A support definition is invalid.',
  }
  return messages[issue.code] || issue.message || issue.code || 'Validation issue.'
}

function shortId(id) { return id ? id.slice(0, 8).toUpperCase() : '—' }
function selectElement(id) { selectedElementId.value = id || '' }
</script>

<template>
  <section class="page-content detail-page">
    <div v-if="loading" class="detail-loading"><span class="large-spinner"></span><strong>Loading analysis</strong><p>Retrieving its saved sketch and interpretation.</p></div>
    <div v-else-if="!analysis" class="empty-panel detail-not-found"><div class="eyebrow">ANALYSIS UNAVAILABLE</div><strong>{{ error || 'This saved analysis could not be found.' }}</strong><button class="button button-secondary" type="button" @click="emit('history')">Back to history</button></div>
    <template v-else>
      <div class="detail-back-row"><button class="back-button" type="button" @click="emit('history')"><span>←</span> Analysis history</button><span class="detail-id">ANALYSIS #{{ shortId(analysis.analysis_id) }}</span></div>
      <div class="detail-heading">
        <div>
          <div class="eyebrow">ANALYSIS REVIEW</div>
          <h1>{{ analysis.sketch?.original_filename || analysis.original_filename || 'Solver analysis' }}</h1>
          <div class="detail-meta">
            <span>{{ formatDate(analysis.created_at) }}</span><i></i>
            <span>{{ imageWidth && imageHeight ? `${imageWidth} × ${imageHeight} px` : 'No source image' }}</span><i></i>
            <span>{{ analysis.provider ? `${analysis.provider} · ${analysis.model_id || ''}` : 'Deterministic solver' }}</span>
          </div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
          <button class="button button-primary" type="button" @click="emit('editor', analysis.analysis_id)">
            <svg viewBox="0 0 20 20" fill="none" width="16" height="16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px;"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
            Edit geometry
          </button>
          <span class="status-badge large-status" :class="statusClass(analysis.status)"><i></i>{{ displayStatus(analysis.status) }}</span>
        </div>
      </div>

      <div v-if="analysis.status === 'failed'" class="alert alert-error analysis-alert" role="alert"><span class="alert-icon">!</span><div><strong>{{ humanizeError(analysis.error_code, analysis.error_message) }}</strong><p>{{ analysis.error_code }} · This attempt was saved to history. <template v-if="!analysis.human_review?.geometry">Retry only when you choose to submit another provider request.</template></p></div><button v-if="analysis.sketch?.image_url && !analysis.human_review?.geometry" class="button button-secondary" type="button" :disabled="uploading" @click="retryAnalysis">{{ uploading ? 'Retrying…' : 'Retry analysis' }}</button></div>
      <div v-if="error" class="alert alert-error analysis-alert" role="alert"><span class="alert-icon">!</span><div><strong>Could not refresh this analysis</strong><p>{{ error }}</p></div><button class="button button-secondary" type="button" @click="loadAnalysis">Retry</button></div>

      <section v-if="activeImageUrl" class="visual-section">
        <div class="section-title-row visual-title"><div><div class="eyebrow">SIDE-BY-SIDE EVIDENCE</div><h2>Compare the readings</h2></div><span class="review-state"><span class="state-dot"></span>{{ displayStatus(analysis.review_status) }}</span></div>
        <div v-if="imageUnavailable" class="notice notice-warning image-unavailable">The original sketch file is unavailable. Saved geometry is still shown, but image overlays cannot be compared.</div>
        <div class="visual-toolbar" aria-label="Visualization controls">
          <label><input v-model="showOpenCv" type="checkbox" /> OpenCV detections</label><label><input v-model="showEndpoints" type="checkbox" /> Endpoint clusters</label><label><input v-model="showProposal" type="checkbox" /> AI proposal</label><label><input v-model="showIds" type="checkbox" /> Element IDs</label>
          <label class="zoom-control">Zoom <input v-model.number="zoom" type="range" min="1" max="3" step="0.25" /><span>{{ zoom.toFixed(2) }}×</span></label>
        </div>
        <div class="visual-grid">
          <article class="visual-card"><div class="visual-card-heading"><div><span class="visual-index">A</span><div><strong>Original sketch</strong><small>Uploaded source</small></div></div><a class="open-image" :href="activeImageUrl" target="_blank" rel="noreferrer" aria-label="Open original image">↗</a></div><div class="visual-stage" :style="[stageStyle, { '--stage-zoom': zoom }]"><img v-if="!imageUnavailable" :src="activeImageUrl" alt="Original uploaded truss sketch" @error="imageUnavailable = true" /><div v-if="imageUnavailable" class="stage-empty">Original image is unavailable.</div></div><div class="visual-card-footer"><span>{{ analysis.sketch?.mime_type || analysis.mime_type }}</span><span>{{ imageWidth }} × {{ imageHeight }} px</span></div></article>

          <article v-if="showOpenCv" class="visual-card"><div class="visual-card-heading"><div><span class="visual-index index-vision">B</span><div><strong>OpenCV detections</strong><small>Visual evidence only</small></div></div><span class="count-label">{{ perception?.lines?.length || 0 }} segments</span></div><div class="visual-stage" :style="[stageStyle, { '--stage-zoom': zoom }]"><img v-if="activeImageUrl && !imageUnavailable" :src="activeImageUrl" alt="Sketch under OpenCV detections" @error="imageUnavailable = true" /><svg v-if="imageWidth && imageHeight" class="overlay-svg" :viewBox="`0 0 ${imageWidth} ${imageHeight}`" preserveAspectRatio="none" role="img" aria-label="OpenCV candidate segments and endpoint clusters"><line v-for="line in perception?.lines || []" :key="line.id" :x1="line.start?.[0]" :y1="line.start?.[1]" :x2="line.end?.[0]" :y2="line.end?.[1]" :class="['detected-line', { selected: selectedElementId === line.id }]" role="button" tabindex="0" @click.stop="selectElement(line.id)" @keydown.enter.stop="selectElement(line.id)" /><text v-if="showIds" v-for="line in perception?.lines || []" :key="`line-id-${line.id}`" :x="(line.start?.[0] + line.end?.[0]) / 2" :y="(line.start?.[1] + line.end?.[1]) / 2" class="element-id-label">{{ line.id }}</text><g v-for="joint in (showEndpoints ? perception?.joints || [] : [])" :key="joint.id" class="interactive-element" :class="{ selected: selectedElementId === joint.id }" role="button" tabindex="0" @click.stop="selectElement(joint.id)" @keydown.enter.stop="selectElement(joint.id)"><circle :cx="joint.point?.[0]" :cy="joint.point?.[1]" r="5" class="detected-joint" /><text v-if="showIds" :x="joint.point?.[0] + 6" :y="joint.point?.[1] - 6" class="element-id-label">{{ joint.id }}</text></g></svg><div v-if="!perception" class="stage-empty">No visual detection data was saved.</div></div><div class="visual-card-footer"><span><i class="legend-line legend-cyan"></i>Candidate line</span><span><i class="legend-dot legend-cyan-dot"></i>Endpoint cluster</span></div></article>

          <article v-if="showProposal" class="visual-card proposal-card"><div class="visual-card-heading"><div><span class="visual-index index-ai">C</span><div><strong>AI-proposed geometry</strong><small>{{ proposal ? 'Candidate interpretation · unapproved' : 'No proposal available' }}</small></div></div><span v-if="proposal" class="count-label">{{ proposal.members?.length || 0 }} members</span></div><div class="visual-stage proposal-stage" :style="[stageStyle, { '--stage-zoom': zoom }]"><img v-if="activeImageUrl && !imageUnavailable" :src="activeImageUrl" alt="Sketch under AI-proposed geometry" @error="imageUnavailable = true" /><svg v-if="proposal && imageWidth && imageHeight" class="overlay-svg proposal-overlay" :viewBox="`0 0 ${imageWidth} ${imageHeight}`" preserveAspectRatio="none" role="img" aria-label="AI candidate joints, members, supports and loads"><defs><marker id="load-arrow" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0 0 7 3.5 0 7Z" fill="#d18a47" /></marker></defs><g v-for="member in proposal.members || []" :key="`m-${member.id}`" class="interactive-element" :class="{ selected: selectedElementId === member.id }" role="button" tabindex="0" @click.stop="selectElement(member.id)" @keydown.enter.stop="selectElement(member.id)"><line :x1="jointsById[member.joint_i]?.x" :y1="jointsById[member.joint_i]?.y" :x2="jointsById[member.joint_j]?.x" :y2="jointsById[member.joint_j]?.y" :class="['proposal-member', { uncertain: member.connection_uncertain }]" /><text v-if="showIds" :x="((jointsById[member.joint_i]?.x || 0) + (jointsById[member.joint_j]?.x || 0)) / 2" :y="((jointsById[member.joint_i]?.y || 0) + (jointsById[member.joint_j]?.y || 0)) / 2 - 7" class="element-id-label">{{ member.id }}</text></g><g v-for="joint in proposal.joints || []" :key="`j-${joint.id}`" class="interactive-element" :class="{ selected: selectedElementId === joint.id }" role="button" tabindex="0" @click.stop="selectElement(joint.id)" @keydown.enter.stop="selectElement(joint.id)"><circle :cx="joint.x" :cy="joint.y" r="6" class="proposal-joint" /><text v-if="showIds" :x="joint.x + 7" :y="joint.y - 7" class="element-id-label">{{ joint.id }}</text></g><path v-for="support in proposal.supports || []" :key="`s-${support.id}`" :d="`M ${support.x} ${support.y + 9} L ${support.x - 8} ${support.y - 5} L ${support.x + 8} ${support.y - 5} Z`" :class="['proposal-support', { uncertain: support.uncertain, selected: selectedElementId === support.id }]" role="button" tabindex="0" @click.stop="selectElement(support.id)" @keydown.enter.stop="selectElement(support.id)"><title>{{ support.possible_type }} support{{ support.uncertain ? ' · uncertain' : '' }}</title></path><text v-if="showIds" v-for="support in proposal.supports || []" :key="`support-id-${support.id}`" :x="support.x + 8" :y="support.y + 15" class="element-id-label">{{ support.id }}</text><line v-for="load in proposalLoads" :key="`l-${load.id}`" :x1="load.x" :y1="load.y" :x2="load.x + load.dx" :y2="load.y + load.dy" :class="['proposal-load', { selected: selectedElementId === load.id }]" marker-end="url(#load-arrow)" role="button" tabindex="0" @click.stop="selectElement(load.id)" @keydown.enter.stop="selectElement(load.id)"><title>{{ load.direction }} load{{ load.magnitude == null ? '' : ` · ${load.magnitude} ${load.unit || ''}` }}</title></line><text v-if="showIds" v-for="load in proposal.loads || []" :key="`load-id-${load.id}`" :x="load.x" :y="load.y - 8" class="element-id-label">{{ load.id }}</text></svg><div v-if="!proposal" class="stage-empty">{{ analysis.status === 'failed' ? 'Interpretation did not complete.' : 'No interpretation proposal was saved.' }}</div></div><div class="visual-card-footer"><span><i class="legend-line legend-amber"></i>Proposed member</span><span><i class="legend-dot legend-amber-dot"></i>Proposed joint</span></div></article>
        </div>
        <div v-if="perception?.lines?.length >= 300" class="detector-cap-note">The OpenCV detector reached its 300-segment cap. Candidate lines can include labels, dimensions, and drawing artifacts.</div><div v-if="perception?.warnings?.length" class="notice-list"><div v-for="warning in perception.warnings" :key="warning" class="notice notice-warning"><span>!</span>{{ warning }}</div></div>
      </section>

      <div class="results-grid">
        <section class="result-card card-surface"><div class="result-heading"><div><div class="eyebrow">MODEL OUTPUT</div><h2>Interpretation proposal</h2></div><span v-if="proposal" class="proposal-only-badge">CANDIDATE ONLY</span></div><template v-if="proposal"><div class="proposal-stats"><div><strong>{{ proposal.joints?.length || 0 }}</strong><span>Joints</span></div><div><strong>{{ proposal.members?.length || 0 }}</strong><span>Members</span></div><div><strong>{{ proposal.supports?.length || 0 }}</strong><span>Supports</span></div><div><strong>{{ proposal.loads?.length || 0 }}</strong><span>Loads</span></div></div><details class="proposal-records"><summary>Inspect proposed elements</summary><div class="proposal-record-grid"><section v-if="proposal.joints?.length"><h3>Joints</h3><div v-for="joint in proposal.joints" :key="`detail-j-${joint.id}`" :class="['element-row', { selected: selectedElementId === joint.id }]" role="button" tabindex="0" @click="selectElement(joint.id)" @keydown.enter="selectElement(joint.id)"><strong>{{ joint.id }}</strong><span>{{ joint.x }}, {{ joint.y }} px · model coordinates not confirmed</span></div></section><section v-if="proposal.members?.length"><h3>Members</h3><div v-for="member in proposal.members" :key="`detail-m-${member.id}`" :class="['element-row', { selected: selectedElementId === member.id }]" role="button" tabindex="0" @click="selectElement(member.id)" @keydown.enter="selectElement(member.id)"><strong>{{ member.id }}</strong><span>{{ member.joint_i }} ↔ {{ member.joint_j }}<b v-if="member.connection_uncertain" class="uncertain-label">uncertain</b></span><small v-if="member.notes">{{ member.notes }}</small></div></section><section v-if="proposal.supports?.length"><h3>Supports</h3><div v-for="support in proposal.supports" :key="`detail-s-${support.id}`" :class="['element-row', { selected: selectedElementId === support.id }]" role="button" tabindex="0" @click="selectElement(support.id)" @keydown.enter="selectElement(support.id)"><strong>{{ support.id }}</strong><span>{{ support.possible_type }} · {{ support.x }}, {{ support.y }} px<b v-if="support.uncertain" class="uncertain-label">uncertain</b></span><small v-if="support.notes">{{ support.notes }}</small></div></section><section v-if="proposal.loads?.length"><h3>Loads</h3><div v-for="load in proposal.loads" :key="`detail-l-${load.id}`" :class="['element-row', { selected: selectedElementId === load.id }]" role="button" tabindex="0" @click="selectElement(load.id)" @keydown.enter="selectElement(load.id)"><strong>{{ load.id }}</strong><span>{{ load.direction }}<template v-if="load.magnitude != null"> · {{ load.magnitude }} {{ load.unit }}</template><b v-if="load.uncertain" class="uncertain-label">uncertain</b></span><small v-if="load.notes">{{ load.notes }}</small></div></section></div></details><div v-if="proposal.ambiguities?.length" class="text-list"><h3>Ambiguities to check</h3><ul><li v-for="item in proposal.ambiguities" :key="item">{{ item }}</li></ul></div><div v-if="proposal.missing_information?.length" class="text-list"><h3>Information not visible</h3><ul><li v-for="item in proposal.missing_information" :key="item">{{ item }}</li></ul></div><div v-if="!proposal.ambiguities?.length && !proposal.missing_information?.length" class="quiet-note">No ambiguities were returned. This does not confirm the geometry is correct.</div></template><div v-else class="quiet-note">{{ analysis.status === 'failed' ? 'No candidate interpretation is available for this run.' : 'This record has no AI interpretation proposal.' }}</div></section>

        <section class="result-card card-surface"><div class="result-heading"><div><div class="eyebrow">CHECKS & DIAGNOSTICS</div><h2>Validation state</h2></div><span class="not-run-badge">{{ analysis.validation?.status === 'not_performed' ? 'NOT RUN' : analysis.validation?.status || '—' }}</span></div><p v-if="analysis.validation?.status === 'not_performed'" class="validation-intro">Candidate geometry has not been converted into a solver model. Nothing is approved or solved from this proposal.</p><ul v-if="validationIssues.length" class="issue-list"><li v-for="(issue, index) in validationIssues" :key="`${issue.code}-${index}`"><span class="issue-mark">!</span><span><strong>{{ issue.path || issue.code }}</strong><small>{{ issueMessage(issue) }}</small></span></li></ul><ul v-if="validationWarnings.length" class="issue-list warning-issue-list"><li v-for="(warning, index) in validationWarnings" :key="`warning-${index}`"><span class="issue-mark">i</span><span><strong>{{ warning.path || warning.code || 'Review note' }}</strong><small>{{ typeof warning === 'string' ? warning : issueMessage(warning) }}</small></span></li></ul><div v-if="!validationIssues.length && !validationWarnings.length && analysis.validation?.status !== 'not_performed' && analysis.validation" class="quiet-note">{{ analysis.validation.message || 'No validation issues were saved.' }}</div><div v-if="analysis.diagnostics" class="diagnostics"><span>Solver diagnostics</span><b>{{ analysis.diagnostics.category || 'Available' }}</b><small>{{ analysis.diagnostics.equation_count ?? '—' }} equations · {{ analysis.diagnostics.unknown_count ?? '—' }} unknowns</small></div><div v-if="analysis.solver_results" class="solver-result-note"><strong>Deterministic solver results</strong><p>These values belong to the model submitted to the solver; they do not approve any separate AI proposal.</p><div v-if="solverMemberForces.length" class="solver-values"><h3>Member forces <span>{{ analysis.solver_results.force_unit || 'declared force units' }}</span></h3><div v-for="[id, value] in solverMemberForces" :key="`force-${id}`"><strong>{{ id }}</strong><span>{{ Number(value).toPrecision(5) }}</span></div></div><div v-if="solverReactions.length" class="solver-values"><h3>Support reactions <span>{{ analysis.solver_results.force_unit || 'declared force units' }}</span></h3><div v-for="[id, axis, value] in solverReactions" :key="`reaction-${id}-${axis}`"><strong>{{ id }} · {{ axis }}</strong><span>{{ Number(value).toPrecision(5) }}</span></div></div><small v-if="analysis.solver_results.max_equilibrium_residual != null" class="solver-residual">Maximum equilibrium residual {{ Number(analysis.solver_results.max_equilibrium_residual).toPrecision(4) }} · tolerance {{ Number(analysis.solver_results.residual_tolerance).toPrecision(4) }}</small></div></section>
      </div>

      <GeometryReview v-if="analysis.analysis_type === 'sketch' && proposal" :analysis="analysis" :selected-element-id="selectedElementId" @select-element="selectElement" @updated="loadAnalysis" @editor="emit('editor', $event)" />
      <div class="review-disclaimer"><span class="disclaimer-icon">i</span><div><strong>Engineering review boundary</strong><p>Model validation checks the request schema and references; solver diagnostics are numerical checks. Neither establishes physical stability, code compliance, or engineering suitability. Review all dimensions and loads.</p></div><span class="review-status-label"><i></i>{{ displayStatus(analysis.review_status) }}</span></div>
    </template>
  </section>
</template>
