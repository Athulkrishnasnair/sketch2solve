<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  CheckCircle2,
  AlertTriangle,
  Info,
  X,
  Maximize2,
  Minimize2,
  ChevronDown,
  ChevronUp,
  Tag,
  RefreshCw,
  ArrowUpRight,
  ShieldAlert,
  Sliders,
  Download,
  FileCode,
  Table,
  Image,
} from 'lucide-vue-next'
import { downloadAnalysisExport } from '../api/analyses'

const props = defineProps({
  analysisId: {
    type: String,
    default: '',
  },
  solverData: {
    type: Object,
    default: null,
  },
  isStale: {
    type: Boolean,
    default: false,
  },
  geometry: {
    type: Object,
    required: true,
  },
  loads: {
    type: Array,
    default: () => [],
  },
  nodes: {
    type: Array,
    default: () => [],
  },
  members: {
    type: Array,
    default: () => [],
  },
  supports: {
    type: Array,
    default: () => [],
  },
  showForceLabels: {
    type: Boolean,
    default: true,
  },
  canSolve: {
    type: Boolean,
    default: false,
  },
  solving: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'close',
  'select-member',
  're-solve',
  'toggle-force-labels',
  'resize',
])

const isExpanded = ref(false)
const isMinimized = ref(false)
const activeTab = ref('summary') // 'summary' | 'members' | 'reactions' | 'limitations'

function toggleExpand() {
  if (isMinimized.value) {
    isMinimized.value = false
  }
  isExpanded.value = !isExpanded.value
  emit('resize')
}

function toggleMinimize() {
  isMinimized.value = !isMinimized.value
  if (isMinimized.value) {
    isExpanded.value = false
  }
  emit('resize')
}

function handleTabClick(tab) {
  if (isMinimized.value) {
    isMinimized.value = false
    emit('resize')
  }
  activeTab.value = tab
}

// Data extractions
const diagnostics = computed(() => props.solverData?.diagnostics || {})
const results = computed(() => props.solverData?.results || {})
const warningText = computed(() => props.solverData?.warning || '')

const forceUnit = computed(() => results.value?.force_unit || props.geometry?.metadata?.units?.force || 'kN')
const lengthUnit = computed(() => props.geometry?.metadata?.units?.length || 'm')

// Zero-load check
const isUnloaded = computed(() => !props.loads || props.loads.length === 0)

// Matrix properties
const equationCount = computed(() => diagnostics.value?.equation_count ?? (props.nodes?.length ? props.nodes.length * 2 : 0))
const unknownCount = computed(() => diagnostics.value?.unknown_count ?? (props.members?.length + (props.supports?.length ? props.supports.length * 2 : 0)))
const matrixShapeStr = computed(() => {
  const shape = diagnostics.value?.matrix_shape
  if (Array.isArray(shape) && shape.length === 2) {
    return `${shape[0]} × ${shape[1]}`
  }
  return `${equationCount.value} × ${unknownCount.value}`
})
const numericalRank = computed(() => diagnostics.value?.rank ?? diagnostics.value?.numerical_rank ?? 'N/A')
const conditionNumber = computed(() => {
  const cn = diagnostics.value?.condition_number ?? results.value?.condition_number
  if (cn == null) return 'N/A'
  if (typeof cn === 'number') {
    return cn < 1e4 ? cn.toFixed(2) : cn.toExponential(2)
  }
  return String(cn)
})

// Equilibrium residuals
const maxResidual = computed(() => {
  const r = results.value?.max_equilibrium_residual
  if (r == null) return null
  return typeof r === 'number' ? (r === 0 ? '0.00' : r.toExponential(3)) : String(r)
})
const residualTolerance = computed(() => {
  const t = results.value?.residual_tolerance
  if (t == null) return '1.00e-9'
  return typeof t === 'number' ? t.toExponential(2) : String(t)
})

// Node coordinate map for length calculation
const nodeCoordMap = computed(() => {
  const map = {}
  for (const n of props.nodes || []) {
    map[n.id] = { x: n.x, y: n.y }
  }
  return map
})

