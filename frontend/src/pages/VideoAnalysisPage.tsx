import { useState } from 'react'
import PageHeader from '../components/layout/PageHeader'
import VideoAnalysisEmptyState from '../components/video/VideoAnalysisEmptyState'
import AnnotationWorkspace from '../components/video/AnnotationWorkspace'
import AnnotationEditor from '../components/video/AnnotationEditor'
import PendingVideosTable from '../components/video/PendingVideosTable'
import CompletedVideosTable from '../components/video/CompletedVideosTable'
import { mockVideos, pendingVideos, completedVideos } from '../data/mockVideos'
import type { Video } from '../types/video'
import type { AnnotationSession } from '../types/annotationSession'
import '../styles/video-analysis.css'

export default function VideoAnalysisPage() {
  const [activeSession, setActiveSession] = useState<AnnotationSession | null>(null)
  const activeVideo = mockVideos.find(video => video.id === activeSession?.videoId)
  const focusControl = (id: string) => document.getElementById(id)?.focus()
  const openVideo = (video: Video) => setActiveSession({
    id: `preview-${video.id}`, videoId: video.id, matchName: video.matchName,
    date: video.dateAdded, annotator: 'Coach', progress: video.progress ?? (video.status === 'Not Started' ? 0 : 100),
    status: video.status === 'Annotated' || video.status === 'Reviewed' ? 'Completed' : 'In Progress',
  })
  const newSession = () => openVideo(pendingVideos[0])

  return <div className="va-page">
    <PageHeader title="Video Analysis" subtitle="Upload match footage, annotate clips, and review completed work." actions={<>
      <button type="button" className="va-button" title="Upload preview only">Upload Video</button>
      <button type="button" className="va-button va-button--primary" onClick={newSession}>New Annotation Session</button>
    </>} />
    {activeSession && activeVideo ? <div className="va-session-grid">
      <AnnotationWorkspace session={activeSession} video={activeVideo} onClose={() => setActiveSession(null)} />
      <AnnotationEditor key={activeSession.id} />
    </div> : <VideoAnalysisEmptyState onNew={newSession} onSelect={() => focusControl('first-pending-video')} />}
    <div className="va-dashboard-grid">
      <PendingVideosTable videos={pendingVideos} onStart={openVideo} />
      <CompletedVideosTable videos={completedVideos} onReview={openVideo} />
    </div>
  </div>
}
