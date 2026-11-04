<script setup>
import { computed } from 'vue'
import {
  Check,
  X,
  Sparkles,
  Layers,
  ArrowRight,
  AlertTriangle,
  HelpCircle,
  Hash,
  ShieldAlert,
  ShieldCheck,
  FileText,
  Activity,
  PlusCircle,
  Trash2,
  Edit3,
} from 'lucide-vue-next'

const props = defineProps({
  proposal: {
    type: Object,
    required: true,
  },
  compact: {
    type: Boolean,
    default: false,
  },
  isBusy: {
    type: Boolean,
    default: false,
  },
  canApply: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['apply', 'reject', 'select-clarification'])

const intent = computed(() => (props.proposal?.intent || 'modify').toUpperCase())
const isExplain = computed(() => intent.value === 'EXPLAIN')
const isCreate = computed(() => intent.value === 'CREATE')
const isModify = computed(() => intent.value === 'MODIFY')

const isValid = computed(() => props.proposal?.validation?.is_valid !== false)
const diagnostics = computed(() => props.proposal?.predicted_diagnostics || null)
const status = computed(() => props.proposal?.status || 'proposed')
const operations = computed(() => props.proposal?.operations || [])
const affectedElements = computed(() => props.proposal?.affected_elements || { nodes: [], members: [], supports: [], loads: [] })
const clarificationQuestions = computed(() => props.proposal?.clarification_questions || [])
const model = computed(() => props.proposal?.proposed_model?.model || null)

const modelStats = computed(() => {
  if (!model.value) return null
  const nodes = model.value.nodes || []
  const members = model.value.members || []
  const supports = model.value.supports || []
  const loads = model.value.loads || []

  let minX = 0, maxX = 0, minY = 0, maxY = 0
  if (nodes.length > 0) {
    minX = Math.min(...nodes.map((n) => n.x))
    maxX = Math.max(...nodes.map((n) => n.x))
    minY = Math.min(...nodes.map((n) => n.y))
    maxY = Math.max(...nodes.map((n) => n.y))
  }

  const units = props.proposal?.proposed_model?.metadata?.units || { length: 'm', force: 'kN' }

  return {
    nodeCount: nodes.length,
    memberCount: members.length,
    supportCount: supports.length,
    loadCount: loads.length,
    span: (maxX - minX).toFixed(2),
    height: (maxY - minY).toFixed(2),
    units,
  }
})

// Mini SVG preview bounds
const previewSvg = computed(() => {
  if (!model.value || !model.value.nodes || model.value.nodes.length === 0) return null
  const nodes = model.value.nodes
  const members = model.value.members || []

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  nodes.forEach((n) => {
    if (n.x < minX) minX = n.x
    if (n.x > maxX) maxX = n.x
    if (n.y < minY) minY = n.y
    if (n.y > maxY) maxY = n.y
  })

  const spanX = Math.max(1, maxX - minX)
  const spanY = Math.max(1, maxY - minY)
  const pad = Math.max(spanX, spanY) * 0.15

  const vx = minX - pad
  const vy = minY - pad
  const vw = spanX + pad * 2
  const vh = spanY + pad * 2

  const nodeMap = {}
  nodes.forEach((n) => { nodeMap[n.id] = n })

  return {
    viewBox: `${vx} ${vy} ${vw} ${vh}`,
    nodes,
    members,
    supports: model.value.supports || [],
    loads: model.value.loads || [],
    nodeMap,
    minY,
    maxY,
  }
})

function opIcon(opType) {
  if (opType.startsWith('add_')) return PlusCircle
  if (opType.startsWith('remove_')) return Trash2
  return Edit3
}

function opBadgeClass(opType) {
  if (opType.startsWith('add_')) return 'op-add'
  if (opType.startsWith('remove_')) return 'op-remove'
  return 'op-update'
}

function formatOpText(op) {
  if (op.op === 'add_member') return `Add Member ${op.id} (${op.node_i} ↔ ${op.node_j})`
  if (op.op === 'remove_member') return `Remove Member ${op.id}`
  if (op.op === 'add_joint') return `Add Joint ${op.id} (${op.x}, ${op.y})`
  if (op.op === 'update_joint') {
    if (op.dy !== undefined || op.dx !== undefined) {
      const parts = []
      if (op.dx) parts.push(`dx: ${op.dx > 0 ? '+' : ''}${op.dx}`)
      if (op.dy) parts.push(`dy: ${op.dy > 0 ? '+' : ''}${op.dy}`)
      return `Move Joint ${op.id} (${parts.join(', ')})`
    }
    return `Move Joint ${op.id} to (${op.x}, ${op.y})`
  }
  if (op.op === 'remove_joint') return `Remove Joint ${op.id}`
  if (op.op === 'add_support') return `Add ${op.type} support at ${op.node}`
  if (op.op === 'update_support') return `Update support ${op.id} at ${op.node} to ${op.type}`
  if (op.op === 'remove_support') return `Remove support ${op.id}`
  if (op.op === 'add_load') return `Apply load ${op.id} at ${op.node} (${op.fy} ${modelStats.value?.units?.force || 'kN'})`
  if (op.op === 'update_load') return `Update load ${op.id} (${op.fy} ${modelStats.value?.units?.force || 'kN'})`
  if (op.op === 'remove_load') return `Remove load ${op.id}`
  return `${op.op}: ${op.id || ''}`
}
</script>

<template>
  <div
    class="design-proposal-card"
    :class="[
      `intent-${intent.toLowerCase()}`,
      `status-${status.toLowerCase()}`,
      { compact, invalid: !isValid }
    ]"
  >
    <!-- Top Bar: Technical Metadata -->
    <header class="card-header">
      <div class="header-left">
        <span class="intent-pill">
          <Sparkles v-if="isCreate" :size="12" />
          <Layers v-else-if="isModify" :size="12" />
          <Activity v-else :size="12" />
          {{ intent }}
        </span>
        <span v-if="proposal.proposal_id" class="proposal-id" :title="`Proposal ID: ${proposal.proposal_id}`">
          #{{ proposal.proposal_id.slice(0, 8) }}
        </span>
        <span v-if="proposal.base_revision !== undefined" class="revision-pill">
          rev {{ proposal.base_revision }}
          <ArrowRight :size="10" />
          rev {{ proposal.base_revision + 1 }}
        </span>
      </div>

      <div class="header-right">
        <span v-if="isValid" class="validation-pill valid">
          <ShieldCheck :size="12" /> Valid
        </span>
        <span v-else class="validation-pill invalid">
          <ShieldAlert :size="12" /> Invalid
        </span>
      </div>
    </header>

    <!-- Structural Explanation -->
    <div class="card-explanation">
      <p>{{ proposal.explanation || 'Design proposal formulated.' }}</p>
    </div>

    <!-- Clarification Needed Notice (if any) -->
    <div v-if="clarificationQuestions.length > 0" class="clarification-section">
      <div class="clarification-header">
        <HelpCircle :size="14" />
        <strong>Specification Details Needed</strong>
      </div>
      <div class="clarification-list">
        <div
          v-for="(cq, idx) in clarificationQuestions"
          :key="idx"
          class="clarification-item"
        >
          <div class="cq-prompt">{{ cq.question || cq.prompt || 'Specification Details Needed:' }}</div>
          <div v-if="cq.options?.length" class="cq-options">
            <button
              v-for="(opt, optIdx) in cq.options"
              :key="optIdx"
              type="button"
              class="cq-chip"
              @click="emit('select-clarification', { question: cq, answer: opt })"
            >
              {{ opt }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Proposed Operations Breakdown (for MODIFY) -->
    <div v-if="isModify && operations.length > 0" class="operations-section">
      <div class="section-label">Proposed Topology Changes ({{ operations.length }})</div>
      <div class="operations-grid">
        <div
          v-for="(op, idx) in operations"
          :key="idx"
          class="op-card"
          :class="opBadgeClass(op.op)"
        >
          <component :is="opIcon(op.op)" :size="13" class="op-icon" />
          <span class="op-label">{{ formatOpText(op) }}</span>
        </div>
      </div>
    </div>

    <!-- Mini Wireframe Preview (for CREATE or when viewing isolated geometry) -->
    <div v-if="previewSvg && (isCreate || (!compact && isModify))" class="mini-preview-container">
      <div class="section-label">Topology Preview</div>
      <div class="mini-preview-frame">
        <svg
          class="mini-preview-svg"
          :viewBox="previewSvg.viewBox"
          preserveAspectRatio="xMidYMid meet"
        >
          <g transform="scale(1, -1)">
            <!-- Members -->
            <line
              v-for="m in previewSvg.members"
              :key="m.id"
              :x1="previewSvg.nodeMap[m.node_i]?.x ?? 0"
              :y1="-(previewSvg.nodeMap[m.node_i]?.y ?? 0)"
              :x2="previewSvg.nodeMap[m.node_j]?.x ?? 0"
              :y2="-(previewSvg.nodeMap[m.node_j]?.y ?? 0)"
              stroke="#0284c7"
              stroke-width="0.12"
              stroke-linecap="round"
            />
            <!-- Joints -->
            <circle
              v-for="n in previewSvg.nodes"
              :key="n.id"
              :cx="n.x"
              :cy="-n.y"
              r="0.18"
              fill="#292a28"
            />
            <!-- Supports -->
            <polygon
              v-for="s in previewSvg.supports"
              :key="s.id"
              :points="`${(previewSvg.nodeMap[s.node]?.x ?? 0) - 0.25},${-(previewSvg.nodeMap[s.node]?.y ?? 0) - 0.35} ${(previewSvg.nodeMap[s.node]?.x ?? 0) + 0.25},${-(previewSvg.nodeMap[s.node]?.y ?? 0) - 0.35} ${(previewSvg.nodeMap[s.node]?.x ?? 0)},${-(previewSvg.nodeMap[s.node]?.y ?? 0)}`"
              fill="#7c8a74"
            />
          </g>
        </svg>
      </div>
    </div>

    <!-- Model Technical Metrics -->
    <div v-if="modelStats" class="metrics-grid">
      <div class="metric-item">
        <span class="metric-num">{{ modelStats.nodeCount }}</span>
        <span class="metric-name">Joints</span>
      </div>
      <div class="metric-item">
        <span class="metric-num">{{ modelStats.memberCount }}</span>
        <span class="metric-name">Members</span>
      </div>
      <div class="metric-item">
        <span class="metric-num">{{ modelStats.supportCount }}</span>
        <span class="metric-name">Supports</span>
      </div>
      <div class="metric-item">
        <span class="metric-num">{{ modelStats.loadCount }}</span>
        <span class="metric-name">Loads</span>
      </div>
      <div class="metric-item">
        <span class="metric-num">{{ modelStats.span }} {{ modelStats.units.length }}</span>
        <span class="metric-name">Span</span>
      </div>
      <div class="metric-item">
        <span class="metric-num">{{ modelStats.height }} {{ modelStats.units.length }}</span>
        <span class="metric-name">Height</span>
      </div>
    </div>

    <!-- Predicted Diagnostics / Solvability -->
    <div v-if="diagnostics" class="diagnostics-bar">
      <div class="diagnostics-status" :class="diagnostics.status">
        <span class="status-indicator"></span>
        <span class="status-text">
          Predicted: <strong>{{ diagnostics.category || diagnostics.status }}</strong>
          ({{ diagnostics.equation_count }} eq vs {{ diagnostics.unknown_count }} unk)
        </span>
      </div>
    </div>

    <!-- Action Buttons (Human-in-the-loop Gate) -->
    <div v-if="!isExplain" class="card-actions">
      <button
        class="btn-discard"
        type="button"
        :disabled="isBusy"
        @click="emit('reject', proposal)"
      >
        <X :size="13" /> Discard
      </button>

      <button
        class="btn-apply"
        type="button"
        :disabled="!isValid || isBusy || !canApply"
        :title="!isValid ? 'Cannot apply invalid proposal' : 'Apply proposed structural changes'"
        @click="emit('apply', proposal)"
      >
        <Check :size="14" />
        {{ isCreate ? 'Apply & Open Editor' : 'Apply Changes' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.design-proposal-card {
  background: #fffef9;
  border: 1px solid #e5e0d4;
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 4px 16px rgba(41, 42, 40, 0.04);
  font-family: inherit;
  color: #292a28;
}

.design-proposal-card.compact {
  padding: 10px 12px;
  gap: 9px;
}

.design-proposal-card.invalid {
  border-color: #fca5a5;
  background: #fffafa;
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0ece1;
  padding-bottom: 8px;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.intent-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #f4efe4;
  color: #3f423b;
  font: 700 10px var(--mono, monospace);
  padding: 2px 7px;
  border-radius: 6px;
  letter-spacing: 0.5px;
}

.intent-create .intent-pill { background: #e0f2fe; color: #0369a1; }
.intent-modify .intent-pill { background: #fef3c7; color: #b45309; }
.intent-explain .intent-pill { background: #ede9fe; color: #6d28d9; }

.proposal-id {
  font: 9px var(--mono, monospace);
  color: #8b8e83;
}

.revision-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: 9px var(--mono, monospace);
  color: #696b63;
  background: #f7f5ed;
  padding: 2px 6px;
  border-radius: 4px;
}

.validation-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 999px;
}

.validation-pill.valid {
  background: #ecfdf5;
  color: #047857;
}

.validation-pill.invalid {
  background: #fef2f2;
  color: #b91c1c;
}

/* Explanation */
.card-explanation p {
  margin: 0;
  font-size: 12px;
  line-height: 1.55;
  color: #3b3d37;
}

/* Clarification */
.clarification-section {
  background: #fefce8;
  border: 1px solid #fef08a;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.clarification-header {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #a16207;
  font-size: 11px;
}

.clarification-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cq-prompt {
  font-size: 11px;
  color: #4b4d45;
}

.cq-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.cq-chip {
  background: #fff;
  border: 1px solid #eab308;
  color: #854d0e;
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.cq-chip:hover {
  background: #fef9c3;
}

/* Operations */
.section-label {
  font: 700 9px var(--mono, monospace);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #888b80;
  margin-bottom: 5px;
}

.operations-grid {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.op-card {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 9px;
  border-radius: 6px;
  font-size: 11px;
  background: #f7f6f0;
  border: 1px solid #eae7dc;
}

.op-card.op-add {
  background: #f0f9ff;
  border-color: #bae6fd;
  color: #0369a1;
}

.op-card.op-remove {
  background: #fef2f2;
  border-color: #fecaca;
  color: #b91c1c;
}

.op-card.op-update {
  background: #fffbeb;
  border-color: #fde68a;
  color: #b45309;
}

/* Mini Preview */
.mini-preview-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mini-preview-frame {
  height: 120px;
  background: #faf8f3;
  border: 1px solid #eae5d7;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 8px;
}

.mini-preview-svg {
  width: 100%;
  height: 100%;
}

/* Metrics */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
  background: #f8f6f0;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #eae6db;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.metric-num {
  font: 700 12px var(--mono, monospace);
  color: #292a28;
}

.metric-name {
  font: 9px var(--mono, monospace);
  color: #85877c;
  text-transform: uppercase;
}

/* Diagnostics */
.diagnostics-bar {
  background: #f5f4ed;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 11px;
}

.diagnostics-status {
  display: flex;
  align-items: center;
  gap: 7px;
}

.status-indicator {
  width: 7px;
  height: 7px;
  border-radius: 999px;
}

.diagnostics-status.solvable .status-indicator { background: #10b981; }
.diagnostics-status.unsolvable .status-indicator { background: #ef4444; }
.diagnostics-status.incomplete .status-indicator { background: #f59e0b; }

/* Actions */
.card-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
  border-top: 1px solid #f0ece1;
  padding-top: 10px;
}

.btn-discard {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #d5d1c4;
  background: #fff;
  color: #61645c;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-discard:hover:not(:disabled) {
  background: #f8f6f1;
  color: #292a28;
}

.btn-apply {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #292a28;
  background: #292a28;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-apply:hover:not(:disabled) {
  background: #42453e;
}

.btn-apply:disabled, .btn-discard:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
