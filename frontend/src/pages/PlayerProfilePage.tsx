import { Link, Navigate, useParams } from 'react-router-dom'
import PageHeader from '../components/layout/PageHeader'
import PerformanceChart from '../components/players/PerformanceChart'
import PlayerHeader from '../components/players/PlayerHeader'
import PlayerStatsGrid from '../components/players/PlayerStatsGrid'
import RecentMatchesTable from '../components/players/RecentMatchesTable'
import VideoClipsCard from '../components/players/VideoClipsCard'
import WinLossComparison from '../components/players/WinLossComparison'
import { getPlayerById } from '../data/mockPlayers'

export default function PlayerProfilePage() {
  const { id } = useParams()
  const player = getPlayerById(id)
  if (!player) return <Navigate to="/players" replace />

  return (
    <div className="player-profile-page">
      <PageHeader
        title={player.name}
        eyebrow={<nav className="breadcrumb" aria-label="Breadcrumb"><Link to="/players">Players</Link><span>/</span><strong>{player.name}</strong></nav>}
      />
      <PlayerHeader player={player} />
      <PlayerStatsGrid stats={player.seasonStats} />
      <div className="profile-analytics-grid"><PerformanceChart values={player.performanceRatings}/><WinLossComparison metrics={player.winLossMetrics}/></div>
      <RecentMatchesTable matches={player.recentMatches}/>
      <div className="profile-detail-grid">
        <section className="card role-card"><div className="section-heading"><div><span>Playing profile</span><h2>Position / Role</h2></div></div><dl><div><dt>Primary position</dt><dd>{player.positionName}</dd></div><div><dt>Secondary position</dt><dd>{player.secondaryPosition}</dd></div><div><dt>Primary role</dt><dd>{player.role}</dd></div></dl><p>{player.roleDescription}</p></section>
        <VideoClipsCard clips={player.videoClips}/>
        <section className="card notes-card"><div className="section-heading"><div><span>Coach observations</span><h2>Notes / Focus Areas</h2></div></div><div className="notes-columns"><div><h3>Strengths</h3><ul>{player.strengths.map((item) => <li key={item}>{item}</li>)}</ul></div><div><h3>Focus Areas</h3><ul>{player.focusAreas.map((item) => <li key={item}>{item}</li>)}</ul></div></div></section>
      </div>
    </div>
  )
}
