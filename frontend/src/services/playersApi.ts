import { api, allPages } from './api'
import type { MetricSources, PlayerHistory, PlayerSummary, ResultComparison, RosterResponse } from '../types/reporting'

type Filters = { team_id?: string; season_id?: string; competition_id?: string; position?: string; metrics?: string[] }
function query(filters: Filters = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (Array.isArray(value)) value.forEach(item => params.append('metrics', item))
    else if (value) params.set(key, value)
  })
  return params.size ? `?${params}` : ''
}
export const playersApi = {
  teams: () => allPages<{ id: string; name: string }>('/teams'),
  seasons: () => allPages<{ id: string; name: string; start_date: string; end_date: string }>('/seasons'),
  roster: (filters: Filters = {}, signal?: AbortSignal) => api<RosterResponse>(`/players/summary${query(filters)}`, { signal }),
  summary: (id: string, filters: Filters = {}, signal?: AbortSignal) => api<PlayerSummary>(`/players/${id}/summary${query(filters)}`, { signal }),
  history: (id: string, filters: Filters = {}, signal?: AbortSignal) => api<PlayerHistory>(`/players/${id}/metrics/history${query(filters)}`, { signal }),
  byResult: (id: string, filters: Filters = {}, signal?: AbortSignal) => api<ResultComparison>(`/players/${id}/metrics/by-result${query(filters)}`, { signal }),
  sources: (id: string, metric: string, signal?: AbortSignal) => api<MetricSources>(`/players/${id}/metrics/sources?metric=${encodeURIComponent(metric)}`, { signal }),
}
