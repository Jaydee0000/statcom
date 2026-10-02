import { useEffect, useState } from 'react'
import PageHeader from '../components/layout/PageHeader'
import { analyticsApi } from '../services/analyticsApi'
import { matchesApi } from '../services/matchesApi'
import type { MatchReference, MetricDefinition, TeamStatSheet } from '../types/reporting'
import { formatMetric, metricValue } from '../types/reporting'

const defaults = ['minutes_played','passes','completed_passes','pass_completion_pct','progressive_passes','tackles','turnovers']
export default function TeamStatSheetPage() {
  const [teams, setTeams] = useState<{id:string;name:string}[]>([]), [seasons, setSeasons] = useState<{id:string;name:string}[]>([]), [competitions, setCompetitions] = useState<{id:string;name:string}[]>([])
  const [matches, setMatches] = useState<MatchReference[]>([]), [definitions, setDefinitions] = useState<MetricDefinition[]>([])
  const [team, setTeam] = useState(''), [season, setSeason] = useState(''), [competition, setCompetition] = useState(''), [match, setMatch] = useState('')
  const [dateFrom, setDateFrom] = useState(''), [dateTo, setDateTo] = useState(''), [selected, setSelected] = useState<string[]>(defaults)
  const [data, setData] = useState<TeamStatSheet | null>(null), [loading, setLoading] = useState(false), [error, setError] = useState('')
  useEffect(() => { Promise.all([analyticsApi.teams(), analyticsApi.seasons(), analyticsApi.competitions(), analyticsApi.definitions(), matchesApi.overview()]).then(([t,s,c,d,m]) => { setTeams(t); setSeasons(s); setCompetitions(c); setDefinitions(d); setMatches(m.matches); setTeam(t[0]?.id || '') }).catch(error => setError(error.message)) }, [])
  useEffect(() => {
    if (!team || !selected.length) { setData(null); return }
    const controller = new AbortController(); setLoading(true); setError('')
    analyticsApi.teamStats({ team_id: team, season_id: season || undefined, competition_id: competition || undefined, match_id: match || undefined, date_from: dateFrom || undefined, date_to: dateTo || undefined, metrics: selected }, controller.signal)
      .then(setData).catch(error => { if (error.name !== 'AbortError') setError(error.message) }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [team, season, competition, match, dateFrom, dateTo, selected])
  const toggle = (key: string) => setSelected(current => current.includes(key) ? current.filter(item => item !== key) : [...current, key])
  return <div><PageHeader title="Team Stat Sheet" subtitle="Dynamic annotation-derived player matrix" />
    <section className="card stat-controls"><div className="compact-filters"><label>Team<select value={team} onChange={event => setTeam(event.target.value)}><option value="">Select team</option>{teams.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Season<select value={season} onChange={event => setSeason(event.target.value)}><option value="">All</option>{seasons.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Competition<select value={competition} onChange={event => setCompetition(event.target.value)}><option value="">All</option>{competitions.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Match<select value={match} onChange={event => setMatch(event.target.value)}><option value="">All</option>{matches.filter(item => !team || item.home_team_id === team || item.away_team_id === team).map(item => <option key={item.id} value={item.id}>{item.match_date} · {item.home_team} vs {item.away_team}</option>)}</select></label><label>From<input type="date" value={dateFrom} onChange={event => setDateFrom(event.target.value)}/></label><label>To<input type="date" value={dateTo} onChange={event => setDateTo(event.target.value)}/></label></div>
      <details className="metric-picker"><summary>Select Metrics ({selected.length})</summary><div>{definitions.map(definition => <label key={definition.key}><input type="checkbox" checked={selected.includes(definition.key)} onChange={() => toggle(definition.key)}/><span>{definition.label}{definition.custom ? ' · Custom' : ''}</span></label>)}</div></details></section>
    {error && <p className="coverage-banner coverage-banner--error">{error}</p>}
    {data && data.incomplete_matches > 0 && <p className="coverage-banner">{data.incomplete_matches} of {data.match_count} selected matches have incomplete annotation coverage.</p>}
    <section className="card table-card"><div className="section-heading"><div><span>Selected metrics from backend definitions</span><h2>Player Statistics</h2></div></div>
      {loading ? <div className="data-state">Updating stat sheet…</div> : !team ? <div className="data-state">Select a team.</div> : !selected.length ? <div className="data-state">Select at least one metric.</div> : !data?.players.length ? <div className="data-state">No appearances found for these filters.</div> : <div className="table-scroll"><table className="data-table stat-sheet"><thead><tr><th>Player</th><th>Position</th><th>Apps</th>{data.metric_definitions.map(metric => <th key={metric.key}>{metric.label}</th>)}<th>Coverage</th></tr></thead><tbody>{data.players.map(player => <tr key={player.id}><td>{player.first_name} {player.last_name}</td><td>{player.primary_position || '—'}</td><td>{player.appearances}</td>{data.metric_definitions.map(metric => <td key={metric.key}>{formatMetric(metric, metricValue(player.metrics, metric.key))}</td>)}<td>{player.incomplete_matches ? `${player.incomplete_matches} incomplete` : 'Reviewed'}</td></tr>)}<tr className="totals-row"><td>Team Total</td><td>—</td><td>—</td>{data.metric_definitions.map(metric => <td key={metric.key}>{formatMetric(metric, metricValue(data.totals.metrics, metric.key))}</td>)}<td>{data.incomplete_matches ? 'Incomplete' : 'Reviewed'}</td></tr></tbody></table></div>}
    </section>
  </div>
}
