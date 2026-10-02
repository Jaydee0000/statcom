import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/layout/PageHeader'
import { matchesApi } from '../services/matchesApi'
import type { MatchReference } from '../types/reporting'
import { coverageLabel } from '../types/reporting'

export default function MatchesPage() {
  const [matches, setMatches] = useState<MatchReference[]>([]), [loading, setLoading] = useState(true), [error, setError] = useState('')
  useEffect(() => { const controller = new AbortController(); matchesApi.overview(controller.signal).then(data => setMatches(data.matches)).catch(error => { if (error.name !== 'AbortError') setError(error.message) }).finally(() => { if (!controller.signal.aborted) setLoading(false) }); return () => controller.abort() }, [])
  return <div><PageHeader title="Matches" subtitle="Match management and review" actions={<Link className="va-button" to="/team-stats">Team Stat Sheet</Link>} />
    <section className="card table-card"><div className="section-heading"><div><span>PostgreSQL match records</span><h2>Matches</h2></div></div>
      {loading ? <div className="data-state">Loading matches…</div> : error ? <div className="data-state data-state--error">{error}</div> : !matches.length ? <div className="data-state">No matches have been recorded.</div> : <div className="table-scroll"><table className="data-table"><thead><tr><th>Date</th><th>Home</th><th>Away</th><th>Score</th><th>Competition</th><th>Season</th><th>Status</th><th>Annotation Status</th><th>Action</th></tr></thead><tbody>{matches.map(match => <tr key={match.id}><td>{new Date(match.match_date+'T00:00:00').toLocaleDateString()}</td><td>{match.home_team}</td><td>{match.away_team}</td><td>{match.home_score === null || match.away_score === null ? '—' : `${match.home_score}–${match.away_score}`}</td><td>{match.competition || '—'}</td><td>{match.season || '—'}</td><td>{match.status}</td><td><span className={match.coverage.complete ? 'coverage-ok' : 'coverage-warning'}>{coverageLabel(match.coverage.status)}</span></td><td><div className="row-actions"><Link to={`/matches/${match.id}`}>View Match</Link><Link to={`/video-analysis?match=${match.id}`}>Open Video Analysis</Link></div></td></tr>)}</tbody></table></div>}
    </section>
  </div>
}
