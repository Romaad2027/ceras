import { Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout.jsx'
import { AuthGuard } from './components/layout/AuthGuard.jsx'
import { LoginPage } from './pages/LoginPage.jsx'
import { RegisterPage } from './pages/RegisterPage.jsx'
import { JoinPage } from './pages/JoinPage.jsx'
import { DashboardPage } from './pages/DashboardPage.jsx'
import { SettingsPage } from './pages/SettingsPage.jsx'
import { ResourcesPage } from './pages/ResourcesPage.jsx'
import { MembersPage } from './pages/MembersPage.jsx'
import { IdentitiesPage } from './pages/IdentitiesPage.jsx'
import { CloudAccountsPage } from './pages/CloudAccountsPage.jsx'

const isAuthed = () => Boolean(localStorage.getItem('token'))

export const App = () => {
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('token_type')
    window.location.href = '/login'
  }

  const email = ''

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/join" element={<JoinPage />} />

      <Route
        path="/"
        element={
          <AuthGuard>
            <MainLayout email={email} onLogout={handleLogout} />
          </AuthGuard>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="resources" element={<ResourcesPage />} />
        <Route path="cloud-accounts" element={<CloudAccountsPage />} />
        <Route path="members" element={<MembersPage />} />
        <Route path="identities" element={<IdentitiesPage />} />
      </Route>

      <Route path="*" element={<Navigate to={isAuthed() ? '/' : '/login'} replace />} />
    </Routes>
  )
}

export default App
