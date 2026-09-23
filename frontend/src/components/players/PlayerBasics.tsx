import type { MatchResult, Player, PlayerStatus } from '../../types/player'

export function PlayerAvatar({ player, large = false }: { player: Player; large?: boolean }) {
  return <div className={`player-avatar${large ? ' player-avatar--large' : ''}`}>{player.initials}</div>
}

export function PlayerStatusBadge({ status }: { status: PlayerStatus }) {
  return <span className={`status-badge status-badge--${status.toLowerCase()}`}><i />{status}</span>
}

export function RecentForm({ form }: { form: MatchResult[] }) {
  return <div className="recent-form" aria-label={`Recent form: ${form.join(', ')}`}>{form.map((result, index) => <span key={`${result}-${index}`} className={`form-result form-result--${result.toLowerCase()}`}>{result}</span>)}</div>
}

export function ResultBadge({ result }: { result: MatchResult }) {
  return <span className={`match-result match-result--${result.toLowerCase()}`}>{result}</span>
}
