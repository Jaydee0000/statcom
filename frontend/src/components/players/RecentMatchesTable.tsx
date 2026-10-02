import { useNavigate } from 'react-router-dom'
import type { HistoryRow, MetricDefinition } from '../../types/reporting'
import { coverageLabel, formatMetric, metricValue } from '../../types/reporting'
import { ResultBadge } from './PlayerBasics'

export default function RecentMatchesTable({ matches, metrics }: { matches: HistoryRow[]; metrics: MetricDefinition[] }) {
  const navigate = useNavigate()
  const shown = matches.slice().reverse().slice(0, 8)
  return <section className="card matches-card"><div className="section-heading"><div><span>Latest appearances</span><h2>Recent Matches</h2></div></div>{!shown.length ? <div className="data-state">No appearances found for the selected season.</div> : <div className="table-scroll"><table className="data-table recent-matches"><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th>Minutes</th>{metrics.map(metric => <th key={metric.key}>{metric.label}</th>)}<th>Coverage</th></tr></thead><tbody>{shown.map(row => <tr key={row.match.id} className="clickable-row" onClick={() => navigate(`/matches/${row.match.id}`)}><td>{new Date(row.match.match_date+'T00:00:00').toLocaleDateString()}</td><td><strong>{row.match.opponent}</strong></td><td>{row.match.result ? <ResultBadge result={row.match.result}/> : '—'}</td><td>{row.minutes ?? '—'}</td>{metrics.map(metric => <td key={metric.key}>{formatMetric(metric, metricValue(row.metrics, metric.key))}</td>)}<td><span className={row.match.coverage.complete ? 'coverage-ok' : 'coverage-warning'}>{coverageLabel(row.match.coverage.status)}</span></td></tr>)}</tbody></table></div>}</section>
}
