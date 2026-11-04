<script setup>
import { ref, computed, watch } from 'vue'
import {
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  Check,
  X,
  Loader2,
  Info,
  Wrench,
  HelpCircle,
  Eye,
  EyeOff,
  Maximize2,
} from 'lucide-vue-next'
import { resolveGeometryIssue } from '../api/analyses'

const props = defineProps({
  issues: {
    type: Array,
    default: () => [],
  },
  selectedIssueId: {
    type: String,
    default: null,
  },
  anchorPosition: {
    type: Object,
    default: null, // { x: number, y: number } in canvas screen coordinates
  },
  geometry: {
    type: Object,
    required: true,
  },
  diagnostics: {
    type: Object,
    default: () => ({}),
  },
  modelRevision: {
    type: Number,
    default: 1,
  },
  busy: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'apply-fix',
  'select-issue',
  'clear-highlight',
  'preview-fix',
  'clear-preview',
])

const isDismissed = ref(false)
const isExpanded = ref(false)
const resolving = ref(false)
const resolution = ref(null)
const selectedFixIndex = ref(0)
const resolveError = ref('')
let requestSeq = 0

const hasIssues = computed(() => props.issues && props.issues.length > 0)
const totalIssues = computed(() => props.issues.length)

const currentIndex = computed(() => {
  if (!props.selectedIssueId || !hasIssues.value) return 0
  const idx = props.issues.findIndex((i) => i.id === props.selectedIssueId)
  return idx >= 0 ? idx : 0
})

const activeIssue = computed(() => {
  if (!hasIssues.value) return null
  return props.issues[currentIndex.value] || props.issues[0]
})

// Reset resolution state and invalidate in-flight request when active issue changes
watch(
  () => activeIssue.value?.id,
  () => {
    ++requestSeq
    resolving.value = false
    resolution.value = null
    resolveError.value = ''
    selectedFixIndex.value = 0
    emit('clear-preview')
  }
)

function prevIssue() {
  if (currentIndex.value > 0) {
    const prev = props.issues[currentIndex.value - 1]
    if (prev) emit('select-issue', prev)
  }
}

function nextIssue() {
  if (currentIndex.value < totalIssues.value - 1) {
    const next = props.issues[currentIndex.value + 1]
    if (next) emit('select-issue', next)
  }
}

function clearHighlight() {
  ++requestSeq
  resolving.value = false
  emit('clear-highlight')
  emit('clear-preview')
  resolution.value = null
  resolveError.value = ''
}

function toggleDismiss() {
  isDismissed.value = !isDismissed.value
  if (isDismissed.value) {
    emit('clear-preview')
  } else if (activeIssue.value) {
    emit('select-issue', activeIssue.value)
  }
}

async function handleResolveWithAi() {
  if (!activeIssue.value || resolving.value) return
  const seq = ++requestSeq
  resolving.value = true
  resolveError.value = ''
  resolution.value = null
  selectedFixIndex.value = 0

  try {
    const issuePayload = {
      code: activeIssue.value.code || 'UNKNOWN_ISSUE',
      title: activeIssue.value.title || 'Structural Issue',
      message: activeIssue.value.message || activeIssue.value.summary || '',
      element_id: activeIssue.value.element_id || '',
      path: activeIssue.value.path || '',
      severity: activeIssue.value.severity || 'warning',
      classification: activeIssue.value.classification || 'general',
      affected_elements: activeIssue.value.affected_elements || {},
    }

    const result = await resolveGeometryIssue(
      props.geometry,
      issuePayload,
      props.diagnostics
    )
    if (seq !== requestSeq) return // Stale request, ignore

    result.base_revision = props.modelRevision
    for (const f of result.proposed_fixes || []) {
      f.base_revision = props.modelRevision
      f.proposal_id = result.resolution_id || `fix-${Date.now()}`
    }
    resolution.value = result
    if (result.proposed_fixes && result.proposed_fixes.length > 0) {
      selectedFixIndex.value = 0
      emit('preview-fix', result.proposed_fixes[0])
    }
  } catch (err) {
    if (seq === requestSeq) {
      resolveError.value = err.message || 'AI resolution could not be completed.'
    }
  } finally {
    if (seq === requestSeq) {
      resolving.value = false
    }
  }
}

