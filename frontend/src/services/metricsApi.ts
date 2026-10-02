import { api } from './api'
import type { MatchMetrics, MetricsFilters } from '../types/metrics'

function query(filters: MetricsFilters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') params.set(key, String(value))
  })
  const text = params.toString()
  return text ? `?${text}` : ''
}

export const metricsApi = {
  match: (matchId: string, filters: MetricsFilters = {}) => api<MatchMetrics>(`/matches/${matchId}/metrics${query(filters)}`),
}