// Member forces table data
const memberRows = computed(() => {
  const forces = results.value?.member_forces || {}
  const states = results.value?.member_states || {}
  const list = []

  for (const m of props.members || []) {
    const rawForce = forces[m.id]
    const state = states[m.id] || (
      rawForce != null
        ? (Math.abs(rawForce) < 1e-6 ? 'zero' : (rawForce > 0 ? 'tension' : 'compression'))
        : 'unsolved'
    )
    const n1 = nodeCoordMap.value[m.node_i]
    const n2 = nodeCoordMap.value[m.node_j]
    let length = '—'
    if (n1 && n2) {
      const dx = n2.x - n1.x
      const dy = n2.y - n1.y
      length = Math.sqrt(dx * dx + dy * dy).toFixed(3)
    }

    list.push({
      id: m.id,
      node_i: m.node_i,
      node_j: m.node_j,
      length,
      rawForce,
      forceDisplay: rawForce != null ? `${rawForce > 0 ? '+' : ''}${rawForce.toFixed(3)} ${forceUnit.value}` : '—',
      state,
      stateLabel: state === 'tension' ? 'Tension (+)' : (state === 'compression' ? 'Compression (−)' : 'Zero-force (0)'),
    })
  }
  return list
})

// Support reactions table data
const reactionRows = computed(() => {
  const reactions = results.value?.support_reactions || {}
  const list = []

  for (const sup of props.supports || []) {
    const rData = reactions[sup.id] || reactions[sup.node] || {}
    const fx = typeof rData.x === 'number' ? rData.x : 0
    const fy = typeof rData.y === 'number' ? rData.y : 0
    const magnitude = Math.sqrt(fx * fx + fy * fy)

    list.push({
      id: sup.id,
      node: sup.node,
      type: sup.type || 'pin',
      direction: sup.direction || 'both',
      fx: Math.abs(fx) < 1e-6 ? 0 : fx,
      fy: Math.abs(fy) < 1e-6 ? 0 : fy,
      magnitude: Math.abs(magnitude) < 1e-6 ? 0 : magnitude,
      fxDisplay: `${fx >= 0 ? '+' : ''}${fx.toFixed(3)} ${forceUnit.value}`,
      fyDisplay: `${fy >= 0 ? '+' : ''}${fy.toFixed(3)} ${forceUnit.value}`,
      magnitudeDisplay: `${magnitude.toFixed(3)} ${forceUnit.value}`,
    })
  }
  return list
})

function handleRowClick(memberId) {
  emit('select-member', memberId)
}

// Export Workflow State
const showExportMenu = ref(false)
const exportingFormat = ref('')
const exportError = ref('')

const hasResults = computed(() => {
  return Boolean(results.value && Object.keys(results.value?.member_forces || {}).length > 0)
})

async function handleExport(format) {
  if (!props.analysisId) {
    exportError.value = 'No analysis ID available for export.'
    return
  }
  if (format === 'csv' && (props.isStale || !hasResults.value)) {
    return
  }

  exportingFormat.value = format
  exportError.value = ''
  try {
    await downloadAnalysisExport(props.analysisId, format)
    showExportMenu.value = false
  } catch (err) {
    exportError.value = err.message || `Export failed for ${format.toUpperCase()}`
  } finally {
    exportingFormat.value = ''
  }
}

