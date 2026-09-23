import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import DashboardPage from './pages/DashboardPage'
import PlayerProfilePage from './pages/PlayerProfilePage'
import PlayersPage from './pages/PlayersPage'
import MatchesPage from './pages/MatchesPage'
import VideoAnalysisPage from './pages/VideoAnalysisPage'
import AnalyticsPage from './pages/AnalyticsPage'
import ReportsPage from './pages/ReportsPage'
import TeamManagementPage from './pages/TeamManagementPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="players" element={<PlayersPage />} />
        <Route path="players/:id" element={<PlayerProfilePage />} />
        <Route path="matches" element={<MatchesPage />} />
        <Route path="video-analysis" element={<VideoAnalysisPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="team-management" element={<TeamManagementPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
