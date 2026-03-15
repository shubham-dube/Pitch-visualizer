import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Response interceptor: normalize errors ─────────────────────
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data
    const message =
      detail?.message ||
      detail?.detail ||
      (Array.isArray(detail?.detail) ? detail.detail.map(d => d.msg).join(', ') : null) ||
      err.message ||
      'An unexpected error occurred'
    return Promise.reject({ ...err, userMessage: message, status: err.response?.status })
  }
)

// ── Projects ──────────────────────────────────────────────────────
export const projectsApi = {
  list: () =>
    apiClient.get('/projects').then(r => r.data),

  create: (payload) =>
    apiClient.post('/projects', payload).then(r => r.data),

  get: (id) =>
    apiClient.get(`/projects/${id}`).then(r => r.data),

  delete: (id) =>
    apiClient.delete(`/projects/${id}`),

  getStatus: (id) =>
    apiClient.get(`/projects/${id}/status`).then(r => r.data),

  regenerate: (id, payload = {}) =>
    apiClient.post(`/projects/${id}/regenerate`, payload).then(r => r.data),
}

// ── Panels ───────────────────────────────────────────────────────
export const panelsApi = {
  regenerate: (projectId, panelIndex, payload = {}) =>
    apiClient.post(`/projects/${projectId}/panels/${panelIndex}/regenerate`, payload).then(r => r.data),

  updatePrompt: (projectId, panelIndex, engineeredPrompt) =>
    apiClient.patch(`/projects/${projectId}/panels/${panelIndex}/prompt`, {
      engineered_prompt: engineeredPrompt,
    }).then(r => r.data),

  previewPrompt: (payload) =>
    apiClient.post('/preview-prompt', payload).then(r => r.data),
}

// ── Exports ───────────────────────────────────────────────────────
export const exportsApi = {
  htmlUrl: (id) => `${BASE_URL}/api/v1/projects/${id}/export/html`,
  jsonUrl: (id) => `${BASE_URL}/api/v1/projects/${id}/export/json`,
}

// ── Config ────────────────────────────────────────────────────────
export const configApi = {
  styles: () => apiClient.get('/styles').then(r => r.data),
  models: () => apiClient.get('/models').then(r => r.data),
}

// ── Health ────────────────────────────────────────────────────────
export const healthApi = {
  check: () => axios.get(`${BASE_URL}/health`).then(r => r.data),
}

export const imageUrl = (path) =>
  path.startsWith('http') ? path : `${BASE_URL}${path}`