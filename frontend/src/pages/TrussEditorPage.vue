<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  MousePointer,
  Hand,
  PlusCircle,
  Spline,
  Trash2,
  Anchor,
  CircleDot,
  ArrowDown,
  Ruler,
  Undo2,
  Redo2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Grid3x3,
  Magnet,
  Sparkles,
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ChevronUp,
  ChevronDown,
  ArrowLeft,
  Bot,
  Play,
  Save,
  Check,
  Loader2,
  Link2,
  BarChart3,
  Tag,
  Sliders,
} from 'lucide-vue-next'
import {
  getAnalysis,
  getAnalysisDraft,
  markAnalysisReviewed,
  previewAnalysisGeometry,
  saveAnalysisDraft,
  solveReviewedAnalysis,
  designTruss,
  applyDesignProposal,
  rejectDesignProposal,
} from '../api/analyses'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import IssueResolutionAssistant from '../components/IssueResolutionAssistant.vue'
import AnalysisResultsPanel from '../components/AnalysisResultsPanel.vue'
import DesignInstructionPanel from '../components/DesignInstructionPanel.vue'

const props = defineProps({
  analysisId: { type: String, required: true },
})
const emit = defineEmits(['back', 'history', 'updated'])

// --- State ---
const loading = ref(true)
const analysis = ref(null)
const error = ref('')
const activeTool = ref('select') // 'select' | 'pan' | 'joint' | 'member' | 'delete' | 'pin' | 'roller' | 'load' | 'measure'
const selectedElement = ref(null) // { type: 'node'|'member'|'support'|'load', id: string }
const memberStartJoint = ref(null)
const measureStart = ref(null)
const measureDistance = ref(null)

// Layers
const showGrid = ref(true)
const snapToGrid = ref(true)
const snapInterval = ref(0.5) // in model units
const showAiProposal = ref(true)
const showOpenCv = ref(false)
const showWarningsDrawer = ref(false)
const showAiAssistant = ref(false)

// Canvas Navigation
const svgRef = ref(null)
const pan = ref({ x: 350, y: 300 })
const scale = ref(60) // pixels per unit
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const initialPan = ref({ x: 0, y: 0 })
const cursorCoords = ref({ x: 0, y: 0 })
const draggingNodeId = ref(null)
const hasDraggedNode = ref(false)

// Canonical Geometry
const geometry = ref({
  schema_version: '1.0',
  metadata: {
    name: 'Truss Model',
    source: 'human_review',
    units: { length: 'm', force: 'kN' },
  },
  model: {
    nodes: [],
    members: [],
    supports: [],
    loads: [],
  },
})

// Review / Persistence State
const coordinatesConfirmed = ref(false)
const reviewStatus = ref('pending_review')
const isDirty = ref(false)
const saving = ref(false)
const reviewing = ref(false)
const solving = ref(false)
const statusMessage = ref('')

// History (Undo / Redo)
const historyStack = ref([])
const historyIndex = ref(-1)
const isHistoryNavigating = ref(false)

// Live Preview / Calculation
const previewResult = ref(null)
const calculating = ref(false)
let previewSeq = 0
let previewDebounceTimer = null

// AI Assistant & Conversational Natural-Language Design Studio
const activeSidebarTab = ref('tools') // 'tools' | 'design'
const showIssueAssistant = ref(true)
const showDesignAssistant = ref(false)
const designModelRevision = ref(1)
const designProposal = ref(null)
const designBusy = ref(false)
const designError = ref('')

function switchSidebarTab(tab) {
  activeSidebarTab.value = tab
  showDesignAssistant.value = tab === 'design'
  nextTick(() => {
    fitView()
  })
}

const memberMap = computed(() => {
  const map = {}
  for (const m of members.value) {
    map[m.id] = m
  }
  return map
})

const effectiveNodeMap = computed(() => {
  const map = { ...nodeMap.value }
  if (designProposal.value?.operations) {
    for (const op of designProposal.value.operations) {
      if (op.op === 'add_joint') {
        map[op.id] = { id: op.id, x: op.x ?? 0, y: op.y ?? 0 }
      } else if (op.op === 'update_joint') {
        const cur = map[op.id] || { id: op.id, x: 0, y: 0 }
        const newX = op.x !== undefined ? op.x : (cur.x + (op.dx || 0))
        const newY = op.y !== undefined ? op.y : (cur.y + (op.dy || 0))
        map[op.id] = { id: op.id, x: newX, y: newY }
      }
    }
  }
  return map
})

const designProposedAdditions = computed(() => {
  if (!designProposal.value?.operations) return []
  return designProposal.value.operations.filter((op) => op.op === 'add_member')
})

const designProposedRemovals = computed(() => {
  if (!designProposal.value?.operations) return []
  return designProposal.value.operations
    .filter((op) => op.op === 'remove_member')
    .map((op) => op.id)
})

const designProposedJointOps = computed(() => {
  if (!designProposal.value?.operations) return []
  return designProposal.value.operations.filter(
    (op) => op.op === 'add_joint' || op.op === 'update_joint'
  )
})

const aiAssistantMessage = ref('')
const aiSuggestions = ref([])
const aiAnalyzing = ref(false)

// ConfirmDialog state
const dialog = ref({
  open: false,
  title: '',
  message: '',
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  variant: 'default',
  onConfirm: null,
})

// Toast / inline error notification
const toastMessage = ref('')
const toastVariant = ref('info') // 'info' | 'error' | 'success'
let toastTimer = null

function showToast(msg, variant = 'info', durationMs = 3500) {
  clearTimeout(toastTimer)
  toastMessage.value = msg
  toastVariant.value = variant
  toastTimer = setTimeout(() => { toastMessage.value = '' }, durationMs)
}

