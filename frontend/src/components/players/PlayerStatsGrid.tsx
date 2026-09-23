import type { PlayerStats } from '../../types/player'

export default function PlayerStatsGrid({ stats }: { stats: PlayerStats }) {
  const items = [
    ['Minutes Played', stats.minutesPlayed.toLocaleString()], ['Goals', stats.goals], ['Assists', stats.assists],
    ['Progressive Passes', stats.progressivePasses], ['Tackles', stats.tackles], ['Interceptions', stats.interceptions],
    ['Turnovers', stats.turnovers], ['Average Rating', stats.averageRating.toFixed(1)],
  ]
  return <section className="stats-grid" aria-label="Current season statistics">{items.map(([label, value]) => <div className="stat-block" key={label}><span>{label}</span><strong>{value}</strong></div>)}</section>
}
