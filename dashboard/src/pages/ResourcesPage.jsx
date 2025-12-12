import { useEffect, useMemo, useState } from 'react'
import api from '../services/api.js'
import { Card, CardHeader, CardContent } from '../components/ui/Card.jsx'
import { Table } from '../components/ui/Table.jsx'
import { Badge } from '../components/ui/Badge.jsx'
import { Button } from '../components/ui/Button.jsx'
import { ResourceDetailModal } from '../components/resources/ResourceDetailModal.jsx'

const normalizeCriticality = (value) => {
  const v = (value || '').toString().trim().toUpperCase()
  if (v.includes('CRIT')) return 'CRITICAL'
  if (v === 'LOW') return 'LOW'
  if (v === 'STANDARD' || v === 'MEDIUM' || v === 'NORMAL') return 'STANDARD'
  return v || 'STANDARD'
}

const getResourceId = (row) => row?.id || row?.resource_id || row?.uuid || row?.arn || row?.resource_arn

const criticalityClasses = (level) => {
  const v = normalizeCriticality(level)
  if (v === 'CRITICAL') {
    return 'bg-error-container text-[var(--md-sys-color-on-error-container)]'
  }
  if (v === 'LOW') {
    return 'bg-tertiary-container text-[var(--md-sys-color-on-tertiary-container)]'
  }
  return 'bg-surface-variant text-[var(--md-sys-color-on-surface-variant)]'
}

const typeToBadgeVariant = (typeValue) => {
  const t = (typeValue || '').toString().toLowerCase()
  if (t.includes('s3')) return 'info'
  if (t.includes('ec2')) return 'warning'
  if (t.includes('rds') || t.includes('db')) return 'success'
  if (t.includes('iam') || t.includes('auth')) return 'default'
  return 'default'
}

export const ResourcesPage = () => {
  const [resources, setResources] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [updatingId, setUpdatingId] = useState(null)
  const [toast, setToast] = useState(null)
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false)
  const [lastNonEmpty, setLastNonEmpty] = useState([])
  const [selectedResource, setSelectedResource] = useState(null)

  const showToast = (type, message) => {
    setToast({ type, message })
    window.clearTimeout(showToast._t)
    showToast._t = window.setTimeout(() => setToast(null), 2200)
  }

  const fetchResources = async () => {
    try {
      setLoading(true)
      setError('')
      const { data } = await api.get('/resources')
      const items = Array.isArray(data) ? data : data?.resources || data?.items || []
      if (items.length > 0 || !hasLoadedOnce) {
        setResources(items)
        if (items.length > 0) {
          setLastNonEmpty(items)
        }
      }
      if (!hasLoadedOnce) {
        setHasLoadedOnce(true)
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Failed to fetch resources.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    const init = async () => {
      try {
        await fetchResources()
      } catch (_) {}
    }
    init()
    return () => {
      cancelled = true
      if (cancelled) {
        window.clearTimeout(showToast._t)
      }
    }
  }, [])

  const handleCriticalityChange = async (row, newValue) => {
    const id = getResourceId(row)
    if (!id) return
    const normalized = normalizeCriticality(newValue)

    const prev = resources
    const next = resources.map((r) =>
      getResourceId(r) === id ? { ...r, criticality: normalized } : r
    )
    setResources(next)
    if (next.length > 0) {
      setLastNonEmpty(next)
    }
    setUpdatingId(id)
    try {
      const encodedId = encodeURIComponent(id)
      await api.patch(`/resources/${encodedId}`, { criticality: normalized })
      await fetchResources()
      showToast('success', 'Criticality updated')
    } catch (err) {
      setResources(prev)
      if (prev.length > 0) {
        setLastNonEmpty(prev)
      }
      showToast('error', err?.response?.data?.detail || err?.response?.data?.message || 'Failed to update criticality')
    } finally {
      setUpdatingId(null)
    }
  }

  const columns = useMemo(
    () => [
      {
        header: 'Name',
        accessor: (row) => row.name || row.resource_name || row.title || row.id || '—',
        cell: (value) => <span className="font-semibold text-surface-foreground">{value}</span>,
      },
      {
        header: 'Type',
        accessor: (row) => row.resource_type || row.service || row.kind || '—',
        cell: (value) => <Badge variant={typeToBadgeVariant(value)}>{value}</Badge>,
      },
      {
        header: 'Region',
        accessor: (row) => 'eu-north-1',
      },
      {
        header: 'Criticality',
        accessor: (row) => normalizeCriticality(row.criticality || row.risk || row.severity || 'STANDARD'),
        cell: (value, row) => {
          const id = row?.id || row?.resource_id || row?.uuid
          const isUpdating = updatingId === id
          return (
            <select
              className={[
                'rounded-md px-3 py-2 text-sm border border-outline-variant',
                'outline-none focus:ring-2 focus:ring-[var(--md-sys-color-outline-variant)]',
                criticalityClasses(value),
              ].join(' ')}
              value={normalizeCriticality(value)}
              onChange={(e) => handleCriticalityChange(row, e.target.value)}
              disabled={isUpdating}
            >
              <option value="LOW">LOW</option>
              <option value="STANDARD">STANDARD</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          )
        },
      },
      {
        header: 'Actions',
        accessor: () => '',
        cell: (_v, row) => (
          <Button variant="secondary" size="sm" onClick={() => setSelectedResource(row)}>
            Details
          </Button>
        ),
      },
    ],
    [updatingId]
  )

  const displayResources = resources.length > 0 ? resources : lastNonEmpty

  return (
    <>
    <Card className="shadow-md">
      <CardHeader className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-surface-foreground">Resources</h2>
        <div className="flex items-center gap-2">
          <Button variant="primary" onClick={fetchResources} isLoading={loading}>
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {toast && (
          <div
            className={[
              'mb-4 rounded-lg px-4 py-2 text-sm border',
              toast.type === 'success'
                ? 'bg-primary-container text-primary-container-foreground border-outline-variant'
                : 'bg-error-container text-[var(--md-sys-color-on-error-container)] border-outline-variant',
            ].join(' ')}
          >
            {toast.message}
          </div>
        )}

        {loading && resources.length === 0 ? (
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
            data={displayResources}
            rowKey={(row) => getResourceId(row)}
            emptyMessage="No resources found. Ensure your AWS keys are configured."
          />
        )}

        {error && <div className="mt-3 text-sm text-error">{error}</div>}
      </CardContent>
    </Card>
    {selectedResource && (
      <ResourceDetailModal
        resource={selectedResource}
        onClose={() => setSelectedResource(null)}
        onSave={fetchResources}
      />
    )}
    </>
  )
}

export default ResourcesPage


