import { api, allPages } from './api'
import type { MatchReference, MatchStats } from '../types/reporting'
export type TeamRecord = { id: string; name: string }
export type MatchRecord = { id: string; home_team_id: string; away_team_id: string; match_date: string }
export const matchesApi = {
  list: () => allPages<MatchRecord>('/matches'),
  teams: () => allPages<TeamRecord>('/teams'),
  createTeam: (name: string) => api<TeamRecord>('/teams', { method: 'POST', body: JSON.stringify({ name }) }),
  create: (data: Omit<MatchRecord, 'id'>) => api<MatchRecord>('/matches', { method: 'POST', body: JSON.stringify(data) }),
  overview: (signal?: AbortSignal) => api<{ matches: MatchReference[] }>('/matches/overview', { signal }),
  stats: (id: string, metrics: string[] = [], signal?: AbortSignal) => {
    const params = new URLSearchParams(); metrics.forEach(metric => params.append('metrics', metric))
    return api<MatchStats>(`/matches/${id}/stats${params.size ? `?${params}` : ''}`, { signal })
  },
}
