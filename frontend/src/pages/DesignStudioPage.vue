<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  Sparkles,
  Layers,
  ArrowRight,
  ExternalLink,
  RotateCcw,
  Check,
  X,
  Loader2,
  FolderOpen,
  PlusCircle,
  HelpCircle,
  CheckCircle2,
  AlertTriangle,
  Activity,
  Compass,
} from 'lucide-vue-next'
import {
  listAnalyses,
  getAnalysis,
  getAnalysisDraft,
  designTruss,
  applyDesignProposal,
  rejectDesignProposal,
} from '../api/analyses'
import DesignInstructionPanel from '../components/DesignInstructionPanel.vue'
import DesignProposalCard from '../components/DesignProposalCard.vue'

const props = defineProps({
  initialAnalysisId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['open', 'editor', 'new', 'history'])

// Studio State
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const toastMessage = ref('')
const toastVariant = ref('info')

// Analysis & Model Context
const savedAnalyses = ref([])
const selectedAnalysisId = ref(props.initialAnalysisId || '')
const currentModel = ref(null)
const modelRevision = ref(1)
const activeProposal = ref(null)

// Toast Helper
let toastTimer = null
function showToast(msg, variant = 'info') {
  clearTimeout(toastTimer)
  toastMessage.value = msg
  toastVariant.value = variant
  toastTimer = setTimeout(() => { toastMessage.value = '' }, 3500)
}

// Load recent analyses for the analysis selector
async function loadRecentAnalyses() {
  try {
    const res = await listAnalyses({ page: 1, perPage: 20 })
    savedAnalyses.value = res.items || []
  } catch (err) {
    console.warn('Could not load analysis list:', err)
  }
}

// Load a specific analysis model
async function loadSelectedAnalysis(id) {
  if (!id) {
    currentModel.value = null
    modelRevision.value = 1
    activeProposal.value = null
    return
  }

  loading.value = true
  error.value = ''
  activeProposal.value = null

  try {
    const analysisData = await getAnalysis(id)
    const draftData = await getAnalysisDraft(id).catch(() => ({ draft: null }))

    let baseModel = null
    if (draftData.draft) {
      baseModel = draftData.draft
    } else if (analysisData.human_review?.geometry) {
      baseModel = analysisData.human_review.geometry
    } else if (analysisData.proposal) {
      // Convert proposal joints/members to Schema 1.0 if needed
      baseModel = {
        schema_version: '1.0',
        metadata: { name: analysisData.original_filename || 'Analysis Truss', source: 'proposal', units: { length: 'm', force: 'kN' } },
        model: {
          nodes: (analysisData.proposal.joints || []).map((j) => ({ id: j.id, x: (j.x || 0) / 100, y: (j.y || 0) / 100 })),
          members: (analysisData.proposal.members || []).map((m) => ({ id: m.id, node_i: m.joint_i, node_j: m.joint_j })),
          supports: [],
          loads: [],
        },
      }
    }

    currentModel.value = baseModel
    modelRevision.value = analysisData.validation_json?.revision || 1
  } catch (err) {
    error.value = err.message || 'Failed to load analysis geometry.'
  } finally {
    loading.value = false
  }
}

watch(selectedAnalysisId, (newId) => {
  loadSelectedAnalysis(newId)
})

onMounted(async () => {
  await loadRecentAnalyses()
  if (selectedAnalysisId.value) {
    await loadSelectedAnalysis(selectedAnalysisId.value)
  }
})

// Handle Design Submission
async function handleDesignSubmit({ message, intent }) {
  busy.value = true
  error.value = ''

  const context = {
    analysis_id: selectedAnalysisId.value || undefined,
    model_revision: modelRevision.value,
    model: currentModel.value || undefined,
    units: currentModel.value?.metadata?.units || { length: 'm', force: 'kN' },
  }

  try {
    const result = await designTruss({
      message,
      intent,
      context,
    })
    activeProposal.value = result
    if (result.intent === 'explain') {
      showToast('Engineering explanation generated.', 'info')
    } else {
      showToast('Design proposal formulated. Review proposed geometry before applying.', 'info')
    }
  } catch (err) {
    if (err.body?.error === 'OUT_OF_SCOPE' || err.status === 400) {
      error.value = err.message || 'Prompt out of scope. Please specify structural geometry or questions.'
    } else {
      error.value = err.message || 'Natural language design service error.'
    }
  } finally {
    busy.value = false
  }
}

// Handle Proposal Approval
async function handleApplyProposal(proposal) {
  if (!proposal || !proposal.proposed_model) return
  busy.value = true
  error.value = ''

  const isCreatingNew = !selectedAnalysisId.value

  try {
    const result = await applyDesignProposal({
      proposal_id: proposal.proposal_id,
      analysis_id: selectedAnalysisId.value || null,
      base_revision: proposal.base_revision ?? modelRevision.value,
      proposed_model: proposal.proposed_model,
      create_record: isCreatingNew,
    })

    if (result.status === 'applied') {
      currentModel.value = result.model
      modelRevision.value = result.model_revision || (modelRevision.value + 1)
      activeProposal.value = null
      showToast(result.message || 'Changes applied successfully.', 'success')

      // If a new analysis was created, navigate to editor or update selection
      if (result.analysis_id) {
        selectedAnalysisId.value = result.analysis_id
        await loadRecentAnalyses()
        emit('editor', result.analysis_id)
      }
    }
  } catch (err) {
    if (err.status === 409) {
      error.value = 'Revision conflict: Canvas model was modified after proposal generation. Please formulate a fresh request.'
    } else {
      error.value = err.message || 'Failed to apply proposal.'
    }
  } finally {
    busy.value = false
  }
}

// Handle Proposal Rejection
async function handleRejectProposal(proposal) {
  if (!proposal) return
  busy.value = true
  try {
    await rejectDesignProposal({
      proposal_id: proposal.proposal_id,
      analysis_id: selectedAnalysisId.value || null,
      base_revision: proposal.base_revision ?? modelRevision.value,
    })
    activeProposal.value = null
    showToast('Proposal discarded. Original geometry preserved.', 'info')
  } catch (err) {
    activeProposal.value = null
  } finally {
    busy.value = false
  }
}

// Geometry Display Computation
const displayModel = computed(() => {
  if (activeProposal.value?.proposed_model?.model) {
    return activeProposal.value.proposed_model.model
  }
  return currentModel.value?.model || null
})

// Proposed Changes for Canvas Highlighting
const proposedAdditions = computed(() => {
  if (!activeProposal.value?.operations) return []
  return activeProposal.value.operations.filter((op) => op.op === 'add_member')
})

const proposedRemovals = computed(() => {
  if (!activeProposal.value?.operations) return []
  return activeProposal.value.operations
    .filter((op) => op.op === 'remove_member')
    .map((op) => op.id)
})

// SVG Canvas ViewBox & Coordinates
const canvasSvg = computed(() => {
  if (!displayModel.value || !displayModel.value.nodes || displayModel.value.nodes.length === 0) return null
  const nodes = displayModel.value.nodes
  const members = displayModel.value.members || []

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  nodes.forEach((n) => {
    if (n.x < minX) minX = n.x
    if (n.x > maxX) maxX = n.x
    if (n.y < minY) minY = n.y
    if (n.y > maxY) maxY = n.y
  })

  const spanX = Math.max(2, maxX - minX)
  const spanY = Math.max(2, maxY - minY)
  const pad = Math.max(spanX, spanY) * 0.2

  const vx = minX - pad
  const vy = -(maxY + pad)
  const vw = spanX + pad * 2
  const vh = spanY + pad * 2

  const nodeMap = {}
  nodes.forEach((n) => { nodeMap[n.id] = n })

  return {
    viewBox: `${vx} ${vy} ${vw} ${vh}`,
    nodes,
    members,
    supports: displayModel.value.supports || [],
    loads: displayModel.value.loads || [],
    nodeMap,
    span: (maxX - minX).toFixed(2),
    height: (maxY - minY).toFixed(2),
  }
})
</script>

<template>
  <div class="design-studio-page">
    <!-- Studio Header -->
    <header class="studio-header">
      <div class="header-titles">
        <div class="eyebrow">CONVERSATIONAL TRUSS WORKBENCH</div>
        <h1>Natural Language Design Studio</h1>
        <p>Synthesize new structural geometries, modify canvas snapshots, and inspect determinacy using deterministic engineering rules.</p>
      </div>

      <!-- Action Actions & Model Selector -->
      <div class="header-controls">
        <div class="analysis-select-group">
          <label for="analysis-select">Target Structure:</label>
          <select
            id="analysis-select"
            v-model="selectedAnalysisId"
            class="analysis-select"
            :disabled="busy || loading"
          >
            <option value="">＋ New Truss Design (Blank Canvas)</option>
            <option
              v-for="item in savedAnalyses"
              :key="item.analysis_id"
              :value="item.analysis_id"
            >
              {{ item.original_filename || `Analysis #${item.analysis_id.slice(0, 8)}` }} ({{ item.status }})
            </option>
          </select>
        </div>

        <button
          v-if="selectedAnalysisId"
          class="btn-open-editor"
          type="button"
          @click="emit('editor', selectedAnalysisId)"
        >
          <ExternalLink :size="13" /> Open in Editor
        </button>
      </div>
    </header>

    <!-- Toast Notification -->
    <div v-if="toastMessage" class="studio-toast" :class="toastVariant">
      <span>{{ toastMessage }}</span>
    </div>

    <!-- Main Workspace: Split Pane -->
    <div class="studio-workspace">
      <!-- Left Column: Design Controls & Prompts -->
      <section class="studio-left-pane">
        <DesignInstructionPanel
          :analysis-id="selectedAnalysisId"
          :model-revision="modelRevision"
          :proposal="activeProposal"
          :busy="busy || loading"
          :error="error"
          @submit="handleDesignSubmit"
          @apply="handleApplyProposal"
          @reject="handleRejectProposal"
          @clear-error="error = ''"
        />

        <!-- Engineering Guidance Card -->
        <div class="engineering-guidance-card">
          <div class="guidance-header">
            <Compass :size="14" />
            <strong>CAD Design Conventions</strong>
          </div>
          <ul class="guidance-list">
            <li><strong>CREATE:</strong> Specify span, height, panel count, and support conditions (e.g. <em>"Warren truss, 6 m span, 4 panels"</em>).</li>
            <li><strong>MODIFY:</strong> Reference existing joint/member IDs (e.g. <em>"Add diagonal between J1 and J3"</em>, <em>"Move J2 up 0.5 m"</em>).</li>
            <li><strong>EXPLAIN:</strong> Ask about determinacy, stability, or support reactions (e.g. <em>"Why is this unstable?"</em>).</li>
            <li><strong>SAFETY GATE:</strong> AI proposals are strictly non-destructive previews until explicitly approved.</li>
          </ul>
        </div>
      </section>

      <!-- Right Column: Live Vector Canvas Preview -->
      <section class="studio-right-pane">
        <div class="canvas-header">
          <div class="canvas-title">
            <span class="live-dot"></span>
            <strong>Structural Geometry Preview</strong>
            <span v-if="activeProposal" class="preview-badge">
              Previewing Proposal #{{ activeProposal.proposal_id?.slice(0, 6) }}
            </span>
          </div>

          <div v-if="canvasSvg" class="canvas-meta">
            <span>Span: <strong>{{ canvasSvg.span }} m</strong></span>
            <span>Height: <strong>{{ canvasSvg.height }} m</strong></span>
            <span>Joints: <strong>{{ canvasSvg.nodes.length }}</strong></span>
            <span>Members: <strong>{{ canvasSvg.members.length }}</strong></span>
          </div>
        </div>

        <!-- SVG Canvas Viewer -->
        <div class="canvas-viewport">
          <div v-if="loading" class="canvas-loading">
            <Loader2 :size="24" class="spin-icon" />
            <span>Loading structural geometry…</span>
          </div>

          <div v-else-if="!canvasSvg" class="canvas-empty">
            <div class="empty-icon"><Compass :size="36" /></div>
            <strong>Ready to Design</strong>
            <p>Type a prompt on the left to synthesize a new truss structure, or select an existing analysis above.</p>
          </div>

          <svg
            v-else
            class="cad-svg"
            :viewBox="canvasSvg.viewBox"
            preserveAspectRatio="xMidYMid meet"
          >
            <!-- Background Grid (Visual CAD Feel) -->
            <defs>
              <pattern id="cad-grid" width="1" height="1" patternUnits="userSpaceOnUse">
                <path d="M 1 0 L 0 0 0 1" fill="none" stroke="#ede9df" stroke-width="0.04" />
              </pattern>
            </defs>
            <rect :x="-50" :y="-50" width="100" height="100" fill="url(#cad-grid)" />

            <!-- Existing Members -->
            <g class="cad-members-group">
              <line
                v-for="m in canvasSvg.members"
                :key="m.id"
                :x1="canvasSvg.nodeMap[m.node_i]?.x ?? 0"
                :y1="-(canvasSvg.nodeMap[m.node_i]?.y ?? 0)"
                :x2="canvasSvg.nodeMap[m.node_j]?.x ?? 0"
                :y2="-(canvasSvg.nodeMap[m.node_j]?.y ?? 0)"
                :class="['cad-member', { 'proposed-removal': proposedRemovals.includes(m.id) }]"
              />
            </g>

            <!-- Proposed Added Members (Dashed Cyan) -->
            <g class="cad-proposed-additions">
              <line
                v-for="(op, idx) in proposedAdditions"
                :key="`prop-add-${idx}`"
                :x1="canvasSvg.nodeMap[op.node_i]?.x ?? 0"
                :y1="-(canvasSvg.nodeMap[op.node_i]?.y ?? 0)"
                :x2="canvasSvg.nodeMap[op.node_j]?.x ?? 0"
                :y2="-(canvasSvg.nodeMap[op.node_j]?.y ?? 0)"
                class="cad-member proposed-addition"
              />
            </g>

            <!-- Supports -->
            <g class="cad-supports-group">
              <polygon
                v-for="s in canvasSvg.supports"
                :key="s.id"
                :points="`${(canvasSvg.nodeMap[s.node]?.x ?? 0) - 0.28},${-(canvasSvg.nodeMap[s.node]?.y ?? 0) + 0.4} ${(canvasSvg.nodeMap[s.node]?.x ?? 0) + 0.28},${-(canvasSvg.nodeMap[s.node]?.y ?? 0) + 0.4} ${(canvasSvg.nodeMap[s.node]?.x ?? 0)},${-(canvasSvg.nodeMap[s.node]?.y ?? 0)}`"
                class="cad-support"
                :class="s.type"
              />
            </g>

            <!-- Loads (Downward Arrows) -->
            <g class="cad-loads-group">
              <g
                v-for="l in canvasSvg.loads"
                :key="l.id"
                :transform="`translate(${canvasSvg.nodeMap[l.node]?.x ?? 0}, ${-(canvasSvg.nodeMap[l.node]?.y ?? 0)})`"
              >
                <line x1="0" y1="-0.9" x2="0" y2="0" stroke="#ef4444" stroke-width="0.1" />
                <polygon points="-0.15,-0.25 0.15,-0.25 0,0" fill="#ef4444" />
                <text x="0.25" y="-0.5" font-size="0.32" fill="#ef4444" font-family="monospace">
                  {{ l.fy }} kN
                </text>
              </g>
            </g>

            <!-- Joints -->
            <g class="cad-joints-group">
              <g
                v-for="n in canvasSvg.nodes"
                :key="n.id"
                :transform="`translate(${n.x}, ${-n.y})`"
              >
                <circle cx="0" cy="0" r="0.18" class="cad-joint" />
                <text x="0.25" y="-0.22" font-size="0.3" class="joint-label">
                  {{ n.id }}
                </text>
              </g>
            </g>
          </svg>

          <!-- Legend Bar -->
          <div class="canvas-legend">
            <span class="legend-item"><span class="legend-swatch normal"></span> Existing Member</span>
            <span class="legend-item"><span class="legend-swatch added"></span> Proposed Addition</span>
            <span class="legend-item"><span class="legend-swatch removal"></span> Proposed Deletion</span>
            <span class="legend-item"><span class="legend-swatch support"></span> Support Constraint</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.design-studio-page {
  padding: 24px clamp(20px, 3vw, 40px);
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: calc(100vh - 80px);
}

/* Header */
.studio-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  padding-bottom: 18px;
  border-bottom: 1px solid #eee8d8;
}

