import type { Video } from '../../types/video'

type Props = { videos: Video[]; onReview: (video: Video) => void; loading?: boolean; busy?: boolean }
export default function CompletedVideosTable({ videos, onReview, loading, busy }: Props) {
  return <section className="card va-dashboard-card" aria-labelledby="completed-title">
    <div className="va-card-heading"><h2 id="completed-title">Completed Videos</h2><span className="va-count">{videos.length}</span></div>
    <p className="va-helper" role="status">{loading ? 'Loading videos…' : videos.length === 0 ? 'No videos yet.' : ''}</p>
    <div className="table-scroll"><table className="data-table va-table"><thead><tr><th scope="col">File / Match</th><th scope="col">Date</th><th scope="col">Status</th><th scope="col">Action</th></tr></thead>
      <tbody>{videos.map(video => <tr key={video.id}><td><strong>{video.fileName}</strong><small>{video.matchName}</small></td><td>{video.dateAdded}</td>
        <td><span className="va-badge">{video.status}</span></td><td><button type="button" className="va-row-action" disabled={busy} onClick={() => onReview(video)} aria-label={`Review ${video.matchName}`}>Review</button></td>
      </tr>)}</tbody></table></div>
  </section>
}
