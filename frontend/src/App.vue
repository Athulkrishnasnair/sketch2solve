<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AnalysisDetailPage from './pages/AnalysisDetailPage.vue'
import AnalysisHistoryPage from './pages/AnalysisHistoryPage.vue'
import DashboardPage from './pages/DashboardPage.vue'
import NewAnalysisPage from './pages/NewAnalysisPage.vue'

const view = ref('dashboard')
const analysisId = ref('')
const historyCount = ref(0)
const pageTitle = computed(() => ({ dashboard: 'Dashboard', new: 'New analysis', history: 'Analysis history', detail: 'Analysis review' })[view.value])

function updateAddress(nextView, id = '') {
  const url = new URL(window.location.href)
  url.searchParams.delete('analysis')
  url.searchParams.delete('view')
  if (id) url.searchParams.set('analysis', id)
  else if (nextView !== 'dashboard') url.searchParams.set('view', nextView)
  window.history.pushState({}, '', `${url.pathname}${url.search}${url.hash}`)
}

function navigate(nextView) {
  view.value = nextView
  analysisId.value = ''
  updateAddress(nextView)
}

function openAnalysis(id) {
  analysisId.value = id
  view.value = 'detail'
  updateAddress('detail', id)
}

function handleCreated(id) {
  historyCount.value += 1
  openAnalysis(id)
}

function handlePopState() {
  const params = new URLSearchParams(window.location.search)
  const id = params.get('analysis')
  if (id) {
    analysisId.value = id
    view.value = 'detail'
  } else {
    analysisId.value = ''
    view.value = ['new', 'history'].includes(params.get('view')) ? params.get('view') : 'dashboard'
  }
}

onMounted(() => {
  window.addEventListener('popstate', handlePopState)
  handlePopState()
})

onBeforeUnmount(() => window.removeEventListener('popstate', handlePopState))
</script>

<template>
  <div class="app-frame">
    <aside class="sidebar">
      <a class="brand" href="/" @click.prevent="navigate('dashboard')">
        <span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 36 36" fill="none"><path d="M5 28.5 18 7l13 21.5H5Z" stroke="currentColor" stroke-width="2" /><path d="m11.4 18 13.1 0M9 22.1h18M18 7v21.5" stroke="currentColor" stroke-width="1.5" /><circle cx="18" cy="7" r="2" fill="currentColor" /><circle cx="5" cy="28.5" r="2" fill="currentColor" /><circle cx="31" cy="28.5" r="2" fill="currentColor" /></svg></span>
        <span class="brand-copy"><strong>Sketch2Solve</strong><small>STRUCTURE REVIEW</small></span>
      </a>

      <div class="local-banner"><span class="local-dot"></span> Local workspace</div>
      <nav class="primary-nav" aria-label="Main navigation">
        <button :class="['nav-item', { active: view === 'dashboard' } ]" type="button" @click="navigate('dashboard')"><svg viewBox="0 0 20 20" aria-hidden="true"><rect x="3" y="3" width="5.5" height="5.5" rx="1"/><rect x="11.5" y="3" width="5.5" height="5.5" rx="1"/><rect x="3" y="11.5" width="5.5" height="5.5" rx="1"/><rect x="11.5" y="11.5" width="5.5" height="5.5" rx="1"/></svg><span>Dashboard</span></button>
        <button :class="['nav-item', { active: view === 'new' }]" type="button" @click="navigate('new')"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v14M3 10h14" /></svg><span>New analysis</span></button>
        <button :class="['nav-item', { active: view === 'history' || view === 'detail' }]" type="button" @click="navigate('history')"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 5.5h14M3 10h14M3 14.5h9" /><circle cx="2.5" cy="5.5" r=".7" fill="currentColor" /><circle cx="2.5" cy="10" r=".7" fill="currentColor" /><circle cx="2.5" cy="14.5" r=".7" fill="currentColor" /></svg><span>Analysis history</span><span class="nav-count">{{ historyCount }}</span></button>
      </nav>

      <div class="sidebar-spacer"></div>
      <div class="privacy-card"><svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M10 2.8 16 5v4.4c0 3.8-2.4 6.2-6 7.8-3.6-1.6-6-4-6-7.8V5l6-2.2Z" stroke="currentColor" stroke-width="1.4"/><path d="m7.5 9.8 1.7 1.7 3.5-3.7" stroke="currentColor" stroke-width="1.4"/></svg><div><strong>Private by default</strong><p>Runs stay in your local backend. Don’t expose this workspace publicly.</p></div></div>
      <div class="sidebar-footer"><span class="backend-indicator"></span> Backend API · localhost:5000</div>
    </aside>

    <main class="main-area">
      <header class="topbar"><div class="breadcrumb"><span>Workspace</span><span class="crumb-separator">/</span><strong>{{ pageTitle }}</strong></div><div class="topbar-right"><span class="local-pill"><span></span> LOCAL ONLY</span><span class="avatar" aria-hidden="true">S</span></div></header>
      <DashboardPage v-if="view === 'dashboard'" @open="openAnalysis" @new="navigate('new')" @history="navigate('history')" @count="historyCount = $event" />
      <NewAnalysisPage v-else-if="view === 'new'" @created="handleCreated" />
      <AnalysisHistoryPage v-else-if="view === 'history'" @open="openAnalysis" @new="navigate('new')" @count="historyCount = $event" />
      <AnalysisDetailPage v-else :analysis-id="analysisId" @history="navigate('history')" @created="handleCreated" />
      <footer class="main-footer"><span>Sketch2Solve · Local review workspace</span><span>Interpretation is a starting point, not a structural check.</span></footer>
    </main>
  </div>
</template>
