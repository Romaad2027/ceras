import { useEffect, useMemo, useState } from 'react'
import api, { cloudAccountsApi } from '../services/api.js'
import { useAlertsSocket } from '../hooks/useAlertsSocket.js'
import { Card, CardHeader, CardContent } from '../components/ui/Card.jsx'
import { Button } from '../components/ui/Button.jsx'
import { Badge } from '../components/ui/Badge.jsx'
import { Table } from '../components/ui/Table.jsx'
import { Input } from '../components/ui/Input.jsx'

const normalizeSeverity = (value) => {
  const sev = (value || '').toString().trim().toUpperCase()
  if (sev.includes('CRIT')) return 'CRITICAL'
  if (sev.includes('HIGH')) return 'HIGH'
  if (sev.includes('MED')) return 'MEDIUM'
  if (sev.includes('LOW')) return 'LOW'
  return sev || '—'
}

const isCriticalLike = (row) => {
  const sev = normalizeSeverity(row?.severity || row?.level || row?.priority)
  return sev === 'CRITICAL' || sev === 'HIGH'
}

const getAlertTimeIso = (row) =>
  row?.time || row?.timestamp || row?.created_at || row?.createdAt || row?.event_time || ''

const getAlertTimeFormatted = (row) => {
  const t = getAlertTimeIso(row)
  const d = t ? new Date(t) : null
  return d && !isNaN(d.valueOf()) ? d.toLocaleString() : '—'
}

const getAlertStatus = (row) => {
  const statusRaw =
    row?.status ||
    row?.state ||
    (typeof row?.resolved === 'boolean' ? (row.resolved ? 'RESOLVED' : 'OPEN') : '') ||
    ''
  const s = (statusRaw || '').toString().trim().toUpperCase()
  if (s.includes('RESOLVED') || s === 'CLOSED') return 'RESOLVED'
  if (s.includes('OPEN') || s.includes('NEW') || s.includes('ACTIVE')) return 'OPEN'
  if (s.includes('IN_PROGRESS')) return 'IN_PROGRESS'
  return s || 'OPEN'
}

const truncate = (text, max = 96) => {
  const str = (text || '').toString()
  if (str.length <= max) return str || '—'
  return `${str.slice(0, max - 1)}…`
}

