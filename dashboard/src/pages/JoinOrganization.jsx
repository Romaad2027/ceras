import { useMemo, useState } from 'react'
import api from '../services/api.js'

export const JoinOrganization = ({ onSuccess }) => {
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const query = useMemo(() => new URLSearchParams(window.location.search), [])
  const token = query.get('token') || ''
  const email = query.get('email') || ''
  const org = query.get('org') || ''

  const styles = {
    card: {
      maxWidth: 960,
      margin: '0 auto',
      background: 'var(--md-sys-color-surface-container)',
      border: '1px solid var(--md-sys-color-outline-variant)',
      borderRadius: 12,
      padding: 24,
      boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
    },
    h1: { fontSize: 22, margin: 0, color: 'var(--md-sys-color-on-surface)' },
    label: {
      display: 'block',
      fontSize: 12,
      color: 'var(--md-sys-color-on-surface-variant, var(--md-sys-color-on-surface))',
      marginBottom: 6,
    },
    input: {
      width: '100%',
      padding: '10px 12px',
      borderRadius: 8,
      border: '1px solid var(--md-sys-color-outline-variant)',
      background: 'var(--md-sys-color-surface)',
      color: 'var(--md-sys-color-on-surface)',
      outline: 'none',
    },
    btnRow: { display: 'flex', gap: 8, flexWrap: 'wrap' },
    button: {
      background: 'var(--md-sys-color-surface-variant)',
      color: 'var(--md-sys-color-on-surface)',
      border: '1px solid var(--md-sys-color-outline-variant)',
      padding: '10px 14px',
      borderRadius: 8,
      cursor: 'pointer',
    },
    buttonPrimary: {
      background: 'var(--md-sys-color-primary)',
      border: '1px solid var(--md-sys-color-primary)',
      color: 'var(--md-sys-color-on-primary)',
    },
    notice: { marginTop: 8, fontSize: 13 },
  }

  const extractToken = (data) =>
    (data && (data.access_token || data.token || data.jwt)) ||
    (data && data.data && (data.data.access_token || data.data.token || data.data.jwt)) ||
    ''
  const extractTokenType = (data) =>
    (data && (data.token_type || (data.data && data.data.token_type))) || 'Bearer'

  const submit = async (e) => {
    e.preventDefault()
    setMessage('')
    setError('')
    if (!token) {
      setError('Invite token missing or invalid.')
      return
    }
    setLoading(true)
    try {
      const payload = {
        token,
        password,
        full_name: fullName,
        email: email || undefined,
      }
      const { data } = await api.post('/auth/accept-invite', payload)
      const t = extractToken(data)
      const tt = extractTokenType(data)
      if (t) {
        localStorage.setItem('token', t)
        localStorage.setItem('token_type', tt)
        setMessage('Registration completed. Redirecting…')
        onSuccess && onSuccess(t, tt)
      } else {
        setMessage('Registration completed.')
      }
    } catch (err) {
      setError(err?.response?.data?.message || err?.message || 'Failed to accept invite.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.card}>
      <h1 style={styles.h1}>
        Join {org ? org : 'Organization'}
      </h1>
      {email && (
        <p
          style={{
            color: 'var(--md-sys-color-on-surface-variant, var(--md-sys-color-on-surface))',
            margin: '6px 0 16px',
          }}
        >
          Invited as{' '}
          <span style={{ color: 'var(--md-sys-color-primary)' }}>{email}</span>
        </p>
      )}
      <form onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
        <div>
          <label style={styles.label}>Full Name</label>
          <input
            style={styles.input}
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="John Ceras"
            required
          />
        </div>
        <div>
          <label style={styles.label}>Password</label>
          <input
            style={styles.input}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            autoComplete="new-password"
          />
        </div>
        <div style={styles.btnRow}>
          <button
            type="submit"
            disabled={loading}
            style={{ ...styles.button, ...styles.buttonPrimary, opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Completing…' : 'Complete Registration'}
          </button>
        </div>
      </form>
      {message && (
        <div style={{ ...styles.notice, color: 'var(--md-sys-color-success, #86efac)' }}>
          {message}
        </div>
      )}
      {error && (
        <div style={{ ...styles.notice, color: 'var(--md-sys-color-error, #fca5a5)' }}>
          {error}
        </div>
      )}
    </div>
  )
}

export default JoinOrganization


