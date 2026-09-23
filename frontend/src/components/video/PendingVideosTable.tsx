import type { Video } from '../../types/video'

type Props = { videos: Video[]; onStart: (video: Video) => void }
export default function PendingVideosTable({ videos, onStart }: Props) {
  return <section className="card va-dashboard-card" aria-labelledby="pending-title">
    <div className="va-card-heading"><h2 id="pending-title">Videos Awaiting Annotation</h2><span className="va-count">{videos.length}</span></div>
    <div className="table-scroll"><table className="data-table va-table"><thead><tr><th scope="col">File / Match</th><th scope="col">Date Added</th><th scope="col">Status</th><th scope="col">Progress</th><th scope="col">Action</th></tr></thead>
      <tbody>{videos.map((video, index) => <tr key={video.id}>
        <td><strong>{video.matchName}</strong><small>{video.fileName}</small></td><td>{video.dateAdded}</td>
        <td><span className={`va-badge${video.status === 'Not Started' ? ' va-badge--pending' : ''}`}>{video.status}</span></td>
        <td>{video.status === 'In Progress' ? <div className="va-progress"><progress max="100" value={video.progress ?? 0} aria-label={`${video.matchName} progress`} /><span>{video.progress}%</span></div> : '—'}</td>
        <td><button id={index === 0 ? 'first-pending-video' : undefined} className="va-row-action" type="button" onClick={() => onStart(video)} aria-label={`${video.status === 'In Progress' ? 'Resume' : 'Start'} ${video.matchName}`}>{video.status === 'In Progress' ? 'Resume' : 'Start'}</button></td>
      </tr>)}</tbody></table></div>
  </section>
}
