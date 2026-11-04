<script setup>
import { computed, onMounted, ref } from 'vue'
import { Sparkles, X, Loader2, Send, ArrowRight, BookOpen } from 'lucide-vue-next'
import { apiUrl, listAnalyses, designTruss, applyDesignProposal } from '../api/analyses'
import DesignProposalCard from '../components/DesignProposalCard.vue'

const emit = defineEmits(['open', 'new', 'history', 'count', 'design', 'editor', 'guide'])
const analyses = ref([])
const total = ref(0)
const loading = ref(true)
const error = ref('')
const brokenImages = ref(new Set())
const recentFailure = computed(() => analyses.value.find((item) => item.status === 'failed'))

// Dashboard Create with AI state
const showCreateAi = ref(false)
const createPrompt = ref('')
const createBusy = ref(false)
const createError = ref('')
const createProposal = ref(null)

const examplePrompts = [
  'Create a triangular truss with a 6 m span and 3 m height.',
  'Create a Warren truss with 4 panels and 10 m span.',
  'Design a simple roof truss with pin and roller supports.',
  'Triangular truss with pin at left, roller at right, and 10 kN downward load at apex.',
]

function toggleCreateAi() {
  showCreateAi.value = !showCreateAi.value
  createError.value = ''
}

async function submitCreateAi(text) {
  const prompt = (text || createPrompt.value).trim()
  if (!prompt || createBusy.value) return
  createPrompt.value = prompt
  createBusy.value = true
  createError.value = ''
  createProposal.value = null

  try {
    const res = await designTruss({
      message: prompt,
      intent: 'create',
      context: {},
    })
    createProposal.value = res
  } catch (err) {
    if (err.body?.error === 'OUT_OF_SCOPE') {
      createError.value = err.message || 'I can help create, modify or explain truss structures. Describe the structural design you want.'
    } else {
      createError.value = err.message || 'Failed to synthesize truss model.'
    }
  } finally {
    createBusy.value = false
  }
}

async function handleApplyCreatedProposal(prop) {
  if (!prop?.proposed_model) return
  createBusy.value = true
  createError.value = ''
  try {
    const res = await applyDesignProposal({
      proposal_id: prop.proposal_id,
      proposed_model: prop.proposed_model,
      create_record: true,
    })
    if (res.analysis_id) {
      emit('count', total.value + 1)
      emit('editor', res.analysis_id)
    }
  } catch (err) {
    createError.value = err.message || 'Failed to persist created truss analysis.'
  } finally {
    createBusy.value = false
  }
}

function handleDiscardCreatedProposal() {
  createProposal.value = null
  createError.value = ''
}


function statusLabel(status) {
  return ({ pending_review: 'Needs review', reviewed: 'Reviewed', solved: 'Solved', failed: 'Failed', pending: 'Processing', draft: 'Draft saved' })[status] || status || 'Unknown'
}

function statusClass(status) {
  if (status === 'failed') return 'failed'
  if (status === 'reviewed' || status === 'solved') return 'complete'
  return 'pending'
}

function formatDate(value) {
  const date = value ? new Date(value) : null
  return date && !Number.isNaN(date.getTime())
    ? new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date)
    : 'Date unavailable'
}

function markImageUnavailable(id) {
  brokenImages.value = new Set([...brokenImages.value, id])
}

