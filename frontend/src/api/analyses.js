export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000').replace(/\/+$/, '')

export function apiUrl(path) {
  if (!path) return ''
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(apiUrl(path), options)
  } catch {
    const isLocal = API_BASE.includes('localhost') || API_BASE.includes('127.0.0.1')
    throw new Error(
      isLocal
        ? 'Could not reach the local Sketch2Solve backend. Check that Flask is running on port 5000.'
        : `Could not reach the Sketch2Solve backend at ${API_BASE}. Check your network connection or server status.`
    )
  }

  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message = typeof body === 'object' && body?.message
      ? body.message
      : `The backend returned HTTP ${response.status}.`
    const error = new Error(message)
    error.status = response.status
    error.body = body
    throw error
  }
  return body
}

export function listAnalyses({ page = 1, perPage = 50 } = {}) {
  return request(`/api/analyses?page=${page}&per_page=${perPage}`)
}

export function getAnalysis(analysisId) {
  return request(`/api/analyses/${encodeURIComponent(analysisId)}`)
}

export function getAnalysisDraft(analysisId) {
  return request(`/api/analyses/${encodeURIComponent(analysisId)}/draft`)
}

export async function getAnalysisImage(imageUrl) {
  try {
    const response = await fetch(apiUrl(imageUrl))
    if (!response.ok) throw new Error('The saved source image is unavailable.')
    return await response.blob()
  } catch (error) {
    if (error instanceof TypeError) throw new Error('Could not reach the local Sketch2Solve backend.')
    throw error
  }
}

export function saveAnalysisDraft(analysisId, draft, coordinatesConfirmed, reopen = false) {
  const query = reopen ? '?reopen=true' : ''
  return request(`/api/analyses/${encodeURIComponent(analysisId)}/draft${query}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ geometry: draft, coordinates_confirmed: coordinatesConfirmed }),
  })
}

export function exportAnalysisUrl(analysisId, format = 'json') {
  return apiUrl(`/api/analyses/${encodeURIComponent(analysisId)}/export/${encodeURIComponent(format)}`)
}

export async function downloadAnalysisExport(analysisId, format = 'json') {
  const url = exportAnalysisUrl(analysisId, format)
  const response = await fetch(url)
  if (!response.ok) {
    let message = `Export failed with HTTP ${response.status}.`
    try {
      const errJson = await response.json()
      if (errJson?.message) message = errJson.message
    } catch (_) {}
    const err = new Error(message)
    err.status = response.status
    throw err
  }
  const blob = await response.blob()
  const disposition = response.headers.get('content-disposition') || ''
  let filename = `truss_${analysisId.slice(0, 8)}.${format}`
  const match = disposition.match(/filename="?([^";]+)"?/)
  if (match && match[1]) {
    filename = match[1]
  }
  const blobUrl = window.URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = blobUrl
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  window.URL.revokeObjectURL(blobUrl)
}

export function markAnalysisReviewed(analysisId) {
  return request(`/api/analyses/${encodeURIComponent(analysisId)}/review`, { method: 'POST' })
}

export function solveReviewedAnalysis(analysisId) {
  return request(`/api/analyses/${encodeURIComponent(analysisId)}/solve`, { method: 'POST' })
}

export function previewAnalysisGeometry(geometry, analysisId = '') {
  const path = analysisId
    ? `/api/analyses/${encodeURIComponent(analysisId)}/preview`
    : '/api/analyses/preview'
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ geometry }),
  })
}

export function createAnalysis(file, provider = 'meta') {
  const body = new FormData()
  body.append('image', file)
  body.append('provider', provider)
  return request('/api/analyses', { method: 'POST', body })
}

export function resolveGeometryIssue(geometry, issue, diagnostics = null) {
  return request('/api/ai/assistant', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      geometry,
      issue,
      diagnostics,
    }),
  })
}

export function designTruss({ message, intent = 'auto', context = {}, provider = null }) {
  return request('/api/ai/design', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      intent,
      context,
      provider,
    }),
  })
}

export function applyDesignProposal({ proposal_id, analysis_id = null, base_revision = null, proposed_model, create_record = false }) {
  return request('/api/ai/design/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      proposal_id,
      analysis_id,
      base_revision,
      proposed_model,
      create_record,
      persist: create_record,
    }),
  })
}

export function rejectDesignProposal({ proposal_id, analysis_id = null, base_revision = null }) {
  return request('/api/ai/design/reject', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      proposal_id,
      analysis_id,
      base_revision,
    }),
  })
}
