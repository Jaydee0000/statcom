import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import PageHeader from '../components/layout/PageHeader'
import VideoAnalysisEmptyState from '../components/video/VideoAnalysisEmptyState'
import AnnotationWorkspace, { type WorkspaceHandle } from '../components/video/AnnotationWorkspace'
import AnnotationEditor from '../components/video/AnnotationEditor'
import PendingVideosTable from '../components/video/PendingVideosTable'
import CompletedVideosTable from '../components/video/CompletedVideosTable'
import VideoIntake from '../components/video/VideoIntake'
import { videosApi, type WorkflowRow } from '../services/videosApi'
import { annotationSessionsApi, type SessionRecord } from '../services/annotationSessionsApi'
import { playbackPositions } from '../services/playbackPositions'
import { annotationsApi } from '../services/annotationsApi'
import type { Video } from '../types/video'
import type { AnnotationRecord, MatchContext, SkillRecord, TagRecord } from '../types/annotation'
import '../styles/video-analysis.css'

const labels = { NOT_STARTED: 'Not Started', IN_PROGRESS: 'In Progress', READY_FOR_REVIEW: 'Ready for Review', REVIEWED: 'Reviewed' } as const
const activeSessionKey = 'statcom-active-annotation-session'
function display(row: WorkflowRow): Video {
  return { id: row.video.id, fileName: row.video.original_filename, matchName: row.match_name,
    dateAdded: (row.session?.completed_at && row.session.status === 'REVIEWED' ? row.session.completed_at : row.video.uploaded_at)?.slice(0, 10),
    duration: String(row.video.duration_seconds || 0), status: labels[row.session?.status || 'NOT_STARTED'],
    progress: row.video.duration_seconds ? Math.round((row.session?.last_playback_position || 0) / row.video.duration_seconds * 100) : undefined }
}
export default function VideoAnalysisPage() {
  const [searchParams] = useSearchParams()
  const requestedVideo = searchParams.get('video')
  const requestedMatch = searchParams.get('match')
  const requestedAnnotation = searchParams.get('annotation')
  const [rows, setRows] = useState<WorkflowRow[]>([])
  const [active, setActive] = useState<{ row: WorkflowRow; session: SessionRecord } | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [annotationError, setAnnotationError] = useState('')
  const [annotations, setAnnotations] = useState<AnnotationRecord[]>([])
  const [tags, setTags] = useState<TagRecord[]>([])
  const [skills, setSkills] = useState<SkillRecord[]>([])
  const [context, setContext] = useState<MatchContext | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [editorDirty, setEditorDirty] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const opening = useRef(false)
  const restoring = useRef(false)
  const duplicating = useRef(false)
  const workspace = useRef<WorkspaceHandle>(null)
  const deepLinkOpened = useRef(false)
  const deepLinkFocused = useRef(false)
  const refresh = async () => {
    setLoading(true)
    try { const [pending, completed] = await Promise.all([videosApi.list(false), videosApi.list(true)]); setRows([...new Map([...pending, ...completed].map(row => [row.video.id, row])).values()]) }
    catch (e) { setError(`Could not load videos: ${(e as Error).message}`) } finally { setLoading(false) }
  }
  useEffect(() => { void refresh() }, [])
  useEffect(() => {
    if (loading || active || restoring.current || requestedVideo || requestedMatch) return
    const sessionId = localStorage.getItem(activeSessionKey)
    if (!sessionId) return
    const row = rows.find(item => item.session?.id === sessionId)
    if (!row?.session || row.session.status === 'NOT_STARTED') {
      localStorage.removeItem(activeSessionKey)
      return
    }
    restoring.current = true
    setBusy(true)
    annotationSessionsApi.get(sessionId).then(session => {
      setActive({ row, session })
      setRows(current => current.map(item => item.video.id === row.video.id ? { ...item, session } : item))
    }).catch(e => {
      localStorage.removeItem(activeSessionKey)
      setError(`Could not restore the active session: ${(e as Error).message}`)
    }).finally(() => { restoring.current = false; setBusy(false) })
  }, [active, loading, rows, requestedVideo, requestedMatch])
  useEffect(() => {
    if (!editorDirty) return
    const guardNavigation = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
      const link = (event.target as Element).closest('a[href]') as HTMLAnchorElement | null
      if (!link || link.target === '_blank' || link.href === window.location.href) return
      if (!window.confirm('Discard unsaved annotation changes and leave this page?')) {
        event.preventDefault()
        event.stopPropagation()
      }
    }
    document.addEventListener('click', guardNavigation, true)
    return () => document.removeEventListener('click', guardNavigation, true)
  }, [editorDirty])
  useEffect(() => {
    if (!active) { setAnnotations([]); setSelectedId(null); setContext(null); return }
    let cancelled = false
    setAnnotationError('')
    Promise.all([annotationsApi.list(active.session.id), annotationsApi.tags(), annotationsApi.skills(), annotationsApi.context(active.row.video.match_id)])
      .then(([saved, loadedTags, loadedSkills, loadedContext]) => {
        if (!cancelled) { setAnnotations(saved); setTags(loadedTags); setSkills(loadedSkills); setContext(loadedContext) }
      }).catch(e => { if (!cancelled) setAnnotationError(`Could not load annotation data: ${(e as Error).message}`) })
    return () => { cancelled = true }
  }, [active?.session.id])
  const openVideo = async (video: Video) => {
    if (opening.current) return
    if (editorDirty && !window.confirm('Discard unsaved annotation changes and switch sessions?')) return
    opening.current = true; setBusy(true); setError('')
    const row = rows.find(r => r.video.id === video.id)
    try {
      if (!row) throw new Error('Video is no longer available. Reload the list.')
      if (active && row.session && active.session.id === row.session.id) return
      // Save the outgoing workspace before switching; keep it open on failure.
      await workspace.current?.save()
      setActive(null)
      if (row.session) await playbackPositions.flush(row.session.id)
      const session = row.session && row.session.status !== 'NOT_STARTED'
        ? await annotationSessionsApi.get(row.session.id) : await annotationSessionsApi.start(video.id)
      setActive({ row, session })
      localStorage.setItem(activeSessionKey, session.id)
      setRows(current => current.map(r => r.video.id === video.id ? { ...r, session } : r))
    } catch (e) { setError(`Could not open session: ${(e as Error).message}`) } finally { opening.current = false; setBusy(false) }
  }
  const focusControl = (id: string) => { const element = document.getElementById(id); element?.scrollIntoView({ block: 'center', behavior: 'smooth' }); element?.focus() }
  const newSession = () => focusControl(rows.some(r => r.session?.status !== 'REVIEWED') ? 'first-pending-video' : 'video-match')
  const pending = rows.filter(r => r.session?.status !== 'REVIEWED').map(display)
  const completed = rows.filter(r => r.session?.status === 'REVIEWED').map(display)
  const selected = annotations.find(annotation => annotation.id === selectedId) || null
  const selectAnnotation = (annotation: AnnotationRecord) => {
    if (editorDirty && annotation.id !== selectedId && !window.confirm('Discard unsaved changes and open this annotation?')) return false
    setSelectedId(annotation.id); setEditorDirty(false); return true
  }
  const closeSession = () => {
    if (editorDirty && !window.confirm('Discard unsaved annotation changes and close the session?')) return
    localStorage.removeItem(activeSessionKey)
    setActive(null); setEditorDirty(false); void refresh()
  }
  const duplicate = async (annotation: AnnotationRecord, at: number) => {
    if (duplicating.current) return
    if (editorDirty && !window.confirm('Discard unsaved changes and duplicate this annotation at the current time?')) return
    duplicating.current = true
    try {
      const matchTime = Math.max(0, at - active!.row.video.video_time_offset + active!.row.video.match_time_offset)
      const copy = await annotationsApi.duplicate(annotation.id, at, null, matchTime, active!.row.video.period)
      setAnnotations(current => [...current, copy].sort((a, b) => a.video_start_time - b.video_start_time)); setSelectedId(copy.id); setEditorDirty(false)
    } catch (e) { setAnnotationError(`Could not duplicate annotation: ${(e as Error).message}`) }
    finally { duplicating.current = false }
  }
  useEffect(() => {
    if (loading || active || deepLinkOpened.current || (!requestedVideo && !requestedMatch)) return
    const row = rows.find(item => requestedVideo ? item.video.id === requestedVideo : item.video.match_id === requestedMatch)
    if (!row) { if (rows.length) setError('The requested match video is not available.'); return }
    deepLinkOpened.current = true
    void openVideo(display(row))
  }, [loading, rows, active, requestedVideo, requestedMatch])
  useEffect(() => {
    if (!requestedAnnotation || !active || deepLinkFocused.current || !annotations.length) return
    const annotation = annotations.find(item => item.id === requestedAnnotation)
    if (!annotation) { setAnnotationError('The requested source annotation is not active or does not belong to this video.'); return }
    deepLinkFocused.current = true
    setSelectedId(annotation.id)
    workspace.current?.seek(annotation.video_start_time)
  }, [requestedAnnotation, active, annotations])
  return <div className="va-page">
    <PageHeader title="Video Analysis" subtitle="Upload match footage, annotate clips, and review completed work." actions={<>
      <button type="button" className="va-button" onClick={() => focusControl('video-match')}>Upload Video</button>
      <button type="button" className="va-button va-button--primary" onClick={newSession}>New Annotation Session</button>
    </>} />
    {error && <p className="va-error" role="alert">{error} <button className="va-row-action" onClick={() => { setError(''); void refresh() }}>Reload</button></p>}
    {busy && <p className="va-helper" role="status">Opening session…</p>}
    {annotationError && <p className="va-error" role="alert">{annotationError}</p>}
    {active ? <div className="va-session-grid">
      <AnnotationWorkspace ref={workspace} key={active.session.id} session={active.session} row={active.row} annotations={annotations} skills={skills} selectedId={selectedId} onClose={closeSession}
        onTimeChange={(time, length) => { setCurrentTime(time); setDuration(length) }} onSelect={selectAnnotation} onDuplicate={(annotation, at) => void duplicate(annotation, at)}
        onUpdated={session => { setActive({ ...active, session }); setRows(current => current.map(r => r.video.id === active.row.video.id ? { ...r, session } : r)) }} />
      <AnnotationEditor key={`${active.session.id}-editor`} sessionId={active.session.id} matchId={active.row.video.match_id} videoId={active.row.video.id} period={active.row.video.period}
        videoOffset={active.row.video.video_time_offset} matchOffset={active.row.video.match_time_offset} currentTime={currentTime} duration={duration || active.row.video.duration_seconds || 0}
        selected={selected} tags={tags} skills={skills} context={context} onDirtyChange={setEditorDirty}
        onSaved={saved => { setAnnotations(current => [...current.filter(item => item.id !== saved.id), saved].sort((a, b) => a.video_start_time - b.video_start_time)); setSelectedId(saved.id) }}
        onArchived={id => { setAnnotations(current => current.filter(item => item.id !== id)); setSelectedId(null) }} onClearSelection={() => setSelectedId(null)}
        onTagCreated={tag => setTags(current => [...current, tag])} onSkillCreated={skill => setSkills(current => [...current, skill])} />
    </div> : <VideoAnalysisEmptyState onNew={newSession} onSelect={newSession} />}
    <div className="va-dashboard-grid">
      <VideoIntake onUploaded={refresh} />
      <PendingVideosTable videos={pending} onStart={v => void openVideo(v)} loading={loading} busy={busy} />
      <CompletedVideosTable videos={completed} onReview={v => void openVideo(v)} loading={loading} busy={busy} />
    </div>
  </div>
}
