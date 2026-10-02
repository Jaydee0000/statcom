import type { MetricDefinition, ResultComparison } from '../../types/reporting'
import { formatMetric, metricValue } from '../../types/reporting'

export default function WinLossComparison({ comparison }: { comparison: ResultComparison }) {
  return <section className="card comparison-card">
    <div className="section-heading"><div><span>Observed match outcome split</span><h2>Wins / Draws / Losses</h2></div></div>
    <p className="comparison-note">Per-match observed values; percentages are recomputed from their underlying totals and do not imply causation.</p>
    <div className="comparison-list">{comparison.metric_definitions.filter(item => !['appearances','minutes_played'].includes(item.key)).map(definition => {
      const values = comparison.groups.map(group => metricValue(group.metrics, definition.key))
      const max = Math.max(...values.map(value => value ?? 0), 1)
      return <div className="comparison-row" key={definition.key}><div className="comparison-row__label"><strong>{definition.label}</strong><span>{comparison.groups.map((group, index) => <b key={group.result} title={`${group.match_count} matches, ${group.complete_match_count} reviewed`}>{group.result}: {formatMetric(definition, values[index])}</b>)}</span></div><div className="comparison-bars comparison-bars--three">{values.map((value, index) => <i key={comparison.groups[index].result} style={{width: `${((value ?? 0)/max)*100}%`}} />)}</div></div>
    })}</div>
  </section>
}
