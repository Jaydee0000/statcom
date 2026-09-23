export default function PerformanceChart({ values }: { values: number[] }) {
  const width = 720
  const height = 220
  const padX = 34
  const padY = 24
  const min = 6.5
  const max = 8.7
  const points = values.map((value, index) => ({ x: padX + index * ((width - padX * 2) / (values.length - 1)), y: padY + (max - value) * ((height - padY * 2) / (max - min)), value }))
  const line = points.map((point) => `${point.x},${point.y}`).join(' ')
  const area = `${padX},${height - padY} ${line} ${width - padX},${height - padY}`

  return (
    <section className="card chart-card">
      <div className="section-heading"><div><span>Last 10 matches</span><h2>Performance Over Time</h2></div><div className="chart-average"><span>Average</span><strong>7.7</strong></div></div>
      <div className="performance-chart">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Player rating across the last ten matches">
          <defs><linearGradient id="ratingArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#20b876" stopOpacity=".2"/><stop offset="1" stopColor="#20b876" stopOpacity="0"/></linearGradient></defs>
          {[7, 7.5, 8, 8.5].map((tick) => { const y = padY + (max - tick) * ((height - padY * 2) / (max - min)); return <g key={tick}><line x1={padX} x2={width-padX} y1={y} y2={y} className="chart-gridline"/><text x="2" y={y+4}>{tick.toFixed(1)}</text></g> })}
          <polygon points={area} fill="url(#ratingArea)"/><polyline points={line} className="chart-line"/>
          {points.map((point, index) => <g key={index}><circle cx={point.x} cy={point.y} r="4" className="chart-dot"/><text x={point.x} y={height-3} textAnchor="middle">M{index+1}</text></g>)}
        </svg>
      </div>
    </section>
  )
}
