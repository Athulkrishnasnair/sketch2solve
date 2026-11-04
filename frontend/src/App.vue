<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AnalysisDetailPage from './pages/AnalysisDetailPage.vue'
import AnalysisHistoryPage from './pages/AnalysisHistoryPage.vue'
import DashboardPage from './pages/DashboardPage.vue'
import DesignStudioPage from './pages/DesignStudioPage.vue'
import NewAnalysisPage from './pages/NewAnalysisPage.vue'
import TrussEditorPage from './pages/TrussEditorPage.vue'
import UserOnboardingModal from './components/UserOnboardingModal.vue'
import GettingStartedGuide from './components/GettingStartedGuide.vue'

const view = ref('dashboard')
const analysisId = ref('')
const historyCount = ref(0)
const pageTitle = computed(() => ({
  dashboard: 'Dashboard',
  new: 'New analysis',
  history: 'Analysis history',
  detail: 'Analysis review',
  editor: 'Truss Editor',
  design: 'Natural Language Design',
})[view.value])

const backendDisplay = computed(() => {
  const url = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000'
  try {
    const parsed = new URL(url)
    return parsed.host || 'localhost:5000'
  } catch (_) {
    return url.replace(/^https?:\/\//, '').replace(/\/.*$/, '') || 'localhost:5000'
  }
})

// User Profile & Onboarding State
const userName = ref(localStorage.getItem('sketch2solve_username') || '')
const showOnboarding = ref(!localStorage.getItem('sketch2solve_username'))
const isEditingName = ref(false)
const showUserMenu = ref(false)
const mobileNavOpen = ref(false)

function navigateFromMobile(nextView) {
  mobileNavOpen.value = false
  navigate(nextView)
}

function openGuideFromMobile() {
  mobileNavOpen.value = false
  showGuide.value = true
}

// Getting Started Guide State
const showGuide = ref(false)

function handleSaveName(name) {
  userName.value = name
  showOnboarding.value = false
  isEditingName.value = false
}

function handleOpenRename() {
  showUserMenu.value = false
  isEditingName.value = true
  showOnboarding.value = true
}

function handleOpenGuideFromMenu() {
  showUserMenu.value = false
  showGuide.value = true
}

function onDocumentClick(e) {
  if (showUserMenu.value && !e.target.closest('.user-menu-container')) {
    showUserMenu.value = false
  }
}

function updateAddress(nextView, id = '') {
  const url = new URL(window.location.href)
  url.searchParams.delete('analysis')
  url.searchParams.delete('view')
  if (nextView === 'editor' && id) {
    url.searchParams.set('analysis', id)
    url.searchParams.set('view', 'editor')
  } else if (id) {
    url.searchParams.set('analysis', id)
  } else if (nextView !== 'dashboard') {
    url.searchParams.set('view', nextView)
  }
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

function openEditor(id) {
  analysisId.value = id
  view.value = 'editor'
  updateAddress('editor', id)
}

function handleCreated(id) {
  historyCount.value += 1
  openAnalysis(id)
}

function handlePopState() {
  const pathMatch = window.location.pathname.match(/\/analyses\/([^/]+)\/editor/)
  const params = new URLSearchParams(window.location.search)
  const id = pathMatch ? pathMatch[1] : params.get('analysis')
  const isEditor = Boolean(pathMatch) || params.get('view') === 'editor'
  if (id && isEditor) {
    analysisId.value = id
    view.value = 'editor'
  } else if (id) {
    analysisId.value = id
    view.value = 'detail'
  } else {
    analysisId.value = ''
    view.value = ['new', 'history', 'design'].includes(params.get('view')) ? params.get('view') : 'dashboard'
  }
}

onMounted(() => {
  window.addEventListener('popstate', handlePopState)
  window.addEventListener('click', onDocumentClick)
  handlePopState()
})

watch(view, (nextView) => {
  if (typeof document !== 'undefined') {
    document.body.classList.toggle('in-editor-mode', nextView === 'editor')
  }
}, { immediate: true })

onBeforeUnmount(() => {
  window.removeEventListener('popstate', handlePopState)
  window.removeEventListener('click', onDocumentClick)
  if (typeof document !== 'undefined') {
    document.body.classList.remove('in-editor-mode')
  }
})
</script>

<template>
  <div class="app-frame" :class="{ 'in-editor-frame': view === 'editor' }">
    <!-- Desktop / Tablet Fixed Sidebar -->
    <aside class="sidebar">
      <a class="brand" href="/" @click.prevent="navigate('dashboard')">
        <span class="brand-mark" aria-hidden="true">
          <img src="/logo.png" alt="Sketch2Solve Logo" class="brand-logo-img" />
        </span>
        <span class="brand-copy"><strong>Sketch2Solve</strong><small>STRUCTURE REVIEW</small></span>
      </a>

      <div class="local-banner"><span class="local-dot"></span> Local workspace</div>
      <nav class="primary-nav" aria-label="Main navigation">
        <button :class="['nav-item', { active: view === 'dashboard' } ]" type="button" @click="navigate('dashboard')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="3" y="3" width="5.5" height="5.5" rx="1"/><rect x="11.5" y="3" width="5.5" height="5.5" rx="1"/><rect x="3" y="11.5" width="5.5" height="5.5" rx="1"/><rect x="11.5" y="11.5" width="5.5" height="5.5" rx="1"/></svg>
          <span>Dashboard</span>
        </button>
        <button :class="['nav-item', { active: view === 'design' }]" type="button" @click="navigate('design')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2.5 12 7l4.5 2-4.5 2-2 4.5-2-4.5-4.5-2 4.5-2 2-4.5Z" fill="none" stroke="currentColor" stroke-width="1.3"/><circle cx="16" cy="4" r="1.2" fill="currentColor"/><circle cx="4" cy="16" r="1.2" fill="currentColor"/></svg>
          <span>Natural Language Design</span>
        </button>
        <button :class="['nav-item', { active: view === 'new' }]" type="button" @click="navigate('new')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v14M3 10h14" /></svg>
          <span>New analysis</span>
        </button>
        <button :class="['nav-item', { active: view === 'history' || view === 'detail' }]" type="button" @click="navigate('history')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 5.5h14M3 10h14M3 14.5h9" /><circle cx="2.5" cy="5.5" r=".7" fill="currentColor" /><circle cx="2.5" cy="10" r=".7" fill="currentColor" /><circle cx="2.5" cy="14.5" r=".7" fill="currentColor" /></svg>
          <span>Analysis history</span>
          <span class="nav-count">{{ historyCount }}</span>
        </button>
      </nav>

      <div class="sidebar-spacer"></div>

      <!-- Getting Started Guide Sidebar Card -->
      <div class="sidebar-guide-card">
        <span class="guide-card-icon" aria-hidden="true">📘</span>
        <div class="guide-card-copy">
          <strong>Getting Started</strong>
          <p>6-step structural engineering workflow guide.</p>
          <button type="button" class="btn-guide-start" @click="showGuide = true">Open guide →</button>
        </div>
      </div>

      <div class="sidebar-footer"><span class="backend-indicator"></span> Backend API · {{ backendDisplay }}</div>
    </aside>

    <!-- Mobile Drawer & Backdrop -->
    <div v-if="mobileNavOpen" class="mobile-drawer-backdrop" @click="mobileNavOpen = false"></div>
    <aside
      v-if="mobileNavOpen"
      class="mobile-drawer open"
      aria-label="Mobile navigation drawer"
    >
      <div class="mobile-drawer-header">
        <a class="brand" href="/" @click.prevent="navigateFromMobile('dashboard')">
          <span class="brand-mark" aria-hidden="true">
            <img src="/logo.png" alt="Sketch2Solve Logo" class="brand-logo-img" />
          </span>
          <span class="brand-copy"><strong>Sketch2Solve</strong><small>STRUCTURE REVIEW</small></span>
        </a>
        <button class="btn-close-drawer" type="button" aria-label="Close navigation" @click="mobileNavOpen = false">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M5 5l10 10M15 5L5 15"/>
          </svg>
        </button>
      </div>

      <div class="local-banner"><span class="local-dot"></span> Local workspace</div>

      <nav class="primary-nav" aria-label="Mobile main navigation">
        <button :class="['nav-item', { active: view === 'dashboard' } ]" type="button" @click="navigateFromMobile('dashboard')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="3" y="3" width="5.5" height="5.5" rx="1"/><rect x="11.5" y="3" width="5.5" height="5.5" rx="1"/><rect x="3" y="11.5" width="5.5" height="5.5" rx="1"/><rect x="11.5" y="11.5" width="5.5" height="5.5" rx="1"/></svg>
          <span>Dashboard</span>
        </button>
        <button :class="['nav-item', { active: view === 'design' }]" type="button" @click="navigateFromMobile('design')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2.5 12 7l4.5 2-4.5 2-2 4.5-2-4.5-4.5-2 4.5-2 2-4.5Z" fill="none" stroke="currentColor" stroke-width="1.3"/><circle cx="16" cy="4" r="1.2" fill="currentColor"/><circle cx="4" cy="16" r="1.2" fill="currentColor"/></svg>
          <span>Natural Language Design</span>
        </button>
        <button :class="['nav-item', { active: view === 'new' }]" type="button" @click="navigateFromMobile('new')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v14M3 10h14" /></svg>
          <span>New analysis</span>
        </button>
        <button :class="['nav-item', { active: view === 'history' || view === 'detail' }]" type="button" @click="navigateFromMobile('history')">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 5.5h14M3 10h14M3 14.5h9" /><circle cx="2.5" cy="5.5" r=".7" fill="currentColor" /><circle cx="2.5" cy="10" r=".7" fill="currentColor" /><circle cx="2.5" cy="14.5" r=".7" fill="currentColor" /></svg>
          <span>Analysis history</span>
          <span class="nav-count">{{ historyCount }}</span>
        </button>
      </nav>

      <div class="sidebar-spacer"></div>

      <div class="sidebar-guide-card">
        <span class="guide-card-icon" aria-hidden="true">📘</span>
        <div class="guide-card-copy">
          <strong>Getting Started</strong>
          <p>6-step structural engineering workflow guide.</p>
          <button type="button" class="btn-guide-start" @click="openGuideFromMobile">Open guide →</button>
        </div>
      </div>

      <div class="sidebar-footer"><span class="backend-indicator"></span> Backend API · {{ backendDisplay }}</div>
    </aside>

    <main class="main-area" :class="{ 'in-editor': view === 'editor' }">
      <!-- Fixed Header Bar -->
      <header v-if="view !== 'editor'" class="topbar">
        <div class="topbar-left-cluster">
          <button
            class="btn-mobile-nav-toggle"
            type="button"
            aria-label="Toggle navigation menu"
            :aria-expanded="mobileNavOpen"
            @click="mobileNavOpen = !mobileNavOpen"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="hamburger-icon" aria-hidden="true">
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          <a class="mobile-header-brand" href="/" @click.prevent="navigate('dashboard')">
            <img src="/logo.png" alt="Sketch2Solve Logo" />
            <strong>Sketch2Solve</strong>
          </a>
          <div class="breadcrumb">
            <span>Workspace</span>
            <span class="crumb-separator">/</span>
            <strong>{{ pageTitle }}</strong>
          </div>
        </div>
        <div class="topbar-right">
          <!-- Guide Button in Topbar -->
          <button
            class="btn-topbar-tool btn-topbar-guide"
            type="button"
            title="Getting Started Guide"
            aria-label="Open Getting Started Guide"
            @click="showGuide = true"
          >
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" class="topbar-icon" aria-hidden="true">
              <circle cx="10" cy="10" r="7.5"/>
              <path d="M10 6.5v.5M10 9.5v4" stroke-linecap="round"/>
            </svg>
            <span class="guide-btn-label">Guide</span>
          </button>

          <!-- User Name Profile Menu -->
          <div class="user-menu-container">
            <button
              class="user-profile-btn"
              type="button"
              aria-haspopup="true"
              :aria-expanded="showUserMenu"
              @click="showUserMenu = !showUserMenu"
            >
              <span class="user-avatar-badge">{{ userName ? userName.charAt(0).toUpperCase() : 'E' }}</span>
              <span class="user-name-text">{{ userName || 'Engineer' }}</span>
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" class="caret-icon" aria-hidden="true">
                <path d="m6 8 4 4 4-4"/>
              </svg>
            </button>

            <!-- Dropdown Menu -->
            <div v-if="showUserMenu" class="user-dropdown-menu modal-animate">
              <div class="menu-header">
                <span class="menu-label">Workspace Profile</span>
                <strong class="menu-username">{{ userName || 'Engineer' }}</strong>
              </div>
              <div class="menu-divider"></div>
              <button type="button" class="menu-item" @click="handleOpenRename">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                  <path d="M13.5 3.5a2.1 2.1 0 0 1 3 3L6 17H3v-3L13.5 3.5Z"/>
                </svg>
                <span>Edit name</span>
              </button>
              <button type="button" class="menu-item" @click="handleOpenGuideFromMenu">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                  <circle cx="10" cy="10" r="7.5"/>
                  <path d="M10 6.5v.5M10 9.5v4" stroke-linecap="round"/>
                </svg>
                <span>Getting Started Guide</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- Main Content Viewport: Unified Internal Vertical Scrolling across Routes -->
      <div v-if="view !== 'editor'" class="main-content-viewport">
        <transition name="view-fade" mode="out-in">
          <DashboardPage
            v-if="view === 'dashboard'"
            key="dashboard"
            @open="openAnalysis"
            @editor="openEditor"
            @new="navigate('new')"
            @history="navigate('history')"
            @design="navigate('design')"
            @guide="showGuide = true"
            @count="historyCount = $event"
          />
          <DesignStudioPage
            v-else-if="view === 'design'"
            key="design"
            :initial-analysis-id="analysisId"
            @open="openAnalysis"
            @editor="openEditor"
            @new="navigate('new')"
            @history="navigate('history')"
          />
          <NewAnalysisPage
            v-else-if="view === 'new'"
            key="new"
            @created="handleCreated"
          />
          <AnalysisHistoryPage
            v-else-if="view === 'history'"
            key="history"
            @open="openAnalysis"
            @new="navigate('new')"
            @count="historyCount = $event"
          />
          <AnalysisDetailPage
            v-else
            key="detail"
            :analysis-id="analysisId"
            @history="navigate('history')"
            @created="handleCreated"
            @editor="openEditor"
          />
        </transition>

        <footer class="main-footer">
          <span>Sketch2Solve · Structural Truss Engineering</span>
          <span>Deterministic analysis and verification.</span>
        </footer>
      </div>

      <!-- Dedicated Editor Route (Canvas Viewport) -->
      <TrussEditorPage v-else-if="view === 'editor'"
        key="editor"
        :analysis-id="analysisId"
        @back="openAnalysis(analysisId)"
        @history="navigate('history')"
      />
    </main>

    <!-- Onboarding Modal Dialog for First-Time Users -->
    <UserOnboardingModal
      v-if="showOnboarding"
      :current-name="userName"
      :is-editing="isEditingName"
      @save="handleSaveName"
      @close="showOnboarding = false"
    />

    <!-- Getting Started Beginner Guide -->
    <GettingStartedGuide
      v-if="showGuide"
      @close="showGuide = false"
      @finish="showGuide = false"
    />
  </div>
</template>

<style scoped>
.brand-logo-img {
  width: 32px;
  height: 32px;
  object-fit: contain;
  border-radius: 8px;
}

/* Topbar right tools */
.btn-topbar-tool {
  border: 1px solid #dfe5e1;
  background: #ffffff;
  color: #485650;
  min-height: 32px;
  padding: 0 10px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.btn-topbar-tool:hover {
  background: #f4f6f4;
  border-color: #cbd5e1;
}

.topbar-icon {
  width: 14px;
  height: 14px;
}

.guide-btn-label {
  font-size: 11px;
  font-weight: 600;
}

/* User Menu & Profile */
.user-menu-container {
  position: relative;
}

.user-profile-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 2px 10px 2px 4px;
  border: 1px solid #dfe5e1;
  background: #ffffff;
  border-radius: 999px;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.user-profile-btn:hover {
  background: #f4f6f4;
  border-color: #cbd5e1;
}

.user-avatar-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #252b2c;
  color: #f7f3df;
  font-family: var(--heading, sans-serif);
  font-size: 11px;
  font-weight: 700;
  display: grid;
  place-items: center;
}

.user-name-text {
  font-size: 11px;
  font-weight: 600;
  color: #343731;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.caret-icon {
  width: 12px;
  height: 12px;
  color: #7b8582;
}

.user-dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 180px;
  background: #ffffff;
  border: 1px solid #e3e8e4;
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(31, 55, 44, 0.12), 0 2px 6px rgba(31, 55, 44, 0.04);
  padding: 6px;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.menu-header {
  padding: 8px 10px 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-label {
  font-size: 8px;
  font-family: var(--mono, monospace);
  color: #8c9691;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.menu-username {
  font-size: 12px;
  color: #252b2c;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-divider {
  height: 1px;
  background: #edf0ed;
  margin: 4px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border: none;
  background: transparent;
  border-radius: 6px;
  color: #485650;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.menu-item:hover {
  background: #f4f6f4;
  color: #252b2c;
}

.menu-item svg {
  width: 14px;
  height: 14px;
  color: #68736f;
  flex-shrink: 0;
}
</style>
