import { API_BASE, allPages, errorMessage } from './api'
import type { SessionRecord } from './annotationSessionsApi'
export type VideoRecord = {
  id: string; match_id: string; original_filename: string; duration_seconds: number | null
  uploaded_at: string; period: string | null; video_time_offset: number; match_time_offset: number
}
export type WorkflowRow = { video: VideoRecord; session: SessionRecord | null; match_name: string; match_date: string }
export const videosApi = {
  list: (completed: boolean) => allPages<WorkflowRow>(`/videos/workflow?completed=${completed}`),
  media: (id: string) => `${API_BASE}/videos/${id}/media`,
  upload: (file: File, matchId: string, progress: (value: number) => void) => new Promise<VideoRecord>((resolve, reject) => {
    const data = new FormData(); data.append('file', file); data.append('match_id', matchId)
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}/videos/upload`)
    xhr.upload.onprogress = e => { if (e.lengthComputable) progress(Math.round(e.loaded / e.total * 100)) }
    xhr.onerror = () => reject(new Error('Upload failed. Check the backend connection.'))
    xhr.onabort = () => reject(new Error('Upload was cancelled.'))
    xhr.onload = () => {
      let body: unknown
      try { body = JSON.parse(xhr.responseText) } catch { reject(new Error('Upload failed. The server returned an unreadable response.')); return }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as VideoRecord)
      else reject(new Error(errorMessage(body)))
    }
    xhr.send(data)
  }),
}
