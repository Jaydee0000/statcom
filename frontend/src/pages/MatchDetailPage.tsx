import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import PageHeader from '../components/layout/PageHeader'
import { matchesApi } from '../services/matchesApi'
import type { MatchStats } from '../types/reporting'
import { coverageLabel, formatMetric, metricValue } from '../types/reporting'

export default function MatchDetailPage() {
  const { id = '' } = useParams()
  const [data, setData] = useState<MatchStats | null>(null), [loading, setLoading] = useState(true), [error, setError] = useState('')
  useEffect(() => { const controller = new AbortController(); matchesApi.stats(id, [], controller.signal).then(setData).catch(error => { if (error.name !== 'AbortError') setError(error.message) }).finally(() => { if (!controller.signal.aborted) setLoading(false) }); return () => controller.abort() }, [id])
  if (loading) return <div className="data-state">Loading match…</div>
  if (error || !data) return <div className="data-state data-state--error">{error || 'Match not found.'} <Link to="/matches">Back to Matches</Link></div>
  const match = data.match
  return <div><PageHeader title={`${match.home_team} vs ${match.away_team}`} eyebrow={<nav className="breadcrumb"><Link to="/matches">Matches</Link><span>/</span><strong>{match.match_date}</strong></nav>} actions={<Link className="va-button va-button--primary" to={`/video-analysis?match=${match.id}`}>Open Video Analysis</Link>} />
    {!match.coverage.complete && <p className="coverage-banner">This match is {coverageLabel(match.coverage.status).toLowerCase()}. Statistics may be incomplete.</p>}
    <section className="card match-hero"><div><span>{new Date(match.match_date+'T00:00:00').toLocaleDateString()}</span><h2>{match.home_team} <strong>{match.home_score ?? '—'} – {match.away_score ?? '—'}</strong> {match.away_team}</h2></div><dl><div><dt>Location</dt><dd>{match.location || 'Not recorded'}</dd></div><div><dt>Competition</dt><dd>{match.competition || 'Not recorded'}</dd></div><div><dt>Season</dt><dd>{match.season || 'Not recorded'}</dd></div><div><dt>Annotation</dt><dd>{coverageLabel(match.coverage.status)}</dd></div></dl></section>
    <section className="card table-card"><div className="section-heading"><div><span>Match participation and annotation-derived values</span><h2>Lineup & Player Statistics</h2></div></div>{!data.participants.length ? <div className="data-state">No lineup has been recorded for this match.</div> : <div className="table-scroll"><table className="data-table"><thead><tr><th>Player</th><th>Team</th><th>Role</th><th>Position</th><th>Minutes</th>{data.metric_definitions.map(metric => <th key={metric.key}>{metric.label}</th>)}</tr></thead><tbody>{data.participants.map(row => <tr key={row.player.id}><td><Link to={`/players/${row.player.id}`}>{row.player.first_name} {row.player.last_name}</Link></td><td>{row.team_id === match.home_team_id ? match.home_team : match.away_team}</td><td>{row.starter ? 'Starter' : 'Substitute'}</td><td>{row.position || row.player.primary_position || '—'}</td><td>{row.minutes ?? '—'}</td>{data.metric_definitions.map(metric => <td key={metric.key}>{formatMetric(metric, metricValue(row.metrics, metric.key))}</td>)}</tr>)}</tbody></table></div>}</section>
    <section className="card table-card"><div className="section-heading"><div><span>Stored media</span><h2>Videos</h2></div></div>{!data.videos.length ? <div className="data-state">No videos have been attached.</div> : <div className="clip-list">{data.videos.map(video => <Link className="video-row" key={video.id} to={`/video-analysis?video=${video.id}`}><strong>{video.original_filename}</strong><span>{video.period || 'Period not recorded'} · {coverageLabel(video.annotation_status)}</span></Link>)}</div>}</section>
  </div>
}
