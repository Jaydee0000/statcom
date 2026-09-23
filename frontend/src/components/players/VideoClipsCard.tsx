import type { VideoClip } from '../../types/player'

export default function VideoClipsCard({ clips }: { clips: VideoClip[] }) {
  return <section className="card clips-card"><div className="section-heading"><div><span>Tagged moments</span><h2>Video Clips</h2></div></div><div className="clip-list">{clips.map((clip) => <div className="clip-item" key={clip.title}><div className={`clip-thumbnail clip-thumbnail--${clip.tone}`}><span className="play-icon">▶</span><small>{clip.length}</small></div><div><strong>{clip.title}</strong><span>{clip.opponent} · {clip.date}</span></div></div>)}</div></section>
}
