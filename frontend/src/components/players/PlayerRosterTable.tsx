import { Link, useNavigate } from 'react-router-dom'
import type { MetricDefinition, RosterPlayer } from '../../types/reporting'
import { formatMetric, metricValue } from '../../types/reporting'
import { PlayerAvatar, PlayerStatusBadge, RecentForm } from './PlayerBasics'

export default function PlayerRosterTable({ players, metrics }: { players: RosterPlayer[]; metrics: MetricDefinition[] }) {
  const navigate = useNavigate()
  if (!players.length) return <div className="data-state">No players found for these filters.</div>
  return <div className="table-scroll"><table className="data-table roster-table">
    <thead><tr><th>Player</th><th>Position</th><th>Status</th><th>Recent Form</th><th>Matches</th><th>Minutes</th>{metrics.map(metric => <th key={metric.key}>{metric.label}</th>)}<th>Coverage</th><th aria-label="Actions" /></tr></thead>
    <tbody>{players.map(player => <tr key={player.id} onClick={() => navigate(`/players/${player.id}`)}>
      <td><div className="player-cell"><PlayerAvatar player={player} /><div><Link to={`/players/${player.id}`} onClick={event => event.stopPropagation()}>{player.first_name} {player.last_name}</Link><span>{player.jersey_number === null ? 'No number recorded' : `#${player.jersey_number}`}</span></div></div></td>
      <td>{player.primary_position ? <span className="position-chip">{player.primary_position}</span> : '—'}</td>
      <td><PlayerStatusBadge status={player.availability} /></td><td><RecentForm form={player.recent_form} /></td>
      <td>{player.appearances}</td><td>{player.minutes === null ? '—' : player.minutes.toLocaleString()}</td>
      {metrics.map(metric => <td key={metric.key}>{formatMetric(metric, metricValue(player.metrics, metric.key))}</td>)}
      <td>{player.incomplete_matches ? <span className="coverage-warning">{player.incomplete_matches} incomplete</span> : player.appearances ? 'Reviewed' : '—'}</td>
      <td><button type="button" className="more-button" aria-label={`View ${player.first_name} ${player.last_name}`} onClick={event => { event.stopPropagation(); navigate(`/players/${player.id}`) }}>•••</button></td>
    </tr>)}</tbody>
  </table></div>
}