async function loadDashboard() {
  loading.value = true
  error.value = ''
  try {
    const result = await listAnalyses({ page: 1, perPage: 6 })
    analyses.value = result.items || []
    total.value = result.total || 0
    emit('count', total.value)
  } catch (cause) {
    error.value = cause.message
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <section class="page-content dashboard-page">
    <div class="dashboard-welcome">
      <div>
        <div class="eyebrow">LOCAL ENGINEERING WORKSPACE</div>
        <h1>Sketch review,<br /><em>with evidence in view.</em></h1>
        <p>Compare visual detections and model interpretations, then decide what belongs in a structural model.</p>
        <div class="dashboard-actions">
          <button class="dashboard-primary btn-new-analysis" type="button" @click="emit('new')"><span>＋</span> New analysis</button>
          <button
            class="dashboard-ai-btn"
            type="button"
            :class="{ active: showCreateAi }"
            @click="toggleCreateAi"
          >
            <Sparkles :size="14" /> Create with AI
          </button>
          <button class="dashboard-guide-btn" type="button" @click="emit('guide')">
            <BookOpen :size="14" /> Guide
          </button>
          <button class="dashboard-link" type="button" @click="emit('history')">Browse all history <span>↗</span></button>
        </div>
      </div>
      <div class="welcome-mark" aria-hidden="true">
        <svg viewBox="0 0 280 190" fill="none"><path d="M28 160 140 28l112 132H28Z"/><path d="m84 94 112 0M58 126h164M140 28v132M84 94l56 66 56-66"/><circle cx="140" cy="28" r="7"/><circle cx="28" cy="160" r="7"/><circle cx="252" cy="160" r="7"/><circle cx="84" cy="94" r="6"/><circle cx="196" cy="94" r="6"/><circle cx="140" cy="160" r="6"/></svg>
        <span>IMAGE-SPACE EVIDENCE</span>
      </div>
    </div>

    <!-- In-place Natural-Language Design Workbench -->
    <div v-if="showCreateAi" class="dashboard-ai-workbench">
      <div class="workbench-header">
        <div class="workbench-title">
          <Sparkles :size="15" class="sparkle-icon" />
          <strong>Create Truss with Natural Language</strong>
          <span class="workbench-badge">No sketch needed</span>
        </div>
        <button type="button" class="btn-close-workbench" aria-label="Close workbench" @click="showCreateAi = false">✕</button>
      </div>

      <div class="workbench-input-row">
        <input
          v-model="createPrompt"
          type="text"
          class="workbench-input"
          placeholder="Describe your truss (e.g. 'Create a triangular truss with a 6 m span and 3 m height')..."
          :disabled="createBusy"
          @keydown.enter="submitCreateAi()"
        />
        <button
          type="button"
          class="workbench-submit-btn"
          :disabled="!createPrompt.trim() || createBusy"
          @click="submitCreateAi()"
        >
          <Loader2 v-if="createBusy" :size="13" class="spin-icon" />
          <Send v-else :size="13" />
          <span>{{ createBusy ? 'Synthesizing...' : 'Generate Proposal' }}</span>
        </button>
      </div>

      <!-- Example Prompt Chips -->
      <div class="workbench-chips">
        <span class="chips-label">Examples:</span>
        <button
          v-for="(p, idx) in examplePrompts"
          :key="idx"
          type="button"
          class="workbench-chip"
          :disabled="createBusy"
          @click="submitCreateAi(p)"
        >
          {{ p }}
        </button>
      </div>

      <!-- Error Notice -->
      <div v-if="createError" class="workbench-error" role="alert">
        {{ createError }}
      </div>

      <!-- Generated Proposal Card -->
      <div v-if="createProposal" class="workbench-proposal-wrapper">
        <DesignProposalCard
          :proposal="createProposal"
          :is-busy="createBusy"
          @apply="handleApplyCreatedProposal"
          @reject="handleDiscardCreatedProposal"
        />
      </div>
    </div>

    <div class="dashboard-overview">
      <section class="overview-card saved-card">
        <span class="overview-icon">▤</span>
        <div><small>Saved analyses</small><strong>{{ loading ? '—' : total }}</strong></div>
        <span class="overview-note">from local history</span>
      </section>
      <section class="overview-card review-card">
        <span class="overview-icon review-icon">◉</span>
        <div><small>Review boundary</small><strong>Human checked</strong></div>
        <span class="overview-note">AI proposals stay unapproved</span>
      </section>
      <section v-if="recentFailure" class="overview-card failure-card" role="status">
        <span class="overview-icon failure-icon">!</span>
        <div><small>Recent failure</small><strong>{{ recentFailure.error_code || 'Analysis failed' }}</strong></div>
        <button type="button" aria-label="Open recent failed analysis" @click="emit('open', recentFailure.analysis_id)">↗</button>
      </section>
      <section v-else class="overview-card solver-card">
        <span class="overview-icon solver-icon">∑</span>
        <div><small>Solver access</small><strong>After review</strong></div>
        <span class="overview-note">explicit submission only</span>
      </section>
    </div>

    <section class="recent-work-section">
      <div class="recent-work-heading">
        <div><div class="eyebrow">SAVED WORK</div><h2>Recent sketches <span v-if="!loading">{{ total }}</span></h2></div>
        <button class="dashboard-link" type="button" @click="emit('history')">View history <span>↗</span></button>
      </div>

      <div v-if="loading" class="dashboard-state"><span class="loading-dots">•••</span><p>Loading recent analyses…</p></div>
      <div v-else-if="error" class="dashboard-state dashboard-error" role="alert"><strong>Recent work is unavailable</strong><p>{{ error }}</p><button type="button" @click="loadDashboard">Try again</button></div>
      <div v-else-if="!analyses.length" class="dashboard-empty">
        <div class="empty-sketch" aria-hidden="true"><svg viewBox="0 0 90 60" fill="none"><path d="M8 49 45 9l37 40H8Zm18-20h38M17 39h56M45 9v40M26 29l19 20 19-20"/><circle cx="45" cy="9" r="3"/><circle cx="8" cy="49" r="3"/><circle cx="82" cy="49" r="3"/></svg></div>
        <div><strong>Your review space is ready</strong><p>Upload a truss sketch to create the first saved analysis.</p></div>
        <button class="dashboard-primary btn-empty-start" type="button" @click="emit('new')">Start with a sketch <span>→</span></button>
      </div>
      <div v-else class="recent-analysis-grid">
        <button v-for="(item, index) in analyses" :key="item.analysis_id" class="recent-analysis-card" :class="{ 'featured-analysis': index === 0 }" type="button" @click="emit('open', item.analysis_id)">
          <span class="analysis-thumb">
            <img v-if="item.image_url && !brokenImages.has(item.analysis_id)" :src="apiUrl(item.image_url)" alt="" loading="lazy" @error="markImageUnavailable(item.analysis_id)" />
            <span v-if="!item.image_url || brokenImages.has(item.analysis_id)" class="thumb-placeholder" aria-hidden="true"><svg viewBox="0 0 90 60" fill="none"><path d="M8 49 45 9l37 40H8Zm18-20h38M17 39h56M45 9v40M26 29l19 20 19-20"/><circle cx="45" cy="9" r="3"/><circle cx="8" cy="49" r="3"/><circle cx="82" cy="49" r="3"/></svg></span>
            <span class="thumb-index">{{ String(index + 1).padStart(2, '0') }}</span>
          </span>
          <span class="analysis-card-details">
            <span class="analysis-card-topline"><span class="dashboard-status" :class="statusClass(item.status)"><i></i>{{ statusLabel(item.status) }}</span><span class="dashboard-arrow">↗</span></span>
            <strong>{{ item.original_filename || (item.analysis_type === 'solver' ? 'Solver run' : 'Untitled sketch') }}</strong>
            <span class="analysis-card-meta"><span>{{ item.provider || 'Deterministic solver' }}</span><span>{{ formatDate(item.created_at) }}</span></span>
            <span v-if="item.error_message" class="analysis-failure-message">{{ item.error_message }}</span>
          </span>
        </button>
      </div>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page { padding-top: 27px; }
.dashboard-welcome { min-height: 228px; display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(240px, .8fr); align-items: center; overflow: hidden; position: relative; padding: 30px clamp(24px, 3.3vw, 48px); border: 1px solid #eee5c5; border-radius: 22px; background: linear-gradient(112deg, #fffdf2 0%, #fcf8e7 66%, #f7edc6 100%); }
.dashboard-welcome h1 { margin: 4px 0 9px; font-size: clamp(30px, 3vw, 42px); letter-spacing: -1.8px; }
.dashboard-welcome p { max-width: 490px; margin-bottom: 17px; color: #575a53; font-size: 12px; line-height: 1.65; }
.dashboard-actions { display: flex; align-items: center; gap: 19px; flex-wrap: wrap; }
.dashboard-primary { min-height: 38px; display: inline-flex; align-items: center; gap: 9px; border: 1px solid #292a28; border-radius: 999px; padding: 0 16px; color: #fffef8; background: #292a28; font-size: 11px; font-weight: 700; cursor: pointer; }
.dashboard-primary:hover { background: #454741; }
.dashboard-primary span { font-size: 15px; line-height: 1; }
.btn-new-analysis { /* Semantic handle for header action */ }
.btn-empty-start { /* Semantic handle for empty state action */ }
.dashboard-ai-btn { min-height: 38px; display: inline-flex; align-items: center; gap: 7px; border: 1px solid #0284c7; border-radius: 999px; padding: 0 16px; color: #0284c7; background: #f0f9ff; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.15s ease; }
.dashboard-ai-btn:hover { background: #e0f2fe; color: #0369a1; }
.dashboard-ai-btn.active { background: #0284c7; color: #fff; }
.dashboard-guide-btn { min-height: 38px; display: inline-flex; align-items: center; gap: 7px; border: 1px solid #cbd5e1; border-radius: 999px; padding: 0 16px; color: #334155; background: #fff; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.15s ease; }
.dashboard-guide-btn:hover { background: #f1f5f9; color: #0f172a; border-color: #94a3b8; }
.dashboard-link { border: 0; padding: 7px 0; color: #575b52; background: none; font-size: 10px; font-weight: 700; cursor: pointer; }

/* In-place AI Workbench */
.dashboard-ai-workbench {
  margin-top: 14px;
  background: #fffdf9;
  border: 1px solid #ecd897;
  border-radius: 16px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 4px 18px rgba(180, 140, 20, 0.08);
}
.workbench-header { display: flex; align-items: center; justify-content: space-between; }
.workbench-title { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #292a28; }
.sparkle-icon { color: #d97706; }
.workbench-badge { font: 700 9px var(--mono, monospace); background: #fef3c7; color: #b45309; padding: 2px 7px; border-radius: 4px; }
.btn-close-workbench { border: none; background: transparent; font-size: 14px; color: #52564c; cursor: pointer; padding: 2px 6px; }
.workbench-input-row { display: flex; gap: 8px; align-items: center; }
.workbench-input { flex: 1; min-height: 38px; padding: 0 14px; border: 1px solid #dcd7c9; border-radius: 8px; font-size: 12px; font-family: inherit; color: #292a28; outline: none; background: #fff; }
.workbench-input:focus { border-color: #0284c7; box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.15); }
.workbench-submit-btn { min-height: 38px; display: inline-flex; align-items: center; gap: 6px; padding: 0 16px; border-radius: 8px; border: 1px solid #292a28; background: #292a28; color: #fff; font-size: 11px; font-weight: 700; cursor: pointer; transition: background 0.15s ease; white-space: nowrap; }
.workbench-submit-btn:hover:not(:disabled) { background: #42453e; }
.workbench-submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.workbench-chips { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.chips-label { font: 700 9px var(--mono, monospace); color: #8c8f82; text-transform: uppercase; }
.workbench-chip { background: #fff; border: 1px solid #e2ddd0; border-radius: 999px; padding: 3px 10px; font-size: 10px; color: #5a5d53; cursor: pointer; transition: all 0.15s ease; }
.workbench-chip:hover:not(:disabled) { background: #fdf8e6; border-color: #d4caa8; color: #292a28; }
.workbench-error { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 8px 12px; font-size: 11px; color: #991b1b; }
.workbench-proposal-wrapper { margin-top: 4px; }
.empty-actions { display: flex; align-items: center; gap: 10px; }
.dashboard-secondary-empty { min-height: 38px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid #0284c7; border-radius: 999px; padding: 0 14px; color: #0284c7; background: #f0f9ff; font-size: 11px; font-weight: 700; cursor: pointer; }
.spin-icon { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }

.dashboard-link span { padding-left: 5px; font-size: 13px; }
.welcome-mark { align-self: stretch; display: flex; flex-direction: column; align-items: flex-end; justify-content: center; padding: 0 8px; color: #747d6b; }
.welcome-mark svg { width: min(100%, 290px); max-height: 150px; stroke: #a7a984; stroke-width: 1.4; }
.welcome-mark circle { fill: #f4dc68; stroke: #8e9879; stroke-width: 1.4; }
.welcome-mark span { margin: 6px 4px 0 0; color: #a09c7a; font: 8px var(--mono); letter-spacing: 1px; }
.dashboard-overview { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 14px 0 31px; }
.overview-card { min-height: 75px; display: flex; align-items: center; gap: 11px; padding: 12px 14px; border: 1px solid #eae7dc; border-radius: 14px; background: #fffef9; box-shadow: 0 3px 9px #3b362508; }
.overview-icon { width: 31px; height: 31px; flex: 0 0 auto; display: grid; place-items: center; border-radius: 10px; color: #707568; background: #f1f0e7; font-size: 17px; }
.overview-card > div { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.overview-card small { color: #9b9b8d; font: 8px var(--mono); text-transform: uppercase; letter-spacing: .55px; }
.overview-card strong { overflow: hidden; color: #343731; font: 600 13px var(--heading); text-overflow: ellipsis; white-space: nowrap; }
.overview-note { margin-left: auto; color: #9a9b8e; font-size: 8px; text-align: right; }
.review-icon { color: #437768; background: #e8f1e8; }
.solver-card { color: #fff9e8; background: #2a2b29; border-color: #2a2b29; }
.solver-card .solver-icon { color: #e8d16e; background: #41413a; }
.solver-card small { color: #b8b6a6; }
.solver-card strong { color: #fff9e7; }
.solver-card .overview-note { color: #c1bd9d; }
.failure-card { background: #2a2b29; border-color: #2a2b29; }
.failure-card .failure-icon { color: #f1d36f; background: #41413a; }
.failure-card small { color: #b8b6a6; }
.failure-card strong { color: #fff9e7; }
.failure-card button { width: 26px; height: 26px; margin-left: auto; border: 1px solid #55564f; border-radius: 50%; color: #f8e7a3; background: transparent; cursor: pointer; }
.recent-work-section { margin-top: 6px; }
.recent-work-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 13px; }
.recent-work-heading .eyebrow { margin-bottom: 5px; }
.recent-work-heading h2 { color: #30332e; font: 650 19px var(--heading); letter-spacing: -.5px; }
.recent-work-heading h2 span { display: inline-grid; min-width: 22px; height: 22px; margin-left: 5px; place-items: center; vertical-align: 2px; border-radius: 50%; color: #777968; background: #eeeddf; font: 9px var(--mono); }
.dashboard-state, .dashboard-empty { min-height: 145px; display: flex; align-items: center; justify-content: center; gap: 20px; padding: 23px; border: 1px dashed #dedccc; border-radius: 17px; color: #858477; background: #fffef7a8; }
.dashboard-state { flex-direction: column; gap: 4px; }
.dashboard-state p, .dashboard-empty p { margin: 5px 0 0; color: #939285; font-size: 10px; }
.dashboard-state strong, .dashboard-empty strong { color: #4e5048; font: 650 13px var(--heading); }
.dashboard-error { border-color: #ead0c8; color: #a3554d; }
.dashboard-error p { max-width: 540px; }
.dashboard-error button { margin-top: 7px; border: 0; color: #81564d; background: transparent; font-weight: 700; cursor: pointer; }
.empty-sketch { width: 95px; flex: 0 0 auto; }
.empty-sketch svg { width: 100%; stroke: #9ba58c; stroke-width: 1.4; }
.empty-sketch circle { fill: #f1d86e; stroke: #87917b; }
.dashboard-empty > div:nth-child(2) { flex: 1; }
.recent-analysis-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-items: stretch; gap: 12px; }
.recent-analysis-card { min-width: 0; display: flex; flex-direction: column; overflow: hidden; padding: 0; border: 1px solid #e8e5d9; border-radius: 15px; color: inherit; background: #fffef9; box-shadow: 0 3px 10px #3b362508; text-align: left; cursor: pointer; transition: transform .16s ease, box-shadow .16s ease; }
.recent-analysis-card:hover { transform: translateY(-2px); box-shadow: 0 8px 18px #3b362511; }
.analysis-thumb { height: 126px; position: relative; display: grid; place-items: center; overflow: hidden; background: #e8e7de; }
.analysis-thumb img { width: 100%; height: 100%; padding: 6px; object-fit: contain; }
.thumb-index { position: absolute; top: 9px; left: 9px; padding: 5px 7px; border: 1px solid #ffffffa3; border-radius: 99px; color: #45483f; background: #fffef0d9; font: 8px var(--mono); }
.thumb-placeholder { width: 94px; opacity: .68; }
.thumb-placeholder svg { width: 100%; stroke: #7a8779; stroke-width: 1.5; }
.thumb-placeholder circle { fill: #e5cf67; stroke: #818879; }
.analysis-card-details { display: flex; flex-direction: column; gap: 9px; padding: 11px 13px 12px; }
.analysis-card-topline, .analysis-card-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.dashboard-status { display: inline-flex; align-items: center; gap: 5px; padding: 4px 7px; border-radius: 99px; font: 8px var(--mono); }
.dashboard-status i { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.dashboard-status.pending { color: #907832; background: #f7f0d4; }
.dashboard-status.complete { color: #467763; background: #e8f1e8; }
.dashboard-status.failed { color: #9c514a; background: #f7eae3; }
.dashboard-arrow { color: #61645a; font-size: 13px; }
.analysis-card-details > strong { overflow: hidden; color: #393c36; font: 650 11px var(--heading); text-overflow: ellipsis; white-space: nowrap; }
.analysis-card-meta { color: #5a6058; font: 8px var(--mono); text-transform: capitalize; }
.analysis-failure-message { overflow: hidden; color: #a76157; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
@media (max-width: 1050px) { .dashboard-overview { grid-template-columns: repeat(2, minmax(0, 1fr)); } .recent-analysis-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) { .dashboard-page { padding-top: 21px; } .dashboard-welcome { min-height: auto; grid-template-columns: 1fr; padding: 24px 20px; border-radius: 17px; } .dashboard-welcome h1 { font-size: 31px; } .welcome-mark { display: none; } .dashboard-overview { grid-template-columns: 1fr; gap: 8px; margin-bottom: 25px; } .overview-card { min-height: 66px; } .overview-note { font-size: 7px; } .recent-analysis-grid { grid-template-columns: 1fr; } .analysis-thumb { height: 158px; } .dashboard-empty { align-items: flex-start; flex-wrap: wrap; gap: 12px; } .empty-sketch { width: 58px; } .dashboard-empty > div:nth-child(2) { flex-basis: calc(100% - 76px); } .dashboard-empty .dashboard-primary { margin-left: 70px; } .recent-work-heading h2 { font-size: 17px; } }
</style>
