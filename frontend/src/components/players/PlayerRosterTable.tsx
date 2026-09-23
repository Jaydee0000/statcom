import { Link, useNavigate } from 'react-router-dom'
import type { Player } from '../../types/player'
import { PlayerAvatar, PlayerStatusBadge, RecentForm } from './PlayerBasics'

export default function PlayerRosterTable({ players }: { players: Player[] }) {
  const navigate = useNavigate()

  return (
    <div className="table-scroll">
      <table className="data-table roster-table">
        <thead><tr><th>Player</th><th>Position</th><th>Age</th><th>Status</th><th>Recent Form</th><th>Matches</th><th>Minutes</th><th>Goals</th><th>Assists</th><th>Rating</th><th aria-label="Actions" /></tr></thead>
        <tbody>
          {players.map((player) => (
            <tr key={player.id} onClick={() => navigate(`/players/${player.id}`)}>
              <td><div className="player-cell"><PlayerAvatar player={player} /><div><Link to={`/players/${player.id}`} onClick={(event) => event.stopPropagation()}>{player.name}</Link><span>#{player.number}</span></div></div></td>
              <td><span className="position-chip">{player.position}</span></td>
              <td>{player.age}</td>
              <td><PlayerStatusBadge status={player.status} /></td>
              <td><RecentForm form={player.recentForm} /></td>
              <td>{player.matchesPlayed}</td>
              <td>{player.minutes.toLocaleString()}</td>
              <td>{player.goals}</td>
              <td>{player.assists}</td>
              <td><strong className="rating-value">{player.rating.toFixed(1)}</strong></td>
              <td><button type="button" className="more-button" aria-label={`View ${player.name}`} onClick={(event) => { event.stopPropagation(); navigate(`/players/${player.id}`) }}>•••</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
