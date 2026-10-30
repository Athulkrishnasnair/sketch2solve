<script setup>
import { onMounted, ref } from 'vue'
import { listAnalyses } from '../api/analyses'

const emit = defineEmits(['open', 'new', 'count'])
const analyses = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 20
const loading = ref(false)
const loadingMore = ref(false)
const error = ref('')
let requestSequence = 0

function formatDate(value) {
  if (!value) return 'Date unavailable'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function displayStatus(status) {
  return ({ pending_review: 'Pending review', reviewed: 'Reviewed', failed: 'Failed', solved: 'Solved', draft: 'Draft saved', submitted: 'Submitted to solver' })[status] || status || 'Unknown'
}

function statusClass(status) {
  if (status === 'failed') return 'status-failed'
  if (status === 'reviewed' || status === 'solved') return 'status-complete'
  return 'status-pending'
}

async function refresh() {
  if (loading.value || loadingMore.value) return
  const sequence = ++requestSequence
  loading.value = true
  error.value = ''
  try {
    const result = await listAnalyses({ page: 1, perPage })
    if (sequence !== requestSequence) return
    analyses.value = result.items || []
    page.value = result.page || 1
    total.value = result.total || 0
    emit('count', total.value)
  } catch (cause) {
    if (sequence === requestSequence) error.value = cause.message
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

async function loadMore() {
  if (loading.value || loadingMore.value || analyses.value.length >= total.value) return
  const sequence = requestSequence
  loadingMore.value = true
  error.value = ''
  try {
    const result = await listAnalyses({ page: page.value + 1, perPage })
    if (sequence !== requestSequence) return
    const existing = new Set(analyses.value.map((item) => item.analysis_id))
    analyses.value = [...analyses.value, ...(result.items || []).filter((item) => !existing.has(item.analysis_id))]
    page.value = result.page || page.value + 1
    total.value = result.total ?? total.value
    emit('count', total.value)
  } catch (cause) {
    if (sequence === requestSequence) error.value = cause.message
  } finally {
    loadingMore.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <section class="page-content history-page">
    <div class="page-heading compact-heading"><div><div class="eyebrow">SAVED WORK</div><h1>Analysis history</h1><p>Saved sketch interpretations and solver runs, newest first.</p></div><div class="heading-actions"><button class="button button-secondary" type="button" :disabled="loading || loadingMore" @click="refresh">Refresh history</button><button class="button button-primary" type="button" @click="emit('new')"><span>＋</span> New analysis</button></div></div>
    <div v-if="error" class="alert alert-error" role="alert"><span class="alert-icon">!</span><div><strong>History could not be loaded</strong><p>{{ error }}</p></div><button class="button button-secondary" type="button" :disabled="loading" @click="refresh">Retry</button></div>
    <div v-if="loading && !analyses.length" class="empty-panel"><span class="loading-dots">•••</span><p>Loading saved analyses…</p></div>
    <div v-else-if="!analyses.length && !error" class="empty-panel"><div class="empty-drawing"><span></span><span></span><span></span><i></i></div><strong>Your history is clear</strong><p>Upload a sketch to create your first saved analysis.</p><button class="button button-primary" type="button" @click="emit('new')">Upload a sketch</button></div>
    <template v-else-if="analyses.length">
      <div class="history-summary"><span><strong>{{ total }}</strong> saved records</span><span>Analysis results are stored in this local workspace.</span></div>
      <div class="history-list card-surface">
        <div class="history-header"><span>ANALYSIS</span><span>PROVIDER / MODEL</span><span>CREATED</span><span>STATUS</span><span></span></div>
        <button v-for="item in analyses" :key="item.analysis_id" class="history-row" type="button" @click="emit('open', item.analysis_id)">
          <span class="history-name"><span class="file-icon"><svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M4.5 2.8h7l4 4v10.4H4.5V2.8Z" stroke="currentColor" stroke-width="1.3"/><path d="M11.5 2.8v4h4M7 11h6M7 13.5h4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg></span><span><strong>{{ item.original_filename || (item.analysis_type === 'solver' ? 'Solver run' : 'Untitled sketch') }}</strong><small>#{{ item.analysis_id?.slice(0, 8).toUpperCase() }} · {{ item.image_width && item.image_height ? `${item.image_width} × ${item.image_height} px` : item.analysis_type }}</small></span></span>
          <span class="provider-cell"><b :class="item.provider === 'gemini' ? 'provider-gemini' : item.provider === 'meta' ? 'provider-meta' : ''">{{ item.provider || 'Deterministic solver' }}</b><small>{{ item.model_id || (item.analysis_type === 'solver' ? 'Truss model' : 'Model unavailable') }}</small></span>
          <span class="date-cell">{{ formatDate(item.created_at) }}</span>
          <span class="history-status"><span class="status-badge" :class="statusClass(item.status)"><i></i>{{ displayStatus(item.status) }}</span><small v-if="item.error_message">{{ item.error_message }}</small></span>
          <span class="row-arrow" aria-hidden="true">↗</span>
        </button>
      </div>
      <div v-if="analyses.length < total" class="load-more-row"><span>Showing {{ analyses.length }} of {{ total }} saved runs</span><button class="button button-secondary" type="button" :disabled="loadingMore" @click="loadMore">{{ loadingMore ? 'Loading…' : 'Load more' }}</button></div>
    </template>
  </section>
</template>
