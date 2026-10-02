import { allPages, api } from './api'
import type { AnnotationRecord, AnnotationWrite, MatchContext, SkillRecord, TagRecord } from '../types/annotation'

export type SkillCreate = {
  name: string; description: string | null; category: string | null
  fields: { key: string; label: string; data_type: string; required: boolean; options: string[] | null; display_order: number }[]
}

export const annotationsApi = {
  list: (sessionId: string) => api<AnnotationRecord[]>(`/annotation-sessions/${sessionId}/annotations`),
  create: (sessionId: string, data: AnnotationWrite) => api<AnnotationRecord>(`/annotation-sessions/${sessionId}/annotations`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: AnnotationWrite) => api<AnnotationRecord>(`/annotations/${id}/aggregate`, { method: 'PATCH', body: JSON.stringify(data) }),
  archive: (id: string) => api<void>(`/annotations/${id}/archive`, { method: 'DELETE' }),
  duplicate: (id: string, videoStart: number, videoEnd: number | null, matchTime: number, matchPeriod: string | null) =>
    api<AnnotationRecord>(`/annotations/${id}/duplicate`, { method: 'POST', body: JSON.stringify({ video_start_time: videoStart, video_end_time: videoEnd, match_time: matchTime, match_period: matchPeriod }) }),
  tags: () => allPages<TagRecord>('/tags?is_active=true'),
  createTag: (data: { name: string; description: string | null; category: string | null; color: string | null }) =>
    api<TagRecord>('/tags', { method: 'POST', body: JSON.stringify(data) }),
  skills: () => api<SkillRecord[]>('/annotation-library/skills'),
  createSkill: (data: SkillCreate) => api<SkillRecord>('/annotation-library/skills', { method: 'POST', body: JSON.stringify(data) }),
  context: (matchId: string) => api<MatchContext>(`/matches/${matchId}/annotation-context`),
}
