import { useState } from 'react'
import api from '../services/api.js'

export const RegisterTenant = ({ onSuccess, onCancel }) => {
  const [organizationName, setOrganizationName] = useState('')
  const [adminEmail, setAdminEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

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
    setLoading(true)
    try {
      const payload = {
        organization_name: organizationName,
        email: adminEmail,
        full_name: fullName,
        password,
      }
      const { data } = await api.post('/auth/register-tenant', payload)
      const token = extractToken(data)
      const tokenType = extractTokenType(data)
      if (token) {
        localStorage.setItem('token', token)
        localStorage.setItem('token_type', tokenType)
        localStorage.setItem('user_email', adminEmail)
        setMessage('Organization created. Redirecting…')
        onSuccess && onSuccess(token, tokenType)
      } else {
        setMessage('Organization created.')
      }
    } catch (err) {
      setError(err?.response?.data?.message || err?.message || 'Failed to create organization.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.card}>
      <h1 style={styles.h1}>Create Organization</h1>
      <p
        style={{
          color: 'var(--md-sys-color-on-surface-variant, var(--md-sys-color-on-surface))',
          margin: '6px 0 16px',
        }}
      >
        Set up your organization and the first admin account.
      </p>
      <form onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
        <div>
          <label style={styles.label}>Organization Name</label>
          <input
            style={styles.input}
            type="text"
            value={organizationName}
            onChange={(e) => setOrganizationName(e.target.value)}
            placeholder="Acme Corp"
            required
          />
        </div>
        <div>
          <label style={styles.label}>Admin Email</label>
          <input
            style={styles.input}
            type="email"
            value={adminEmail}
            onChange={(e) => setAdminEmail(e.target.value)}
            placeholder="admin@acme.com"
            required
            autoComplete="username"
          />
        </div>
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
            {loading ? 'Creating…' : 'Create Organization'}
          </button>
          <button type="button" onClick={onCancel} style={styles.button}>
            Have an account? Login
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

export default RegisterTenant


