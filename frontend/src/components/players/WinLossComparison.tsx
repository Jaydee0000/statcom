import type { WinLossMetric } from '../../types/player'

export default function WinLossComparison({ metrics }: { metrics: WinLossMetric[] }) {
  return (
    <section className="card comparison-card">
      <div className="section-heading"><div><span>Match outcome split</span><h2>Wins vs Losses</h2></div><div className="comparison-legend"><span><i className="legend-win"/>Wins</span><span><i className="legend-loss"/>Losses</span></div></div>
      <p className="comparison-note">Average match statistics grouped by team result.</p>
      <div className="comparison-list">{metrics.map((metric) => {
        const max = Math.max(metric.wins, metric.losses) * 1.12
        return <div className="comparison-row" key={metric.label}><div className="comparison-row__label"><strong>{metric.label}</strong><span><b>{metric.wins}{metric.suffix}</b><b>{metric.losses}{metric.suffix}</b></span></div><div className="comparison-bars"><i style={{width: `${(metric.wins/max)*100}%`}}/><i style={{width: `${(metric.losses/max)*100}%`}}/></div></div>
      })}</div>
    </section>
  )
}
