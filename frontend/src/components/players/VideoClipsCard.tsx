import { Link } from 'react-router-dom'
import type { SourceAnnotation } from '../../types/reporting'

const time = (seconds: number) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`
export default function VideoClipsCard({ clips }: { clips: SourceAnnotation[] }) {
  return <section className="card clips-card"><div className="section-heading"><div><span>Annotation references</span><h2>Video Clips</h2></div></div>{!clips.length ? <div className="data-state">No traceable clips are available yet.</div> : <div className="clip-list">{clips.slice(0, 6).map(clip => <Link className="clip-item" key={clip.annotation_id} to={`/video-analysis?video=${clip.video_id}&annotation=${clip.annotation_id}`}><div className="clip-thumbnail clip-thumbnail--green"><span className="play-icon">▶</span><small>{time(clip.match_time)}</small></div><div><strong>{clip.skill}</strong><span>vs {clip.opponent || 'Unknown opponent'} · {new Date(clip.match_date+'T00:00:00').toLocaleDateString()}</span></div></Link>)}</div>}</section>
}
