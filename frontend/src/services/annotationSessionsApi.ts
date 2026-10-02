import { api } from './api'
export type SessionStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'READY_FOR_REVIEW' | 'REVIEWED'
export type SessionRecord = {
  id: string; video_id: string; match_id: string; status: SessionStatus
  last_playback_position: number; progress: number; completed_at: string | null
}
export const annotationSessionsApi = {
  get: (id: string) => api<SessionRecord>(`/annotation-sessions/${id}`),
  start: (videoId: string) => api<SessionRecord>(`/videos/${videoId}/start`, { method: 'POST' }),
  update: (id: string, data: Partial<Pick<SessionRecord, 'status' | 'last_playback_position'>>, keepalive = false) =>
    api<SessionRecord>(`/annotation-sessions/${id}`, { method: 'PATCH', body: JSON.stringify(data), keepalive }),
}
