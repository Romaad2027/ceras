import React from 'react'
import { Card, CardContent, CardHeader } from '../components/ui/Card.jsx'
import { Table } from '../components/ui/Table.jsx'
import { Badge } from '../components/ui/Badge.jsx'
import { Button } from '../components/ui/Button.jsx'
import { TagInput } from '../components/ui/TagInput.jsx'
import { identitiesApi } from '../services/api.js'

export const IdentitiesPage = () => {
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState('')
  const [identities, setIdentities] = React.useState([])

  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [detailsLoading, setDetailsLoading] = React.useState(false)
  const [saving, setSaving] = React.useState(false)
  const [activeIdentity, setActiveIdentity] = React.useState(null)

  const [ipWhitelist, setIpWhitelist] = React.useState([])
  const [allowedActions, setAllowedActions] = React.useState([])
  const [forbiddenActions, setForbiddenActions] = React.useState([])

  const cidrRegex =
    /^(?:\d{1,3}\.){3}\d{1,3}(?:\/(?:[0-9]|[1-2][0-9]|3[0-2]))?$/

  const fetchIdentities = React.useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await identitiesApi.list()
      setIdentities(Array.isArray(data) ? data : data?.results || [])
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load identities')
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    fetchIdentities()
  }, [fetchIdentities])

  const openConfigure = async (row) => {
    setIsModalOpen(true)
    setActiveIdentity({ id: row.id, name: row.name || row.identity_name || row.arn || 'Identity' })
    setDetailsLoading(true)
    try {
      const details = await identitiesApi.get(row.id)
      const rules = details?.rules || details?.policy || details || {}
      setIpWhitelist(rules.ip_whitelist || rules.ipWhitelist || [])
      setAllowedActions(rules.allowed_actions || rules.allowedActions || [])
      setForbiddenActions(rules.forbidden_actions || rules.forbiddenActions || [])
      setActiveIdentity((prev) => ({ ...prev, ...details }))
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load identity details')
    } finally {
      setDetailsLoading(false)
    }
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setActiveIdentity(null)
    setIpWhitelist([])
    setAllowedActions([])
    setForbiddenActions([])
  }

  const handleSave = async () => {
    if (!activeIdentity?.id) return
    setSaving(true)
    setError('')
    try {
      await identitiesApi.update(activeIdentity.id, {
        rules: {
          ip_whitelist: ipWhitelist,
          allowed_actions: allowedActions,
          forbidden_actions: forbiddenActions,
        },
      })
      closeModal()
      fetchIdentities()
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to save changes')
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    {
      header: 'Identity',
      accessor: (row) => row,
      cell: (_v, row) => {
        const name = row.name || row.identity_name || row.user_name || row.role_name || '—'
        const arn = row.arn || row.identity_arn || ''
        return (
          <div className="max-w-[520px]">
            <div className="font-medium text-surface-foreground truncate">{name}</div>
            {arn && <div className="text-xs text-[var(--md-sys-color-on-surface-variant)] truncate">{arn}</div>}
          </div>
        )
      },
    },
    {
      header: 'Type',
      accessor: (row) => row.type || row.identity_type || '',
      cell: (v) => {
        const label = (v || '').toString().toLowerCase() === 'role' ? 'Role' : 'User'
        return <Badge className="rounded-full px-2 py-0.5 text-xs">{label}</Badge>
      },
      width: 120,
    },
    {
      header: 'MFA',
      accessor: (row) => row.mfa_enabled ?? row.mfa ?? false,
      cell: (enabled) => {
        return enabled ? (
          <span className="inline-flex items-center text-xs text-emerald-400">
            <svg className="mr-1 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            MFA Enabled
          </span>
        ) : (
          <Badge variant="error" className="rounded-full px-2 py-0.5 text-xs">
            MFA Missing
          </Badge>
        )
      },
      width: 140,
    },
    {
      header: 'Actions',
      accessor: () => null,
      cell: (_v, row) => (
        <Button size="sm" onClick={(e) => { e.stopPropagation(); openConfigure(row) }}>
          Configure Rules
        </Button>
      ),
      width: 160,
    },
  ]

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Cloud Identities</h2>
            <div />
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 text-sm text-rose-400">
              {error}
            </div>
          )}
          <Table
            data={identities}
            columns={columns}
            zebra
            emptyMessage={loading ? 'Loading identities…' : 'No identities found.'}
          />
        </CardContent>
      </Card>

      {isModalOpen && (
        <div className="fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/50" onClick={saving ? undefined : closeModal} />
          <div className="absolute inset-0 flex items-center justify-center p-4">
            <div className="w-full max-w-3xl rounded-xl border border-outline-variant bg-[var(--md-sys-color-surface-container-lowest)] shadow-lg">
              <div className="flex items-center justify-between px-6 py-4 border-b border-outline-variant">
                <h3 className="text-base font-semibold">
                  Behavior Rules for {activeIdentity?.name || activeIdentity?.arn || 'Identity'}
                </h3>
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded p-2 text-[var(--md-sys-color-on-surface-variant)] hover:bg-secondary-container"
                  disabled={saving}
                  aria-label="Close"
                >
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
                  </svg>
                </button>
              </div>
              <div className="px-6 py-5 space-y-5">
                {detailsLoading ? (
                  <div className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Loading details…</div>
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="rounded-lg border border-outline-variant p-4">
                        <div className="text-sm font-medium mb-2 text-surface-foreground">Identity Info</div>
                        <div className="space-y-1">
                          {activeIdentity?.arn && (
                            <div className="text-xs text-[var(--md-sys-color-on-surface-variant)] truncate">
                              <span className="font-medium text-surface-foreground">ARN: </span>
                              {activeIdentity.arn}
                            </div>
                          )}
                          <div className="flex items-center gap-2 text-xs">
                            <span className="font-medium text-surface-foreground">Type:</span>
                            <Badge className="rounded-full px-2 py-0.5 text-xs">
                              {((activeIdentity?.type || activeIdentity?.identity_type || '') + '').toLowerCase() === 'role' ? 'Role' : 'User'}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <span className="font-medium text-surface-foreground">MFA:</span>
                            {(activeIdentity?.mfa_enabled ?? activeIdentity?.mfa ?? false) ? (
                              <span className="inline-flex items-center text-emerald-400">
                                <svg className="mr-1 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                                Enabled
                              </span>
                            ) : (
                              <Badge variant="error" className="rounded-full px-2 py-0.5 text-xs">Missing</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="rounded-lg border border-outline-variant p-4">
                        <div className="text-sm font-medium mb-2 text-surface-foreground">Current Rules</div>
                        <div className="space-y-3">
                          <div>
                            <div className="text-xs mb-1 text-[var(--md-sys-color-on-surface-variant)]">
                              Allowed IPs ({ipWhitelist.length})
                            </div>
                            <div className="flex flex-wrap gap-2 max-h-24 overflow-auto pr-1">
                              {ipWhitelist.length ? (
                                ipWhitelist.map((ip, idx) => (
                                  <Badge key={`${ip}-${idx}`} className="bg-indigo-50 text-indigo-700 rounded-md border-indigo-200">
                                    {ip}
                                  </Badge>
                                ))
                              ) : (
                                <span className="text-xs text-[var(--md-sys-color-on-surface-variant)]">None</span>
                              )}
                            </div>
                          </div>
                          <div>
                            <div className="text-xs mb-1 text-[var(--md-sys-color-on-surface-variant)]">
                              Allowed Actions ({allowedActions.length})
                            </div>
                            <div className="flex flex-wrap gap-2 max-h-24 overflow-auto pr-1">
                              {allowedActions.length ? (
                                allowedActions.map((act, idx) => (
                                  <Badge key={`${act}-${idx}`} className="bg-indigo-50 text-indigo-700 rounded-md border-indigo-200">
                                    {act}
                                  </Badge>
                                ))
                              ) : (
                                <span className="text-xs text-[var(--md-sys-color-on-surface-variant)]">None</span>
                              )}
                            </div>
                          </div>
                          <div>
                            <div className="text-xs mb-1 text-[var(--md-sys-color-on-surface-variant)]">
                              Forbidden Actions ({forbiddenActions.length})
                            </div>
                            <div className="flex flex-wrap gap-2 max-h-24 overflow-auto pr-1">
                              {forbiddenActions.length ? (
                                forbiddenActions.map((act, idx) => (
                                  <Badge key={`${act}-f-${idx}`} className="bg-indigo-50 text-indigo-700 rounded-md border-indigo-200">
                                    {act}
                                  </Badge>
                                ))
                              ) : (
                                <span className="text-xs text-[var(--md-sys-color-on-surface-variant)]">None</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div>
                      <div className="mb-2 text-sm font-medium text-surface-foreground">IP Whitelist</div>
                      <TagInput
                        value={ipWhitelist}
                        onChange={setIpWhitelist}
                        placeholder="Add allowed CIDRs (e.g., 10.0.0.5/32)"
                        validationRegex={cidrRegex}
                      />
                    </div>
                    <div>
                      <div className="mb-2 text-sm font-medium text-surface-foreground">Allowed Actions</div>
                      <TagInput
                        value={allowedActions}
                        onChange={setAllowedActions}
                        placeholder="Manually allow actions (e.g., TerminateInstances)"
                      />
                    </div>
                    <div>
                      <div className="mb-2 text-sm font-medium text-surface-foreground">Forbidden Actions</div>
                      <TagInput
                        value={forbiddenActions}
                        onChange={setForbiddenActions}
                        placeholder="Manually block actions"
                      />
                    </div>
                  </>
                )}
              </div>
              <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-outline-variant">
                <Button variant="secondary" onClick={closeModal} disabled={saving}>Cancel</Button>
                <Button onClick={handleSave} isLoading={saving}>Save Changes</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default IdentitiesPage


