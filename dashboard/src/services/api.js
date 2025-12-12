import axios from 'axios'

const DEBUG =
  (import.meta.env.VITE_DEBUG && import.meta.env.VITE_DEBUG.toString() === 'true') ||
  (typeof window !== 'undefined' && window.localStorage && localStorage.getItem('debug') === 'true')
const log = (...args) => {
  if (DEBUG) {
    console.log('[API]', ...args)
  }
}

const apiBaseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export const api = axios.create({ baseURL: apiBaseURL })

api.interceptors.request.use((config) => {
  const storedToken = localStorage.getItem('token')
  const storedTokenType = localStorage.getItem('token_type') || 'Bearer'
  if (storedToken) {
    config.headers = config.headers || {}
    config.headers.Authorization = `${storedTokenType} ${storedToken}`
  }
  log('→', (config.method || 'get').toUpperCase(), `${config.baseURL || ''}${config.url || ''}`)
  return config
})

api.interceptors.response.use(
  (res) => {
    log('←', res.status, res?.config?.url)
    return res
  },
  (error) => {
    const status = error?.response?.status
    const url = error?.config ? `${error.config.baseURL || ''}${error.config.url || ''}` : undefined
    log('⤬', status, url, error?.message)
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('token_type')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export default api

export const cloudAccountsApi = {
  list: async () => {
    const res = await api.get('/cloud-accounts/')
    return res.data
  },
  create: async (payload) => {
    const res = await api.post('/cloud-accounts/', payload)
    return res.data
  },
  remove: async (id) => {
    const res = await api.delete(`/cloud-accounts/${id}/`)
    return res.data
  },
}

export const alertsApi = {
  list: async (params) => {
    const res = await api.get('/alerts/', { params })
    return res.data
  },
}

export const organizationApi = {
  listUsers: async () => {
    const res = await api.get('/organization/users/')
    return res.data
  },
  listInvitations: async () => {
    const res = await api.get('/organization/invitations/')
    return res.data
  },
}

export const identitiesApi = {
  list: async () => {
    const res = await api.get('/identities/')
    return res.data
  },
  get: async (id) => {
    const res = await api.get(`/identities/${id}/`)
    return res.data
  },
  update: async (id, payload) => {
    const res = await api.patch(`/identities/${id}/`, payload)
    return res.data
  },
}

