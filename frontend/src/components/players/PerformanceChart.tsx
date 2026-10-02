import type { HistoryRow, MetricDefinition } from '../../types/reporting'
import { formatMetric, metricValue } from '../../types/reporting'

export default function PerformanceChart({ matches, metrics, selected, onSelect }: { matches: HistoryRow[]; metrics: MetricDefinition[]; selected: string; onSelect: (key: string) => void }) {
  const definition = metrics.find(item => item.key === selected)
  const rows = matches.slice(-10)
  const values = rows.map(row => metricValue(row.metrics, selected))
  const recorded = values.filter((value): value is number => value !== null)
  const width = 720, height = 220, padX = 44, padY = 26
  const min = recorded.length ? Math.min(...recorded) : 0
  const max = recorded.length ? Math.max(...recorded) : 1
  const range = Math.max(max - min, Math.max(Math.abs(max), 1) * .15)
  const points = values.map((value, index) => value === null ? null : ({
    x: padX + index * ((width - padX * 2) / Math.max(rows.length - 1, 1)),
    y: padY + (max + range * .15 - value) * ((height - padY * 2) / (range * 1.3)), value,
  }))
  const line = points.filter(Boolean).map(point => `${point!.x},${point!.y}`).join(' ')
  const average = recorded.length ? recorded.reduce((a, b) => a + b, 0) / recorded.length : null
  return <section className="card chart-card">
    <div className="section-heading"><div><span>Chronological appearances</span><h2>Performance Over Time</h2></div><div className="chart-controls"><select aria-label="Performance metric" value={selected} onChange={event => onSelect(event.target.value)}>{metrics.filter(item => !['appearances','minutes_played'].includes(item.key)).map(item => <option value={item.key} key={item.key}>{item.label}</option>)}</select><div className="chart-average"><span>Average</span><strong>{definition ? formatMetric(definition, average) : '—'}</strong></div></div></div>
    {!rows.length ? <div className="data-state">No appearances found for the selected season.</div> : !recorded.length ? <div className="data-state">This metric has not been recorded for these matches.</div> : <div className="performance-chart"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${definition?.label || 'Metric'} across recent matches`}>
      {[0, .5, 1].map(portion => { const value = min + range * portion; const y = padY + (max + range * .15 - value) * ((height - padY * 2) / (range * 1.3)); return <g key={portion}><line x1={padX} x2={width-padX} y1={y} y2={y} className="chart-gridline"/><text x="2" y={y+4}>{value.toFixed(1)}</text></g> })}
      {points.length > 1 && <polyline points={line} className="chart-line"/>}
      {points.map((point, index) => <g key={rows[index].match.id}>{point && <><circle cx={point.x} cy={point.y} r="4" className="chart-dot"/><title>{rows[index].match.opponent}: {definition ? formatMetric(definition, point.value) : point.value}</title></>}<text x={padX + index * ((width-padX*2)/Math.max(rows.length-1,1))} y={height-3} textAnchor="middle">{new Date(rows[index].match.match_date+'T00:00:00').toLocaleDateString(undefined,{month:'short',day:'numeric'})}</text></g>)}
    </svg></div>}
  </section>
}
