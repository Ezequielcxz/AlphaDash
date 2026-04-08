import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Accounts API
export const accountsApi = {
  list: () => api.get('/accounts/'),
  get: (id) => api.get(`/accounts/${id}`),
  getByNumber: (number) => api.get(`/accounts/number/${number}`),
  create: (data) => api.post('/accounts/', data),
  update: (id, data) => api.patch(`/accounts/${id}`, data),
  delete: (id) => api.delete(`/accounts/${id}`),
}

// Trades API
export const tradesApi = {
  list: (params) => api.get('/trades/', { params }),
  get: (id) => api.get(`/trades/${id}`),
  getByAccount: (accountNumber, params) =>
    api.get(`/trades/account/${accountNumber}`, { params }),
  symbols: (accountId) => api.get('/trades/symbols/list', { params: { account_id: accountId } }),
  magicNumbers: (accountId) => api.get('/trades/magic-numbers/list', { params: { account_id: accountId } }),
}

// Metrics API
export const metricsApi = {
  global: (days) => api.get('/metrics/global', { params: days != null ? { days } : {} }),
  byAccount: (accountId, days) => api.get(`/metrics/account/${accountId}`, { params: days != null ? { days } : {} }),
  byStrategy: (magicNumber, accountId) =>
    api.get(`/metrics/strategy/${magicNumber}`, { params: { account_id: accountId } }),
  equityCurve: (accountId, days) => api.get('/metrics/equity-curve', { params: { ...(accountId ? { account_id: accountId } : {}), ...(days != null ? { days } : {}) } }),
  heatmap: (accountId, days) => api.get('/metrics/heatmap', { params: { ...(accountId ? { account_id: accountId } : {}), ...(days != null ? { days } : {}) } }),
  temporal: (accountId) => api.get('/metrics/temporal', { params: { account_id: accountId } }),
}

// Ingest API
export const ingestApi = {
  single: (trade) => api.post('/ingest/', trade),
  batch: (trades) => api.post('/ingest/batch', trades),
  uploadCsv: async (file, accountNumber, brokerName) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('account_number', accountNumber)
    if (brokerName) formData.append('broker_name', brokerName)
    return api.post('/ingest/upload-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

// MT5 Sync API
export const syncApi = {
  connect: (credentials) => api.post('/sync/connect', credentials),
  disconnect: () => api.post('/sync/disconnect'),
  status: () => api.get('/sync/status'),
  history: (params) => api.post('/sync/history', params),
  positions: () => api.get('/sync/positions'),
  summary: () => api.get('/sync/summary'),
  symbolInfo: (symbol) => api.get(`/sync/symbols/${symbol}`),
  syncStatus: (login) => api.get(`/sync/sync-status/${login}`),
  terminals: () => api.get('/sync/terminals'),
}

export default api