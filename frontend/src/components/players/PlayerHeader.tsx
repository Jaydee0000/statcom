import type { PlayerIdentity } from '../../types/reporting'
import { PlayerAvatar, PlayerStatusBadge } from './PlayerBasics'

const display = (value: string | number | null) => value === null || value === '' ? 'Not recorded' : String(value)

export default function PlayerHeader({ player }: { player: PlayerIdentity }) {
  const age = player.date_of_birth ? Math.floor((Date.now() - new Date(player.date_of_birth).getTime()) / 31557600000) : null
  const details = [
    ['Team', display(player.team_name)], ['Primary Position', display(player.primary_position)],
    ['Secondary Position', display(player.secondary_position)], ['Age', display(age)],
    ['Preferred Foot', display(player.preferred_foot)],
  ]
  return <section className="card player-header">
    <div className="player-header__identity"><div className="player-header__avatar-wrap"><PlayerAvatar player={player} large />{player.jersey_number !== null && <span>#{player.jersey_number}</span>}</div><PlayerStatusBadge status={player.availability} /></div>
    <dl className="player-header__details">{details.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
  </section>
}
