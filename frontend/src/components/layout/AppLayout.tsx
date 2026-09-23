import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function AppLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-shell__main">
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
