import { NavLink } from 'react-router-dom'
import Icon, { type IconName } from '../ui/Icon'

const navigation: { label: string; icon: IconName; path: string }[] = [
  { label: 'Dashboard', icon: 'dashboard', path: '/' },
  { label: 'Players', icon: 'players', path: '/players' },
  { label: 'Matches', icon: 'matches', path: '/matches' },
  { label: 'Team Stat Sheet', icon: 'analytics', path: '/team-stats' },
  { label: 'Video Analysis', icon: 'video', path: '/video-analysis' },
  { label: 'Analytics', icon: 'analytics', path: '/analytics' },
  { label: 'Reports', icon: 'reports', path: '/reports' },
  { label: 'Team Management', icon: 'team', path: '/team-management' },
  { label: 'Settings', icon: 'settings', path: '/settings' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand__mark" aria-hidden="true">
          <span className="brand__ball">⬡</span>
        </div>
        <div className="brand__name">StatCom</div>
      </div>

      <nav className="sidebar__nav" aria-label="Main navigation">
        {navigation.map((item) => (
          <NavLink
            key={item.label}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' nav-item--active' : ''}`}
          >
            <Icon name={item.icon} className="nav-item__icon" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="profile-card">
        <div className="profile-card__avatar">C</div>
        <div className="profile-card__details">
          <strong>Coach</strong>
          <span>Admin</span>
        </div>
        <button className="icon-button icon-button--dark" type="button" aria-label="Sign out">
          <Icon name="exit" />
        </button>
      </div>
    </aside>
  )
}
