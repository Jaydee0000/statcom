import type { RecentMatch } from '../../types/player'
import { ResultBadge } from './PlayerBasics'

export default function RecentMatchesTable({ matches }: { matches: RecentMatch[] }) {
  return <section className="card matches-card"><div className="section-heading"><div><span>Latest appearances</span><h2>Recent Matches</h2></div></div><div className="table-scroll"><table className="data-table recent-matches"><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th>Minutes</th><th>Rating</th><th>Goals</th><th>Assists</th></tr></thead><tbody>{matches.map((match) => <tr key={`${match.date}-${match.opponent}`}><td>{match.date}</td><td><strong>{match.opponent}</strong></td><td><ResultBadge result={match.result}/></td><td>{match.minutes}</td><td><strong className="rating-value">{match.rating.toFixed(1)}</strong></td><td>{match.goals}</td><td>{match.assists}</td></tr>)}</tbody></table></div></section>
}
