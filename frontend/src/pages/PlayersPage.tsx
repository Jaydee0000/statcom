import { useEffect, useMemo, useState } from 'react'
import PageHeader from '../components/layout/PageHeader'
import PlayerRosterTable from '../components/players/PlayerRosterTable'
import { playersApi } from '../services/playersApi'
import type { RosterResponse } from '../types/reporting'

const positionGroups = ['All', 'Goalkeepers', 'Defenders', 'Midfielders', 'Forwards'] as const
const positionMap: Record<string, string[]> = {
  Goalkeepers: ['GK'], Defenders: ['CB','LB','RB','LWB','RWB'], Midfielders: ['CDM','CM','CAM','DM','AM','MF'], Forwards: ['LW','RW','ST','CF','FW'],
}

export default function PlayersPage() {
  const [data, setData] = useState<RosterResponse | null>(null)
  const [teams, setTeams] = useState<{id:string;name:string}[]>([])
  const [seasons, setSeasons] = useState<{id:string;name:string}[]>([])
  const [team, setTeam] = useState(''), [season, setSeason] = useState(''), [position, setPosition] = useState<(typeof positionGroups)[number]>('All')
  const [loading, setLoading] = useState(true), [error, setError] = useState('')
  useEffect(() => { Promise.all([playersApi.teams(), playersApi.seasons()]).then(([t,s]) => { setTeams(t); setSeasons(s) }).catch(() => {}) }, [])
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError('')
    playersApi.roster({ team_id: team || undefined, season_id: season || undefined, metrics: ['goals','assists'] }, controller.signal)
      .then(loaded => { setData(loaded); setError('') }).catch(error => { if (error.name !== 'AbortError') setError(error.message) }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [team, season])
  const players = useMemo(() => (data?.players || []).filter(player => position === 'All' || positionMap[position].includes((player.primary_position || '').toUpperCase())), [data, position])
  return <div className="players-page"><PageHeader title="Players" subtitle="Squad roster" />
    <section className="card roster-card"><div className="roster-card__header"><div><span>PostgreSQL roster</span><h2>Squad Roster</h2><p>{players.length} players shown · statistics derived from saved annotations</p></div></div>
      <div className="roster-toolbar"><div className="filter-group" aria-label="Filter by position">{positionGroups.map(filter => <button key={filter} type="button" className={position === filter ? 'filter-button filter-button--active' : 'filter-button'} onClick={() => setPosition(filter)}>{filter}</button>)}</div>
        <div className="compact-filters"><label>Team<select value={team} onChange={event => setTeam(event.target.value)}><option value="">All teams</option>{teams.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label>Season<select value={season} onChange={event => setSeason(event.target.value)}><option value="">All seasons</option>{seasons.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label></div></div>
      {loading ? <div className="data-state" role="status">Loading players…</div> : error && !data ? <div className="data-state data-state--error" role="alert">{error}</div> : data && <PlayerRosterTable players={players} metrics={data.metric_definitions} />}
    </section>
  </div>
}
