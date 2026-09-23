import type { Player } from '../../types/player'
import { PlayerAvatar, PlayerStatusBadge } from './PlayerBasics'

export default function PlayerHeader({ player }: { player: Player }) {
  const details = [
    ['Team', player.team],
    ['Primary Position', player.positionName],
    ['Secondary Position', player.secondaryPosition],
    ['Age', String(player.age)],
    ['Preferred Foot', player.preferredFoot],
  ]

  return (
    <section className="card player-header">
      <div className="player-header__identity"><div className="player-header__avatar-wrap"><PlayerAvatar player={player} large /><span>#{player.number}</span></div><PlayerStatusBadge status={player.status} /></div>
      <dl className="player-header__details">{details.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    </section>
  )
}