export const DashboardPage = () => {
  const [alerts, setAlerts] = useState([])
  const [showToast, setShowToast] = useState(false)
  const [lastNewAlert, setLastNewAlert] = useState(null)
  const [resources, setResources] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [accounts, setAccounts] = useState([])
  const [selectedAccountId, setSelectedAccountId] = useState('all')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [severity, setSeverity] = useState('all')
  const [ruleCode, setRuleCode] = useState('')
  const [search, setSearch] = useState('')
  const [createdFrom, setCreatedFrom] = useState('')
  const [createdTo, setCreatedTo] = useState('')

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  const { alerts: liveAlerts } = useAlertsSocket(token)

  const fetchResources = async () => {
    try {
      const { data } = await api.get('/resources')
      const items = Array.isArray(data) ? data : data?.resources || data?.items || []
      setResources(items)
    } catch (_) {
      console.error('[Dashboard] Failed to fetch resources', _)
    }
  }

  const fetchAccounts = async () => {
    try {
      const data = await cloudAccountsApi.list()
      const items = Array.isArray(data) ? data : data?.items || []
      setAccounts(items)
    } catch (_) {
      console.error('[Dashboard] Failed to fetch accounts', _)
    }
  }

  useEffect(() => {
    let cancelled = false
    const init = async () => {
      try {
        await Promise.all([fetchAccounts(), fetchResources()])
      } catch (_) {
        console.error('[Dashboard] Failed to fetch data', _)
      }
    }
    init()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (liveAlerts && liveAlerts.length > 0) {
      setLastNewAlert(liveAlerts[0] || null)
      setShowToast(true)
      const t = setTimeout(() => setShowToast(false), 3000)
      return () => clearTimeout(t)
    }
    return undefined
  }, [liveAlerts])

  const computeRowKey = (row) =>
    row?.id ||
    row?.uuid ||
    `${getAlertTimeIso(row)}_${row?.rule_code || row?.ruleCode || row?.rule || row?.code || ''}`

  const mergedAlerts = useMemo(() => {
    const seen = new Set()
    const result = []
    const pushUnique = (row) => {
      const key = computeRowKey(row)
      if (!seen.has(key)) {
        seen.add(key)
        result.push(row)
      }
    }
    ;(liveAlerts || []).forEach(pushUnique)
    ;(alerts || []).forEach(pushUnique)
    return result
  }, [liveAlerts, alerts])

  const filteredAlerts = useMemo(() => {
    const fromDate = createdFrom ? new Date(createdFrom) : null
    const toDate = createdTo ? new Date(createdTo) : null
    const ruleCodeNeedle = (ruleCode || '').toString().trim().toLowerCase()
    const searchNeedle = (search || '').toString().trim().toLowerCase()
    const severityNeedle = (severity || 'all').toString().trim().toUpperCase()
    const accountIdNeedle = (selectedAccountId || 'all').toString()

    const inRange = (row) => {
      const iso = getAlertTimeIso(row)
      if (!iso) return !(fromDate || toDate)
      const d = new Date(iso)
      if (Number.isNaN(d.valueOf())) return !(fromDate || toDate)
      if (fromDate && d < fromDate) return false
      if (toDate && d > toDate) return false
      return true
    }

    const matchesAccount = (row) => {
      if (!accountIdNeedle || accountIdNeedle === 'all') return true
      const id = row?.cloud_account_id || row?.cloudAccountId || row?.account_id || row?.accountId
      return id ? String(id) === accountIdNeedle : false
    }

    const matchesSeverity = (row) => {
      if (!severityNeedle || severityNeedle === 'ALL') return true
      const val = normalizeSeverity(row?.severity || row?.level || row?.priority)
      return val === severityNeedle
    }

    const matchesRuleCode = (row) => {
      if (!ruleCodeNeedle) return true
      const v = (row?.rule_code || row?.ruleCode || row?.rule || row?.code || '').toString().toLowerCase()
      return v.includes(ruleCodeNeedle)
    }

    const matchesSearch = (row) => {
      if (!searchNeedle) return true
      const blob = (
        row?.description ||
        row?.message ||
        row?.details ||
        row?.text ||
        ''
      )
        .toString()
        .toLowerCase()
      return blob.includes(searchNeedle)
    }

    return (mergedAlerts || []).filter((row) => {
      return (
        matchesAccount(row) &&
        matchesSeverity(row) &&
        matchesRuleCode(row) &&
        matchesSearch(row) &&
        inRange(row)
      )
    })
  }, [mergedAlerts, selectedAccountId, severity, ruleCode, search, createdFrom, createdTo])

  const filteredTotal = filteredAlerts.length
  const paginatedAlerts = useMemo(() => {
    const start = Math.max(0, (page - 1) * (pageSize || 20))
    const end = start + (pageSize || 20)
    return filteredAlerts.slice(start, end)
  }, [filteredAlerts, page, pageSize])

  const summary = useMemo(() => {
    const totalUnresolved = filteredAlerts.filter((a) => getAlertStatus(a) !== 'RESOLVED').length
    const criticalRisks = filteredAlerts.filter((a) => isCriticalLike(a)).length
    const activeResources = resources.length
    return { totalUnresolved, criticalRisks, activeResources }
  }, [filteredAlerts, resources])

  const columns = useMemo(
    () => {
      const wrapCell = (inner, row) => {
        const critical = isCriticalLike(row)
        return (
          <div className={critical ? 'inline-flex max-w-full items-center px-2 py-1 bg-red-50/40 dark:bg-red-950/20 rounded-md' : undefined}>
            {inner}
          </div>
        )
      }
      return [
        {
          header: 'Severity',
          accessor: (row) => normalizeSeverity(row.severity || row.level || row.priority),
          cell: (value, row) => {
            const v = (value || '').toString().toUpperCase()
            const variant = v === 'CRITICAL' || v === 'HIGH' ? 'error' : v === 'MEDIUM' ? 'warning' : v === 'LOW' ? 'success' : 'info'
            return <Badge variant={variant}>{v || '—'}</Badge>
          },
          width: '12rem',
        },
        {
          header: 'Timestamp',
          accessor: (row) => getAlertTimeFormatted(row),
          cell: (value, row) => <span className="tabular-nums">{value}</span>,
          width: '16rem',
        },
        {
          header: 'Rule Code',
          accessor: (row) => row.rule_code || row.ruleCode || row.rule || row.code || '—',
          cell: (value, row) => <span className="font-medium">{value}</span>,
          width: '14rem',
        },
        {
          header: 'Description',
          accessor: (row) => truncate(row.description || row.message || row.details || row.text, 100),
          cell: (value, row) =>
            wrapCell(
              <span className="text-[var(--md-sys-color-on-surface-variant)]" title={row.description || row.message || row.details || row.text || ''}>
                {value}
              </span>,
              row
            ),
        },
        {
          header: 'Status',
          accessor: (row) => getAlertStatus(row),
          cell: (value, row) => {
            const v = (value || '').toString().toUpperCase()
            const variant = v === 'RESOLVED' ? 'success' : v === 'IN_PROGRESS' ? 'info' : 'warning'
            return <Badge variant={variant}>{v}</Badge>
          },
          width: '12rem',
        },
      ]
    },
    []
  )

  const emptyMessage = "All systems operational. No alerts to show."

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="flex items-center justify-between">
            <div>
              <div className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Total Alerts</div>
              <div className="mt-1 text-3xl font-bold text-surface-foreground">{summary.totalUnresolved}</div>
            </div>
            <Badge variant="warning">Unresolved</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between">
            <div>
              <div className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Critical Risks</div>
              <div className="mt-1 text-3xl font-bold text-surface-foreground">{summary.criticalRisks}</div>
            </div>
            <Badge variant="error">High/Critical</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between">
            <div>
              <div className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Active Resources</div>
              <div className="mt-1 text-3xl font-bold text-surface-foreground">{summary.activeResources}</div>
            </div>
            <Badge variant="info">Monitored</Badge>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-md">
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-surface-foreground">Recent Alerts</h2>
          <div className="flex items-center gap-2">
            <select
              className="h-10 rounded-lg border border-outline-variant bg-surface-variant px-3 text-sm outline-none text-surface-foreground"
              value={selectedAccountId}
              onChange={(e) => {
                const id = e.target.value
                setSelectedAccountId(id)
                setPage(1)
              }}
            >
              <option value="all">All Accounts</option>
              {accounts.map((a) => {
                const id = a.id || a.uuid
                const label = a.name || a.provider || id
                return (
                  <option key={id || label} value={id}>
                    {label}
                  </option>
                )
              })}
            </select>
            <Button variant="primary" isLoading={loading}>
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-6">
            <div className="lg:col-span-1">
              <label className="mb-1 block text-sm font-medium text-surface-foreground">Severity</label>
              <select
                className="h-10 w-full rounded-lg border border-outline-variant bg-surface-variant px-3 text-sm outline-none text-surface-foreground"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
              >
                <option value="all">All</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
            </div>
            <Input
              className="lg:col-span-1"
              label="Rule Code"
              placeholder="CRITICAL_RESOURCE_TAMPERING"
              value={ruleCode}
              onChange={(e) => setRuleCode(e.target.value)}
            />
            <Input
              className="lg:col-span-2"
              label="Search"
              placeholder="Search description…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Input
              className="lg:col-span-1"
              type="datetime-local"
              label="From"
              value={createdFrom}
              onChange={(e) => setCreatedFrom(e.target.value)}
            />
            <Input
              className="lg:col-span-1"
              type="datetime-local"
              label="To"
              value={createdTo}
              onChange={(e) => setCreatedTo(e.target.value)}
            />
            <div className="lg:col-span-6 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <label className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Page size</label>
                <select
                  className="h-9 rounded-lg border border-outline-variant bg-surface-variant px-2 text-sm outline-none text-surface-foreground"
                  value={pageSize}
                  onChange={(e) => {
                    const ps = parseInt(e.target.value, 10) || 20
                    setPageSize(ps)
                    setPage(1)
                  }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={200}>200</option>
                </select>
              </div>
              <Button
                variant="secondary"
                onClick={() => {
                  setPage(1)
                }}
                isLoading={loading}
              >
                Apply Filters
              </Button>
            </div>
          </div>
          <Table
            zebra
            stickyHeader
            rowKey={(row, idx) =>
              row.id ||
              row.uuid ||
              `${getAlertTimeIso(row)}_${row.rule_code || row.ruleCode || row.rule || row.code || idx}`
            }
            columns={columns}
            data={paginatedAlerts}
            emptyMessage={emptyMessage}
          />
          {error && <div className="mt-3 text-sm text-error">{error}</div>}
          {showToast && lastNewAlert && (
            <div className="mt-3 rounded-md bg-primary/10 px-3 py-2 text-sm text-primary-foreground">
              New Incident: {truncate(lastNewAlert?.description || lastNewAlert?.message || lastNewAlert?.details || lastNewAlert?.text, 80)}
            </div>
          )}
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-[var(--md-sys-color-on-surface-variant)]">
              Page <span className="font-medium">{page}</span> of{' '}
              <span className="font-medium">{Math.max(1, Math.ceil((filteredTotal || 0) / (pageSize || 20)))}</span>
              {` • ${filteredTotal} total`}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                onClick={() => {
                  if (page > 1) {
                    const next = page - 1
                    setPage(next)
                  }
                }}
                disabled={page <= 1 || loading}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  const totalPages = Math.max(1, Math.ceil((filteredTotal || 0) / (pageSize || 20)))
                  if (page < totalPages) {
                    const next = page + 1
                    setPage(next)
                  }
                }}
                disabled={
                  loading ||
                  Math.ceil((filteredTotal || 0) / (pageSize || 20)) <= page ||
                  (Array.isArray(paginatedAlerts) && paginatedAlerts.length < Math.min(pageSize, filteredTotal))
                }
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default DashboardPage

