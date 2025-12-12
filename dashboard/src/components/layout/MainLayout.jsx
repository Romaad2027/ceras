import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar.jsx'
import { Topbar } from './Topbar.jsx'

export const MainLayout = ({ email = '', onLogout }) => {
  return (
    <div className="min-h-dvh bg-background text-surface-foreground">
      <Sidebar email={email} />
      <div className="md:ml-64 min-h-dvh flex flex-col">
        <Topbar onLogout={onLogout} />
        <main className="flex-1 p-6 md:p-8">
          <div className="mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}


