export type User = { id: number; phone: string; name: string; role: string; is_active: boolean }

const TOKEN_KEY = 'reval_access_token'
const REFRESH_KEY = 'reval_refresh_token'

export function getToken() { return localStorage.getItem(TOKEN_KEY) }
export function getRefreshToken() { return localStorage.getItem(REFRESH_KEY) }
export function setTokens(access: string, refresh: string) {
  localStorage.setItem(TOKEN_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}
export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

async function request<T>(path: string, opts: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(opts.headers || {})
  if (!headers.has('Content-Type') && !(opts.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(path, { ...opts, headers })
  if (res.status === 401 && retry && getRefreshToken()) {
    const ok = await tryRefresh()
    if (ok) return request<T>(path, opts, false)
    clearTokens()
  }
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try { const j = await res.json(); msg = j.detail || JSON.stringify(j) } catch {}
    throw new Error(msg)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json() as Promise<T>
  return (await res.blob()) as unknown as T
}

async function tryRefresh(): Promise<boolean> {
  const rt = getRefreshToken()
  if (!rt) return false
  try {
    const res = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    })
    if (!res.ok) return false
    const j = await res.json()
    setTokens(j.access_token, j.refresh_token)
    return true
  } catch { return false }
}

export const api = {
  login: (phone: string, password: string) => request<{access_token:string;refresh_token:string}>('/api/auth/login', { method: 'POST', body: JSON.stringify({ phone, password }) }),
  me: () => request<User>('/api/auth/me'),
  listComparables: (params?: { page?: number; size?: number; city?: string; district?: string; keyword?: string }) => {
    const sp = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '' && v !== null) sp.set(k, String(v)) })
    }
    const q = sp.toString()
    return request<any>(`/api/comparables${q ? `?${q}` : ''}`)
  },
  getComparable: (id: number) => request<any>(`/api/comparables/${id}`),
  createComparable: (data: any) => request<any>('/api/comparables', { method: 'POST', body: JSON.stringify(data) }),
  updateComparable: (id: number, data: any) => request<any>(`/api/comparables/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteComparable: (id: number) => request<any>(`/api/comparables/${id}`, { method: 'DELETE' }),
  nearbyComparables: (data: any) => request<any>('/api/comparables/nearby', { method: 'POST', body: JSON.stringify(data) }),
  importComparables: (file: File) => { const fd = new FormData(); fd.append('file', file); return request<any>('/api/comparables/import', { method: 'POST', body: fd }) },
  createValuation: (data: any) => request<any>('/api/valuations', { method: 'POST', body: JSON.stringify(data) }),
  listValuations: () => request<any>('/api/valuations'),
  getValuation: (id: number) => request<any>(`/api/valuations/${id}`),
  listReports: (taskId?: number) => request<any>(`/api/reports${taskId ? `?task_id=${taskId}` : ''}`),
  generateReport: (task_id: number) => request<any>('/api/reports/generate', { method: 'POST', body: JSON.stringify({ task_id, file_format: 'docx' }) }),
  downloadReport: async (id: number, filename: string) => {
    const token = getToken()
    const res = await fetch(`/api/reports/${id}/download`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
    if (!res.ok) { let msg = `HTTP ${res.status}`; try { const j=await res.json(); msg=j.detail||msg } catch {}; throw new Error(msg) }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = filename || `report_${id}.docx`; a.click()
    URL.revokeObjectURL(url)
  },
  seedFactors: () => request<any>('/api/factors/seed-defaults', { method: 'POST' }),
  listFactors: () => request<any>('/api/factors'),
}
