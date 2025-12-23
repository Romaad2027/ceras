import React from 'react'
import { Card, CardContent, CardHeader } from '../components/ui/Card.jsx'
import { Table } from '../components/ui/Table.jsx'
import { Badge } from '../components/ui/Badge.jsx'
import { Button } from '../components/ui/Button.jsx'
import { TagInput } from '../components/ui/TagInput.jsx'
import { identitiesApi, profilesApi } from '../services/api.js'

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
  
  const [profile, setProfile] = React.useState(null)
  const [profileError, setProfileError] = React.useState('')

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
    const entityArn = row.arn || row.identity_arn || ''
    setActiveIdentity({ 
      id: row.id, 
      arn: entityArn,
      name: row.name || row.identity_name || entityArn || 'Identity' 
    })
    setDetailsLoading(true)
    setProfileError('')
    try {
      const details = await identitiesApi.get(row.id)
      setActiveIdentity((prev) => ({ ...prev, ...details }))
      
      if (entityArn) {
        try {
          const profileData = await profilesApi.get(entityArn)
          setProfile(profileData)
          console.log(profileData)
          setIpWhitelist(profileData.whitelisted_cidrs || [])
          setAllowedActions(profileData.manual_allowed_actions || [])
          setForbiddenActions(profileData.manual_forbidden_actions || [])
        } catch (profileErr) {
          console.log('No profile found for this entity')

          if (profileErr?.response?.status === 404) {
            setProfileError('No profile found for this entity')
            // Initialize with empty arrays if profile doesn't exist
            setIpWhitelist([])
            setAllowedActions([])
            setForbiddenActions([])
          } else {
            setProfileError(profileErr?.response?.data?.detail || profileErr?.message || 'Failed to load profile')
          }
          setProfile(null)
        }
      } else {
        setProfileError('Identity ARN not available')
        setProfile(null)
        setIpWhitelist([])
        setAllowedActions([])
        setForbiddenActions([])
      }
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
    setProfile(null)
    setProfileError('')
  }

  const handleSave = async () => {
    const entityArn = activeIdentity?.arn
    if (!entityArn) {
      setError('Identity ARN not available')
      return
    }
    setSaving(true)
    setError('')
    try {
      await profilesApi.update(entityArn, {
        whitelisted_cidrs: ipWhitelist,
        manual_allowed_actions: allowedActions,
        manual_forbidden_actions: forbiddenActions,
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
            <div className="w-full max-w-3xl max-h-[90vh] flex flex-col rounded-xl border border-outline-variant bg-[var(--md-sys-color-surface-container-lowest)] shadow-lg">
              <div className="flex items-center justify-between px-6 py-4 border-b border-outline-variant flex-shrink-0">
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
              <div className="px-6 py-5 space-y-5 overflow-y-auto flex-1">
                {detailsLoading ? (
                  <div className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Loading details…</div>
                ) : (
                  <>
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
                    
                    {/* Entity Profile Section */}
                    <div className="rounded-lg border border-outline-variant p-4 bg-[var(--md-sys-color-surface-container-highest)]">
                      <div className="text-sm font-medium mb-3 text-surface-foreground flex items-center gap-2">
                        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Security Profile
                      </div>
                      {profileError ? (
                        <div className="text-xs text-[var(--md-sys-color-on-surface-variant)] italic">
                          {profileError}
                        </div>
                      ) : profile ? (
                        <div className="space-y-4">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium text-surface-foreground">Profile Mode:</span>
                            <Badge variant={
                              profile.profile_mode === 'AUTO' ? 'default' : 
                              profile.profile_mode === 'MANUAL' ? 'warning' : 
                              'success'
                            } className="rounded-full px-2 py-0.5 text-xs">
                              {profile.profile_mode || 'AUTO'}
                            </Badge>
                          </div>
                          
                          {/* Manual Configuration Section */}
                          <div className="space-y-3 border-t border-outline-variant pt-3">
                            <div className="text-xs font-semibold text-surface-foreground uppercase tracking-wide">
                              Manual Configuration
                            </div>
                            
                            <div>
                              <div className="text-xs mb-1 font-medium text-surface-foreground">
                                Whitelisted CIDRs ({profile.whitelisted_cidrs?.length || 0})
                              </div>
                              <div className="flex flex-wrap gap-2 max-h-20 overflow-auto pr-1">
                                {profile.whitelisted_cidrs?.length ? (
                                  profile.whitelisted_cidrs.map((cidr, idx) => (
                                    <Badge key={`profile-cidr-${idx}`} className="bg-emerald-50 text-emerald-700 rounded-md border-emerald-200">
                                      {cidr}
                                    </Badge>
                                  ))
                                ) : (
                                  <span className="text-xs text-[var(--md-sys-color-on-surface-variant)]">None</span>
                                )}
                              </div>
                            </div>
                            
                            <div>
                              <div className="text-xs mb-1 font-medium text-surface-foreground">
                                Manual Allowed Actions ({profile.manual_allowed_actions?.length || 0})
                              </div>
                              <div className="flex flex-wrap gap-2 max-h-20 overflow-auto pr-1">
                                {profile.manual_allowed_actions?.length ? (
                                  profile.manual_allowed_actions.map((action, idx) => (
                                    <Badge key={`profile-allowed-${idx}`} className="bg-emerald-50 text-emerald-700 rounded-md border-emerald-200">
                                      {action}
                                    </Badge>
                                  ))
                                ) : (
                                  <span className="text-xs text-[var(--md-sys-color-on-surface-variant)]">None</span>
                                )}
                              </div>
                            </div>
                            
                            <div>
                              <div className="text-xs mb-1 font-medium text-surface-foreground">
                                Manual Forbidden Actions ({profile.manual_forbidden_actions?.length || 0})
                              </div>
                              <div className="flex flex-wrap gap-2 max-h-20 overflow-auto pr-1">
                                {profile.manual_forbidden_actions?.length ? (
                                  profile.manual_forbidden_actions.map((action, idx) => (
                                    <Badge key={`profile-forbidden-${idx}`} className="bg-rose-50 text-rose-700 rounded-md border-rose-200">
                                      {action}
                                    </Badge>
                                  ))
                                ) : (
                                  <span className="text-xs text-[var(--md-sys-color-on-surface-variant)]">None</span>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          {/* Auto-Detected Behavior Section */}
                          {(profile.auto_common_hours || profile.auto_common_ips || profile.auto_common_actions) && (
                            <div className="space-y-3 border-t border-outline-variant pt-3">
                              <div className="text-xs font-semibold text-surface-foreground uppercase tracking-wide flex items-center gap-1">
                                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                                Auto-Detected Patterns
                              </div>
                              
                              {profile.auto_common_hours && profile.auto_common_hours.length > 0 && (
                                <div>
                                  <div className="text-xs mb-1 font-medium text-surface-foreground">
                                    Common Active Hours ({profile.auto_common_hours.length})
                                  </div>
                                  <div className="flex flex-wrap gap-2 max-h-20 overflow-auto pr-1">
                                    {profile.auto_common_hours.map((hour, idx) => (
                                      <Badge key={`auto-hour-${idx}`} className="bg-blue-50 text-blue-700 rounded-md border-blue-200">
                                        {hour}:00
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              {profile.auto_common_ips && profile.auto_common_ips.length > 0 && (
                                <div>
                                  <div className="text-xs mb-1 font-medium text-surface-foreground">
                                    Common IPs ({profile.auto_common_ips.length})
                                  </div>
                                  <div className="flex flex-wrap gap-2 max-h-20 overflow-auto pr-1">
                                    {profile.auto_common_ips.map((ip, idx) => (
                                      <Badge key={`auto-ip-${idx}`} className="bg-blue-50 text-blue-700 rounded-md border-blue-200">
                                        {ip}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              {profile.auto_common_actions && profile.auto_common_actions.length > 0 && (
                                <div>
                                  <div className="text-xs mb-1 font-medium text-surface-foreground">
                                    Common Actions ({profile.auto_common_actions.length})
                                  </div>
                                  <div className="flex flex-wrap gap-2 max-h-20 overflow-auto pr-1">
                                    {profile.auto_common_actions.map((action, idx) => (
                                      <Badge key={`auto-action-${idx}`} className="bg-blue-50 text-blue-700 rounded-md border-blue-200">
                                        {action}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-xs text-[var(--md-sys-color-on-surface-variant)]">
                          Loading profile...
                        </div>
                      )}
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
              <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-outline-variant flex-shrink-0">
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


