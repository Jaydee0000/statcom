import { api, allPages } from './api'
import type { MetricDefinition, TeamStatSheet } from '../types/reporting'

type TeamFilters = { team_id: string; season_id?: string; competition_id?: string; match_id?: string; date_from?: string; date_to?: string; position?: string; metrics?: string[] }
function query(filters: TeamFilters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (Array.isArray(value)) value.forEach(item => params.append('metrics', item))
    else if (value) params.set(key, value)
  })
  return `?${params}`
}
export const analyticsApi = {
  teams: () => allPages<{ id: string; name: string }>('/teams'),
  seasons: () => allPages<{ id: string; name: string }>('/seasons'),
  competitions: () => allPages<{ id: string; name: string }>('/competitions'),
  definitions: (signal?: AbortSignal) => api<MetricDefinition[]>('/metric-definitions', { signal }),
  teamStats: (filters: TeamFilters, signal?: AbortSignal) => api<TeamStatSheet>(`/team-stats${query(filters)}`, { signal }),
}