.header-titles .eyebrow {
  font: 700 9px var(--mono, monospace);
  color: #8c8f82;
  letter-spacing: 1px;
}

.header-titles h1 {
  margin: 3px 0 6px;
  font-size: clamp(24px, 2.5vw, 32px);
  color: #292a28;
  letter-spacing: -1px;
}

.header-titles p {
  margin: 0;
  max-width: 580px;
  color: #66695e;
  font-size: 12px;
  line-height: 1.55;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.analysis-select-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.analysis-select-group label {
  font: 700 9px var(--mono, monospace);
  color: #828579;
  text-transform: uppercase;
}

.analysis-select {
  min-height: 34px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid #d5d0c2;
  background: #fff;
  font-size: 11px;
  color: #292a28;
  outline: none;
  cursor: pointer;
}

.btn-open-editor {
  align-self: flex-end;
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid #292a28;
  background: #292a28;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-open-editor:hover {
  background: #42453e;
}

/* Toast */
.studio-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.studio-toast.info {
  background: #292a28;
  color: #fff;
}

.studio-toast.success {
  background: #047857;
  color: #fff;
}

/* Workspace Layout */
.studio-workspace {
  display: grid;
  grid-template-columns: minmax(360px, 440px) 1fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 960px) {
  .studio-workspace {
    grid-template-columns: 1fr;
  }
}

/* Left Pane */
.studio-left-pane {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.engineering-guidance-card {
  background: #fbf9f4;
  border: 1px solid #ece7d8;
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 11px;
}

.guidance-header {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #63665a;
  margin-bottom: 8px;
}

.guidance-list {
  margin: 0;
  padding-left: 16px;
  color: #55584d;
  display: flex;
  flex-direction: column;
  gap: 5px;
  line-height: 1.45;
}

/* Right Pane */
.studio-right-pane {
  background: #fff;
  border: 1px solid #e5e0d2;
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 3px 12px rgba(41, 42, 40, 0.04);
}

.canvas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #faf8f3;
  border-bottom: 1px solid #eae5d7;
}

.canvas-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #10b981;
}