function selectFix(index) {
  selectedFixIndex.value = index
  if (resolution.value?.proposed_fixes?.[index]) {
    emit('preview-fix', resolution.value.proposed_fixes[index])
  }
}

function handleApplyFix() {
  const fix = resolution.value?.proposed_fixes?.[selectedFixIndex.value]
  if (!fix) return
  if (fix.base_revision != null && props.modelRevision !== fix.base_revision) {
    resolveError.value = 'Proposal is stale: The canvas model was modified after this fix was proposed. Please request a fresh fix.'
    resolution.value = null
    emit('clear-preview')
    return
  }
  emit('apply-fix', fix)
  resolution.value = null
  emit('clear-preview')
}

function handleCancelFix() {
  ++requestSeq
  resolving.value = false
  resolution.value = null
  resolveError.value = ''
  emit('clear-preview')
}

function classificationLabel(classification, severity) {
  if (classification === 'mechanism') return 'Mechanism'
  if (classification === 'disconnected_geometry') return 'Disconnected Geometry'
  if (classification === 'invalid_geometry') return 'Invalid Geometry'
  if (classification === 'underconstrained_system') return 'Under-constrained'
  if (classification === 'statically_indeterminate') return 'Statically Indeterminate'
  if (classification === 'high_axial_force') return 'High Axial Force'
  return severity === 'error' ? 'Error' : 'Warning'
}

function badgeClass(classification, severity) {
  if (severity === 'error' || classification === 'invalid_geometry') return 'badge-danger'
  if (classification === 'mechanism' || severity === 'mechanism') return 'badge-mechanism'
  return 'badge-warning'
}

const scrollContainer = ref(null)

function handleCardWheel(e) {
  // Prevent canvas zoom by stopping event propagation, while allowing
  // the card's own scrollable content to receive the wheel event.
  e.stopPropagation()
}

// Compute dynamic card placement styles in bottom-right region of canvas (non-obstructing)
const cardPositionStyle = computed(() => {
  return {
    position: 'absolute',
    right: '16px',
    bottom: '90px',
    maxHeight: 'min(480px, calc(100% - 110px))',
    maxWidth: 'min(360px, calc(100% - 32px))',
  }
})
</script>

