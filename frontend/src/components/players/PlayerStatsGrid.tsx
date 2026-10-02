import type { MetricDefinition, MetricValue } from '../../types/reporting'
import { formatMetric, metricValue } from '../../types/reporting'

export default function PlayerStatsGrid({ values, definitions, onTrace }: { values: MetricValue[]; definitions: MetricDefinition[]; onTrace: (key: string) => void }) {
  return <section className="stats-grid" aria-label="Current season statistics">{definitions.map(definition => {
    const value = metricValue(values, definition.key)
    return <div className="stat-block" key={definition.key}><span>{definition.label}</span>{definition.traceable && value !== null
      ? <button type="button" className="trace-stat" onClick={() => onTrace(definition.key)}>{formatMetric(definition, value)}</button>
      : <strong>{formatMetric(definition, value)}</strong>}</div>
  })}</section>
}