.preview-badge {
  background: #e0f2fe;
  color: #0369a1;
  font: 700 9px var(--mono, monospace);
  padding: 2px 6px;
  border-radius: 4px;
}

.canvas-meta {
  display: flex;
  gap: 12px;
  font: 10px var(--mono, monospace);
  color: #797c71;
}

.canvas-viewport {
  height: 520px;
  background: #fffefb;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.cad-svg {
  width: 100%;
  height: 100%;
}

.cad-member {
  stroke: #292a28;
  stroke-width: 0.12;
  stroke-linecap: round;
}

.cad-member.proposed-addition {
  stroke: #0284c7;
  stroke-width: 0.14;
  stroke-dasharray: 0.35, 0.15;
}

.cad-member.proposed-removal {
  stroke: #ef4444;
  stroke-width: 0.12;
  stroke-dasharray: 0.2, 0.15;
  opacity: 0.75;
}

.cad-joint {
  fill: #f4dc68;
  stroke: #292a28;
  stroke-width: 0.06;
}

.joint-label {
  font-family: var(--mono, monospace);
  font-weight: 700;
  fill: #3e4139;
}

.cad-support {
  fill: #606859;
}

.canvas-legend {
  position: absolute;
  bottom: 12px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
  padding: 5px 12px;
  border-radius: 8px;
  border: 1px solid #eae5d7;
  font-size: 10px;
  color: #55584e;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.legend-swatch {
  width: 12px;
  height: 3px;
  border-radius: 2px;
}

.legend-swatch.normal { background: #292a28; }
.legend-swatch.added { background: #0284c7; border-top: 1px dashed #0284c7; }
.legend-swatch.removal { background: #ef4444; }
.legend-swatch.support { width: 8px; height: 8px; background: #606859; border-radius: 1px; }

.canvas-loading, .canvas-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #8b8e82;
  font-size: 12px;
}

.canvas-empty p {
  margin: 0;
  max-width: 320px;
  text-align: center;
  font-size: 11px;
}

.empty-icon {
  color: #c0bcae;
}

.spin-icon {
  animation: spin 1s linear infinite;
}
</style>
