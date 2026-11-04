const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000').replace(/\/+$/, '')

export function apiUrl(path) {
  if (!path) return ''
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(apiUrl(path), options)
  } catch {
    throw new Error('Could not reach the local Sketch2Solve backend. Check that Flask is running on port 5000.')
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

export function saveAnalysisDraft(analysisId, draft, coordinatesConfirmed) {
  return request(`/api/analyses/${encodeURIComponent(analysisId)}/draft`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ geometry: draft, coordinates_confirmed: coordinatesConfirmed }),
  })
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

export function createAnalysis(file, provider) {
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
