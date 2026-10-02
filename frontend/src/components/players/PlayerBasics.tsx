import type { PlayerIdentity, Result } from '../../types/reporting'

export function PlayerAvatar({ player, large = false }: { player: PlayerIdentity; large?: boolean }) {
  const initials = `${player.first_name[0] || ''}${player.last_name[0] || ''}`
  return player.photo_url
    ? <img className={`player-avatar${large ? ' player-avatar--large' : ''}`} src={player.photo_url} alt="" />
    : <div className={`player-avatar${large ? ' player-avatar--large' : ''}`}>{initials}</div>
}

export function PlayerStatusBadge({ status }: { status: string | null }) {
  if (!status) return <span className="not-recorded">Not recorded</span>
  return <span className={`status-badge status-badge--${status.toLowerCase()}`}><i />{status}</span>
}

export function RecentForm({ form }: { form: Result[] }) {
  if (!form.length) return <span className="not-recorded">—</span>
  return <div className="recent-form" aria-label={`Recent form: ${form.join(', ')}`}>{form.map((result, index) => <span key={`${result}-${index}`} className={`form-result form-result--${result.toLowerCase()}`}>{result}</span>)}</div>
}

export function ResultBadge({ result }: { result: Result }) {
  return <span className={`match-result match-result--${result.toLowerCase()}`}>{result}</span>
}
