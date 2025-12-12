import { useEffect, useMemo, useState } from 'react'
import { Card, CardHeader, CardContent } from '../components/ui/Card.jsx'
import { Table } from '../components/ui/Table.jsx'
import { Badge } from '../components/ui/Badge.jsx'
import { Button } from '../components/ui/Button.jsx'
import { cloudAccountsApi } from '../services/api.js'
import { Input } from '../components/ui/Input.jsx'

const providerVariant = (provider) => {
  const p = (provider || '').toString().toUpperCase()
  if (p === 'AWS') return 'warning'
  if (p === 'AZURE') return 'info'
  if (p === 'GCP') return 'success'
  return 'default'
}

export const CloudAccountsPage = () => {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')
  const [createSuccess, setCreateSuccess] = useState('')
  const [form, setForm] = useState({
    name: '',
    provider: 'AWS',
    region: '',
    credentialsText: '',
  })

  const fetchAccounts = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await cloudAccountsApi.list()
      const items = Array.isArray(data) ? data : data?.items || []
      setAccounts(items)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load cloud accounts.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    const init = async () => {
      try {
        await fetchAccounts()
      } catch (_) {}
    }
    init()
    return () => {
      cancelled = true
    }
  }, [])

  const handleInput = (key) => (e) => {
    setForm((prev) => ({ ...prev, [key]: e.target.value }))
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreateError('')
    setCreateSuccess('')

    const name = form.name.trim()
    const provider = form.provider.trim()
    const region = form.region.trim()
    if (!name || !provider || !region) {
      setCreateError('Please fill in name, provider, and region.')
      return
    }
    let credentials
    try {
      credentials = form.credentialsText ? JSON.parse(form.credentialsText) : {}
    } catch {
      setCreateError('Credentials must be valid JSON.')
      return
    }

    try {
      setCreating(true)
      const payload = { name, provider, region, credentials }
      await cloudAccountsApi.create(payload)
      setCreateSuccess('Cloud account connected.')
      setForm({ name: '', provider, region: '', credentialsText: '' })
      await fetchAccounts()
    } catch (err) {
      const status = err?.response?.status
      const detail =
        err?.response?.data?.detail ||
        (status === 403
          ? 'Only admins can connect cloud accounts.'
          : status === 401
          ? 'Could not validate credentials.'
          : 'Failed to connect cloud account.')
      setCreateError(detail)
    } finally {
      setCreating(false)
    }
  }

  const columns = useMemo(
    () => [
      {
        header: 'Name',
        accessor: (row) => row.name || '—',
      },
      {
        header: 'Provider',
        accessor: (row) => row.provider || '—',
        cell: (value) => <Badge variant={providerVariant(value)}>{value}</Badge>,
      },
      {
        header: 'Region',
        accessor: (row) => row.region || '—',
      },
      {
        header: 'Status',
        accessor: (row) => (row.is_active ? 'Active' : 'Inactive'),
        cell: (value, row) => (
          <Badge variant={row.is_active ? 'success' : 'default'}>{row.is_active ? 'Active' : 'Inactive'}</Badge>
        ),
      },
      {
        header: 'Created',
        accessor: (row) => {
          const ts = row.created_at
          try {
            return ts ? new Date(ts).toLocaleString() : '—'
          } catch {
            return ts || '—'
          }
        },
      },
    ],
    []
  )

  return (
    <Card className="shadow-md">
      <CardHeader className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-surface-foreground">Cloud Accounts</h2>
        <div className="flex items-center gap-2">
          <Button variant="primary" onClick={fetchAccounts} isLoading={loading}>
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleCreate} className="mb-6 grid grid-cols-1 gap-3 md:grid-cols-2">
          <Input
            label="Name"
            placeholder="Acme AWS Prod"
            value={form.name}
            onChange={handleInput('name')}
          />

          <div className="w-full">
            <label className="mb-1 block text-sm font-medium text-surface-foreground">Provider</label>
            <select
              className={[
                'w-full rounded-lg bg-surface-variant text-surface-foreground',
                'border border-transparent focus:border-primary focus:ring-2 focus:ring-outline-variant focus:outline-none',
                'px-3 py-2 transition-shadow',
              ].join(' ')}
              value={form.provider}
              onChange={handleInput('provider')}
            >
              <option value="AWS">AWS</option>
              <option value="AZURE">AZURE</option>
              <option value="GCP">GCP</option>
            </select>
          </div>

          <Input
            label="Region"
            placeholder="us-east-1"
            value={form.region}
            onChange={handleInput('region')}
          />

          <div className="w-full md:col-span-2">
            <label className="mb-1 block text-sm font-medium text-surface-foreground">Credentials (JSON)</label>
            <textarea
              className={[
                'w-full rounded-lg bg-surface-variant text-surface-foreground',
                'border border-transparent focus:border-primary focus:ring-2 focus:ring-outline-variant focus:outline-none',
                'px-3 py-2 transition-shadow min-h-[120px] font-mono text-sm',
              ].join(' ')}
              placeholder='{"access_key_id":"...", "secret_access_key":"..."}'
              value={form.credentialsText}
              onChange={handleInput('credentialsText')}
            />
            <p className="mt-1 text-xs text-[var(--md-sys-color-on-surface-variant)]">
              Paste provider-specific credentials as JSON. No secrets are displayed back.
            </p>
          </div>

          <div className="md:col-span-2 flex items-center gap-3">
            <Button type="submit" variant="primary" isLoading={creating}>
              Connect Account
            </Button>
            {createError && <span className="text-sm text-error">{createError}</span>}
            {createSuccess && <span className="text-sm text-success">{"✓ "}{createSuccess}</span>}
          </div>
        </form>

        {loading && accounts.length === 0 ? (
          <div className="space-y-3">
            <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
            <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
            <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
            <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
          </div>
        ) : (
          <Table
            zebra
            stickyHeader
            columns={columns}
            data={accounts}
            rowKey={(row) => row.id}
            emptyMessage="No cloud accounts connected yet."
          />
        )}

        {error && <div className="mt-3 text-sm text-error">{error}</div>}
      </CardContent>
    </Card>
  )
}

export default CloudAccountsPage


