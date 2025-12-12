import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api.js'

export const LoginPage = () => {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', { email, password })
      const token =
        data?.access_token || data?.token || data?.jwt || data?.data?.access_token || ''
      const tokenType = data?.token_type || data?.data?.token_type || 'Bearer'
      if (!token) throw new Error('Token not found in response')
      localStorage.setItem('token', token)
      if (tokenType) localStorage.setItem('token_type', tokenType)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err?.response?.data?.message || err?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-[var(--md-sys-color-surface-container-lowest)] border border-outline-variant rounded-lg p-6 shadow-md max-w-md mx-auto">
      <h1 className="text-xl font-semibold mb-1">Sign in</h1>
      <p className="text-[var(--md-sys-color-on-surface-variant)] text-sm mb-4">CERAS</p>
      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">Email</label>
          <input
            className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="username"
          />
        </div>
        <div>
          <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">Password</label>
          <input
            className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:brightness-95 disabled:opacity-70"
          >
            {loading ? 'Please wait…' : 'Login'}
          </button>
          <Link to="/register" className="text-sm text-primary underline">
            Create Organization
          </Link>
        </div>
        {error && <div className="text-sm text-error">{error}</div>}
      </form>
    </div>
  )
}


