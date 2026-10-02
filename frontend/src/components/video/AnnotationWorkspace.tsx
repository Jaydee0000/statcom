import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { annotationSessionsApi, type SessionRecord, type SessionStatus } from '../../services/annotationSessionsApi'
import { playbackPositions } from '../../services/playbackPositions'
import { videosApi, type WorkflowRow } from '../../services/videosApi'
import type { AnnotationRecord, SkillRecord } from '../../types/annotation'

type Props = { session: SessionRecord; row: WorkflowRow; annotations: AnnotationRecord[]; skills: SkillRecord[]; selectedId: string | null
  onClose: () => void; onUpdated: (session: SessionRecord) => void; onTimeChange: (time: number, duration: number) => void
  onSelect: (annotation: AnnotationRecord) => boolean; onDuplicate: (annotation: AnnotationRecord, currentTime: number) => void }
const time = (value: number) => `${Math.floor(value / 60).toString().padStart(2, '0')}:${(value % 60).toFixed(1).padStart(4, '0')}`
export type WorkspaceHandle = { save: () => Promise<void>; seek: (time: number) => void }
export default forwardRef<WorkspaceHandle, Props>(function AnnotationWorkspace({ session, row, annotations, skills, selectedId, onClose, onUpdated, onTimeChange, onSelect, onDuplicate }, ref) {
  const player = useRef<HTMLVideoElement>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const position = useRef(session.last_playback_position)
  const ready = useRef(false)
  const seekSave = useRef<number | undefined>(undefined)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saveError, setSaveError] = useState(sessionStorage.getItem(`statcom-save-error-${session.id}`) || '')
  const [busy, setBusy] = useState(false)
  const [current, setCurrent] = useState(session.last_playback_position)
  const [duration, setDuration] = useState(row.video.duration_seconds || 0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [volume, setVolume] = useState(1)
  const [muted, setMuted] = useState(false)
  const save = async () => {
    if (!ready.current) return
    try { await playbackPositions.save(session.id, position.current); setSaveError('') }
    catch (e) { setSaveError(`Playback position was not saved: ${(e as Error).message}`); throw e }
  }
  const saveQuietly = () => { void save().catch(() => {}) }
  useImperativeHandle(ref, () => ({ save: async () => { player.current?.pause(); await save() }, seek: value => seek(value) }))
  useEffect(() => {
    heading.current?.focus()
    const video = player.current
    const persist = () => {
      if (ready.current) void playbackPositions.save(session.id, position.current).catch(() => {})
    }
    const hidden = () => { if (document.visibilityState === 'hidden') persist() }
    const timer = window.setInterval(() => { if (video && !video.paused) saveQuietly() }, 5000)
    window.addEventListener('pagehide', persist); document.addEventListener('visibilitychange', hidden)
    return () => {
      window.clearInterval(timer); window.removeEventListener('pagehide', persist)
      window.clearTimeout(seekSave.current)
      document.removeEventListener('visibilitychange', hidden); persist()
    }
  }, [session.id])
  useEffect(() => {
    const shortcuts = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement
      if (target.matches('input, textarea, select, [contenteditable="true"]')) return
      const video = player.current
      if (!video || !ready.current) return
      if (event.code === 'Space') { event.preventDefault(); if (video.paused) void video.play(); else video.pause() }
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); seek(Math.max(0, Math.min(duration, video.currentTime + (event.key === 'ArrowLeft' ? -2 : 2)))) }
    }
    window.addEventListener('keydown', shortcuts)
    return () => window.removeEventListener('keydown', shortcuts)
  }, [duration])
  const changeStatus = async (status: SessionStatus) => {
    setBusy(true); setError('')
    try { player.current?.pause(); await save(); onUpdated(await annotationSessionsApi.update(session.id, { status })) }
    catch (e) { setError(`Session update failed: ${(e as Error).message}`) } finally { setBusy(false) }
  }
  const close = async () => {
    setBusy(true); player.current?.pause()
    try { await save(); onClose() } catch { /* Keep workspace open so the user can retry. */ } finally { setBusy(false) }
  }
  const seek = (value: number) => { if (player.current && ready.current) player.current.currentTime = value }
  return <section className="card va-workspace" aria-labelledby="workspace-title">
    <div className="va-card-heading"><div><span className="va-eyebrow">Annotation Workspace</span><h2 ref={heading} tabIndex={-1} id="workspace-title">{row.match_name}</h2></div>
      <button type="button" className="va-row-action" disabled={busy} onClick={() => void close()}>Close Session</button></div>
    <div className="va-player">
      <video ref={player} src={videosApi.media(row.video.id)} preload="metadata" playsInline aria-label="Match video"
        onLoadedMetadata={e => {
          const v = e.currentTarget
          const max = Math.min(Number.isFinite(v.duration) ? v.duration : duration, row.video.duration_seconds ?? Infinity)
          const saved = Number.isFinite(session.last_playback_position) ? session.last_playback_position : 0
          position.current = Math.max(0, Math.min(saved, max)); v.currentTime = position.current
          setDuration(max); setCurrent(position.current); onTimeChange(position.current, max); ready.current = true; setLoading(false)
        }} onTimeUpdate={e => {
          if (!ready.current) return
          position.current = Math.max(0, Math.min(e.currentTarget.currentTime, row.video.duration_seconds ?? Infinity)); setCurrent(position.current); onTimeChange(position.current, duration)
        }} onPlay={() => setPlaying(true)} onPause={() => { setPlaying(false); saveQuietly() }}
        onSeeked={e => { if (ready.current) {
          position.current = Math.min(e.currentTarget.currentTime, row.video.duration_seconds ?? Infinity); setCurrent(position.current); onTimeChange(position.current, duration)
          window.clearTimeout(seekSave.current)
          seekSave.current = window.setTimeout(saveQuietly, 350)
        } }}
        onError={() => { setLoading(false); setError('Video could not be loaded. Check that the file is available and its codec is supported by your browser (H.264 MP4 is recommended).') }} />
      {loading && <span className="va-player__badge va-badge" role="status">Loading video…</span>}
      <div className="va-player__controls" aria-label="Video controls">
        <button type="button" aria-label={playing ? 'Pause' : 'Play'} disabled={loading} onClick={() => {
          const v = player.current; if (!v) return
          if (v.paused) void v.play().catch(e => setError(`Playback failed: ${e.message}`)); else v.pause()
        }}>{playing ? 'Ⅱ' : '▶'}</button><span>{time(current)} / {time(duration)}</span>
        <input aria-label="Seek" type="range" min="0" max={duration} step="0.1" value={Math.min(current, duration)} disabled={loading} onChange={e => seek(Number(e.target.value))} />
        <button type="button" aria-label={muted ? 'Unmute' : 'Mute'} onClick={() => { if (player.current) player.current.muted = !muted; setMuted(!muted) }}>{muted ? 'Unmute' : 'Mute'}</button>
        <input aria-label="Volume" type="range" min="0" max="1" step="0.05" value={volume} onChange={e => { const value = Number(e.target.value); setVolume(value); if (player.current) player.current.volume = value }} />
        <select aria-label="Playback speed" value={speed} onChange={e => { const value = Number(e.target.value); setSpeed(value); if (player.current) player.current.playbackRate = value }}>
          {[0.25, 0.5, 0.75, 1, 1.25, 1.5, 2].map(value => <option key={value} value={value}>{value}×</option>)}</select>
      </div>
    </div>
    <div className="va-timeline"><div className="va-timeline__heading"><strong>Annotation Timeline</strong><span>{annotations.length} saved</span></div>
      <div className="va-timeline__track">{duration > 0 && annotations.map(annotation => {
        const skill = skills.find(item => item.id === annotation.skill_definition_id)
        const color = annotation.tags.find(tag => tag.color)?.color || '#20b876'
        const left = Math.max(0, Math.min(100, annotation.video_start_time / duration * 100))
        const width = annotation.video_end_time === null ? undefined : Math.max(.7, (annotation.video_end_time - annotation.video_start_time) / duration * 100)
        return <button type="button" aria-label={`${skill?.name || 'Annotation'} at ${time(annotation.video_start_time)}`} title={`${skill?.name || 'Annotation'} · ${time(annotation.video_start_time)}`} className={`va-marker ${annotation.video_end_time === null ? 'va-marker--point' : 'va-marker--range'} ${selectedId === annotation.id ? 'is-selected' : ''}`} key={annotation.id} style={{ left: `${left}%`, width: width ? `${Math.min(width, 100 - left)}%` : undefined, backgroundColor: color }} onClick={() => { if (onSelect(annotation)) seek(annotation.video_start_time) }} />
      })}</div><div className="va-timeline__labels"><span>00:00</span><span>{time(duration)}</span></div>
      <p className="va-helper">Video: {time(current)} · Match: {time(Math.max(0, current - row.video.video_time_offset + row.video.match_time_offset))}{row.video.period ? ` · ${row.video.period}` : ''} · Position saves automatically</p>
      <div className="va-actions">
        {session.status === 'IN_PROGRESS' && <button className="va-button" disabled={busy} onClick={() => void changeStatus('READY_FOR_REVIEW')}>Ready for Review</button>}
        {session.status === 'READY_FOR_REVIEW' && <button className="va-button va-button--primary" disabled={busy} onClick={() => void changeStatus('REVIEWED')}>Mark Reviewed</button>}
        {(session.status === 'READY_FOR_REVIEW' || session.status === 'REVIEWED') && <button className="va-button" disabled={busy} onClick={() => void changeStatus('IN_PROGRESS')}>Reopen for correction</button>}
        {busy && <span className="va-helper" role="status">Saving session…</span>}
      </div>
      {error && <p className="va-error" role="alert">{error}</p>}
      {saveError && <p className="va-error" role="alert">{saveError} <button className="va-row-action" onClick={saveQuietly}>Retry save</button></p>}
      <div className="va-annotation-list" aria-label="Saved annotations">
        <div className="va-annotation-list__head"><span>Time</span><span>Skill / players</span><span>Tags</span><span>Status</span><span /></div>
        {annotations.map(annotation => <button type="button" className={selectedId === annotation.id ? 'is-selected' : ''} key={annotation.id} onClick={() => { if (onSelect(annotation)) seek(annotation.video_start_time) }}>
          <span>{time(annotation.video_start_time)}{annotation.video_end_time !== null ? `–${time(annotation.video_end_time)}` : ''}</span>
          <span><strong>{skills.find(skill => skill.id === annotation.skill_definition_id)?.name || 'Skill'}</strong><small>{annotation.participants.length ? annotation.participants.map(item => item.player_id ? `${item.first_name} ${item.last_name}` : 'Unknown').join(', ') : 'No player'}</small></span>
          <span>{annotation.tags.map(tag => tag.name).join(', ') || '—'}</span><span>{annotation.review_status.replaceAll('_', ' ')}</span>
          <span><span className="va-row-action" role="button" tabIndex={0} onClick={event => { event.stopPropagation(); onDuplicate(annotation, current) }}>Duplicate here</span></span>
        </button>)}
        {!annotations.length && <p className="va-helper">No annotations saved in this session.</p>}
      </div>
    </div>
  </section>
})
