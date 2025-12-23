import { useMemo } from 'react'
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

const decodeJwt = (token) => {
  if (!token || typeof token !== 'string' || !token.includes('.')) return null
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64.padEnd(base64.length + (4 - (base64.length % 4)) % 4, '=')
    const json = atob(padded)
    return JSON.parse(json)
  } catch (_) {
    return null
  }
}

export const App = () => {
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('token_type')
    localStorage.removeItem('user_email')
    window.location.href = '/login'
  }

  const token = localStorage.getItem('token') || ''
  const claims = useMemo(() => decodeJwt(token), [token])
  const email = claims?.email || claims?.preferred_username || localStorage.getItem('user_email') || ''

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
