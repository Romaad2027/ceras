import { Navigate, Outlet } from 'react-router-dom'

const isAuthed = () => Boolean(localStorage.getItem('token'))

export const AuthGuard = ({ children }) => {
  if (!isAuthed()) {
    return <Navigate to="/login" replace />
  }
  if (children) return children
  return <Outlet />
}

export default AuthGuard