<template>
  <div v-if="hasIssues" class="contextual-issue-wrapper">
    <!-- Minimized Pill Badge (when dismissed) -->
    <div
      v-if="isDismissed"
      class="assistant-minimized-pill"
      @click.stop="toggleDismiss"
      @pointerdown.stop
      @wheel.stop="handleCardWheel"
    >
      <span class="pill-sparkle"><Sparkles :size="13" /></span>
      <span class="pill-count">{{ totalIssues }} Issue{{ totalIssues > 1 ? 's' : '' }} detected</span>
      <span class="pill-action">Fix with AI</span>
    </div>

    <!-- Active Floating Contextual Action Card -->
    <section
      v-else-if="activeIssue"
      class="contextual-action-card"
      :style="cardPositionStyle"
      aria-label="Contextual Issue Resolution"
      @wheel.stop="handleCardWheel"
      @pointerdown.stop
      @pointermove.stop
      @pointerup.stop
      @mousedown.stop
      @click.stop
    >
      <!-- Card Header: Fixed/Sticky at top -->
      <header class="card-header" @wheel.stop="handleCardWheel">
        <div class="header-left">
          <span :class="['classification-pill', badgeClass(activeIssue.classification, activeIssue.severity)]">
            <XCircle v-if="activeIssue.severity === 'error' || activeIssue.classification === 'invalid_geometry'" :size="11" />
            <AlertTriangle v-else :size="11" />
            {{ classificationLabel(activeIssue.classification, activeIssue.severity) }}
          </span>
          <span v-if="totalIssues > 1" class="issue-step-counter">
            {{ currentIndex + 1 }} / {{ totalIssues }}
          </span>
        </div>

        <div class="header-controls">
          <div v-if="totalIssues > 1" class="nav-cluster">
            <button
              class="icon-btn"
              type="button"
              title="Previous issue"
              :disabled="currentIndex === 0"
              @click.stop="prevIssue"
            >
              <ChevronLeft :size="13" />
            </button>
            <button
              class="icon-btn"
              type="button"
              title="Next issue"
              :disabled="currentIndex === totalIssues - 1"
              @click.stop="nextIssue"
            >
              <ChevronRight :size="13" />
            </button>
          </div>

          <button
            class="icon-btn btn-clear-highlight"
            type="button"
            title="Clear issue highlighting"
            @click.stop="clearHighlight"
          >
            <EyeOff :size="12" />
          </button>

          <button
            class="icon-btn"
            type="button"
            title="Minimize"
            @click.stop="toggleDismiss"
          >
            <X :size="12" />
          </button>
        </div>
      </header>

      <!-- Card Body: Independently Scrollable Area -->
      <div
        class="card-body card-content-scroll"
        ref="scrollContainer"
        tabindex="0"
        @wheel.stop="handleCardWheel"
      >
        <div class="issue-headline">
          <strong class="headline-title">{{ activeIssue.title }}</strong>
        </div>

        <!-- 1–2 sentence explanation -->
        <p class="issue-short-explanation">
          {{ activeIssue.summary || activeIssue.message }}
        </p>

        <!-- Affected Element IDs Tags -->
        <div v-if="activeIssue.affected_elements" class="affected-pills-row">
          <span v-for="nodeId in activeIssue.affected_elements.nodes" :key="`af-n-${nodeId}`" class="elem-pill pill-node">
            Joint {{ nodeId }}
          </span>
          <span v-for="memId in activeIssue.affected_elements.members" :key="`af-m-${memId}`" class="elem-pill pill-member">
            Member {{ memId }}
          </span>
          <span v-for="supId in activeIssue.affected_elements.supports" :key="`af-s-${supId}`" class="elem-pill pill-support">
            Support {{ supId }}
          </span>
        </div>

        <!-- Uncertainty explanation when component-level localization -->
        <div v-if="activeIssue.localization_precision === 'component_level' || activeIssue.uncertainty_explanation" class="uncertainty-callout">
          <Info :size="12" class="callout-icon" />
          <span>{{ activeIssue.uncertainty_explanation || 'The mechanism is distributed across this component; the exact affected member cannot be uniquely isolated without panel bracing.' }}</span>
        </div>

        <!-- Technical Details Collapsible -->
        <div v-if="activeIssue.details" class="details-accordion">
          <button class="accordion-toggle" type="button" @click="isExpanded = !isExpanded">
            <span>Diagnostics info</span>
            <ChevronDown v-if="!isExpanded" :size="11" />
            <ChevronUp v-else :size="11" />
          </button>
          <div v-if="isExpanded" class="accordion-body">
            <p>{{ activeIssue.details }}</p>
            <p v-if="activeIssue.path" class="path-text">Path: <code>{{ activeIssue.path }}</code></p>
          </div>
        </div>

        <!-- AI Resolution Flow Display -->
        <div v-if="resolution" class="resolution-subpanel">
          <div class="subpanel-title">
            <Sparkles :size="12" class="sparkle-amber" />
            <span>Root Cause Explanation</span>
          </div>
          <p class="explanation-quote">{{ resolution.root_cause_explanation }}</p>

          <p v-if="resolution.engineering_rationale" class="rationale-note">
            {{ resolution.engineering_rationale }}
          </p>

          <!-- Proposed Corrections List -->
          <div v-if="resolution.proposed_fixes && resolution.proposed_fixes.length > 0" class="fixes-group">
            <span class="fixes-heading">Proposed Repair:</span>
            <div
              v-for="(fix, fIdx) in resolution.proposed_fixes"
              :key="fix.id || fIdx"
              :class="['fix-item', { active: selectedFixIndex === fIdx }]"
              @click="selectFix(fIdx)"
            >
              <div class="fix-item-top">
                <span class="fix-radio-dot" :class="{ selected: selectedFixIndex === fIdx }" />
                <strong class="fix-name">{{ fix.title }}</strong>
                <span v-if="fix.is_valid" class="badge-valid">Valid Schema</span>
                <span v-else class="badge-invalid">Schema Note</span>
              </div>
              <p class="fix-summary-text">{{ fix.description }}</p>

              <!-- Tags for what will change -->
              <div v-if="fix.affected_elements" class="change-tags">
                <span v-for="n in fix.affected_elements.nodes" :key="`fn-${n}`" class="elem-pill pill-node">
                  Joint {{ n }}
                </span>
                <span v-for="m in fix.affected_elements.members" :key="`fm-${m}`" class="elem-pill pill-member">
                  Member {{ m }}
                </span>
                <span v-for="s in fix.affected_elements.supports" :key="`fs-${s}`" class="elem-pill pill-support">
                  Support {{ s }}
                </span>
              </div>
            </div>
          </div>

          <!-- Alternatives List -->
          <div v-if="resolution.alternatives && resolution.alternatives.length > 0" class="alternatives-wrapper">
            <span class="alt-title">Alternative approaches:</span>
            <ul class="alt-bullet-list">
              <li v-for="(alt, aIdx) in resolution.alternatives" :key="`alt-${aIdx}`">
                {{ alt }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Sticky Action Footer: Always Visible and Reachable -->
      <footer class="card-footer" @wheel.stop="handleCardWheel">
        <!-- Action Approval Buttons when resolution exists and has fixes -->
        <div v-if="resolution && resolution.proposed_fixes && resolution.proposed_fixes.length > 0" class="action-approval-row">
          <button
            class="btn-apply-fix"
            type="button"
            :disabled="busy"
            @click.stop="handleApplyFix"
          >
            <Check :size="13" />
            <span>Apply Suggested Fix</span>
          </button>
          <button
            class="btn-cancel-fix"
            type="button"
            :disabled="busy"
            @click.stop="handleCancelFix"
          >
            Cancel
          </button>
        </div>

        <!-- Feedback when resolution exists but has NO proposed fixes -->
        <div v-else-if="resolution" class="no-fixes-feedback" style="display: flex; align-items: center; justify-content: space-between; gap: 8px; width: 100%;">
          <span style="font-size: 11px; color: #55625d;">No automated modifications proposed.</span>
          <div style="display: flex; gap: 6px;">
            <button class="btn-retry-resolve" type="button" @click.stop="handleResolveWithAi">Retry</button>
            <button class="btn-cancel-fix" type="button" @click.stop="handleCancelFix">Dismiss</button>
          </div>
        </div>

        <!-- Provider Error Feedback -->
        <div v-else-if="resolveError" class="resolve-error-banner">
          <AlertTriangle :size="12" />
          <span>{{ resolveError }}</span>
          <div style="display: flex; gap: 6px; margin-left: auto;">
            <button class="btn-retry-resolve" type="button" @click.stop="handleResolveWithAi">Retry</button>
            <button class="btn-cancel-fix" type="button" style="padding: 3px 8px; font-size: 10px;" @click.stop="handleCancelFix">Cancel</button>
          </div>
        </div>

        <!-- Primary Call to Action: Fix with AI -->
        <div v-else class="cta-row">
          <button
            class="btn-fix-ai"
            type="button"
            :disabled="resolving"
            @click.stop="handleResolveWithAi"
          >
            <Loader2 v-if="resolving" :size="13" class="spin-icon" />
            <Sparkles v-else :size="13" class="sparkle-amber" />
            <span>{{ resolving ? 'Analyzing with AI…' : 'Fix with AI' }}</span>
          </button>
        </div>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.contextual-issue-wrapper {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1200;
}

/* ─── Minimized Pill ─── */
.assistant-minimized-pill {
  pointer-events: auto;
  position: absolute;
  bottom: 90px;
  right: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: #fffef8;
  border: 1px solid #e9e5d7;
  border-radius: 999px;
  box-shadow: 0 4px 14px rgba(41, 43, 41, 0.08);
  font-size: 11px;
  font-weight: 600;
  color: #252b2c;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.assistant-minimized-pill:hover {
  transform: translateY(-1px);
  border-color: #d6bd52;
  box-shadow: 0 6px 18px rgba(41, 43, 41, 0.12);
}

.pill-sparkle { color: #d97706; display: grid; place-items: center; }
.pill-count { color: #b9574f; font-weight: 700; }
.pill-action {
  background: #faf3d9;
  color: #252b2c;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

/* ─── Floating Contextual Action Card ─── */
.contextual-action-card {
  pointer-events: auto;
  position: absolute;
  right: 16px;
  bottom: 90px; /* was 16px */
  max-width: 360px;
  width: calc(100% - 32px);
  background: #fffef8;
  border: 1px solid #e9e5d7;
  border-radius: 12px;
  box-shadow: 0 10px 28px rgba(41, 43, 41, 0.14), 0 2px 6px rgba(41, 43, 41, 0.04);
  color: #252b2c;
  overflow: hidden;
  max-height: min(480px, calc(100% - 110px));
  display: flex;
  flex-direction: column;
  overscroll-behavior: contain;
  box-sizing: border-box;
}

/* ─── Header ─── */
.card-header {
  flex-shrink: 0;
  padding: 8px 12px;
  background: #faf8ee;
  border-bottom: 1px solid #e9e5d7;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.classification-pill {
  font-size: 9.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.badge-danger {
  background: #f8ecea;
  color: #b9574f;
  border: 1px solid #f2d4d0;
}

.badge-warning {
  background: #faf3d9;
  color: #78350f;
  border: 1px solid #f3e6b5;
}

.badge-mechanism {
  background: #ede9fe;
  color: #5b21b6;
  border: 1px solid #ddd6fe;
}

.issue-step-counter {
  font-size: 9.5px;
  font-family: ui-monospace, monospace;
  color: #788181;
  background: #fdfcf5;
  border: 1px solid #e9e5d7;
  padding: 1px 5px;
  border-radius: 3px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 2px;
}

.nav-cluster {
  display: flex;
  align-items: center;
  gap: 2px;
}

.icon-btn {
  border: 0;
  background: transparent;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  display: grid;
  place-items: center;
  color: #788181;
  cursor: pointer;
  transition: background 0.1s ease, color 0.1s ease;
}

.icon-btn:hover:not(:disabled) {
  background: #e9e5d7;
  color: #252b2c;
}

.icon-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-clear-highlight:hover {
  background: #fee2e2;
  color: #dc2626;
}

/* ─── Body (Independently Scrollable) ─── */
.card-body,
.card-content-scroll {
  flex: 1 1 auto;
  min-height: 0;
  padding: 10px 12px;
  overflow-y: auto;
  overscroll-behavior: contain;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-content-scroll::-webkit-scrollbar {
  width: 5px;
}
.card-content-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.card-content-scroll::-webkit-scrollbar-thumb {
  background: #d6d3c7;
  border-radius: 4px;
}
.card-content-scroll::-webkit-scrollbar-thumb:hover {
  background: #b8b4a6;
}

/* ─── Sticky Action Footer ─── */
.card-footer {
  flex-shrink: 0;
  padding: 8px 12px;
  background: #faf8ee;
  border-top: 1px solid #e9e5d7;
  border-radius: 0 0 12px 12px;
}

.issue-headline {
  display: flex;
  align-items: center;
  gap: 6px;
}

.headline-title {
  font-size: 12px;
  font-weight: 700;
  color: #252b2c;
}

.issue-short-explanation {
  margin: 0;
  font-size: 11.5px;
  line-height: 1.4;
  color: #3f4746;
}

/* ─── Affected Element Pills ─── */
.affected-pills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}

.elem-pill {
  font-size: 9px;
  font-family: ui-monospace, monospace;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
}

.pill-node { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
.pill-member { background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0; }
.pill-support { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }

/* ─── Uncertainty Callout ─── */
.uncertainty-callout {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  font-size: 10.5px;
  line-height: 1.35;
  color: #64748b;
  background: #faf8ee;
  border-left: 2px solid #d97706;
  padding: 5px 8px;
  border-radius: 0 4px 4px 0;
}

.callout-icon {
  color: #d97706;
  flex-shrink: 0;
  margin-top: 1px;
}

/* ─── Details Accordion ─── */
.details-accordion {
  border-top: 1px dashed #e9e5d7;
  padding-top: 4px;
}

.accordion-toggle {
  border: 0;
  background: transparent;
  padding: 0;
  font-size: 10px;
  font-weight: 600;
  color: #788181;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.accordion-toggle:hover { color: #252b2c; }

.accordion-body {
  margin-top: 4px;
  font-size: 10px;
  color: #64748b;
  background: #faf8ee;
  padding: 6px;
  border-radius: 4px;
}

.accordion-body p { margin: 0 0 3px; }
.path-text code { font-family: ui-monospace, monospace; font-size: 9px; }

/* ─── Resolution Subpanel ─── */
.resolution-subpanel {
  border-top: 1px solid #e9e5d7;
  padding-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.subpanel-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10.5px;
  font-weight: 700;
  color: #252b2c;
}

.explanation-quote {
  margin: 0;
  font-size: 11px;
  line-height: 1.35;
  color: #252b2c;
  background: #faf8ee;
  border-left: 2.5px solid #d6bd52;
  padding: 5px 8px;
  border-radius: 0 4px 4px 0;
}

.rationale-note {
  margin: 0;
  font-size: 10px;
  line-height: 1.3;
  color: #64748b;
}

.fixes-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.fixes-heading {
  font-size: 10px;
  font-weight: 700;
  color: #4b5563;
}

.fix-item {
  border: 1px solid #e9e5d7;
  border-radius: 6px;
  padding: 6px 8px;
  background: #ffffff;
  cursor: pointer;
  transition: border-color 0.1s ease;
}

.fix-item:hover { border-color: #cbd5e1; }
.fix-item.active {
  border-color: #d6bd52;
  background: #fffdf5;
  box-shadow: 0 0 0 1px #d6bd52;
}

.fix-item-top {
  display: flex;
  align-items: center;
  gap: 5px;
}

.fix-radio-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1.5px solid #94a3b8;
  display: inline-block;
}

.fix-radio-dot.selected {
  border-color: #d97706;
  background: #d97706;
  box-shadow: inset 0 0 0 2px #fff;
}

.fix-name {
  font-size: 10.5px;
  font-weight: 700;
  color: #252b2c;
  flex: 1;
}

.badge-valid {
  font-size: 8.5px;
  font-weight: 700;
  color: #15803d;
  background: #dcfce7;
  padding: 1px 4px;
  border-radius: 3px;
}

.badge-invalid {
  font-size: 8.5px;
  font-weight: 700;
  color: #b45309;
  background: #fef3c7;
  padding: 1px 4px;
  border-radius: 3px;
}

.fix-summary-text {
  margin: 3px 0 4px 15px;
  font-size: 10px;
  line-height: 1.3;
  color: #4b5563;
}

.change-tags {
  margin-left: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}

.alternatives-wrapper {
  background: #faf8ee;
  border-radius: 4px;
  padding: 4px 6px;
}

.alt-title { font-size: 9.5px; font-weight: 700; color: #64748b; }
.alt-bullet-list {
  margin: 2px 0 0;
  padding-left: 12px;
  font-size: 10px;
  color: #4b5563;
}

.action-approval-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
}

.btn-apply-fix {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 6px 10px;
  background: #f2dc70;
  border: 1px solid #d6bd52;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 700;
  color: #30312d;
  cursor: pointer;
  transition: background 0.1s ease;
}

.btn-apply-fix:hover:not(:disabled) { background: #e8ce52; }

.btn-cancel-fix {
  padding: 6px 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
}

.btn-cancel-fix:hover:not(:disabled) { background: #e2e8f0; color: #0f172a; }

/* ─── Call to Action Row: Fix with AI ─── */
.cta-row { margin-top: 2px; }

.btn-fix-ai {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 7px 12px;
  background: #faf3d9;
  border: 1px solid #d6bd52;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 700;
  color: #30312d;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(214, 189, 82, 0.12);
  transition: background 0.15s ease, transform 0.1s ease;
}

.btn-fix-ai:hover:not(:disabled) {
  background: #f2dc70;
  transform: translateY(-1px);
}

.btn-fix-ai:disabled { opacity: 0.6; cursor: wait; }
.sparkle-amber { color: #d97706; }
.spin-icon { animation: spin 1s linear infinite; }

@keyframes spin { 100% { transform: rotate(360deg); } }

.resolve-error-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 10px;
}

.btn-retry-resolve {
  margin-left: auto;
  border: 1px solid #dc2626;
  background: #ffffff;
  color: #dc2626;
  border-radius: 3px;
  padding: 1px 5px;
  font-size: 9px;
  font-weight: 700;
  cursor: pointer;
}

/* ─── Docked on Small Screens ─── */
@media (max-width: 768px) {
  .contextual-action-card {
    left: 12px !important;
    right: 12px !important;
    bottom: 12px !important;
    top: auto !important;
    width: auto !important;
    max-width: none !important;
    max-height: min(420px, calc(100% - 24px)) !important;
  }
}
</style>
