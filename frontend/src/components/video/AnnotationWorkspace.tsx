import { useEffect, useRef } from 'react'
import Icon from '../ui/Icon'
import type { AnnotationSession } from '../../types/annotationSession'
import type { Video } from '../../types/video'

type Props = { session: AnnotationSession; video: Video; onClose: () => void }
export default function AnnotationWorkspace({ session, video, onClose }: Props) {
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => { heading.current?.focus() }, [session.id])
  return <section className="card va-workspace" aria-labelledby="workspace-title">
    <div className="va-card-heading"><div><span className="va-eyebrow">Annotation Workspace</span><h2 ref={heading} tabIndex={-1} id="workspace-title">{session.matchName}</h2></div><button type="button" className="va-row-action" onClick={onClose}>Close Session</button></div>
    <div className="va-player">
      <span className="va-badge va-player__badge">Annotation Mode</span>
      <div className="va-player__placeholder"><Icon name="video" /><strong>Match footage preview</strong><span>{video.fileName}</span><small>Visual placeholder · No video loaded</small></div>
      <div className="va-player__controls" aria-label="Mock video controls"><button type="button" aria-label="Play preview (visual only)">▶</button><span>00:00 / {video.duration}</span><div className="va-playback-track" /><span>1×</span><button type="button" aria-label="Fullscreen preview (visual only)">⛶</button></div>
    </div>
    <div className="va-timeline"><div className="va-timeline__heading"><strong>Annotation Timeline</strong><span>Sample markers</span></div>
      <div className="va-timeline__track" aria-label="Illustrative annotation timeline"><i style={{ left: '12%' }} /><i style={{ left: '29%' }} /><i style={{ left: '46%' }} /><i style={{ left: '68%' }} /><i style={{ left: '86%' }} /></div>
      <div className="va-timeline__labels"><span>00:00</span><span>30:00</span><span>60:00</span><span>{video.duration}</span></div>
      <p className="va-helper">Markers illustrate where annotations could appear.</p>
    </div>
  </section>
}
