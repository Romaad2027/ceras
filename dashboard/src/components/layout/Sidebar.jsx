import { NavLink } from 'react-router-dom'
import { Cloud, LayoutDashboard, Server, Settings, Users, Shield } from 'lucide-react'

export const Sidebar = ({ email = '' }) => {
  return (
    <aside className="hidden md:flex md:flex-col md:fixed md:inset-y-0 md:left-0 md:w-64 bg-surface-variant border-r border-outline-variant">
      <div className="h-16 flex items-center px-5">
        <span className="text-lg font-semibold tracking-wide bg-gradient-to-r from-primary to-secondary bg-clip-text">
          Ceras Security
        </span>
      </div>

      <nav className="flex-1 p-3 space-y-1 text-[var(--md-sys-color-on-surface-variant)]">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            [
              'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
              isActive ? 'bg-primary-container text-primary-container-foreground font-medium ring-1 ring-inset ring-outline-variant relative before:content-[""] before:absolute before:left-1 before:top-1 before:bottom-1 before:w-1 before:rounded-full before:bg-primary' : 'hover:bg-secondary-container',
            ].join(' ')
          }
        >
          <LayoutDashboard size={18} strokeWidth={2} />
          <span>Dashboard</span>
        </NavLink>

        <NavLink
          to="/resources"
          className={({ isActive }) =>
            [
              'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
              isActive ? 'bg-primary-container text-primary-container-foreground font-medium ring-1 ring-inset ring-outline-variant relative before:content-[""] before:absolute before:left-1 before:top-1 before:bottom-1 before:w-1 before:rounded-full before:bg-primary' : 'hover:bg-secondary-container',
            ].join(' ')
          }
        >
          <Server size={18} strokeWidth={2} />
          <span>Resources</span>
        </NavLink>

        <NavLink
          to="/identities"
          className={({ isActive }) =>
            [
              'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
              isActive ? 'bg-primary-container text-primary-container-foreground font-medium ring-1 ring-inset ring-outline-variant relative before:content-[""] before:absolute before:left-1 before:top-1 before:bottom-1 before:w-1 before:rounded-full before:bg-primary' : 'hover:bg-secondary-container',
            ].join(' ')
          }
        >
          <Shield size={18} strokeWidth={2} />
          <span>Identities</span>
        </NavLink>

        <NavLink
          to="/cloud-accounts"
          className={({ isActive }) =>
            [
              'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
              isActive ? 'bg-primary-container text-primary-container-foreground font-medium ring-1 ring-inset ring-outline-variant relative before:content-[""] before:absolute before:left-1 before:top-1 before:bottom-1 before:w-1 before:rounded-full before:bg-primary' : 'hover:bg-secondary-container',
            ].join(' ')
          }
        >
          <Cloud size={18} strokeWidth={2} />
          <span>Cloud Accounts</span>
        </NavLink>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            [
              'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
              isActive ? 'bg-primary-container text-primary-container-foreground font-medium ring-1 ring-inset ring-outline-variant relative before:content-[""] before:absolute before:left-1 before:top-1 before:bottom-1 before:w-1 before:rounded-full before:bg-primary' : 'hover:bg-secondary-container',
            ].join(' ')
          }
        >
          <Settings size={18} strokeWidth={2} />
          <span>Settings</span>
        </NavLink>

        <NavLink
          to="/members"
          className={({ isActive }) =>
            [
              'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
              isActive ? 'bg-primary-container text-primary-container-foreground font-medium ring-1 ring-inset ring-outline-variant relative before:content-[""] before:absolute before:left-1 before:top-1 before:bottom-1 before:w-1 before:rounded-full before:bg-primary' : 'hover:bg-secondary-container',
            ].join(' ')
          }
        >
          <Users size={18} strokeWidth={2} />
          <span>Members</span>
        </NavLink>
      </nav>

      <div className="p-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-primary-container flex items-center justify-center text-primary-container-foreground font-semibold ring-1 ring-inset ring-outline-variant">
            {email ? email[0]?.toUpperCase() : 'U'}
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium truncate text-surface-foreground">{email || 'user@example.com'}</div>
            <div className="text-xs text-[var(--md-sys-color-on-surface-variant)]">Logged in</div>
          </div>
        </div>
      </div>
    </aside>
  )
}


