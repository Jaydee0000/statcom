import { useEffect, useMemo, useState } from 'react'
import PageHeader from '../components/layout/PageHeader'
import { annotationsApi } from '../services/annotationsApi'
import { matchesApi, type MatchRecord, type TeamRecord } from '../services/matchesApi'
import { metricsApi } from '../services/metricsApi'
import type { SkillRecord, TagRecord } from '../types/annotation'
import type { MatchMetrics, MetricValues, MetricsFilters } from '../types/metrics'
import '../styles/match-analytics.css'

const time = (seconds: number) => `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${Math.floor(seconds % 60).toString().padStart(2, '0')}`
const pct = (value: number | null) => value === null ? '—' : `${value.toFixed(1)}%`
const zeroMetrics: MetricValues = { total_actions: 0, passes: 0, completed_passes: 0, incomplete_passes: 0,
  pass_completion_pct: null, progressive_passes: 0, shots: 0, shots_on_target: 0, goals: 0,
  assists: 0, tackles: 0, interceptions: 0, turnovers: 0 }

export default function AnalyticsPage() {
  const [matches, setMatches] = useState<MatchRecord[]>([])
  const [teams, setTeams] = useState<TeamRecord[]>([])
  const [skills, setSkills] = useState<SkillRecord[]>([])
  const [tags, setTags] = useState<TagRecord[]>([])
  const [selectedMatch, setSelectedMatch] = useState('')
  const [filters, setFilters] = useState<Record<string, string>>({ player_id: '', skill_id: '', tag_id: '', outcome: '', start_time: '', end_time: '', period: '', bucket_seconds: '300' })
  const [data, setData] = useState<MatchMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([matchesApi.list(), matchesApi.teams(), annotationsApi.skills(), annotationsApi.tags()])
      .then(([loadedMatches, loadedTeams, loadedSkills, loadedTags]) => {
        setMatches(loadedMatches); setTeams(loadedTeams); setSkills(loadedSkills); setTags(loadedTags)
        setSelectedMatch(current => current || loadedMatches[0]?.id || '')
      }).catch(e => setError(`Could not load analytics filters: ${(e as Error).message}`))
  }, [])

  useEffect(() => {
    if (!selectedMatch) { setLoading(false); setData(null); return }
    let cancelled = false
    const request: MetricsFilters = { bucket_seconds: Number(filters.bucket_seconds) }
    for (const key of ['player_id', 'skill_id', 'tag_id', 'outcome', 'period'] as const) if (filters[key]) request[key] = filters[key]
    if (filters.start_time !== '') request.start_time = Number(filters.start_time)
    if (filters.end_time !== '') request.end_time = Number(filters.end_time)
    setLoading(true); setError('')
    metricsApi.match(selectedMatch, request).then(result => { if (!cancelled) setData(result) })
      .catch(e => { if (!cancelled) { setData(null); setError(`Could not load match analytics: ${(e as Error).message}`) } })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [selectedMatch, filters])

  const teamName = (id: string) => teams.find(team => team.id === id)?.name || 'Team'
  const matchLabel = (match: MatchRecord) => `${teamName(match.home_team_id)} vs ${teamName(match.away_team_id)} · ${match.match_date}`
  const update = (key: string, value: string) => setFilters(current => ({ ...current, [key]: value }))
  const clearFilters = () => setFilters({ player_id: '', skill_id: '', tag_id: '', outcome: '', start_time: '', end_time: '', period: '', bucket_seconds: '300' })
  const metrics = data?.metrics || zeroMetrics
  const maxBucket = Math.max(1, ...(data?.breakdowns.timeline_buckets.map(bucket => bucket.count) || []))
  const periods = useMemo(() => [...new Set(data?.breakdowns.events.map(event => event.period).filter((value): value is string => Boolean(value)) || [])].sort(), [data])
  const activeFilterCount = Object.entries(filters).filter(([key, value]) => key !== 'bucket_seconds' && value).length

  return <div className="ma-page">
    <PageHeader title="Match Analytics" subtitle="Annotation-derived team and player match metrics" actions={
      <select className="ma-match-select" aria-label="Match" value={selectedMatch} onChange={event => setSelectedMatch(event.target.value)}>
        {!matches.length && <option value="">No matches available</option>}
        {matches.map(match => <option key={match.id} value={match.id}>{matchLabel(match)}</option>)}
      </select>} />

    <section className="card ma-filters" aria-labelledby="analytics-filters-title">
      <div className="ma-section-heading"><div><span>FILTERS</span><h2 id="analytics-filters-title">Match context</h2></div>{activeFilterCount > 0 && <button type="button" onClick={clearFilters}>Clear {activeFilterCount}</button>}</div>
      <div className="ma-filter-grid">
        <label>Player<select value={filters.player_id} onChange={event => update('player_id', event.target.value)}><option value="">All players</option>{data?.players.map(player => <option key={player.player_id} value={player.player_id}>{player.first_name} {player.last_name}</option>)}</select></label>
        <label>Skill<select value={filters.skill_id} onChange={event => update('skill_id', event.target.value)}><option value="">All skills</option>{skills.map(skill => <option key={skill.id} value={skill.id}>{skill.name}</option>)}</select></label>
        <label>Tag<select value={filters.tag_id} onChange={event => update('tag_id', event.target.value)}><option value="">All tags</option>{tags.map(tag => <option key={tag.id} value={tag.id}>{tag.name}</option>)}</select></label>
        <label>Outcome<input value={filters.outcome} placeholder="Exact structured outcome" onChange={event => update('outcome', event.target.value)} /></label>
        <label>From match second<input type="number" min="0" value={filters.start_time} placeholder="0" onChange={event => update('start_time', event.target.value)} /></label>
        <label>To match second<input type="number" min="0" value={filters.end_time} placeholder="5400" onChange={event => update('end_time', event.target.value)} /></label>
        <label>Period<select value={filters.period} onChange={event => update('period', event.target.value)}><option value="">All periods</option>{periods.map(period => <option key={period}>{period}</option>)}</select></label>
        <label>Timeline buckets<select value={filters.bucket_seconds} onChange={event => update('bucket_seconds', event.target.value)}><option value="60">1 minute</option><option value="300">5 minutes</option><option value="600">10 minutes</option><option value="900">15 minutes</option></select></label>
      </div>
    </section>

    {error && <p className="ma-error" role="alert">{error}</p>}
    {loading && <p className="ma-loading" role="status">Loading match analytics…</p>}
    {!loading && !selectedMatch && <section className="card ma-empty">Create a match and annotations to view analytics.</section>}
    {data && <>
      <section className="ma-overview" aria-label="Match overview">
        {[['Actions', metrics.total_actions], ['Passes', metrics.passes], ['Pass completion', pct(metrics.pass_completion_pct)],
          ['Progressive passes', metrics.progressive_passes], ['Shots', metrics.shots], ['On target', metrics.shots_on_target],
          ['Goals', metrics.goals], ['Turnovers', metrics.turnovers], ['Defensive actions', metrics.tackles + metrics.interceptions]].map(([label, value]) =>
          <article className="card ma-stat" key={label}><span>{label}</span><strong>{value}</strong></article>)}
      </section>

      <section className="card ma-team-comparison" aria-labelledby="team-comparison-title">
        <div className="ma-section-heading"><div><span>MATCH OVERVIEW</span><h2 id="team-comparison-title">Team comparison</h2></div><small>{data.unattributed.ambiguous_team_actions} unassigned team action{data.unattributed.ambiguous_team_actions === 1 ? '' : 's'}</small></div>
        <div className="ma-team-grid">{data.teams.map(team => <article key={team.team_id}><div><b>{team.team_name}</b><span>{team.side}</span></div>
          <dl><div><dt>Passes</dt><dd>{team.metrics.passes}</dd></div><div><dt>Pass %</dt><dd>{pct(team.metrics.pass_completion_pct)}</dd></div><div><dt>Progressive</dt><dd>{team.metrics.progressive_passes}</dd></div><div><dt>Shots / OT</dt><dd>{team.metrics.shots} / {team.metrics.shots_on_target}</dd></div><div><dt>Goals</dt><dd>{team.metrics.goals}</dd></div><div><dt>Turnovers</dt><dd>{team.metrics.turnovers}</dd></div><div><dt>Defensive</dt><dd>{team.metrics.tackles + team.metrics.interceptions}</dd></div></dl>
        </article>)}</div>
      </section>

      <section className="card ma-players" aria-labelledby="player-performance-title">
        <div className="ma-section-heading"><div><span>PLAYERS</span><h2 id="player-performance-title">Player performance</h2></div><small>Unknown and no-player events are never attributed</small></div>
        <div className="table-scroll"><table className="data-table"><thead><tr><th>Player</th><th>Passes</th><th>Pass %</th><th>Progressive</th><th>Shots</th><th>Tackles</th><th>Interceptions</th><th>Turnovers</th></tr></thead><tbody>
          {data.players.map(player => <tr key={player.player_id}><td><div className="player-cell"><span className="player-avatar">{player.first_name[0]}{player.last_name[0]}</span><div><strong>{player.first_name} {player.last_name}</strong><span>{teamName(player.team_id)}{player.jersey_number !== null ? ` · #${player.jersey_number}` : ''}</span></div></div></td><td>{player.metrics.passes}</td><td>{pct(player.metrics.pass_completion_pct)}</td><td>{player.metrics.progressive_passes}</td><td>{player.metrics.shots}</td><td>{player.metrics.tackles}</td><td>{player.metrics.interceptions}</td><td>{player.metrics.turnovers}</td></tr>)}
          {!data.players.length && <tr><td colSpan={8}>No match participants available.</td></tr>}
        </tbody></table></div>
      </section>

      <section className="card ma-timeline" aria-labelledby="analytics-timeline-title">
        <div className="ma-section-heading"><div><span>TIMELINE</span><h2 id="analytics-timeline-title">Actions over match time</h2></div><small>Click a bucket to filter that interval</small></div>
        <div className="ma-bars">{data.breakdowns.timeline_buckets.map(bucket => <button type="button" key={bucket.start_time} title={`${bucket.count} actions from ${time(bucket.start_time)}`} onClick={() => setFilters(current => ({ ...current, start_time: String(bucket.start_time), end_time: String(bucket.end_time) }))}><i style={{ height: `${Math.max(8, bucket.count / maxBucket * 100)}%` }} /><strong>{bucket.count}</strong><span>{time(bucket.start_time)}</span></button>)}{!data.breakdowns.timeline_buckets.length && <p>No actions match these filters.</p>}</div>
      </section>

      <section className="ma-breakdowns" aria-label="Analytics breakdowns">
        {([['By skill', data.breakdowns.actions_by_skill], ['By outcome', data.breakdowns.actions_by_outcome], ['By tag', data.breakdowns.actions_by_tag]] as const).map(([title, items]) => <article className="card" key={title}><div className="ma-section-heading"><div><span>BREAKDOWN</span><h2>{title}</h2></div></div><ol>{items.slice(0, 8).map(item => <li key={`${item.id}-${item.label}`}><span>{item.label}</span><b>{item.count}</b></li>)}</ol>{!items.length && <p>No classified data.</p>}</article>)}
      </section>
      <p className="ma-quality">Data quality: {data.unattributed.unknown_participant_actions} unknown-player · {data.unattributed.no_player_actions} no-player · {data.unattributed.ambiguous_team_actions} team-unassigned actions</p>
    </>}
  </div>
}