function openConfirm({ title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', variant = 'default', onConfirm }) {
  dialog.value = { open: true, title, message, confirmLabel, cancelLabel, variant, onConfirm }
}

function handleDialogConfirm() {
  const cb = dialog.value.onConfirm
  dialog.value = { ...dialog.value, open: false }
  cb?.()
}

function handleDialogCancel() {
  dialog.value = { ...dialog.value, open: false }
}

// --- Computed ---
const nodes = computed(() => geometry.value.model.nodes || [])
const members = computed(() => geometry.value.model.members || [])
const supports = computed(() => geometry.value.model.supports || [])
const loads = computed(() => geometry.value.model.loads || [])
const nodeMap = computed(() => Object.fromEntries(nodes.value.map((n) => [n.id, n])))

const proposal = computed(() => analysis.value?.interpretation_proposal || null)
const proposalJoints = computed(() => proposal.value?.joints || [])
const proposalMembers = computed(() => proposal.value?.members || [])

const validationErrors = computed(() => previewResult.value?.validation?.errors || [])
const validationWarnings = computed(() => previewResult.value?.validation?.warnings || [])
const solvability = computed(() => previewResult.value?.solvability || { status: 'incomplete', message: 'Ready' })

// Solver Results & Transition State
const persistedSolverData = ref(null)
const resultsStale = ref(false)
const showResultsPanel = ref(false)
const showForceLabels = ref(true)

function handleResultsPanelResize() {
  fitView()
  setTimeout(() => {
    fitView()
  }, 220)
}

watch(showResultsPanel, (isOpen) => {
  if (isOpen) {
    fitView()
    setTimeout(() => {
      fitView()
    }, 220)
  }
})

const hasSolvedResults = computed(() => Boolean(persistedSolverData.value?.results))
const isUnloaded = computed(() => !loads.value || loads.value.length === 0)

const solverResults = computed(() => {
  if (resultsStale.value) return null
  return persistedSolverData.value?.results || null
})

// Unified list of actionable structural and geometry issues for the AI Issue Assistant
const activeIssues = computed(() => {
  const list = []

  // 1. Schema Validation Errors (highest severity)
  for (const [idx, err] of validationErrors.value.entries()) {
    const elemId = err.element_id || (err.path ? err.path.split('/').pop() : '')
    list.push({
      id: `err-${idx}-${err.code || 'error'}`,
      code: err.code || 'VALIDATION_ERROR',
      title: err.code ? err.code.replace(/_/g, ' ') : 'Validation Error',
      severity: 'error',
      classification: err.classification || 'invalid_geometry',
      message: err.message,
      summary: err.message,
      element_id: elemId,
      path: err.path || '',
      affected_elements: err.affected_elements || {
        nodes: elemId && nodes.value.some((n) => n.id === elemId) ? [elemId] : [],
        members: elemId && members.value.some((m) => m.id === elemId) ? [elemId] : [],
        supports: [],
      },
      localization_precision: err.localization_precision || 'exact',
      details: err.path ? `Field: ${err.path}` : '',
    })
  }

  // 2. Semantic Engineering Warnings (e.g. INSUFFICIENT_SUPPORTS, DISCONNECTED_JOINT)
  for (const [idx, warn] of validationWarnings.value.entries()) {
    const elemId = warn.element_id || ''
    const isDisc = warn.code === 'DISCONNECTED_JOINT'
    const isSupp = warn.code === 'INSUFFICIENT_SUPPORTS'
    list.push({
      id: `warn-${idx}-${warn.code || 'warn'}`,
      code: warn.code || 'WARNING',
      title: warn.code ? warn.code.replace(/_/g, ' ') : 'Structural Warning',
      severity: isSupp ? 'error' : 'warning',
      classification: warn.classification || (isDisc ? 'disconnected_geometry' : isSupp ? 'underconstrained_system' : 'invalid_geometry'),
      message: warn.message,
      summary: warn.message,
      element_id: elemId,
      path: warn.path || '',
      affected_elements: warn.affected_elements || {
        nodes: isDisc ? [elemId] : isSupp ? (supports.value.length ? supports.value.map((s) => s.node) : nodes.value.map((n) => n.id)) : [],
        members: elemId && members.value.some((m) => m.id === elemId) ? [elemId] : [],
        supports: isSupp ? supports.value.map((s) => s.id) : [],
      },
      localization_precision: warn.localization_precision || 'exact',
      details: elemId ? `Element: ${elemId}` : '',
    })
  }

  // 3. Solvability Diagnostics (e.g. UNDERDETERMINED, SINGULAR_SQUARE, OVERDETERMINED)
  if (solvability.value?.status === 'unsolvable' && solvability.value?.category) {
    const cat = solvability.value.category
    const isMech = cat === 'UNDERDETERMINED' || cat === 'SINGULAR_SQUARE'
    list.push({
      id: `diag-${cat}`,
      code: cat,
      title: isMech
        ? 'Kinematic Mechanism / Stability Issue'
        : cat === 'OVERDETERMINED'
          ? 'Statically Indeterminate System'
          : 'Solver Diagnostic',
      severity: isMech ? 'mechanism' : 'error',
      classification: solvability.value.classification || (isMech ? 'mechanism' : cat === 'OVERDETERMINED' ? 'statically_indeterminate' : 'solver_diagnostic'),
      message: solvability.value.message || 'The structure cannot be solved in static equilibrium.',
      summary: solvability.value.message || 'System is kinematically unstable or rank deficient.',
      affected_elements: solvability.value.affected_elements || {
        nodes: nodes.value.map((n) => n.id),
        members: members.value.map((m) => m.id),
        supports: supports.value.map((s) => s.id),
      },
      localization_precision: solvability.value.localization_precision || 'component_level',
      uncertainty_explanation:
        solvability.value.uncertainty_explanation ||
        'Numerical rank deficiency detected. The kinematic mechanism is distributed across this connected component; the exact affected member cannot be uniquely isolated without additional panel bracing.',
      details: `Equations: ${solvability.value.equation_count || 0}, Unknowns: ${solvability.value.unknown_count || 0}, Numerical Rank: ${solvability.value.rank ?? 'N/A'}`,
    })
  }

  // 4. Excessive Axial Force Advisory (differentiating stability from strength failures)
  if (solverResults.value?.member_forces) {
    for (const [mId, forceVal] of Object.entries(solverResults.value.member_forces)) {
      const forceNum = Number(forceVal)
      if (Math.abs(forceNum) >= 1000.0) {
        const memObj = members.value.find((m) => m.id === mId)
        list.push({
          id: `force-${mId}`,
          code: 'HIGH_AXIAL_FORCE',
          title: 'High Axial Force Advisory',
          severity: 'warning',
          classification: 'high_axial_force',
          element_id: mId,
          affected_elements: {
            nodes: memObj ? [memObj.node_i, memObj.node_j] : [],
            members: [mId],
            supports: [],
          },
          localization_precision: 'exact',
          message: `Member ${mId} carries high axial force (${forceNum.toFixed(1)} ${solverResults.value.force_unit || 'kN'}). Note: material yield strength and cross-sectional properties are not declared in schema; this indicates high loading, not certified strength failure.`,
          summary: `High member load (${forceNum.toFixed(1)} ${solverResults.value.force_unit || 'kN'}). Capacity check requires material properties.`,
          details: `Force: ${forceNum.toFixed(2)}, State: ${solverResults.value.member_states?.[mId] || 'loaded'}`,
        })
      }
    }
  }

  return list
})

const selectedIssueId = ref(null)
const aiPreviewFix = ref(null)
const userClearedHighlight = ref(false)

// Automatically select the first issue when issues appear, or clear when resolved
watch(
  () => activeIssues.value,
  (issues) => {
    if (!issues.length) {
      selectedIssueId.value = null
      userClearedHighlight.value = false
      showIssueAssistant.value = false
      return
    }
    // If user explicitly cleared highlighting, preserve their choice during background recalculation
    if (userClearedHighlight.value) return

    showIssueAssistant.value = true
    if (!selectedIssueId.value || !issues.some((i) => i.id === selectedIssueId.value)) {
      selectedIssueId.value = issues[0].id
      focusOnIssue(issues[0])
    }
  },
  { immediate: true }
)

const selectedIssue = computed(() => {
  if (!selectedIssueId.value) return null
  return activeIssues.value.find((i) => i.id === selectedIssueId.value) || null
})

const isHighlightActive = computed(() => Boolean(selectedIssue.value && showIssueAssistant.value))
const affectedNodeIds = computed(() => new Set(selectedIssue.value?.affected_elements?.nodes || []))
const affectedMemberIds = computed(() => new Set(selectedIssue.value?.affected_elements?.members || []))

function toggleHighlightMode() {
  if (showIssueAssistant.value) {
    userClearedHighlight.value = true
    selectedIssueId.value = null
    aiPreviewFix.value = null
    showIssueAssistant.value = false
  } else if (activeIssues.value.length) {
    userClearedHighlight.value = false
    selectedIssueId.value = activeIssues.value[0].id
    showIssueAssistant.value = true
    focusOnIssue(activeIssues.value[0])
  }
}

function handleSelectIssue(issue) {
  if (!issue) return
  userClearedHighlight.value = false
  selectedIssueId.value = issue.id
  showIssueAssistant.value = true
  focusOnIssue(issue)
}

function handleClearHighlight() {
  userClearedHighlight.value = true
  selectedIssueId.value = null
  aiPreviewFix.value = null
  showIssueAssistant.value = false
}

function focusOnIssue(issue) {
  if (!issue) return
  const affectedNodes = (issue.affected_elements?.nodes || [])
    .map((nid) => nodeMap.value[nid])
    .filter(Boolean)

  let targetX = 0
  let targetY = 0

  if (affectedNodes.length > 0) {
    targetX = affectedNodes.reduce((sum, n) => sum + n.x, 0) / affectedNodes.length
    targetY = affectedNodes.reduce((sum, n) => sum + n.y, 0) / affectedNodes.length
  } else if (issue.affected_elements?.members?.length > 0) {
    const mem = members.value.find((m) => m.id === issue.affected_elements.members[0])
    if (mem && nodeMap.value[mem.node_i] && nodeMap.value[mem.node_j]) {
      targetX = (nodeMap.value[mem.node_i].x + nodeMap.value[mem.node_j].x) / 2
      targetY = (nodeMap.value[mem.node_i].y + nodeMap.value[mem.node_j].y) / 2
    } else {
      return
    }
  } else {
    return
  }

  const rect = svgRef.value?.getBoundingClientRect()
  if (rect) {
    pan.value = {
      x: rect.width / 2 - targetX * scale.value,
      y: rect.height / 2 + targetY * scale.value,
    }
  }
}

// Compute dynamic screen anchor position for floating contextual card
const contextualCardPosition = computed(() => {
  if (!selectedIssue.value) return null
  const issue = selectedIssue.value
  const affectedNodes = (issue.affected_elements?.nodes || [])
    .map((nid) => nodeMap.value[nid])
    .filter(Boolean)

  let wx = 0
  let wy = 0

  if (affectedNodes.length > 0) {
    wx = affectedNodes.reduce((sum, n) => sum + n.x, 0) / affectedNodes.length
    wy = affectedNodes.reduce((sum, n) => sum + n.y, 0) / affectedNodes.length
  } else if (issue.affected_elements?.members?.length > 0) {
    const mem = members.value.find((m) => m.id === issue.affected_elements.members[0])
    if (mem && nodeMap.value[mem.node_i] && nodeMap.value[mem.node_j]) {
      wx = (nodeMap.value[mem.node_i].x + nodeMap.value[mem.node_j].x) / 2
      wy = (nodeMap.value[mem.node_i].y + nodeMap.value[mem.node_j].y) / 2
    } else {
      return null
    }
  } else {
    return null
  }

  const screen = toScreen(wx, wy)
  const rect = svgRef.value?.getBoundingClientRect()
  const cw = rect ? rect.width : 800
  const ch = rect ? rect.height : 600

  const cardWidth = 360
  const cardHeight = 440

  return {
    x: Math.max(16, Math.min(screen.x + 28, Math.max(16, cw - cardWidth - 16))),
    y: Math.max(16, Math.min(screen.y - 40, Math.max(16, ch - cardHeight - 16))),
  }
})

const statusCategory = computed(() => {
  if (calculating.value) return 'calculating'
  if (resultsStale.value && persistedSolverData.value) return 'stale'
  if (hasSolvedResults.value && !resultsStale.value) return 'solved'
  if (!previewResult.value) return 'neutral'
  if (!previewResult.value.is_valid) return 'red'
  if (solvability.value.status === 'solvable') return 'green'
  if (solvability.value.status === 'incomplete') return 'yellow'
  return 'red'
})

const statusPillLabel = computed(() => {
  if (calculating.value) return 'Calculating…'
  if (statusCategory.value === 'stale') return 'STALE — EDITING'
  if (statusCategory.value === 'solved') return 'SOLVED'
  return solvability.value.status.toUpperCase()
})

const reviewChipClass = computed(() => {
  const map = {
    reviewed: 'chip-reviewed',
    draft: 'chip-draft',
    submitted: 'chip-submitted',
  }
  return map[reviewStatus.value] || 'chip-pending'
})

const canSave = computed(() => coordinatesConfirmed.value && !saving.value)
const canReview = computed(() => previewResult.value?.is_valid && !reviewing.value)
const canSolve = computed(() => reviewStatus.value === 'reviewed' && !solving.value)

// Connected members for the selected joint
const connectedMembers = computed(() => {
  if (selectedElement.value?.type !== 'node') return []
  const id = selectedElement.value.id
  return members.value.filter((m) => m.node_i === id || m.node_j === id)
})

// --- Coordinate Transformations ---
// World (Engineering): positive x right, positive y UPWARD
// Screen (SVG pixels): positive x right, positive y DOWNWARD
function toScreen(wx, wy) {
  return {
    x: pan.value.x + wx * scale.value,
    y: pan.value.y - wy * scale.value,
  }
}

function toWorld(sx, sy) {
  return {
    x: (sx - pan.value.x) / scale.value,
    y: (pan.value.y - sy) / scale.value,
  }
}

function snap(val) {
  if (!snapToGrid.value) return val
  return Math.round(val / snapInterval.value) * snapInterval.value
}

// --- Grid Generation ---
const gridLines = computed(() => {
  if (!showGrid.value || !svgRef.value) return []
  const rect = svgRef.value.getBoundingClientRect()
  const w = rect.width || 800
  const h = rect.height || 600

  const topLeft = toWorld(0, 0)
  const bottomRight = toWorld(w, h)

  const minX = Math.floor(topLeft.x) - 1
  const maxX = Math.ceil(bottomRight.x) + 1
  const minY = Math.floor(bottomRight.y) - 1
  const maxY = Math.ceil(topLeft.y) + 1

  const lines = []
  for (let x = minX; x <= maxX; x += 1) {
    const s1 = toScreen(x, minY)
    const s2 = toScreen(x, maxY)
    lines.push({ x1: s1.x, y1: s1.y, x2: s2.x, y2: s2.y, major: x % 5 === 0, isAxis: x === 0 })
  }
  for (let y = minY; y <= maxY; y += 1) {
    const s1 = toScreen(minX, y)
    const s2 = toScreen(maxX, y)
    lines.push({ x1: s1.x, y1: s1.y, x2: s2.x, y2: s2.y, major: y % 5 === 0, isAxis: y === 0 })
  }
  return lines
})

// --- History / Undo / Redo ---
function pushHistory() {
  const skipRevisionBump = Boolean(arguments[0])
  if (isHistoryNavigating.value) return
  const snapshot = JSON.stringify(geometry.value)
  if (historyIndex.value >= 0 && historyStack.value[historyIndex.value] === snapshot) return
  historyStack.value = historyStack.value.slice(0, historyIndex.value + 1)
  historyStack.value.push(snapshot)
  historyIndex.value = historyStack.value.length - 1
  isDirty.value = true
  if (!skipRevisionBump) {
    designModelRevision.value += 1
  }
  if (persistedSolverData.value) {
    resultsStale.value = true
  }
  schedulePreview()
}

function undo() {
  if (historyIndex.value > 0) {
    isHistoryNavigating.value = true
    historyIndex.value -= 1
    geometry.value = JSON.parse(historyStack.value[historyIndex.value])
    isDirty.value = true
    if (persistedSolverData.value) {
      resultsStale.value = true
    }
    isHistoryNavigating.value = false
    schedulePreview()
  }
}

function redo() {
  if (historyIndex.value < historyStack.value.length - 1) {
    isHistoryNavigating.value = true
    historyIndex.value += 1
    geometry.value = JSON.parse(historyStack.value[historyIndex.value])
    isDirty.value = true
    if (persistedSolverData.value) {
      resultsStale.value = true
    }
    isHistoryNavigating.value = false
    schedulePreview()
  }
}

// --- Live Preview Calculation ---
function schedulePreview() {
  clearTimeout(previewDebounceTimer)
  previewDebounceTimer = setTimeout(runPreview, 250)
}

async function runPreview() {
  const seq = ++previewSeq
  calculating.value = true
  try {
    const payload = JSON.parse(JSON.stringify(geometry.value))
    const result = await previewAnalysisGeometry(payload, props.analysisId)
    if (seq === previewSeq) {
      previewResult.value = result
    }
  } catch (err) {
    if (seq === previewSeq) {
      previewResult.value = {
        is_valid: false,
        validation: { status: 'invalid', errors: [{ message: err.message, code: 'NETWORK_ERROR' }], warnings: [] },
        solvability: { status: 'unsolvable', category: 'API_ERROR', message: err.message },
        solver_results: null,
      }
    }
  } finally {
    calculating.value = false
  }
}

// --- Model Editing Helpers ---
function nextId(prefix, list) {
  const existing = new Set(list.map((item) => item.id))
  let idx = 1
  while (existing.has(`${prefix}${idx}`)) idx += 1
  return `${prefix}${idx}`
}

function addJointAt(wx, wy) {
  const id = nextId('J', nodes.value)
  geometry.value.model.nodes.push({ id, x: Number(wx.toFixed(3)), y: Number(wy.toFixed(3)) })
  selectedElement.value = { type: 'node', id }
  pushHistory()
}

function addMemberBetween(nodeI, nodeJ) {
  if (nodeI === nodeJ) return
  const existing = members.value.find(
    (m) => (m.node_i === nodeI && m.node_j === nodeJ) || (m.node_i === nodeJ && m.node_j === nodeI)
  )
  if (existing) {
    selectedElement.value = { type: 'member', id: existing.id }
    return
  }
  const id = nextId('M', members.value)
  geometry.value.model.members.push({ id, node_i: nodeI, node_j: nodeJ })
  selectedElement.value = { type: 'member', id }
  pushHistory()
}

function deleteElement(type, id) {
  if (type === 'node') {
    geometry.value.model.nodes = geometry.value.model.nodes.filter((n) => n.id !== id)
    geometry.value.model.members = geometry.value.model.members.filter(
      (m) => m.node_i !== id && m.node_j !== id
    )
    geometry.value.model.supports = geometry.value.model.supports.filter((s) => s.node !== id)
    geometry.value.model.loads = geometry.value.model.loads.filter((l) => l.node !== id)
  } else if (type === 'member') {
    geometry.value.model.members = geometry.value.model.members.filter((m) => m.id !== id)
  } else if (type === 'support') {
    geometry.value.model.supports = geometry.value.model.supports.filter((s) => s.id !== id)
  } else if (type === 'load') {
    geometry.value.model.loads = geometry.value.model.loads.filter((l) => l.id !== id)
  }
  if (selectedElement.value?.id === id) {
    selectedElement.value = null
  }
  pushHistory()
}

function toggleSupport(nodeId, desiredType) {
  const existingIndex = geometry.value.model.supports.findIndex((s) => s.node === nodeId)
  if (existingIndex >= 0) {
    const existing = geometry.value.model.supports[existingIndex]
    if (existing.type === desiredType) {
      if (desiredType === 'roller' && existing.direction === 'vertical') {
        existing.direction = 'horizontal'
      } else {
        geometry.value.model.supports.splice(existingIndex, 1)
      }
    } else {
      existing.type = desiredType
      if (desiredType === 'roller' && !existing.direction) existing.direction = 'vertical'
    }
  } else {
    const id = nextId('S', supports.value)
    geometry.value.model.supports.push({
      id,
      node: nodeId,
      type: desiredType,
      ...(desiredType === 'roller' ? { direction: 'vertical' } : {}),
    })
  }
  pushHistory()
}

function addOrEditLoad(nodeId, fx = 0, fy = -10) {
  const existing = geometry.value.model.loads.find((l) => l.node === nodeId)
  if (existing) {
    existing.fx = Number(fx)
    existing.fy = Number(fy)
  } else {
    const id = nextId('L', loads.value)
    geometry.value.model.loads.push({ id, node: nodeId, fx: Number(fx), fy: Number(fy) })
  }
  pushHistory()
}

// --- Import AI Proposal ---
function importProposedJoint(joint) {
  if (nodeMap.value[joint.id]) return
  const wx = snap(joint.x / 100)
  const wy = snap(Math.max(0, (600 - joint.y) / 100))
  geometry.value.model.nodes.push({ id: joint.id, x: wx, y: wy })
  pushHistory()
}

function importProposedMember(member) {
  addMemberBetween(member.joint_i, member.joint_j)
}

function importAllProposal() {
  if (!proposal.value) return
  const pj = proposalJoints.value
  if (!pj.length) return
  const xs = pj.map((j) => j.x)
  const ys = pj.map((j) => j.y)
  const minX = Math.min(...xs)
  const maxY = Math.max(...ys)
  const span = Math.max(Math.max(...xs) - minX, maxY - Math.min(...ys), 1)

  const targetSpan = 6.0
  const factor = targetSpan / span

  geometry.value.model.nodes = pj.map((j) => ({
    id: j.id,
    x: Number(snap((j.x - minX) * factor).toFixed(2)),
    y: Number(snap((maxY - j.y) * factor).toFixed(2)),
  }))

  const validNodeIds = new Set(geometry.value.model.nodes.map((n) => n.id))
  geometry.value.model.members = (proposal.value.members || [])
    .filter((m) => validNodeIds.has(m.joint_i) && validNodeIds.has(m.joint_j) && m.joint_i !== m.joint_j)
    .map((m) => ({ id: m.id, node_i: m.joint_i, node_j: m.joint_j }))

  geometry.value.model.supports = (proposal.value.supports || []).map((s) => {
    let nodeId = s.node || s.joint
    if (!nodeId && s.x != null && s.y != null) {
      let closest = null
      let minDist = Infinity
      for (const j of pj) {
        const d = Math.hypot(j.x - s.x, j.y - s.y)
        if (d < minDist) {
          minDist = d
          closest = j.id
        }
      }
      nodeId = closest
    }
    const supType = ['pin', 'roller'].includes(String(s.possible_type || s.type).toLowerCase())
      ? String(s.possible_type || s.type).toLowerCase()
      : 'pin'
    return {
      id: s.id,
      node: nodeId,
      type: supType,
      ...(supType === 'roller' ? { direction: 'vertical' } : {}),
    }
  }).filter((s) => s.node && validNodeIds.has(s.node))

  geometry.value.model.loads = (proposal.value.loads || []).map((l) => {
    let nodeId = l.node || l.joint
    if (!nodeId && l.x != null && l.y != null) {
      let closest = null
      let minDist = Infinity
      for (const j of pj) {
        const d = Math.hypot(j.x - l.x, j.y - l.y)
        if (d < minDist) {
          minDist = d
          closest = j.id
        }
      }
      nodeId = closest
    }
    const mag = Number(l.magnitude) || 10
    const dir = String(l.direction || '').toLowerCase()
    let fx = 0
    let fy = -mag
    if (dir.includes('up')) fy = mag
    else if (dir.includes('left')) { fx = -mag; fy = 0 }
    else if (dir.includes('right')) { fx = mag; fy = 0 }
    return {
      id: l.id,
      node: nodeId,
      fx,
      fy,
    }
  }).filter((l) => l.node && validNodeIds.has(l.node))

  pushHistory()
  fitView()
}

function clearModel() {
  openConfirm({
    title: 'Clear Model',
    message: 'This will remove all joints, members, supports and loads. This action can be undone.',
    confirmLabel: 'Clear All',
    cancelLabel: 'Cancel',
    variant: 'danger',
    onConfirm: () => {
      geometry.value.model = { nodes: [], members: [], supports: [], loads: [] }
      selectedElement.value = null
      if (persistedSolverData.value) {
        resultsStale.value = true
      }
      pushHistory()
    },
  })
}

// --- Canvas Navigation / Zoom / Pan ---
function fitView() {
  if (!nodes.value.length) {
    pan.value = { x: 300, y: 300 }
    scale.value = 60
    return
  }
  const xs = nodes.value.map((n) => n.x)
  const ys = nodes.value.map((n) => n.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)

  const spanX = Math.max(maxX - minX, 1)
  const spanY = Math.max(maxY - minY, 1)

  const rect = svgRef.value?.getBoundingClientRect() || { width: 800, height: 600 }
  const paddingX = Math.min(60, Math.max(16, Math.floor(rect.width * 0.08)))
  const paddingY = Math.min(50, Math.max(16, Math.floor(rect.height * 0.1)))
  const availW = Math.max(rect.width - paddingX * 2, 80)
  const availH = Math.max(rect.height - paddingY * 2, 60)

  const fitScale = Math.min(availW / spanX, availH / spanY, 150)
  scale.value = Math.max(fitScale, 15)

  const midX = (minX + maxX) / 2
  const midY = (minY + maxY) / 2
  pan.value = {
    x: rect.width / 2 - midX * scale.value,
    y: rect.height / 2 + midY * scale.value,
  }
}

function zoomAt(factor, clientX, clientY) {
  const rect = svgRef.value.getBoundingClientRect()
  const sx = clientX - rect.left
  const sy = clientY - rect.top

  const oldScale = scale.value
  const newScale = Math.max(Math.min(oldScale * factor, 300), 15)

  pan.value = {
    x: sx - (sx - pan.value.x) * (newScale / oldScale),
    y: sy - (sy - pan.value.y) * (newScale / oldScale),
  }
  scale.value = newScale
}

function handleWheel(e) {
  // If the event originated inside floating UI (issue assistant, status bar, drawers), do not zoom canvas
  if (e.target && e.target.closest && e.target.closest('.contextual-action-card, .assistant-minimized-pill, .warnings-drawer, .editor-statusbar, .analysis-results-panel')) {
    return
  }
  e.preventDefault()
  const factor = e.deltaY < 0 ? 1.15 : 0.87
  zoomAt(factor, e.clientX, e.clientY)
}

function handlePointerDown(e) {
  // If pointer event originated inside floating UI controls, do not handle canvas interactions
  if (e.target && e.target.closest && e.target.closest('.contextual-action-card, .assistant-minimized-pill, .warnings-drawer, .editor-statusbar, .analysis-results-panel')) {
    return
  }

  if (e.button === 1 || activeTool.value === 'pan' || e.spaceKey) {
    isDragging.value = true
    dragStart.value = { x: e.clientX, y: e.clientY }
    initialPan.value = { ...pan.value }
    return
  }

  const rect = svgRef.value.getBoundingClientRect()
  const sx = e.clientX - rect.left
  const sy = e.clientY - rect.top
  const world = toWorld(sx, sy)

  if (activeTool.value === 'joint') {
    const wx = snap(world.x)
    const wy = snap(world.y)
    addJointAt(wx, wy)
  } else if (activeTool.value === 'measure') {
    if (!measureStart.value) {
      measureStart.value = { x: snap(world.x), y: snap(world.y) }
      measureDistance.value = null
    } else {
      const p2 = { x: snap(world.x), y: snap(world.y) }
      const dx = p2.x - measureStart.value.x
      const dy = p2.y - measureStart.value.y
      measureDistance.value = Math.sqrt(dx * dx + dy * dy).toFixed(3)
      measureStart.value = null
    }
  } else if (activeTool.value === 'select') {
    if (e.target.tagName === 'svg' || e.target.classList.contains('svg-grid-line')) {
      selectedElement.value = null
      memberStartJoint.value = null
    }
  }
}

function handlePointerMove(e) {
  if (e.target && e.target.closest && e.target.closest('.contextual-action-card, .assistant-minimized-pill, .warnings-drawer, .editor-statusbar') && !isDragging.value && !draggingNodeId.value) {
    return
  }

  const rect = svgRef.value.getBoundingClientRect()
  const sx = e.clientX - rect.left
  const sy = e.clientY - rect.top
  const world = toWorld(sx, sy)
  cursorCoords.value = { x: Number(world.x.toFixed(3)), y: Number(world.y.toFixed(3)) }

  if (isDragging.value) {
    pan.value = {
      x: initialPan.value.x + (e.clientX - dragStart.value.x),
      y: initialPan.value.y + (e.clientY - dragStart.value.y),
    }
  } else if (draggingNodeId.value) {
    hasDraggedNode.value = true
    const node = nodeMap.value[draggingNodeId.value]
    if (node) {
      node.x = Number(snap(world.x).toFixed(3))
      node.y = Number(snap(world.y).toFixed(3))
      if (persistedSolverData.value) {
        resultsStale.value = true
      }
      schedulePreview()
    }
  }
}

function handlePointerUp() {
  if (isDragging.value) {
    isDragging.value = false
  }
  if (draggingNodeId.value) {
    if (hasDraggedNode.value) {
      pushHistory()
    }
    draggingNodeId.value = null
    hasDraggedNode.value = false
  }
}

function handleJointClick(node, e) {
  e.stopPropagation()
  if (activeTool.value === 'select') {
    selectedElement.value = { type: 'node', id: node.id }
  } else if (activeTool.value === 'member') {
    if (!memberStartJoint.value) {
      memberStartJoint.value = node.id
    } else {
      addMemberBetween(memberStartJoint.value, node.id)
      memberStartJoint.value = null
    }
  } else if (activeTool.value === 'delete') {
    deleteElement('node', node.id)
  } else if (activeTool.value === 'pin') {
    toggleSupport(node.id, 'pin')
  } else if (activeTool.value === 'roller') {
    toggleSupport(node.id, 'roller')
  } else if (activeTool.value === 'load') {
    selectedElement.value = { type: 'node', id: node.id }
  }
}

function handleJointPointerDown(node, e) {
  if (activeTool.value === 'select') {
    e.stopPropagation()
    selectedElement.value = { type: 'node', id: node.id }
    draggingNodeId.value = node.id
    hasDraggedNode.value = false
  }
}

function handleMemberClick(member, e) {
  e.stopPropagation()
  if (activeTool.value === 'select') {
    selectedElement.value = { type: 'member', id: member.id }
  } else if (activeTool.value === 'delete') {
    deleteElement('member', member.id)
  }
}

function selectWarning(warning) {
  if (warning.element_id) {
    if (nodeMap.value[warning.element_id]) {
      selectedElement.value = { type: 'node', id: warning.element_id }
    } else {
      selectedElement.value = { type: 'member', id: warning.element_id }
    }
  }
  showWarningsDrawer.value = false
}

// --- Element Geometry Calculations for SVG ---
function memberLine(member) {
  const n1 = nodeMap.value[member.node_i]
  const n2 = nodeMap.value[member.node_j]
  if (!n1 || !n2) return null
  const s1 = toScreen(n1.x, n1.y)
  const s2 = toScreen(n2.x, n2.y)
  return { x1: s1.x, y1: s1.y, x2: s2.x, y2: s2.y, mx: (s1.x + s2.x) / 2, my: (s1.y + s2.y) / 2 }
}

function memberState(memberId) {
  if (resultsStale.value || !solverResults.value) return 'unsolved'
  if (solverResults.value.member_states?.[memberId]) {
    return solverResults.value.member_states[memberId]
  }
  const val = solverResults.value.member_forces?.[memberId]
  if (val == null) return 'unsolved'
  const force = Number(val)
  if (Math.abs(force) < 1e-6) return 'zero'
  return force > 0 ? 'tension' : 'compression'
}

function memberForceText(memberId) {
  if (resultsStale.value || !solverResults.value) return ''
  const val = solverResults.value.member_forces?.[memberId]
  if (val == null) return ''
  const force = Number(val).toFixed(2)
  const unit = solverResults.value.force_unit || geometry.value.metadata?.units?.force || 'kN'
  return `${Number(val) > 0 ? '+' : ''}${force} ${unit}`
}

const calculatedReactions = computed(() => {
  if (resultsStale.value || !solverResults.value?.support_reactions) return []
  const reactionsObj = solverResults.value.support_reactions
  const list = []
  const forceUnit = solverResults.value.force_unit || geometry.value.metadata?.units?.force || 'kN'

  for (const sup of supports.value) {
    const rxData = reactionsObj[sup.id] || reactionsObj[sup.node] || {}
    const fx = typeof rxData.x === 'number' ? rxData.x : 0
    const fy = typeof rxData.y === 'number' ? rxData.y : 0
    const node = nodeMap.value[sup.node]
    if (!node) continue

    const pt = toScreen(node.x, node.y)
    const hasFx = Math.abs(fx) >= 1e-4
    const hasFy = Math.abs(fy) >= 1e-4
    const magnitude = Math.sqrt(fx * fx + fy * fy)

    list.push({
      supportId: sup.id,
      nodeId: sup.node,
      supportType: sup.type,
      pt,
      fx,
      fy,
      hasFx,
      hasFy,
      isZero: !hasFx && !hasFy,
      magnitude,
      forceUnit,
      fxLabel: `Rx: ${fx >= 0 ? '+' : ''}${fx.toFixed(2)} ${forceUnit}`,
      fyLabel: `Ry: ${fy >= 0 ? '+' : ''}${fy.toFixed(2)} ${forceUnit}`,
      zeroLabel: `R: 0.00 ${forceUnit}`,
    })
  }
  return list
})

function handleSelectMemberFromResults(memberId) {
  selectedElement.value = { type: 'member', id: memberId }
  const member = members.value.find((m) => m.id === memberId)
  if (member) {
    const coords = memberLine(member)
    if (coords && svgRef.value) {
      const rect = svgRef.value.getBoundingClientRect()
      pan.value = {
        x: rect.width / 2 - (coords.mx - pan.value.x),
        y: rect.height / 2 - (coords.my - pan.value.y),
      }
    }
  }
}

async function handleReSolve() {
  if (reviewStatus.value !== 'reviewed') {
    await saveDraft()
    await markReviewed()
  }
  await submitToSolver()
}

function memberLength(member) {
  const n1 = nodeMap.value[member.node_i]
  const n2 = nodeMap.value[member.node_j]
  if (!n1 || !n2) return 0
  const dx = n2.x - n1.x
  const dy = n2.y - n1.y
  return Math.sqrt(dx * dx + dy * dy).toFixed(3)
}

function nodeLoads(nodeId) {
  return loads.value.filter((l) => l.node === nodeId)
}

function nodeSupport(nodeId) {
  return supports.value.find((s) => s.node === nodeId)
}

// --- Persistence & Workflow Actions ---
async function saveDraft() {
  if (!coordinatesConfirmed.value) {
    showToast('Please confirm that coordinates are in physical units before saving.', 'error')
    return
  }
  saving.value = true
  statusMessage.value = ''
  try {
    const payload = JSON.parse(JSON.stringify(geometry.value))
    const needReopen = reviewStatus.value === 'submitted' || Boolean(persistedSolverData.value)
    if (needReopen) {
      await saveAnalysisDraft(props.analysisId, payload, true, true)
    } else {
      await saveAnalysisDraft(props.analysisId, payload, true)
    }
    isDirty.value = false
    reviewStatus.value = 'draft'
    statusMessage.value = 'Draft saved.'
    showToast('Draft saved successfully.', 'success')
    emit('updated')
  } catch (err) {
    showToast(err.message || 'Failed to save draft.', 'error')
  } finally {
    saving.value = false
  }
}

async function markReviewed() {
  if (isDirty.value) {
    await saveDraft()
  }
  reviewing.value = true
  try {
    await markAnalysisReviewed(props.analysisId)
    reviewStatus.value = 'reviewed'
    statusMessage.value = 'Model marked as reviewed.'
    showToast('Model marked as reviewed and ready for solver.', 'success')
    emit('updated')
  } catch (err) {
    showToast(err.message || 'Failed to mark reviewed.', 'error')
  } finally {
    reviewing.value = false
  }
}

async function submitToSolver() {
  if (reviewStatus.value !== 'reviewed') {
    showToast('Please mark the model as reviewed before submitting.', 'error')
    return
  }
  openConfirm({
    title: 'Submit to Solver',
    message: 'Submit the reviewed geometry to the deterministic equilibrium solver? This will compute member forces and support reactions.',
    confirmLabel: 'Submit',
    cancelLabel: 'Cancel',
    variant: 'default',
    onConfirm: async () => {
      solving.value = true
      try {
        const res = await solveReviewedAnalysis(props.analysisId)
        reviewStatus.value = 'submitted'
        persistedSolverData.value = res
        resultsStale.value = false
        showResultsPanel.value = true
        statusMessage.value = 'Truss solved successfully.'
        showToast('Truss solved successfully — analysis results available.', 'success')
        emit('updated')
        await runPreview()
        await nextTick()
        fitView()
      } catch (err) {
        showToast(err.message || 'Solver failed.', 'error')
      } finally {
        solving.value = false
      }
    },
  })
}

// --- AI Assistant (Phase 2) ---
function openAiAssistant() {
  showAiAssistant.value = true
  askAi('analyze_model')
}

function askAi(promptType) {
  aiAnalyzing.value = true
  aiSuggestions.value = []

  setTimeout(() => {
    if (promptType === 'analyze_model' || promptType === 'why_unstable') {
      if (solvability.value.status === 'solvable') {
        aiAssistantMessage.value =
          'The model is statically determinate and fully constrained. All joints are in static equilibrium, and SVD rank diagnostics confirm no kinematic mechanisms.'
      } else if (solvability.value.category === 'UNDERDETERMINED' || solvability.value.category === 'SINGULAR_SQUARE') {
        aiAssistantMessage.value =
          'The structure forms a kinematic mechanism or has unconstrained degrees of freedom. For a rigid 2D planar truss, the global equilibrium requires at least 3 non-parallel reaction components (e.g. 1 Pin and 1 Roller), and member triangulation must satisfy m + r ≥ 2j.'
        if (supports.value.length < 2 && nodes.value.length >= 2) {
          const secondNode = nodes.value[1]
          aiSuggestions.value.push({
            id: 'sugg_add_roller',
            title: `Add Roller Support at Joint ${secondNode.id}`,
            description: 'Provides horizontal constraint to satisfy the 3-support-reaction requirement.',
            action: () => toggleSupport(secondNode.id, 'roller'),
          })
        }
      } else if (validationErrors.value.length) {
        aiAssistantMessage.value = `Found ${validationErrors.value.length} schema validation issues: ${validationErrors.value[0].message}. Correct these before structural evaluation.`
      } else {
        aiAssistantMessage.value = solvability.value.message || 'Construct truss members to form rigid triangles.'
      }
    } else if (promptType === 'disconnected') {
      const disconnected = validationWarnings.value.filter((w) => w.code === 'DISCONNECTED_JOINT')
      if (disconnected.length) {
        aiAssistantMessage.value = `Identified ${disconnected.length} disconnected joint(s): ${disconnected.map((d) => d.element_id).join(', ')}. Connect them with members or delete them.`
      } else {
        aiAssistantMessage.value = 'All joints are currently connected by at least one member.'
      }
    } else if (promptType === 'suggest_supports') {
      aiAssistantMessage.value =
        'For standard simply-supported planar trusses, place a Pin Support at the bottom-left joint (resisting X & Y), and a Roller Support at the bottom-right joint (resisting Y only).'
      if (nodes.value.length >= 2) {
        aiSuggestions.value.push({
          id: 'sugg_std_supports',
          title: 'Apply Standard Support Arrangement (Pin + Roller)',
          description: `Assign Pin to ${nodes.value[0].id} and Roller to ${nodes.value[nodes.value.length - 1].id}.`,
          action: () => {
            toggleSupport(nodes.value[0].id, 'pin')
            toggleSupport(nodes.value[nodes.value.length - 1].id, 'roller')
          },
        })
      }
    } else if (promptType === 'forces') {
      if (solverResults.value?.member_forces) {
        aiAssistantMessage.value =
          'Axial forces are computed from static equilibrium: positive values represent tension (blue members pulling outward on joints), negative values represent compression (red members pushing into joints).'
      } else {
        aiAssistantMessage.value = 'Solve the model first to inspect internal axial forces and support reactions.'
      }
    }
    aiAnalyzing.value = false
  }, 350)
}

function applySuggestion(sugg) {
  sugg.action()
  aiSuggestions.value = aiSuggestions.value.filter((s) => s.id !== sugg.id)
  aiAssistantMessage.value = `Applied: ${sugg.title}. Model updated.`
}

// --- Natural Language Conversational Design Assistant Handlers ---
async function handleDesignSubmit({ message, intent }) {
  designBusy.value = true
  designError.value = ''

  const currentSnapshot = JSON.parse(JSON.stringify(geometry.value))

  const context = {
    analysis_id: props.analysisId || undefined,
    model_revision: designModelRevision.value,
    model: currentSnapshot,
    units: geometry.value?.metadata?.units || { length: 'm', force: 'kN' },
    selected_element: selectedElement.value ? {
      type: selectedElement.value.type,
      id: selectedElement.value.id,
    } : null,
    diagnostics: previewResult.value?.solvability || null,
    solver_results: (!resultsStale.value && hasSolvedResults.value) ? solverResults.value : null,
  }

  try {
    const res = await designTruss({
      message,
      intent,
      context,
    })
    designProposal.value = res
    if (res.intent === 'explain') {
      showToast('Engineering explanation generated.', 'info')
    } else {
      showToast('Design proposal formulated. Review on-canvas preview.', 'info')
    }
  } catch (err) {
    if (err.body?.error === 'OUT_OF_SCOPE' || err.status === 400) {
      designError.value = err.message || 'Request is out of scope for structural design.'
    } else {
      designError.value = err.message || 'Design assistant encountered an error.'
    }
  } finally {
    designBusy.value = false
  }
}

async function handleApplyDesignProposal(proposal) {
  if (!proposal || !proposal.proposed_model) return
  designBusy.value = true
  designError.value = ''

  if (proposal.base_revision != null && proposal.base_revision !== designModelRevision.value) {
    designError.value = 'Revision conflict: Canvas model was modified after this proposal was generated. Please formulate a fresh request.'
    designBusy.value = false
    return
  }

  try {
    const res = await applyDesignProposal({
      proposal_id: proposal.proposal_id,
      analysis_id: props.analysisId || null,
      base_revision: proposal.base_revision ?? designModelRevision.value,
      proposed_model: proposal.proposed_model,
      create_record: false,
    })

    if (res.status === 'applied') {
      geometry.value = JSON.parse(JSON.stringify(res.model))
      pushHistory()
      isDirty.value = true
      designModelRevision.value = res.model_revision || (designModelRevision.value + 1)
      designProposal.value = null

      // Invalidate solver results associated with previous revision
      persistedSolverData.value = null
      resultsStale.value = true

      await runPreview()
      showToast('Design proposal applied successfully.', 'success')
      emit('updated')
    }
  } catch (err) {
    if (err.status === 409) {
      designError.value = 'Revision conflict: Canvas model was modified after this proposal was generated. Please formulate a fresh request.'
    } else {
      designError.value = err.message || 'Failed to apply design proposal.'
    }
  } finally {
    designBusy.value = false
  }
}

async function handleRejectDesignProposal(proposal) {
  if (!proposal) return
  designBusy.value = true
  try {
    await rejectDesignProposal({
      proposal_id: proposal.proposal_id,
      analysis_id: props.analysisId || null,
      base_revision: proposal.base_revision ?? designModelRevision.value,
    })
    designProposal.value = null
    showToast('Design proposal discarded. Canvas geometry preserved.', 'info')
  } catch (err) {
    designProposal.value = null
  } finally {
    designBusy.value = false
  }
}

// --- Floating AI Issue Resolution Assistant Handlers ---
function handleHighlightIssue(issue) {
  if (!issue) return
  if (issue.element_id) {
    if (nodes.value.some((n) => n.id === issue.element_id)) {
      selectedElement.value = { type: 'node', id: issue.element_id }
    } else if (members.value.some((m) => m.id === issue.element_id)) {
      selectedElement.value = { type: 'member', id: issue.element_id }
    }
  }
}

function handlePreviewFix(fix) {
  aiPreviewFix.value = fix
}

function handleClearPreview() {
  aiPreviewFix.value = null
}

async function applyAiFix(fix) {
  if (!fix || !fix.modifications) return

  // Stale check
  if (fix.base_revision != null && fix.base_revision !== designModelRevision.value) {
    showToast('Cannot apply fix: model has changed since this recommendation was created. Please generate a fresh fix.', 'error')
    aiPreviewFix.value = null
    return
  }

  const mods = fix.modifications
  const newModel = JSON.parse(JSON.stringify(geometry.value.model))

  // 1. Removals
  if (mods.nodes_to_remove?.length) {
    const toRemove = new Set(mods.nodes_to_remove)
    newModel.nodes = newModel.nodes.filter((n) => !toRemove.has(n.id))
    newModel.members = newModel.members.filter((m) => !toRemove.has(m.node_i) && !toRemove.has(m.node_j))
    newModel.supports = newModel.supports.filter((s) => !toRemove.has(s.node))
    newModel.loads = newModel.loads.filter((l) => !toRemove.has(l.node))
  }

  if (mods.members_to_remove?.length) {
    const toRemove = new Set(mods.members_to_remove)
    newModel.members = newModel.members.filter((m) => !toRemove.has(m.id))
  }

  if (mods.supports_to_remove?.length) {
    const toRemove = new Set(mods.supports_to_remove)
    newModel.supports = newModel.supports.filter((s) => !toRemove.has(s.id))
  }

  if (mods.loads_to_remove?.length) {
    const toRemove = new Set(mods.loads_to_remove)
    newModel.loads = newModel.loads.filter((l) => !toRemove.has(l.id))
  }

  // 2. Additions
  if (mods.nodes_to_add?.length) {
    for (const n of mods.nodes_to_add) {
      if (!newModel.nodes.some((ex) => ex.id === n.id)) {
        newModel.nodes.push({ id: n.id, x: Number(n.x), y: Number(n.y) })
      }
    }
  }

  if (mods.members_to_add?.length) {
    for (const m of mods.members_to_add) {
      // Skip if member between these two nodes already exists
      const alreadyConnected = newModel.members.some(
        (ex) => (ex.node_i === m.node_i && ex.node_j === m.node_j) || (ex.node_i === m.node_j && ex.node_j === m.node_i)
      )
      if (alreadyConnected) continue

      let memId = m.id
      if (!memId || newModel.members.some((ex) => ex.id === memId)) {
        memId = nextId('M', newModel.members)
      }
      newModel.members.push({ id: memId, node_i: m.node_i, node_j: m.node_j })
    }
  }

  if (mods.supports_to_add?.length) {
    for (const s of mods.supports_to_add) {
      // Replace existing support at the same node
      newModel.supports = newModel.supports.filter((ex) => ex.node !== s.node)

      let supId = s.id
      if (!supId || newModel.supports.some((ex) => ex.id === supId)) {
        supId = nextId('S', newModel.supports)
      }
      const supRecord = { id: supId, node: s.node, type: s.type }
      if (s.type === 'roller') {
        supRecord.direction = s.direction === 'horizontal' ? 'horizontal' : 'vertical'
      }
      newModel.supports.push(supRecord)
    }
  }

  if (mods.loads_to_add?.length) {
    for (const l of mods.loads_to_add) {
      let loadId = l.id
      if (!loadId || newModel.loads.some((ex) => ex.id === loadId)) {
        loadId = nextId('L', newModel.loads)
      }
      newModel.loads.push({ id: loadId, node: l.node, fx: Number(l.fx || 0), fy: Number(l.fy || 0) })
    }
  }

  // Reactive state update
  geometry.value = {
    ...geometry.value,
    model: newModel,
  }

  aiPreviewFix.value = null
  selectedElement.value = null
  designModelRevision.value += 1
  persistedSolverData.value = null
  resultsStale.value = true

  pushHistory()
  showToast(`Applied fix: ${fix.title}`, 'success')
  await runPreview()
}

// --- Lifecycle & Init ---
async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const analysisData = await getAnalysis(props.analysisId)
    analysis.value = analysisData
    reviewStatus.value = analysisData.review_status || 'pending_review'

    const draftData = await getAnalysisDraft(props.analysisId)
    if (draftData.draft) {
      geometry.value = JSON.parse(JSON.stringify(draftData.draft))
      coordinatesConfirmed.value = true
    } else if (analysisData.human_review?.geometry) {
      geometry.value = JSON.parse(JSON.stringify(analysisData.human_review.geometry))
      coordinatesConfirmed.value = true
    } else if (proposalJoints.value.length) {
      importAllProposal()
    }

    designModelRevision.value = analysisData.validation_json?.revision || (draftData.draft?.metadata?.revision || 1)

    if (analysisData.status === 'solved' && analysisData.solver_results) {
      persistedSolverData.value = {
        analysis_id: analysisData.id,
        status: 'SOLVED',
        diagnostics: analysisData.diagnostics,
        results: analysisData.solver_results,
        warning: 'A numerical solution does not establish physical stability or engineering suitability.',
      }
      resultsStale.value = false
      showResultsPanel.value = true
    }

    pushHistory(true)
    isDirty.value = false
    await runPreview()
    setTimeout(fitView, 100)
  } catch (err) {
    error.value = err.message || 'Failed to load analysis.'
  } finally {
    loading.value = false
  }
}

function handleKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault()
    if (e.shiftKey) redo()
    else undo()
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
    e.preventDefault()
    redo()
  } else if (e.key === 'Delete' || e.key === 'Backspace') {
    if (selectedElement.value && !['INPUT', 'SELECT'].includes(document.activeElement.tagName)) {
      e.preventDefault()
      deleteElement(selectedElement.value.type, selectedElement.value.id)
    }
  } else if (e.key === 'Escape') {
    selectedElement.value = null
    memberStartJoint.value = null
    measureStart.value = null
    showWarningsDrawer.value = false
  }
}

let resizeObserver = null

watch(svgRef, (el) => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (el && typeof window !== 'undefined' && window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      if (!isDragging.value && !draggingNodeId.value) {
        fitView()
      }
    })
    resizeObserver.observe(el)
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  loadData()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  clearTimeout(previewDebounceTimer)
  clearTimeout(toastTimer)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})
</script>

<template>
  <div class="truss-editor-workspace">

    <!-- ConfirmDialog Overlay -->
    <ConfirmDialog
      v-if="dialog.open"
      :title="dialog.title"
      :message="dialog.message"
      :confirm-label="dialog.confirmLabel"
      :cancel-label="dialog.cancelLabel"
      :variant="dialog.variant"
      @confirm="handleDialogConfirm"
      @cancel="handleDialogCancel"
    />

    <!-- Toast Notification -->
    <Transition name="toast-slide">
      <div
        v-if="toastMessage"
        class="editor-toast"
        :class="`toast-${toastVariant}`"
        role="status"
        aria-live="polite"
      >
        <CheckCircle2 v-if="toastVariant === 'success'" :size="14" />
        <XCircle v-else-if="toastVariant === 'error'" :size="14" />
        <span>{{ toastMessage }}</span>
      </div>
    </Transition>

    <!-- ═══════════════════ TOP TOOLBAR ═══════════════════ -->
    <header class="editor-topbar">
      <!-- Left: Navigation + Title -->
      <div class="topbar-left">
        <button class="back-btn" type="button" title="Back to analysis" aria-label="Back to analysis" @click="emit('back')">
          <ArrowLeft :size="14" /> Back
        </button>
        <div class="toolbar-separator" />
        <div class="editor-title">
          <strong>{{ geometry.metadata?.name || 'Truss Editor' }}</strong>
          <small>
            #{{ analysisId?.slice(0, 8).toUpperCase() }}
            <span class="review-chip" :class="reviewChipClass">
              {{ reviewStatus.replace('_', ' ') }}
            </span>
          </small>
        </div>
      </div>

      <!-- Center: Undo/Redo, Units, Coordinate Confirm -->
      <div class="topbar-center">
        <button class="tool-btn" type="button" title="Undo (Ctrl+Z)" aria-label="Undo" :disabled="historyIndex <= 0" @click="undo">
          <Undo2 :size="15" />
        </button>
        <button class="tool-btn" type="button" title="Redo (Ctrl+Y)" aria-label="Redo" :disabled="historyIndex >= historyStack.length - 1" @click="redo">
          <Redo2 :size="15" />
        </button>

        <div class="toolbar-separator" />

        <div class="unit-selectors">
          <span>Length</span>
          <select v-model="geometry.metadata.units.length" @change="pushHistory">
            <option value="m">m</option>
            <option value="mm">mm</option>
            <option value="ft">ft</option>
          </select>
          <span>Force</span>
          <select v-model="geometry.metadata.units.force" @change="pushHistory">
            <option value="kN">kN</option>
            <option value="N">N</option>
            <option value="lbf">lbf</option>
          </select>
        </div>

        <label class="confirm-checkbox" :class="{ confirmed: coordinatesConfirmed }">
          <input v-model="coordinatesConfirmed" type="checkbox" />
          <span>Coords Confirmed</span>
        </label>
      </div>

      <!-- Right: Workflow Actions -->
      <div class="topbar-right">
        <button class="action-btn btn-save" type="button" :disabled="!canSave" @click="saveDraft">
          <Save :size="14" />
          <span>{{ saving ? 'Saving…' : isDirty ? 'Save *' : 'Saved' }}</span>
        </button>
        <button class="action-btn btn-review" type="button" :disabled="!canReview" @click="markReviewed">
          <Check :size="14" />
          <span>{{ reviewing ? 'Reviewing…' : 'Mark Reviewed' }}</span>
        </button>
        <button class="action-btn btn-solve" type="button" :disabled="!canSolve || solving" @click="submitToSolver">
          <Loader2 v-if="solving" :size="14" class="spin-icon" />
          <Play v-else :size="14" />
          <span>{{ solving ? 'Solving…' : 'Solve' }}</span>
        </button>
        <button
          v-if="hasSolvedResults"
          class="action-btn btn-results"
          :class="{ active: showResultsPanel, stale: resultsStale }"
          type="button"
          :title="showResultsPanel ? 'Hide Analysis Results' : 'View Analysis Results'"
          @click="showResultsPanel = !showResultsPanel"
        >
          <BarChart3 :size="14" />
          <span>{{ resultsStale ? 'Results *' : 'Results' }}</span>
        </button>
        <div class="toolbar-separator" />
        <button
          class="action-btn btn-ai"
          :class="{ active: activeSidebarTab === 'design' }"
          type="button"
          title="Natural Language Design Assistant"
          @click="switchSidebarTab(activeSidebarTab === 'design' ? 'tools' : 'design')"
        >
          <Sparkles :size="14" />
          <span>Design with AI</span>
        </button>
      </div>
    </header>

    <!-- ═══════════════════ MAIN BODY ═══════════════════ -->
    <div class="editor-main">

      <!-- Loading Screen -->
      <div v-if="loading" class="canvas-container">
        <div class="editor-loading-screen">
          <div class="spinner" />
          <span>Loading analysis…</span>
        </div>
      </div>

      <!-- Error Screen -->
      <div v-else-if="error" class="canvas-container">
        <div class="editor-error-screen">
          <XCircle :size="36" />
          <strong>Failed to load</strong>
          <p>{{ error }}</p>
          <button @click="loadData">Retry</button>
        </div>
      </div>

      <!-- ─── Center Canvas & Results Viewport Column ─── -->
      <div v-else class="editor-canvas-column">
        <!-- ─── Engineering Canvas Viewport ─── -->
        <div
          class="canvas-container"
          :class="{ panning: isDragging || activeTool === 'pan' }"
          @wheel="handleWheel"
          @pointerdown="handlePointerDown"
          @pointermove="handlePointerMove"
          @pointerup="handlePointerUp"
        >
          <!-- Floating View Controls -->
          <div class="canvas-floating-controls" role="toolbar" aria-label="Canvas view controls">
            <button class="tool-btn" type="button" title="Zoom In" aria-label="Zoom in" @click="zoomAt(1.2, 400, 300)"><ZoomIn :size="14" /></button>
            <button class="tool-btn" type="button" title="Zoom Out" aria-label="Zoom out" @click="zoomAt(0.83, 400, 300)"><ZoomOut :size="14" /></button>
            <button class="tool-btn" type="button" title="Fit Content" aria-label="Fit content to view" @click="fitView"><Maximize2 :size="14" /></button>
            <div class="toolbar-separator" role="separator" />
            <button class="tool-btn" :class="{ active: showGrid }" type="button" title="Toggle Grid" aria-label="Toggle grid" :aria-pressed="showGrid" @click="showGrid = !showGrid"><Grid3x3 :size="14" /></button>
            <button class="tool-btn" :class="{ active: snapToGrid }" type="button" title="Snap to Grid" aria-label="Snap to grid" :aria-pressed="snapToGrid" @click="snapToGrid = !snapToGrid"><Magnet :size="14" /></button>
            <button class="tool-btn" :class="{ active: showAiProposal }" type="button" title="AI Proposal Layer" aria-label="Toggle AI proposal layer" :aria-pressed="showAiProposal" @click="showAiProposal = !showAiProposal"><Sparkles :size="14" /></button>
            <button v-if="activeIssues.length" class="tool-btn" :class="{ active: isHighlightActive }" type="button" :title="isHighlightActive ? 'Clear issue highlighting' : 'Highlight detected issues'" :aria-label="isHighlightActive ? 'Clear issue highlighting' : 'Highlight detected issues'" :aria-pressed="isHighlightActive" @click="toggleHighlightMode"><AlertTriangle :size="14" /></button>
            <div v-if="hasSolvedResults" class="toolbar-separator" role="separator" />
            <button
              v-if="hasSolvedResults && !resultsStale"
              class="tool-btn"
              :class="{ active: showForceLabels }"
              type="button"
              :title="showForceLabels ? 'Hide member force labels' : 'Show member force labels'"
              :aria-label="showForceLabels ? 'Hide member force labels' : 'Show member force labels'"
              :aria-pressed="showForceLabels"
              @click="showForceLabels = !showForceLabels"
            >
              <Tag :size="14" />
            </button>
            <button
              v-if="hasSolvedResults"
              class="tool-btn"
              :class="{ active: showResultsPanel }"
              type="button"
              title="Toggle Analysis Results panel"
              aria-label="Toggle Analysis Results panel"
              :aria-pressed="showResultsPanel"
              @click="showResultsPanel = !showResultsPanel"
            >
              <BarChart3 :size="14" />
            </button>
          </div>

          <!-- Mobile Floating Construction Toolbar (Visible on <= 768px) -->
          <div class="mobile-construction-bar" role="toolbar" aria-label="Mobile construction tools">
            <button class="m-tool-btn" :class="{ active: activeTool === 'select' }" type="button" title="Select / Move" aria-label="Select tool" @click="activeTool = 'select'">
              <MousePointer :size="15" />
              <span>Select</span>
            </button>
            <button class="m-tool-btn" :class="{ active: activeTool === 'pan' }" type="button" title="Pan Canvas" aria-label="Pan canvas" @click="activeTool = 'pan'">
              <Hand :size="15" />
              <span>Pan</span>
            </button>
            <button class="m-tool-btn" :class="{ active: activeTool === 'joint' }" type="button" title="Add Joint" aria-label="Add joint tool" @click="activeTool = 'joint'">
              <PlusCircle :size="15" />
              <span>Joint</span>
            </button>
            <button class="m-tool-btn" :class="{ active: activeTool === 'member' }" type="button" title="Add Member" aria-label="Add member tool" @click="activeTool = 'member'">
              <Spline :size="15" />
              <span>Member</span>
            </button>
            <button class="m-tool-btn" :class="{ active: activeTool === 'pin' }" type="button" title="Pin Support" aria-label="Pin support tool" @click="activeTool = 'pin'">
              <Anchor :size="15" />
              <span>Pin</span>
            </button>
            <button class="m-tool-btn" :class="{ active: activeTool === 'roller' }" type="button" title="Roller Support" aria-label="Roller support tool" @click="activeTool = 'roller'">
              <CircleDot :size="15" />
              <span>Roller</span>
            </button>
            <button class="m-tool-btn" :class="{ active: activeTool === 'load' }" type="button" title="Add Load" aria-label="Add load tool" @click="activeTool = 'load'">
              <ArrowDown :size="15" />
              <span>Load</span>
            </button>
            <button class="m-tool-btn tool-delete" :class="{ active: activeTool === 'delete' }" type="button" title="Delete" aria-label="Delete tool" @click="activeTool = 'delete'">
              <Trash2 :size="15" />
              <span>Delete</span>
            </button>
          </div>

        <!-- Floating Forces Color Legend -->
        <div v-if="hasSolvedResults && !resultsStale" class="canvas-forces-legend" aria-label="Analysis Legend">
          <div class="legend-header">
            <span class="legend-title">Forces Legend</span>
          </div>
          <div class="legend-grid">
            <div class="legend-row">
              <span class="legend-swatch swatch-tension" />
              <span class="legend-text">Tension (+)</span>
            </div>
            <div class="legend-row">
              <span class="legend-swatch swatch-compression" />
              <span class="legend-text">Compression (−)</span>
            </div>
            <div class="legend-row">
              <span class="legend-swatch swatch-zero" />
              <span class="legend-text">Zero-Force (0)</span>
            </div>
            <div class="legend-row">
              <span class="legend-swatch swatch-reaction" />
              <span class="legend-text">Reaction (R)</span>
            </div>
          </div>
        </div>

        <!-- Mode hint: member start -->
        <div v-if="memberStartJoint" class="canvas-mode-hint">
          Click another joint to connect — or Esc to cancel
        </div>
        <div v-else-if="measureStart" class="canvas-mode-hint">
          Click a second point to measure distance
        </div>

        <!-- Coordinate Readout -->
        <div class="canvas-coords-overlay">
          X: {{ cursorCoords.x.toFixed(3) }} {{ geometry.metadata?.units?.length }}
          · Y: {{ cursorCoords.y.toFixed(3) }} {{ geometry.metadata?.units?.length }}
          <span v-if="measureDistance"> · Dist: {{ measureDistance }} {{ geometry.metadata?.units?.length }}</span>
        </div>

        <!-- ─── SVG Rendering Plane ─── -->
        <svg ref="svgRef" class="engineering-svg">
          <defs>
            <marker id="arrow-load" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
              <path d="M 0 0 L 8 4 L 0 8 Z" fill="#d97706" />
            </marker>
          </defs>

          <!-- 1. Grid -->
          <g v-if="showGrid" class="grid-group">
            <line
              v-for="(line, idx) in gridLines"
              :key="`grid-${idx}`"
              :x1="line.x1" :y1="line.y1" :x2="line.x2" :y2="line.y2"
              :class="['svg-grid-line', { major: line.major, 'svg-axis-line': line.isAxis }]"
            />
          </g>

          <!-- 2. Origin Marker -->
          <g class="origin-group">
            <circle :cx="pan.x" :cy="pan.y" r="3" fill="#0f172a" />
            <text :x="pan.x + 6" :y="pan.y + 12" class="svg-origin-label">(0,0)</text>
          </g>

          <!-- 3. AI Proposal Reference Layer -->
          <g v-if="showAiProposal" class="ai-proposal-layer">
            <line
              v-for="pm in proposalMembers"
              :key="`prop-m-${pm.id}`"
              :x1="toScreen(proposalJoints.find((j) => j.id === pm.joint_i)?.x / 100 || 0, Math.max(0, (600 - (proposalJoints.find((j) => j.id === pm.joint_i)?.y || 0)) / 100)).x"
              :y1="toScreen(proposalJoints.find((j) => j.id === pm.joint_i)?.x / 100 || 0, Math.max(0, (600 - (proposalJoints.find((j) => j.id === pm.joint_i)?.y || 0)) / 100)).y"
              :x2="toScreen(proposalJoints.find((j) => j.id === pm.joint_j)?.x / 100 || 0, Math.max(0, (600 - (proposalJoints.find((j) => j.id === pm.joint_j)?.y || 0)) / 100)).x"
              :y2="toScreen(proposalJoints.find((j) => j.id === pm.joint_j)?.x / 100 || 0, Math.max(0, (600 - (proposalJoints.find((j) => j.id === pm.joint_j)?.y || 0)) / 100)).y"
              class="ai-proposal-member"
              @click.stop="importProposedMember(pm)"
            />
            <circle
              v-for="pj in proposalJoints"
              :key="`prop-j-${pj.id}`"
              :cx="toScreen(pj.x / 100, Math.max(0, (600 - pj.y) / 100)).x"
              :cy="toScreen(pj.x / 100, Math.max(0, (600 - pj.y) / 100)).y"
              r="5"
              class="ai-proposal-joint"
              @click.stop="importProposedJoint(pj)"
            />
          </g>

          <!-- 4. Draft Members -->
          <g class="truss-members-group">
            <g v-for="member in members" :key="`m-${member.id}`">
              <template v-if="memberLine(member)">
                <line
                  :x1="memberLine(member).x1" :y1="memberLine(member).y1"
                  :x2="memberLine(member).x2" :y2="memberLine(member).y2"
                  :class="[
                    'truss-member-line',
                    `state-${memberState(member.id)}`,
                    {
                      selected: selectedElement?.id === member.id,
                      'is-muted': isHighlightActive && !affectedMemberIds.has(member.id),
                      'issue-highlight-error': isHighlightActive && affectedMemberIds.has(member.id) && (selectedIssue?.severity === 'error' || selectedIssue?.classification === 'invalid_geometry'),
                      'issue-highlight-mechanism': isHighlightActive && affectedMemberIds.has(member.id) && (selectedIssue?.severity === 'mechanism' || selectedIssue?.classification === 'mechanism'),
                      'issue-highlight-warning': isHighlightActive && affectedMemberIds.has(member.id) && selectedIssue?.severity === 'warning' && selectedIssue?.classification !== 'mechanism',
                    }
                  ]"
                  @click.stop="handleMemberClick(member, $event)"
                />
                <text
                  :x="memberLine(member).mx"
                  :y="memberLine(member).my - 7"
                  :class="['member-label', { 'is-muted': isHighlightActive && !affectedMemberIds.has(member.id) }]"
                >
                  {{ member.id }}
                </text>
                <text
                  v-if="showForceLabels && !resultsStale && memberForceText(member.id)"
                  :x="memberLine(member).mx"
                  :y="memberLine(member).my + 9"
                  :class="['member-force-label', memberState(member.id), { 'is-muted': isHighlightActive && !affectedMemberIds.has(member.id) }]"
                >
                  {{ memberForceText(member.id) }}
                </text>
              </template>
            </g>
          </g>

          <!-- 5. Supports -->
          <g class="truss-supports-group">
            <g v-for="support in supports" :key="`sup-${support.id}`">
              <template v-if="nodeMap[support.node]">
                <g
                  v-if="support.type === 'pin'"
                  :transform="`translate(${toScreen(nodeMap[support.node].x, nodeMap[support.node].y).x}, ${toScreen(nodeMap[support.node].x, nodeMap[support.node].y).y})`"
                  :class="{ 'is-muted': isHighlightActive && !affectedNodeIds.has(support.node) }"
                >
                  <polygon points="0,0 -12,18 12,18" class="support-symbol" />
                  <line x1="-16" y1="18" x2="16" y2="18" class="support-hatch" />
                </g>
                <g
                  v-else-if="support.type === 'roller'"
                  :transform="`translate(${toScreen(nodeMap[support.node].x, nodeMap[support.node].y).x}, ${toScreen(nodeMap[support.node].x, nodeMap[support.node].y).y})`"
                  :class="{ 'is-muted': isHighlightActive && !affectedNodeIds.has(support.node) }"
                >
                  <circle cx="0" cy="8" r="7" class="support-symbol" />
                  <line x1="-14" y1="16" x2="14" y2="16" class="support-hatch" />
                </g>
              </template>
            </g>
          </g>

          <!-- 5b. Support Reaction Vectors (rendered when solved and not stale) -->
          <g v-if="hasSolvedResults && !resultsStale" class="truss-reactions-group">
            <g v-for="rx in calculatedReactions" :key="`rx-vec-${rx.supportId}`">
              <!-- Vertical Reaction Vector Fy -->
              <template v-if="rx.hasFy">
                <!-- Upward reaction (+Fy) -->
                <template v-if="rx.fy > 0">
                  <line
                    :x1="rx.pt.x" :y1="rx.pt.y + 42"
                    :x2="rx.pt.x" :y2="rx.pt.y + 14"
                    class="reaction-vector-line"
                  />
                  <polygon
                    :points="`${rx.pt.x},${rx.pt.y + 10} ${rx.pt.x - 5},${rx.pt.y + 19} ${rx.pt.x + 5},${rx.pt.y + 19}`"
                    class="reaction-arrowhead"
                  />
                  <text :x="rx.pt.x + 8" :y="rx.pt.y + 34" class="reaction-vector-label">
                    {{ rx.fyLabel }}
                  </text>
                </template>
                <!-- Downward reaction (-Fy) -->
                <template v-else>
                  <line
                    :x1="rx.pt.x" :y1="rx.pt.y - 42"
                    :x2="rx.pt.x" :y2="rx.pt.y - 14"
                    class="reaction-vector-line"
                  />
                  <polygon
                    :points="`${rx.pt.x},${rx.pt.y - 10} ${rx.pt.x - 5},${rx.pt.y - 19} ${rx.pt.x + 5},${rx.pt.y - 19}`"
                    class="reaction-arrowhead"
                  />
                  <text :x="rx.pt.x + 8" :y="rx.pt.y - 26" class="reaction-vector-label">
                    {{ rx.fyLabel }}
                  </text>
                </template>
              </template>

              <!-- Horizontal Reaction Vector Fx -->
              <template v-if="rx.hasFx">
                <!-- Rightward reaction (+Fx) -->
                <template v-if="rx.fx > 0">
                  <line
                    :x1="rx.pt.x - 42" :y1="rx.pt.y"
                    :x2="rx.pt.x - 14" :y2="rx.pt.y"
                    class="reaction-vector-line"
                  />
                  <polygon
                    :points="`${rx.pt.x - 10},${rx.pt.y} ${rx.pt.x - 19},${rx.pt.y - 5} ${rx.pt.x - 19},${rx.pt.y + 5}`"
                    class="reaction-arrowhead"
                  />
                  <text :x="rx.pt.x - 44" :y="rx.pt.y - 8" class="reaction-vector-label">
                    {{ rx.fxLabel }}
                  </text>
                </template>
                <!-- Leftward reaction (-Fx) -->
                <template v-else>
                  <line
                    :x1="rx.pt.x + 42" :y1="rx.pt.y"
                    :x2="rx.pt.x + 14" :y2="rx.pt.y"
                    class="reaction-vector-line"
                  />
                  <polygon
                    :points="`${rx.pt.x + 10},${rx.pt.y} ${rx.pt.x + 19},${rx.pt.y - 5} ${rx.pt.x + 19},${rx.pt.y + 5}`"
                    class="reaction-arrowhead"
                  />
                  <text :x="rx.pt.x + 18" :y="rx.pt.y - 8" class="reaction-vector-label">
                    {{ rx.fxLabel }}
                  </text>
                </template>
              </template>

              <!-- Zero reaction (unloaded case) -->
              <template v-if="rx.isZero">
                <text :x="rx.pt.x + 6" :y="rx.pt.y + 26" class="reaction-vector-label zero">
                  {{ rx.zeroLabel }}
                </text>
              </template>
            </g>
          </g>

          <!-- 6. Loads -->
          <g class="truss-loads-group">
            <g v-for="load in loads" :key="`load-${load.id}`">
              <template v-if="nodeMap[load.node]">
                <line
                  :x1="toScreen(nodeMap[load.node].x, nodeMap[load.node].y).x - (load.fx || 0) * 2.5"
                  :y1="toScreen(nodeMap[load.node].x, nodeMap[load.node].y).y + (load.fy || 0) * 2.5"
                  :x2="toScreen(nodeMap[load.node].x, nodeMap[load.node].y).x"
                  :y2="toScreen(nodeMap[load.node].x, nodeMap[load.node].y).y"
                  :class="['load-vector-arrow', { 'is-muted': isHighlightActive && !affectedNodeIds.has(load.node) }]"
                />
                <text
                  :x="toScreen(nodeMap[load.node].x, nodeMap[load.node].y).x - (load.fx || 0) * 2.5"
                  :y="toScreen(nodeMap[load.node].x, nodeMap[load.node].y).y + (load.fy || 0) * 2.5 - 6"
                  :class="['load-label', { 'is-muted': isHighlightActive && !affectedNodeIds.has(load.node) }]"
                >
                  {{ load.id }}: {{ load.fy ? `${load.fy} ${geometry.metadata.units.force}` : `${load.fx} ${geometry.metadata.units.force}` }}
                </text>
              </template>
            </g>
          </g>

          <!-- 7. Joints (rendered last = on top) -->
          <g class="truss-joints-group">
            <g v-for="node in nodes" :key="`n-${node.id}`">
              <circle
                :cx="toScreen(node.x, node.y).x"
                :cy="toScreen(node.x, node.y).y"
                r="7"
                :class="[
                  'truss-joint-node',
                  {
                    selected: selectedElement?.id === node.id,
                    'first-selected': memberStartJoint === node.id,
                    'is-muted': isHighlightActive && !affectedNodeIds.has(node.id),
                  }
                ]"
                @pointerdown="handleJointPointerDown(node, $event)"
                @click="handleJointClick(node, $event)"
              />
              <!-- Subtle pulsing glow ring around affected joints -->
              <circle
                v-if="isHighlightActive && affectedNodeIds.has(node.id)"
                :cx="toScreen(node.x, node.y).x"
                :cy="toScreen(node.x, node.y).y"
                r="14"
                :class="[
                  'joint-issue-pulse-ring',
                  selectedIssue?.severity === 'error' || selectedIssue?.classification === 'invalid_geometry' ? 'ring-error' : 'ring-warning',
                ]"
              />
              <text
                :x="toScreen(node.x, node.y).x + 9"
                :y="toScreen(node.x, node.y).y - 9"
                :class="['joint-label', { 'is-muted': isHighlightActive && !affectedNodeIds.has(node.id) }]"
              >
                {{ node.id }}
              </text>
            </g>
          </g>

          <!-- 8. AI Issue Assistant Proposed Fix Preview Layer (distinct Blue/Cyan) -->
          <g v-if="aiPreviewFix" class="ai-fix-preview-group">
            <g v-for="m in aiPreviewFix.modifications?.members_to_add || []" :key="`prev-m-${m.id}`">
              <line
                v-if="nodeMap[m.node_i] && nodeMap[m.node_j]"
                :x1="toScreen(nodeMap[m.node_i].x, nodeMap[m.node_i].y).x"
                :y1="toScreen(nodeMap[m.node_i].x, nodeMap[m.node_i].y).y"
                :x2="toScreen(nodeMap[m.node_j].x, nodeMap[m.node_j].y).x"
                :y2="toScreen(nodeMap[m.node_j].x, nodeMap[m.node_j].y).y"
                class="ai-proposed-member-line"
              />
            </g>
            <g v-for="s in aiPreviewFix.modifications?.supports_to_add || []" :key="`prev-s-${s.id}`">
              <g v-if="nodeMap[s.node]" :transform="`translate(${toScreen(nodeMap[s.node].x, nodeMap[s.node].y).x}, ${toScreen(nodeMap[s.node].x, nodeMap[s.node].y).y})`">
                <circle cx="0" cy="0" r="14" class="ai-proposed-support-ring" />
              </g>
            </g>
          </g>

          <!-- 9. Natural Language Conversational Design Proposal Preview Layer -->
          <g v-if="designProposal && designProposal.operations" class="design-proposal-canvas-layer">
            <!-- Proposed Added Members: Cyan dashed line (#0284c7) -->
            <g v-for="(op, idx) in designProposedAdditions" :key="`nl-add-m-${idx}`">
              <line
                v-if="effectiveNodeMap[op.node_i] && effectiveNodeMap[op.node_j]"
                :x1="toScreen(effectiveNodeMap[op.node_i].x, effectiveNodeMap[op.node_i].y).x"
                :y1="toScreen(effectiveNodeMap[op.node_i].x, effectiveNodeMap[op.node_i].y).y"
                :x2="toScreen(effectiveNodeMap[op.node_j].x, effectiveNodeMap[op.node_j].y).x"
                :y2="toScreen(effectiveNodeMap[op.node_j].x, effectiveNodeMap[op.node_j].y).y"
                class="design-preview-member-added"
              />
              <text
                v-if="effectiveNodeMap[op.node_i] && effectiveNodeMap[op.node_j]"
                :x="(toScreen(effectiveNodeMap[op.node_i].x, effectiveNodeMap[op.node_i].y).x + toScreen(effectiveNodeMap[op.node_j].x, effectiveNodeMap[op.node_j].y).x) / 2"
                :y="(toScreen(effectiveNodeMap[op.node_i].x, effectiveNodeMap[op.node_i].y).y + toScreen(effectiveNodeMap[op.node_j].x, effectiveNodeMap[op.node_j].y).y) / 2 - 8"
                class="design-preview-label added"
              >
                +{{ op.id }}
              </text>
            </g>

            <!-- Proposed Deleted Members: Red dashed line (#ef4444) -->
            <g v-for="delId in designProposedRemovals" :key="`nl-del-m-${delId}`">
              <template v-if="memberMap[delId] && memberLine(memberMap[delId])">
                <line
                  :x1="memberLine(memberMap[delId]).x1"
                  :y1="memberLine(memberMap[delId]).y1"
                  :x2="memberLine(memberMap[delId]).x2"
                  :y2="memberLine(memberMap[delId]).y2"
                  class="design-preview-member-deleted"
                />
              </template>
            </g>

            <!-- Proposed Added or Moved Joints: Cyan / Amber markers -->
            <g v-for="(op, idx) in designProposedJointOps" :key="`nl-j-op-${idx}`">
              <template v-if="effectiveNodeMap[op.id]">
                <circle
                  :cx="toScreen(effectiveNodeMap[op.id].x, effectiveNodeMap[op.id].y).x"
                  :cy="toScreen(effectiveNodeMap[op.id].x, effectiveNodeMap[op.id].y).y"
                  r="9"
                  :class="['design-preview-joint', op.op === 'add_joint' ? 'added' : 'modified']"
                />
                <text
                  :x="toScreen(effectiveNodeMap[op.id].x, effectiveNodeMap[op.id].y).x + 10"
                  :y="toScreen(effectiveNodeMap[op.id].x, effectiveNodeMap[op.id].y).y - 10"
                  class="design-preview-label"
                >
                  {{ op.op === 'add_joint' ? `+${op.id}` : `Δ${op.id}` }}
                </text>
              </template>
            </g>
          </g>
        </svg>

        <!-- ─── Floating Contextual Action Card (docked in bottom-right corner) ─── -->
        <IssueResolutionAssistant
          v-if="showIssueAssistant && activeIssues.length && selectedIssue"
          :issues="activeIssues"
          :selected-issue-id="selectedIssueId"
          :model-revision="designModelRevision"
          :anchor-position="contextualCardPosition"
          :geometry="geometry"
          :diagnostics="solvability"
          :busy="saving"
          @select-issue="handleSelectIssue"
          @clear-highlight="handleClearHighlight"
          @apply-fix="applyAiFix"
          @preview-fix="handlePreviewFix"
          @clear-preview="handleClearPreview"
        />
      </div>

      <!-- ─── Analysis Results Panel (docked in canvas column) ─── -->
      <AnalysisResultsPanel
        v-if="showResultsPanel && hasSolvedResults"
        :analysis-id="analysisId"
        :solver-data="persistedSolverData"
        :is-stale="resultsStale"
        :geometry="geometry"
        :loads="loads"
        :nodes="nodes"
        :members="members"
        :supports="supports"
        :show-force-labels="showForceLabels"
        :can-solve="canSolve"
        :solving="solving"
        @close="showResultsPanel = false"
        @select-member="handleSelectMemberFromResults"
        @re-solve="handleReSolve"
        @toggle-force-labels="showForceLabels = !showForceLabels"
        @resize="handleResultsPanelResize"
      />
    </div>

      <!-- ─── Right Sidebar: Tabs for Tools vs Design with AI ─── -->
      <aside class="editor-sidebar" :class="{ 'mobile-open': activeSidebarTab === 'design' }">
        <!-- Sidebar Navigation Tabs -->
        <nav class="sidebar-tabs-nav" role="tablist" aria-label="Sidebar navigation">
          <button
            type="button"
            role="tab"
            class="sidebar-tab-btn"
            :class="{ active: activeSidebarTab === 'tools' }"
            :aria-selected="activeSidebarTab === 'tools'"
            @click="switchSidebarTab('tools')"
          >
            <Sliders :size="13" />
            <span>Tools</span>
          </button>
          <button
            type="button"
            role="tab"
            class="sidebar-tab-btn"
            :class="{ active: activeSidebarTab === 'design' }"
            :aria-selected="activeSidebarTab === 'design'"
            @click="switchSidebarTab('design')"
          >
            <Sparkles :size="13" />
            <span>Design with AI</span>
            <span v-if="designProposal" class="tab-indicator-badge">1</span>
          </button>
          <button
            type="button"
            class="sidebar-tab-btn btn-close-mobile-tab"
            aria-label="Close panel"
            title="Close panel"
            @click="switchSidebarTab('tools')"
          >
            ✕
          </button>
        </nav>

        <!-- Tab 1: Tools & Properties Inspector -->
        <div v-show="activeSidebarTab === 'tools'" class="sidebar-tools-pane">
          <!-- Toolbox: grouped -->
          <section class="toolbox-section">
            <!-- Navigation group -->
            <div class="toolbox-group">
              <div class="section-label">Navigate</div>
              <div class="tools-grid tools-grid-2">
                <button class="tool-tile" :class="{ active: activeTool === 'select' }" type="button" title="Select / Move (V)" @click="activeTool = 'select'">
                  <MousePointer :size="15" /> Select
                </button>
                <button class="tool-tile" :class="{ active: activeTool === 'pan' }" type="button" title="Pan Canvas (H)" @click="activeTool = 'pan'">
                  <Hand :size="15" /> Pan
                </button>
              </div>
            </div>

            <!-- Construction group -->
            <div class="toolbox-group">
              <div class="section-label">Construction</div>
              <div class="tools-grid tools-grid-3">
                <button class="tool-tile" :class="{ active: activeTool === 'joint' }" type="button" title="Add Joint — click canvas" @click="activeTool = 'joint'">
                  <PlusCircle :size="15" /> Joint
                </button>
                <button class="tool-tile" :class="{ active: activeTool === 'member' }" type="button" title="Add Member — click two joints" @click="activeTool = 'member'">
                  <Spline :size="15" /> Member
                </button>
                <button class="tool-tile" :class="{ active: activeTool === 'measure' }" type="button" title="Measure Distance" @click="activeTool = 'measure'">
                  <Ruler :size="15" /> Measure
                </button>
              </div>
            </div>

            <!-- Structural group -->
            <div class="toolbox-group">
              <div class="section-label">Structural</div>
              <div class="tools-grid tools-grid-3">
                <button class="tool-tile" :class="{ active: activeTool === 'pin' }" type="button" title="Pin Support — click joint" @click="activeTool = 'pin'">
                  <Anchor :size="15" /> Pin
                </button>
                <button class="tool-tile" :class="{ active: activeTool === 'roller' }" type="button" title="Roller Support — click joint" @click="activeTool = 'roller'">
                  <CircleDot :size="15" /> Roller
                </button>
                <button class="tool-tile" :class="{ active: activeTool === 'load' }" type="button" title="Add Load — click joint then edit in inspector" @click="activeTool = 'load'">
                  <ArrowDown :size="15" /> Load
                </button>
              </div>
            </div>

            <!-- Editing group -->
            <div class="toolbox-group">
              <div class="section-label">Edit</div>
              <div class="tools-grid tools-grid-1">
                <button class="tool-tile tool-delete" :class="{ active: activeTool === 'delete' }" type="button" title="Delete — click element (or select + Delete key)" @click="activeTool = 'delete'">
                  <Trash2 :size="15" /> Delete
                </button>
              </div>
            </div>
          </section>

          <!-- Import AI Proposal strip (only when no model nodes yet) -->
          <div v-if="proposalJoints.length && !nodes.length" class="import-proposal-strip">
            <button class="action-btn btn-review" type="button" @click="importAllProposal">
              <Sparkles :size="13" /> Import AI Proposal
            </button>
          </div>

          <!-- Properties Inspector -->
          <section class="inspector-section">

          <!-- ─── Joint Inspector ─── -->
          <div v-if="selectedElement?.type === 'node' && nodeMap[selectedElement.id]">
            <div class="inspector-header">
              <h3>Joint</h3>
              <span class="element-badge">{{ selectedElement.id }}</span>
            </div>
            <div class="inspector-fields">
              <div class="field-group">
                <label>Joint ID</label>
                <input v-model="nodeMap[selectedElement.id].id" @change="pushHistory" />
              </div>
              <div class="field-row">
                <div class="field-group">
                  <label>X ({{ geometry.metadata.units.length }})</label>
                  <input v-model.number="nodeMap[selectedElement.id].x" type="number" step="0.1" @input="schedulePreview" @change="pushHistory" />
                </div>
                <div class="field-group">
                  <label>Y ({{ geometry.metadata.units.length }})</label>
                  <input v-model.number="nodeMap[selectedElement.id].y" type="number" step="0.1" @input="schedulePreview" @change="pushHistory" />
                </div>
              </div>

              <!-- Support -->
              <div class="field-group">
                <label>Support</label>
                <select :value="nodeSupport(selectedElement.id)?.type || ''" @change="toggleSupport(selectedElement.id, $event.target.value)">
                  <option value="">None (Free)</option>
                  <option value="pin">Pin (Fx &amp; Fy)</option>
                  <option value="roller">Roller (Fy)</option>
                </select>
              </div>

              <!-- Point Load -->
              <div class="field-group">
                <label>Point Load ({{ geometry.metadata.units.force }})</label>
                <div class="field-row">
                  <input
                    placeholder="Fx"
                    type="number"
                    :value="nodeLoads(selectedElement.id)[0]?.fx || 0"
                    @change="addOrEditLoad(selectedElement.id, $event.target.value, nodeLoads(selectedElement.id)[0]?.fy || 0)"
                  />
                  <input
                    placeholder="Fy"
                    type="number"
                    :value="nodeLoads(selectedElement.id)[0]?.fy || 0"
                    @change="addOrEditLoad(selectedElement.id, nodeLoads(selectedElement.id)[0]?.fx || 0, $event.target.value)"
                  />
                </div>
              </div>

              <!-- Connected members -->
              <div class="field-group">
                <label>Connected Members</label>
                <div v-if="connectedMembers.length" class="connected-members-list">
                  <button
                    v-for="m in connectedMembers"
                    :key="m.id"
                    class="connected-member-chip"
                    type="button"
                    @click="selectedElement = { type: 'member', id: m.id }"
                  >
                    <Link2 :size="11" />
                    {{ m.id }}: {{ m.node_i }} → {{ m.node_j }}
                  </button>
                </div>
                <span v-else class="connected-members-none">No members attached</span>
              </div>

              <button class="delete-btn" type="button" @click="deleteElement('node', selectedElement.id)">
                <Trash2 :size="13" /> Delete Joint
              </button>
            </div>
          </div>

          <!-- ─── Member Inspector ─── -->
          <div v-else-if="selectedElement?.type === 'member' && members.find((m) => m.id === selectedElement.id)">
            <div class="inspector-header">
              <h3>Member</h3>
              <span class="element-badge">{{ selectedElement.id }}</span>
            </div>
            <div class="inspector-fields">
              <div class="field-group">
                <label>Member ID</label>
                <input v-model="members.find((m) => m.id === selectedElement.id).id" @change="pushHistory" />
              </div>
              <div class="field-row">
                <div class="field-group">
                  <label>Joint i</label>
                  <select v-model="members.find((m) => m.id === selectedElement.id).node_i" @change="pushHistory">
                    <option v-for="n in nodes" :key="n.id" :value="n.id">{{ n.id }}</option>
                  </select>
                </div>
                <div class="field-group">
                  <label>Joint j</label>
                  <select v-model="members.find((m) => m.id === selectedElement.id).node_j" @change="pushHistory">
                    <option v-for="n in nodes" :key="n.id" :value="n.id">{{ n.id }}</option>
                  </select>
                </div>
              </div>

              <!-- Length stat -->
              <div class="stat-card">
                <small>Length</small>
                <strong>{{ memberLength(members.find((m) => m.id === selectedElement.id)) }} {{ geometry.metadata.units.length }}</strong>
              </div>

              <!-- Axial force with state pill -->
              <div v-if="hasSolvedResults" class="field-group member-analysis-group">
                <label>Analysis Result</label>
                <div v-if="resultsStale" class="member-stale-badge">
                  <AlertTriangle :size="12" /> Results Stale (Geometry modified)
                </div>
                <div v-else-if="memberForceText(selectedElement.id)" class="force-display">
                  <span :class="['force-pill', memberState(selectedElement.id)]">
                    {{ memberForceText(selectedElement.id) }}
                  </span>
                  <span class="force-state-name">
                    {{ memberState(selectedElement.id).toUpperCase() }}
                  </span>
                </div>
                <div v-else-if="isUnloaded" class="force-display">
                  <span class="force-pill zero">0.00 {{ geometry.metadata.units.force }}</span>
                  <span class="force-state-name">UNLOADED</span>
                </div>
              </div>

              <button class="delete-btn" type="button" @click="deleteElement('member', selectedElement.id)">
                <Trash2 :size="13" /> Delete Member
              </button>
            </div>
          </div>

          <!-- ─── Model Overview (nothing selected) ─── -->
          <div v-else>
            <div class="inspector-header">
              <h3>Model</h3>
              <span class="element-badge">TRUSS</span>
            </div>

            <div class="model-stat-grid">
              <div class="stat-card"><small>Joints</small><strong>{{ nodes.length }}</strong></div>
              <div class="stat-card"><small>Members</small><strong>{{ members.length }}</strong></div>
              <div class="stat-card"><small>Supports</small><strong>{{ supports.length }}</strong></div>
              <div class="stat-card"><small>Loads</small><strong>{{ loads.length }}</strong></div>
            </div>

            <p class="empty-inspector">
              Select a joint or member to inspect and edit its properties.
            </p>

            <button class="clear-all-btn" type="button" @click="clearModel">
              <Trash2 :size="12" /> Clear All Model Elements
            </button>
          </div>

        </section>
        </div><!-- /sidebar-tools-pane -->

        <!-- Tab 2: Natural Language Design Studio -->
        <div
          v-show="activeSidebarTab === 'design'"
          class="sidebar-design-pane editor-design-assistant-card"
          @wheel.stop
          @pointerdown.stop
        >
          <DesignInstructionPanel
            :analysis-id="analysisId"
            :model-revision="designModelRevision"
            :selected-element="selectedElement"
            :is-dirty="isDirty"
            :proposal="designProposal"
            :busy="designBusy"
            :error="designError"
            :compact="true"
            @submit="handleDesignSubmit"
            @apply="handleApplyDesignProposal"
            @reject="handleRejectDesignProposal"
            @clear-error="designError = ''"
          />
        </div>
      </aside>

      <!-- ─── AI Assistant Drawer (secondary, on-demand) ─── -->
      <aside v-if="showAiAssistant" class="ai-assistant-drawer">
        <div class="ai-drawer-header">
          <h3>
            <Bot :size="15" />
            AI Assistant
            <span class="ai-drawer-subtitle">Engineering guidance</span>
          </h3>
          <button class="close-btn" type="button" title="Close" @click="showAiAssistant = false">×</button>
        </div>
        <div class="ai-drawer-content">
          <div class="ai-prompt-shortcuts">
            <button class="ai-chip" type="button" @click="askAi('why_unstable')">Why is this unstable?</button>
            <button class="ai-chip" type="button" @click="askAi('disconnected')">Disconnected joints?</button>
            <button class="ai-chip" type="button" @click="askAi('suggest_supports')">Support layout</button>
            <button class="ai-chip" type="button" @click="askAi('forces')">Explain forces</button>
          </div>

          <div class="ai-response-card">
            <p v-if="aiAnalyzing" class="ai-analyzing-text">Analyzing model…</p>
            <p v-else>{{ aiAssistantMessage || 'Select a prompt above to get engineering guidance.' }}</p>
          </div>

          <div v-if="aiSuggestions.length" class="ai-suggestions-list">
            <h4>Suggestions</h4>
            <div v-for="sugg in aiSuggestions" :key="sugg.id" class="ai-suggestion-box">
              <strong>{{ sugg.title }}</strong>
              <p>{{ sugg.description }}</p>
              <div class="suggestion-actions">
                <button class="btn-apply-suggestion" type="button" @click="applySuggestion(sugg)">Apply</button>
                <button class="btn-reject-suggestion" type="button" @click="aiSuggestions = aiSuggestions.filter((s) => s.id !== sugg.id)">Dismiss</button>
              </div>
            </div>
          </div>
        </div>
      </aside>

    </div><!-- /editor-main -->

    <!-- ═══════════════════ WARNINGS DRAWER ═══════════════════ -->
    <div v-if="showWarningsDrawer" class="warnings-drawer">
      <ul>
        <li v-for="(err, idx) in validationErrors" :key="`err-${idx}`" class="warning-item is-error" @click="selectWarning(err)">
          <XCircle :size="13" />
          <span><b>Error:</b> {{ err.message }}<template v-if="err.path"> ({{ err.path }})</template></span>
        </li>
        <li v-for="(warn, idx) in validationWarnings" :key="`warn-${idx}`" class="warning-item" @click="selectWarning(warn)">
          <AlertTriangle :size="13" />
          <span><b>Warning:</b> {{ warn.message }}</span>
        </li>
      </ul>
    </div>

    <!-- ═══════════════════ BOTTOM STATUS BAR ═══════════════════ -->
    <footer class="editor-statusbar">
      <div class="status-left">
        <span :class="['status-pill', `status-${statusCategory}`]">
          <Loader2 v-if="statusCategory === 'calculating'" :size="11" class="spin-icon" />
          <CheckCircle2 v-else-if="statusCategory === 'green' || statusCategory === 'solved'" :size="11" />
          <AlertTriangle v-else-if="statusCategory === 'yellow' || statusCategory === 'stale'" :size="11" />
          <XCircle v-else-if="statusCategory === 'red'" :size="11" />
          <Eye v-else :size="11" />
          {{ statusPillLabel }}
        </span>
        <span class="status-message">
          {{ statusCategory === 'stale' ? 'Results stale — geometry was edited after last solve' : (hasSolvedResults && !resultsStale ? 'Analysis complete — results available' : (solvability.message || statusMessage)) }}
        </span>
        <span v-if="isDirty" class="status-dirty-dot" title="Unsaved changes" />
      </div>

      <div class="status-center">
        {{ nodes.length }} joints · {{ members.length }} members
        <template v-if="cursorCoords">
          · {{ cursorCoords.x.toFixed(2) }}, {{ cursorCoords.y.toFixed(2) }}
        </template>
      </div>

      <div class="status-right">
        <button
          v-if="activeIssues.length"
          class="status-warnings-toggle"
          :class="{ active: isHighlightActive }"
          type="button"
          :title="isHighlightActive ? 'Clear on-canvas issue highlight' : 'Highlight issues on canvas'"
          @click="toggleHighlightMode"
        >
          <EyeOff v-if="isHighlightActive" :size="11" />
          <AlertTriangle v-else :size="11" />
          {{ isHighlightActive ? 'Clear Highlight' : `${activeIssues.length} issues` }}
        </button>
      </div>
    </footer>

  </div>
</template>

<style scoped>
/* Scoped: only styles that cannot live in truss-editor.css (component-specific) */

/* Toast notification */
.editor-toast {
  position: fixed;
  bottom: calc(var(--statusbar-height) + 12px);
  left: 50%;
  transform: translateX(-50%);
  z-index: 8000;
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 7px 16px;
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  box-shadow: var(--shadow-md);
  pointer-events: none;
  white-space: nowrap;
}
.toast-success { background: var(--color-success-subtle); color: var(--color-success-text); border: 1px solid #86efac; }
.toast-error   { background: var(--color-danger-subtle);  color: var(--color-danger-text);  border: 1px solid #fca5a5; }
.toast-info    { background: var(--color-accent-subtle);  color: var(--color-accent-text);  border: 1px solid #bae6fd; }

.toast-slide-enter-active, .toast-slide-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.toast-slide-enter-from  { opacity: 0; transform: translateX(-50%) translateY(8px); }
.toast-slide-leave-to    { opacity: 0; transform: translateX(-50%) translateY(4px); }

/* Spinning loader in status bar */
.spin-icon { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