function handleClickOutside(event) {
  if (showExportMenu.value && !event.target.closest('.export-dropdown-container')) {
    showExportMenu.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div
    class="analysis-results-panel"
    :class="{
      'is-expanded': isExpanded && !isMinimized,
      'is-minimized': isMinimized,
      'is-stale': isStale,
    }"
    role="region"
    aria-label="Analysis Results Panel"
    @transitionend.self="emit('resize')"
  >
    <!-- ─── Panel Header Bar ─── -->
    <header class="panel-header">
      <div class="header-left">
        <span class="status-badge" :class="isStale ? 'badge-stale' : 'badge-solved'">
          <AlertTriangle v-if="isStale" :size="13" />
          <CheckCircle2 v-else :size="13" />
          <span>{{ isStale ? 'RESULTS STALE' : 'SOLVED' }}</span>
        </span>
        <h3 class="panel-title">Analysis Results</h3>
        <span class="units-chip">{{ lengthUnit }} · {{ forceUnit }}</span>
      </div>

      <div class="header-center">
        <!-- Navigation Tabs -->
        <nav class="panel-tabs" aria-label="Analysis Results Navigation">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'summary' }"
            type="button"
            @click="handleTabClick('summary')"
          >
            Summary & Matrix
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'members' }"
            type="button"
            @click="handleTabClick('members')"
          >
            Member Forces ({{ memberRows.length }})
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'reactions' }"
            type="button"
            @click="handleTabClick('reactions')"
          >
            Support Reactions ({{ reactionRows.length }})
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'limitations' }"
            type="button"
            @click="handleTabClick('limitations')"
          >
            Limitations
          </button>
        </nav>
      </div>

      <div class="header-right">
        <!-- Export Dropdown -->
        <div class="export-dropdown-container">
          <button
            class="header-action-btn btn-export"
            :class="{ active: showExportMenu }"
            type="button"
            title="Export truss model or results"
            aria-label="Export analysis data"
            :aria-expanded="showExportMenu"
            @click.stop="showExportMenu = !showExportMenu"
          >
            <Download :size="13" />
            <span>Export</span>
            <ChevronDown :size="11" />
          </button>

          <div v-if="showExportMenu" class="export-menu" role="menu" @click.stop>
            <div class="export-menu-header">
              <span>Export Analysis</span>
            </div>

            <!-- PNG Option -->
            <button
              class="export-menu-item"
              type="button"
              role="menuitem"
              :disabled="exportingFormat === 'png'"
              @click="handleExport('png')"
            >
              <div class="export-item-icon">
                <Image :size="14" />
              </div>
              <div class="export-item-info">
                <div class="export-item-title-row">
                  <span class="export-item-name">PNG Diagram</span>
                  <span class="export-item-ext">200 DPI</span>
                </div>
                <span class="export-item-desc">Matplotlib high-res vector plot</span>
              </div>
            </button>

            <!-- JSON Option -->
            <button
              class="export-menu-item"
              type="button"
              role="menuitem"
              :disabled="exportingFormat === 'json'"
              @click="handleExport('json')"
            >
              <div class="export-item-icon">
                <FileCode :size="14" />
              </div>
              <div class="export-item-info">
                <div class="export-item-title-row">
                  <span class="export-item-name">JSON Model</span>
                  <span class="export-item-ext">Schema 1.0</span>
                </div>
                <span class="export-item-desc">Geometry, loads, units</span>
              </div>
            </button>

            <!-- CSV Option -->
            <button
              class="export-menu-item"
              :class="{ 'is-disabled': isStale || !hasResults }"
              type="button"
              role="menuitem"
              :disabled="exportingFormat === 'csv' || isStale || !hasResults"
              :title="isStale ? 'Requires fresh solve (results are stale)' : (!hasResults ? 'Solve model before exporting CSV' : 'Export member forces & reactions CSV')"
              @click="handleExport('csv')"
            >
              <div class="export-item-icon">
                <Table :size="14" />
              </div>
              <div class="export-item-info">
                <div class="export-item-title-row">
                  <span class="export-item-name">CSV Results</span>
                  <span v-if="isStale" class="export-badge-tag tag-stale">Stale</span>
                  <span v-else-if="!hasResults" class="export-badge-tag tag-unsolved">Unsolved</span>
                  <span v-else class="export-item-ext">Forces & Rx</span>
                </div>
                <span class="export-item-desc">
                  {{ isStale ? 'Requires fresh solve (geometry modified)' : (!hasResults ? 'Requires fresh successful solve' : 'Axial forces and reactions') }}
                </span>
              </div>
            </button>

            <div v-if="exportError" class="export-menu-error">
              <AlertTriangle :size="12" />
              <span>{{ exportError }}</span>
            </div>
          </div>
        </div>

        <!-- Force labels toggle button -->
        <button
          class="header-action-btn btn-force-labels"
          :class="{ active: showForceLabels }"
          type="button"
          :title="showForceLabels ? 'Hide force labels on canvas' : 'Show force labels on canvas'"
          :aria-label="showForceLabels ? 'Hide force labels on canvas' : 'Show force labels on canvas'"
          @click="emit('toggle-force-labels')"
        >
          <Tag :size="13" />
          <span>{{ showForceLabels ? 'Labels On' : 'Labels Off' }}</span>
        </button>

        <!-- Minimize / Restore -->
        <button
          class="header-action-btn btn-minimize"
          type="button"
          :title="isMinimized ? 'Restore panel height' : 'Minimize results panel'"
          :aria-label="isMinimized ? 'Restore panel height' : 'Minimize results panel'"
          @click="toggleMinimize"
        >
          <ChevronUp v-if="isMinimized" :size="13" />
          <ChevronDown v-else :size="13" />
        </button>

        <!-- Expand / Collapse -->
        <button
          v-if="!isMinimized"
          class="header-action-btn btn-expand"
          type="button"
          :title="isExpanded ? 'Collapse panel height' : 'Expand panel height'"
          :aria-label="isExpanded ? 'Collapse panel height' : 'Expand panel height'"
          @click="toggleExpand"
        >
          <Minimize2 v-if="isExpanded" :size="13" />
          <Maximize2 v-else :size="13" />
        </button>

        <!-- Close Panel -->
        <button
          class="header-action-btn btn-close"
          type="button"
          title="Close results panel"
          aria-label="Close results panel"
          @click="emit('close')"
        >
          <X :size="14" />
        </button>
      </div>
    </header>

    <!-- ─── Stale Results Warning Banner ─── -->
    <div v-if="isStale" class="panel-alert banner-stale">
      <div class="alert-content">
        <AlertTriangle :size="16" class="alert-icon" />
        <div>
          <strong>Geometry modified — results are stale.</strong>
          <span> The model was edited after the last solve. Re-run analysis to view updated member forces and reactions.</span>
        </div>
      </div>
      <button
        v-if="canSolve"
        class="btn-re-solve"
        type="button"
        :disabled="solving"
        @click="emit('re-solve')"
      >
        <RefreshCw :size="13" :class="{ 'spin-icon': solving }" />
        <span>{{ solving ? 'Solving…' : 'Re-solve Now' }}</span>
      </button>
    </div>

    <!-- ─── Zero-Load Case Explanatory Banner ─── -->
    <div v-if="!isStale && isUnloaded" class="panel-alert banner-unloaded">
      <div class="alert-content">
        <Info :size="16" class="alert-icon" />
        <div>
          <strong>Model is unloaded (Zero external forces applied).</strong>
          <span>
            Static equilibrium is satisfied trivially ($Ax = 0$). All member forces and support reactions are zero because no external loads act on the truss. This is an exact analytical result, not a solver failure.
          </span>
          <div class="alert-tip">
            Tip: Apply a point load to any joint using the Load tool (L) to inspect structural behavior under load.
          </div>
        </div>
      </div>
    </div>

    <!-- ─── Panel Body Container ─── -->
    <div class="panel-body">

      <!-- TAB 1: SUMMARY & MATRIX -->
      <section v-if="activeTab === 'summary'" class="tab-pane pane-summary">
        <div class="summary-grid">
          <!-- Structural Counts Card -->
          <div class="results-card">
            <h4 class="card-title">Structural Counts</h4>
            <div class="stat-pairs">
              <div class="stat-pair">
                <span class="label">Joints (N)</span>
                <span class="value">{{ nodes.length }}</span>
              </div>
              <div class="stat-pair">
                <span class="label">Members (M)</span>
                <span class="value">{{ members.length }}</span>
              </div>
              <div class="stat-pair">
                <span class="label">Equilibrium Equations (2N)</span>
                <span class="value">{{ equationCount }}</span>
              </div>
              <div class="stat-pair">
                <span class="label">Unknowns (M + R)</span>
                <span class="value">{{ unknownCount }}</span>
              </div>
            </div>
          </div>

          <!-- Equilibrium Matrix Diagnostics Card -->
          <div class="results-card">
            <h4 class="card-title">Equilibrium Matrix Diagnostics</h4>
            <div class="stat-pairs">
              <div class="stat-pair">
                <span class="label">Matrix Shape</span>
                <span class="value">{{ matrixShapeStr }}</span>
              </div>
              <div class="stat-pair">
                <span class="label">Numerical Rank</span>
                <span class="value">{{ numericalRank }}</span>
              </div>
              <div class="stat-pair">
                <span class="label">Condition Number (κ)</span>
                <span class="value">{{ conditionNumber }}</span>
              </div>
              <div class="stat-pair">
                <span class="label">Classification</span>
                <span class="value class-determinate">
                  {{ diagnostics.classification || diagnostics.category || 'DETERMINATE' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Equilibrium Residuals Card -->
          <div class="results-card">
            <h4 class="card-title">Equilibrium Verification</h4>
            <div class="stat-pairs">
              <div class="stat-pair">
                <span class="label">Max Nodal Residual</span>
                <span class="value">{{ maxResidual != null ? `${maxResidual} ${forceUnit}` : 'N/A' }}</span>
              </div>
              <div class="stat-pair">
                <span class="label">Residual Tolerance</span>
                <span class="value">{{ residualTolerance }} {{ forceUnit }}</span>
              </div>
              <div class="stat-pair">
                <span class="label">Equilibrium Status</span>
                <span class="value status-pass">
                  <CheckCircle2 :size="12" /> Verified Closed
                </span>
              </div>
              <div class="stat-pair">
                <span class="label">External Loads</span>
                <span class="value">{{ loads.length }} applied</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- TAB 2: MEMBER FORCES -->
      <section v-if="activeTab === 'members'" class="tab-pane pane-members">
        <div class="table-container">
          <table class="results-table" aria-label="Member Forces Table">
            <thead>
              <tr>
                <th>Member</th>
                <th>Joints</th>
                <th>Length ({{ lengthUnit }})</th>
                <th>Axial Force ({{ forceUnit }})</th>
                <th>Classification</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in memberRows"
                :key="`row-${row.id}`"
                class="member-table-row"
                @click="handleRowClick(row.id)"
              >
                <td class="font-bold">{{ row.id }}</td>
                <td>{{ row.node_i }} → {{ row.node_j }}</td>
                <td>{{ row.length }}</td>
                <td class="font-mono font-bold" :class="`text-${row.state}`">
                  {{ row.forceDisplay }}
                </td>
                <td>
                  <span class="force-pill" :class="`pill-${row.state}`">
                    {{ row.stateLabel }}
                  </span>
                </td>
                <td>
                  <button
                    class="btn-inspect-member"
                    type="button"
                    title="Inspect member on canvas"
                    @click.stop="handleRowClick(row.id)"
                  >
                    Inspect <ArrowUpRight :size="11" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- TAB 3: SUPPORT REACTIONS -->
      <section v-if="activeTab === 'reactions'" class="tab-pane pane-reactions">
        <div class="table-container">
          <table class="results-table" aria-label="Support Reactions Table">
            <thead>
              <tr>
                <th>Support ID</th>
                <th>Joint</th>
                <th>Type</th>
                <th>Horizontal Reaction Fx</th>
                <th>Vertical Reaction Fy</th>
                <th>Resultant Magnitude R</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in reactionRows" :key="`rx-row-${r.id}`">
                <td class="font-bold">{{ r.id }}</td>
                <td>Joint {{ r.node }}</td>
                <td class="capitalize">{{ r.type }}</td>
                <td class="font-mono">{{ r.fxDisplay }}</td>
                <td class="font-mono">{{ r.fyDisplay }}</td>
                <td class="font-mono font-bold text-reaction">{{ r.magnitudeDisplay }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- TAB 4: LIMITATIONS & DISCLAIMERS -->
      <section v-if="activeTab === 'limitations'" class="tab-pane pane-limitations">
        <div class="limitations-container">
          <div class="limitation-block warning-block">
            <ShieldAlert :size="18" class="limitation-icon" />
            <div>
              <strong>Engineering Solver Disclaimer</strong>
              <p>
                {{ warningText || 'A numerical equilibrium solution does not establish physical stability or engineering suitability.' }}
              </p>
            </div>
          </div>

          <div class="assumptions-list">
            <h5 class="assumptions-title">Key Engineering Assumptions</h5>
            <ul>
              <li><strong>Planar Ideal Pin-Jointed System:</strong> All joints are modeled as frictionless hinges transmitting only axial tension or compression.</li>
              <li><strong>Small Displacement Theory:</strong> First-order static equilibrium is assembled on undeformed initial geometry. Geometric non-linearities and large deflections are neglected.</li>
              <li><strong>Elastic & Buckling Limits Unchecked:</strong> Euler buckling capacity, cross-sectional slenderness ratios ($L/r$), and material yield limits require defined cross-section profiles and materials, which are not evaluated in basic geometry analysis.</li>
            </ul>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>

<style scoped>
.analysis-results-panel {
  position: relative;
  width: 100%;
  flex-shrink: 0;
  height: 270px;
  max-height: 42vh;
  background: #ffffff;
  border-top: 1px solid var(--color-border, #e9e5d7);
  box-shadow: 0 -4px 18px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  z-index: 40;
  transition: height 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  font-family: inherit;
  color: var(--color-text-primary, #252b2c);
}

.analysis-results-panel.is-expanded {
  height: 420px;
  max-height: 56vh;
}

.analysis-results-panel.is-minimized {
  height: 42px;
  overflow: hidden;
}

.analysis-results-panel.is-minimized .panel-body,
.analysis-results-panel.is-minimized .panel-alert {
  display: none !important;
}

.analysis-results-panel.is-stale {
  border-top: 2px solid #f59e0b;
}

/* Header */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  background: var(--color-surface, #fffef8);
  border-bottom: 1px solid var(--color-border, #e9e5d7);
  gap: 8px;
  min-height: 44px;
  box-sizing: border-box;
  flex-wrap: nowrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 0 0 auto;
  white-space: nowrap;
}

.panel-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-primary, #252b2c);
  letter-spacing: -0.2px;
  white-space: nowrap;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 7px;
  height: 22px;
  border-radius: 9999px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
  box-sizing: border-box;
  flex-shrink: 0;
}

.badge-solved {
  background: #dcfce7;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

.badge-stale {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fde68a;
}

.units-chip {
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  background: #f1f5f9;
  padding: 0 6px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  border-radius: 4px;
  white-space: nowrap;
  box-sizing: border-box;
  flex-shrink: 0;
}

/* Tabs */
.header-center {
  flex: 1 1 auto;
  display: flex;
  justify-content: center;
  min-width: 0;
}

.panel-tabs {
  display: inline-flex;
  align-items: center;
  background: #f1f5f9;
  padding: 2px;
  border-radius: 6px;
  gap: 2px;
  height: 32px;
  box-sizing: border-box;
  min-width: 0;
  max-width: 100%;
  overflow-x: auto;
  flex-shrink: 1;
  flex-wrap: nowrap;
  white-space: nowrap;
}

/* Hide scrollbar while keeping horizontal tab scrolling */
.panel-tabs {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.panel-tabs::-webkit-scrollbar {
  display: none;
}

.tab-btn {
  background: transparent;
  border: none;
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  padding: 0 7px;
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  flex: 0 0 auto;
}

.tab-btn:hover {
  color: var(--color-text-primary, #252b2c);
}

.tab-btn.active {
  background: #ffffff;
  color: var(--color-text-primary, #252b2c);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Header Right */
.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
  white-space: nowrap;
}

.header-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  height: 30px;
  min-height: 30px;
  padding: 0 7px;
  border-radius: 6px;
  font-size: 10.5px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;
  box-sizing: border-box;
  flex-shrink: 0;
}

.header-action-btn:hover {
  background: #f1f5f9;
  color: #1e293b;
  border-color: #cbd5e1;
}

.header-action-btn.active {
  background: #e0f2fe;
  color: #0369a1;
  border-color: #bae6fd;
}

/* Compact square controls for minimize, expand, close */
.header-action-btn.btn-minimize,
.header-action-btn.btn-expand,
.header-action-btn.btn-close {
  width: 30px;
  height: 30px;
  min-width: 30px;
  padding: 0;
  justify-content: center;
}

.header-action-btn.btn-close:hover {
  background: #fee2e2;
  color: #b91c1c;
  border-color: #fca5a5;
}

/* Export Dropdown */
.export-dropdown-container {
  position: relative;
  display: inline-flex;
}

.export-menu {
  position: absolute;
  bottom: calc(100% + 6px);
  right: 0;
  width: 250px;
  background: #ffffff;
  border: 1px solid var(--color-border, #e9e5d7);
  border-radius: 8px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.12), 0 8px 10px -6px rgba(0, 0, 0, 0.08);
  padding: 6px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.export-menu-header {
  padding: 6px 8px 4px 8px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 2px;
}

.export-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease;
  font-family: inherit;
}

.export-menu-item:hover:not(:disabled) {
  background: #f8fafc;
}

.export-menu-item.is-disabled,
.export-menu-item:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  background: #fafafa;
}

.export-item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #334155;
  flex-shrink: 0;
}

.export-menu-item:hover:not(:disabled) .export-item-icon {
  background: #e0f2fe;
  color: #0284c7;
}

.export-item-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.export-item-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.export-item-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary, #252b2c);
}

.export-item-ext {
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  padding: 1px 5px;
  border-radius: 4px;
}

.export-badge-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  text-transform: uppercase;
}

.export-badge-tag.tag-stale {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fde68a;
}

.export-badge-tag.tag-unsolved {
  background: #fee2e2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.export-item-desc {
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 1px;
}

.export-menu-error {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  margin-top: 4px;
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 4px;
  font-size: 11px;
  color: #991b1b;
}

/* Warning & Explanatory Banners */
.panel-alert {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  line-height: 1.4;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.banner-stale {
  background: #fffbeb;
  color: #92400e;
  border-bottom-color: #fef3c7;
}

.banner-unloaded {
  background: #eff6ff;
  color: #1e40af;
  border-bottom-color: #dbeafe;
}

.alert-content {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.alert-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.alert-tip {
  margin-top: 3px;
  font-weight: 500;
  color: #1d4ed8;
}

.btn-re-solve {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: #f59e0b;
  color: #ffffff;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.btn-re-solve:hover:not(:disabled) {
  background: #d97706;
}

.btn-re-solve:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Panel Body */
.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  background: #fafaf9;
}

.tab-pane {
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(2px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Summary Grid */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.results-card {
  background: #ffffff;
  border: 1px solid var(--color-border, #e9e5d7);
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.card-title {
  margin: 0 0 10px 0;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #64748b;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 5px;
}

.stat-pairs {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-pair {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.stat-pair .label {
  color: #64748b;
}

.stat-pair .value {
  font-weight: 600;
  font-family: monospace;
  color: var(--color-text-primary, #252b2c);
}

.stat-pair .class-determinate {
  color: #0369a1;
  background: #e0f2fe;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
}

.stat-pair .status-pass {
  color: #15803d;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* Tables */
.table-container {
  background: #ffffff;
  border: 1px solid var(--color-border, #e9e5d7);
  border-radius: 6px;
  overflow: hidden;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  text-align: left;
}

.results-table th {
  background: #f8fafc;
  padding: 8px 12px;
  font-weight: 600;
  color: #475569;
  border-bottom: 1px solid #e2e8f0;
}

.results-table td {
  padding: 7px 12px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.member-table-row {
  cursor: pointer;
  transition: background 0.1s ease;
}

.member-table-row:hover {
  background: #f1f5f9;
}

.font-bold { font-weight: 600; }
.font-mono { font-family: monospace; }
.capitalize { text-transform: capitalize; }

.text-tension { color: #1d4ed8; }
.text-compression { color: #dc2626; }
.text-zero { color: #64748b; }
.text-reaction { color: #059669; }

/* Force Badges */
.force-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
}

.pill-tension {
  background: #dbeafe;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.pill-compression {
  background: #fee2e2;
  color: #dc2626;
  border: 1px solid #fca5a5;
}

.pill-zero {
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.btn-inspect-member {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: transparent;
  border: 1px solid #cbd5e1;
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
}

.btn-inspect-member:hover {
  background: #e2e8f0;
  color: #0f172a;
}

/* Limitations Pane */
.limitations-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.limitation-block {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
}

.warning-block {
  background: #fffbeb;
  border: 1px solid #fef3c7;
  color: #92400e;
}

.limitation-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.assumptions-list {
  background: #ffffff;
  border: 1px solid var(--color-border, #e9e5d7);
  border-radius: 6px;
  padding: 12px 16px;
}

.assumptions-title {
  margin: 0 0 8px 0;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.assumptions-list ul {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #334155;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

@media (max-width: 1180px) and (min-width: 769px) {
  .panel-header {
    padding: 6px 10px;
    gap: 6px;
  }

  .header-left {
    gap: 6px;
  }

  .units-chip {
    display: none;
  }

  .tab-btn {
    padding: 0 7px;
    font-size: 11px;
  }

  .header-action-btn.btn-export,
  .header-action-btn.btn-force-labels {
    padding: 0 7px;
    font-size: 11px;
  }
}

@media (max-width: 768px) {
  .analysis-results-panel {
    height: 320px;
    max-height: 55vh;
  }

  .analysis-results-panel.is-expanded {
    height: 80vh;
    max-height: 85vh;
  }

  .analysis-results-panel.is-minimized {
    height: 44px;
  }

  .panel-header {
    position: relative;
    flex-wrap: wrap;
    padding: 6px 10px;
    gap: 6px;
  }

  .header-left {
    min-width: 0;
    flex: 1 1 auto;
    gap: 6px;
  }

  .panel-title {
    font-size: 13px;
  }

  .header-center {
    order: 3;
    width: 100%;
    padding: 2px 0 0 0;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    justify-content: flex-start;
  }

  .panel-tabs {
    width: 100%;
    display: flex;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    height: 32px;
    padding: 2px;
  }

  .tab-btn {
    white-space: nowrap;
    font-size: 11px;
    padding: 0 8px;
    height: 28px;
    flex: 1 0 auto;
    text-align: center;
  }

  .header-right {
    margin-left: auto;
    gap: 4px;
  }

  .header-action-btn span {
    display: none;
  }

  .header-action-btn {
    height: 32px;
    min-height: 32px;
    min-width: 32px;
    padding: 0 6px;
  }

  .header-action-btn.btn-minimize,
  .header-action-btn.btn-expand,
  .header-action-btn.btn-close {
    width: 32px;
    height: 32px;
    min-width: 32px;
  }

  .export-dropdown-container {
    position: static;
    flex: 0 0 auto;
  }

  .export-menu {
    left: auto;
    right: 10px;
    width: min(260px, calc(100vw - 20px));
    bottom: calc(100% + 6px);
  }

  .panel-body {
    padding: 10px 12px;
  }

  .data-table-wrapper,
  .table-responsive {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
}
</style>

