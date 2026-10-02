import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import PageHeader from '../components/layout/PageHeader'
import PerformanceChart from '../components/players/PerformanceChart'
import PlayerHeader from '../components/players/PlayerHeader'
import PlayerStatsGrid from '../components/players/PlayerStatsGrid'
import RecentMatchesTable from '../components/players/RecentMatchesTable'
import VideoClipsCard from '../components/players/VideoClipsCard'
import WinLossComparison from '../components/players/WinLossComparison'
import { analyticsApi } from '../services/analyticsApi'
import { playersApi } from '../services/playersApi'
import type { MetricDefinition, MetricSources, PlayerHistory, PlayerSummary, ResultComparison } from '../types/reporting'

const comparisonKeys = ['pass_completion_pct','progressive_passes','tackles','interceptions','turnovers']
export default function PlayerProfilePage() {
  const { id = '' } = useParams()
  const [summary, setSummary] = useState<PlayerSummary | null>(null), [history, setHistory] = useState<PlayerHistory | null>(null)
  const [comparison, setComparison] = useState<ResultComparison | null>(null), [definitions, setDefinitions] = useState<MetricDefinition[]>([])
  const [selected, setSelected] = useState('progressive_passes'), [clips, setClips] = useState<MetricSources | null>(null), [trace, setTrace] = useState<MetricSources | null>(null)
  const [loading, setLoading] = useState(true), [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController(); setLoading(true)
    Promise.all([playersApi.summary(id, {}, controller.signal), analyticsApi.definitions(controller.signal), playersApi.sources(id, 'progressive_passes', controller.signal)])
      .then(([s,d,c]) => { setSummary(s); setDefinitions(d); setClips(c) })
      .catch(error => { if (error.name !== 'AbortError') setError(error.message) }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [id])
  useEffect(() => {
    if (!id) return
    const controller = new AbortController()
    const metrics = [...new Set([selected, 'goals', 'assists', ...comparisonKeys])]
    Promise.all([playersApi.history(id, { metrics }, controller.signal), playersApi.byResult(id, { metrics: [...new Set([...comparisonKeys, selected])] }, controller.signal)])
      .then(([h,c]) => { setHistory(h); setComparison(c) }).catch(error => { if (error.name !== 'AbortError') setError(error.message) })
    return () => controller.abort()
  }, [id, selected])
  const summaryDefinitions = useMemo(() => definitions.filter(item => summary?.metrics.some(value => value.key === item.key)), [definitions, summary])
  const historyDefinitions = history?.metric_definitions || []
  const traceMetric = async (key: string) => {
    try { setTrace(await playersApi.sources(id, key)) } catch (error) { setError((error as Error).message) }
  }
  if (loading) return <div className="data-state" role="status">Loading player profile…</div>
  if (error && !summary) return <div className="data-state data-state--error" role="alert">{error} <Link to="/players">Back to Players</Link></div>
  if (!summary) return null
  const player = summary.player
  return <div className="player-profile-page">
    <PageHeader title={`${player.first_name} ${player.last_name}`} eyebrow={<nav className="breadcrumb" aria-label="Breadcrumb"><Link to="/players">Players</Link><span>/</span><strong>{player.first_name} {player.last_name}</strong></nav>} />
    {error && <p className="coverage-banner coverage-banner--error" role="alert">{error}</p>}
    {!summary.coverage.complete && <p className="coverage-banner">Statistics include incomplete annotation coverage ({summary.coverage.status.replaceAll('_',' ').toLowerCase()}). They may change after review.</p>}
    <PlayerHeader player={player} />
    <PlayerStatsGrid values={summary.metrics} definitions={summaryDefinitions} onTrace={traceMetric} />
    {history && comparison && <div className="profile-analytics-grid"><PerformanceChart matches={history.matches} metrics={definitions.filter(item => item.traceable)} selected={selected} onSelect={setSelected}/><WinLossComparison comparison={comparison}/></div>}
    {history && <RecentMatchesTable matches={history.matches} metrics={history.metric_definitions.filter(item => ['goals','assists'].includes(item.key))}/>}
    <div className="profile-detail-grid">
      <section className="card role-card"><div className="section-heading"><div><span>Recorded profile</span><h2>Position / Role</h2></div></div><dl><div><dt>Primary position</dt><dd>{player.primary_position || 'Not recorded'}</dd></div><div><dt>Secondary position</dt><dd>{player.secondary_position || 'Not recorded'}</dd></div><div><dt>Preferred foot</dt><dd>{player.preferred_foot || 'Not recorded'}</dd></div></dl></section>
      <VideoClipsCard clips={clips?.sources || []}/>
      <section className="card notes-card"><div className="section-heading"><div><span>Data quality</span><h2>Annotation Coverage</h2></div></div><div className="coverage-summary"><strong>{summary.coverage.status.replaceAll('_',' ')}</strong><span>{summary.coverage.reviewed_sessions} of {summary.coverage.session_count} sessions reviewed</span><p>Only saved annotations contribute. Missing participation minutes and unreviewed footage are never represented as measured zeroes.</p></div></section>
    </div>
    {trace && <section className="card trace-panel" aria-live="polite"><div className="section-heading"><div><span>Source annotations</span><h2>{trace.metric.label}: {trace.sources.length} contributing annotations</h2></div><button type="button" className="filter-button" onClick={() => setTrace(null)}>Close</button></div>{!trace.sources.length ? <div className="data-state">No contributing annotations.</div> : <div className="table-scroll"><table className="data-table"><thead><tr><th>Match</th><th>Time</th><th>Skill / Tags</th><th>Outcome</th><th>Video</th></tr></thead><tbody>{trace.sources.map(source => <tr key={source.annotation_id}><td>{source.match_date} · {source.opponent}</td><td>{Math.floor(source.match_time/60)}:{String(Math.floor(source.match_time%60)).padStart(2,'0')}</td><td>{source.skill}{source.tags.length ? ` · ${source.tags.join(', ')}` : ''}</td><td>{source.outcomes.join(', ') || '—'}</td><td><Link to={`/video-analysis?video=${source.video_id}&annotation=${source.annotation_id}`}>Open at timestamp</Link></td></tr>)}</tbody></table></div>}</section>}
  </div>
}
