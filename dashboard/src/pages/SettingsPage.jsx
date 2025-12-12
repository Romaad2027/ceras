import { useState, useEffect } from 'react'
import api, { cloudAccountsApi } from '../services/api.js'
import { Card, CardContent, CardHeader } from '../components/ui/Card.jsx'
import { Button } from '../components/ui/Button.jsx'
import { Badge } from '../components/ui/Badge.jsx'

export const SettingsPage = () => {
  const [accounts, setAccounts] = useState([])
  const [accLoading, setAccLoading] = useState(false)
  const [accError, setAccError] = useState('')

  const [modalOpen, setModalOpen] = useState(false)
  const [step, setStep] = useState(1)
  const [provider, setProvider] = useState('')
  const [form, setForm] = useState({
    name: '',
    region: '',
    aws_access_key_id: '',
    aws_secret_access_key: '',
    azure_tenant_id: '',
    azure_client_id: '',
    azure_client_secret: '',
    azure_subscription_id: '',
  })
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteLoading, setInviteLoading] = useState(false)
  const [inviteMsg, setInviteMsg] = useState('')
  const [inviteErr, setInviteErr] = useState('')

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    setAccError('')
    setAccLoading(true)
    try {
      const data = await cloudAccountsApi.list()
      const items = Array.isArray(data) ? data : data?.items || []
      setAccounts(items)
    } catch (err) {
      setAccError(err?.response?.data?.message || 'Failed to load cloud accounts.')
    } finally {
      setAccLoading(false)
    }
  }

  const sendInvite = async (e) => {
    e.preventDefault()
    setInviteMsg('')
    setInviteErr('')
    setInviteLoading(true)
    try {
      await api.post('/organization/invites', { email: inviteEmail })
      setInviteMsg('Invite sent.')
      setInviteEmail('')
    } catch (err) {
      setInviteErr(err?.response?.data?.message || 'Failed to send invite.')
    } finally {
      setInviteLoading(false)
    }
  }

  const resetModal = () => {
    setModalOpen(false)
    setStep(1)
    setProvider('')
    setForm({
      name: '',
      region: '',
      aws_access_key_id: '',
      aws_secret_access_key: '',
      azure_tenant_id: '',
      azure_client_id: '',
      azure_client_secret: '',
      azure_subscription_id: '',
    })
  }

  const onSaveAccount = async () => {
    setSaving(true)
    try {
      const payload =
        provider === 'AWS'
          ? {
              provider: 'AWS',
              name: form.name,
              region: form.region,
              credentials: {
                accessKeyId: form.aws_access_key_id,
                secretAccessKey: form.aws_secret_access_key,
              },
            }
          : {
              provider: 'AZURE',
              name: form.name,
              credentials: {
                tenantId: form.azure_tenant_id,
                clientId: form.azure_client_id,
                clientSecret: form.azure_client_secret,
                subscriptionId: form.azure_subscription_id,
              },
            }
      await cloudAccountsApi.create(payload)
      resetModal()
      await loadAccounts()
    } catch (err) {
      alert(err?.response?.data?.message || 'Failed to connect account.')
    } finally {
      setSaving(false)
    }
  }

  const onDisconnect = async (id) => {
    if (!id) return
    const confirm = window.confirm('Disconnect this cloud account?')
    if (!confirm) return
    setDeletingId(id)
    try {
      await cloudAccountsApi.remove(id)
      await loadAccounts()
    } catch (err) {
      alert(err?.response?.data?.message || 'Failed to disconnect account.')
    } finally {
      setDeletingId(null)
    }
  }

  const providerBadge = (value) => {
    const p = (value || '').toString().toUpperCase()
    if (p === 'AWS') return <Badge variant="warning">AWS</Badge>
    if (p === 'AZURE') return <Badge variant="info">Azure</Badge>
    return <Badge>{p || '—'}</Badge>
  }

  const statusBadge = (value) => {
    const s = (value || '').toString().toUpperCase()
    if (s.includes('ERROR') || s.includes('DISCONNECTED')) return <Badge variant="error">{s}</Badge>
    if (s.includes('PENDING') || s.includes('CONNECTING')) return <Badge variant="warning">{s}</Badge>
    return <Badge variant="success">{s || 'CONNECTED'}</Badge>
  }

  return (
    <div className="space-y-6">
      <Card className="shadow-md">
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Cloud Integrations</h2>
          <div className="flex items-center gap-2">
            <Button onClick={() => { setModalOpen(true); setStep(1) }} variant="primary">Connect New</Button>
            <Button onClick={loadAccounts} isLoading={accLoading} variant="secondary">Refresh</Button>
          </div>
        </CardHeader>
        <CardContent>
          {accError && <div className="mb-3 text-sm text-error">{accError}</div>}
          {accounts.length === 0 && !accLoading ? (
            <div className="text-sm text-[var(--md-sys-color-on-surface-variant)]">No cloud accounts connected yet.</div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {accounts.map((acc) => {
                const id = acc.id || acc.uuid
                const prov = (acc.provider || '').toString().toUpperCase()
                const name = acc.name || (prov ? `${prov} Account` : 'Cloud Account')
                const region = acc.region || acc.location || '—'
                const status = (acc.status || 'CONNECTED').toString().toUpperCase()
                return (
                  <Card key={id || name}>
                    <CardContent className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          {providerBadge(prov)}
                          <span className="text-sm text-[var(--md-sys-color-on-surface-variant)]">{region}</span>
                        </div>
                        <div className="mt-2 text-base font-semibold">{name}</div>
                        <div className="mt-2">{statusBadge(status)}</div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <Button
                          variant="danger"
                          size="sm"
                          disabled={!id || deletingId === id}
                          isLoading={deletingId === id}
                          onClick={() => onDisconnect(id)}
                        >
                          Disconnect
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="bg-[var(--md-sys-color-surface-container-lowest)] border border-outline-variant rounded-lg p-4 md:p-6 shadow-md">
        <h2 className="text-lg font-semibold mb-3">Invite Users</h2>
        <form onSubmit={sendInvite} className="grid gap-3 max-w-md" autoComplete="off">
          <div>
            <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">Email</label>
            <input
              className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
              type="email"
              placeholder="user@example.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              autoComplete="off"
              required
            />
          </div>
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={inviteLoading}
              className="inline-flex items-center rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:brightness-95 disabled:opacity-70"
            >
              {inviteLoading ? 'Sending…' : 'Send Invite'}
            </button>
            {inviteMsg && <div className="text-sm text-primary">{inviteMsg}</div>}
            {inviteErr && <div className="text-sm text-error">{inviteErr}</div>}
          </div>
        </form>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={resetModal} />
          <div className="relative z-10 w-full max-w-lg rounded-xl border border-outline-variant bg-[var(--md-sys-color-surface-container-lowest)] shadow-xl">
            <div className="px-6 py-4 border-b border-outline-variant rounded-t-xl">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Connect Cloud Account</h3>
                <button onClick={resetModal} className="text-sm text-[var(--md-sys-color-on-surface-variant)] hover:underline">Close</button>
              </div>
              <div className="mt-2 flex items-center gap-2 text-xs text-[var(--md-sys-color-on-surface-variant)]">
                <span className={step >= 1 ? 'font-medium text-surface-foreground' : ''}>1. Provider</span>
                <span>›</span>
                <span className={step >= 2 ? 'font-medium text-surface-foreground' : ''}>2. Credentials</span>
                <span>›</span>
                <span className={step >= 3 ? 'font-medium text-surface-foreground' : ''}>3. Save</span>
              </div>
            </div>
            <div className="p-6">
              {step === 1 && (
                <div className="space-y-4">
                  <div className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Choose a cloud provider:</div>
                  <div className="flex items-center gap-3">
                    <Button
                      variant={provider === 'AWS' ? 'primary' : 'secondary'}
                      onClick={() => setProvider('AWS')}
                    >
                      AWS
                    </Button>
                    <Button
                      variant={provider === 'AZURE' ? 'primary' : 'secondary'}
                      onClick={() => setProvider('AZURE')}
                    >
                      Azure
                    </Button>
                  </div>
                </div>
              )}
              {step === 2 && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">Account Name</label>
                    <input
                      className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
                      type="text"
                      placeholder={provider === 'AWS' ? 'Prod AWS' : 'Azure Subscription'}
                      value={form.name}
                      onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))}
                      required
                    />
                  </div>
                  {provider === 'AWS' && (
                    <>
                      <div className="grid md:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">AWS Access Key ID</label>
                          <input
                            className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
                            type="text"
                            placeholder="AKIA..."
                            value={form.aws_access_key_id}
                            onChange={(e) => setForm((s) => ({ ...s, aws_access_key_id: e.target.value }))}
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">AWS Secret Access Key</label>
                          <input
                            className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
                            type="password"
                            placeholder="••••••••"
                            value={form.aws_secret_access_key}
                            onChange={(e) => setForm((s) => ({ ...s, aws_secret_access_key: e.target.value }))}
                            required
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">Region</label>
                        <input
                          className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
                          type="text"
                          placeholder="us-east-1"
                          value={form.region}
                          onChange={(e) => setForm((s) => ({ ...s, region: e.target.value }))}
                          required
                        />
                      </div>
                    </>
                  )}
                  {provider === 'AZURE' && (
                    <div className="grid md:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">Tenant ID</label>
                        <input
                          className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
                          type="text"
                          placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                          value={form.azure_tenant_id}
                          onChange={(e) => setForm((s) => ({ ...s, azure_tenant_id: e.target.value }))}
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">Client ID</label>
                        <input
                          className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
                          type="text"
                          value={form.azure_client_id}
                          onChange={(e) => setForm((s) => ({ ...s, azure_client_id: e.target.value }))}
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">Client Secret</label>
                        <input
                          className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
                          type="password"
                          value={form.azure_client_secret}
                          onChange={(e) => setForm((s) => ({ ...s, azure_client_secret: e.target.value }))}
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--md-sys-color-on-surface-variant)] mb-1">Subscription ID</label>
                        <input
                          className="w-full rounded-md bg-surface-variant border border-outline-variant px-3 py-2 text-sm outline-none text-surface-foreground"
                          type="text"
                          value={form.azure_subscription_id}
                          onChange={(e) => setForm((s) => ({ ...s, azure_subscription_id: e.target.value }))}
                          required
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
              {step === 3 && (
                <div className="space-y-3 text-sm">
                  <div className="text-[var(--md-sys-color-on-surface-variant)]">Review and confirm:</div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="text-[var(--md-sys-color-on-surface-variant)]">Provider</div>
                    <div className="font-medium">{provider || '—'}</div>
                    <div className="text-[var(--md-sys-color-on-surface-variant)]">Name</div>
                    <div className="font-medium">{form.name || '—'}</div>
                    {provider === 'AWS' && (
                      <>
                        <div className="text-[var(--md-sys-color-on-surface-variant)]">Region</div>
                        <div className="font-medium">{form.region || '—'}</div>
                      </>
                    )}
                  </div>
                  <div className="text-xs text-[var(--md-sys-color-on-surface-variant)]">
                    Credentials will be sent securely to validate and store integration.
                  </div>
                </div>
              )}
            </div>
            <div className="px-6 py-4 border-t border-outline-variant rounded-b-xl flex items-center justify-between">
              <div className="text-xs text-[var(--md-sys-color-on-surface-variant)]">Step {step} of 3</div>
              <div className="flex items-center gap-2">
                {step > 1 && (
                  <Button variant="secondary" onClick={() => setStep((s) => Math.max(1, s - 1))}>Back</Button>
                )}
                {step < 3 && (
                  <Button
                    onClick={() => setStep((s) => Math.min(3, s + 1))}
                    disabled={
                      (step === 1 && !provider) ||
                      (step === 2 &&
                        (!form.name ||
                          (provider === 'AWS' && (!form.aws_access_key_id || !form.aws_secret_access_key || !form.region)) ||
                          (provider === 'AZURE' && (!form.azure_tenant_id || !form.azure_client_id || !form.azure_client_secret || !form.azure_subscription_id))
                        ))
                    }
                  >
                    Next
                  </Button>
                )}
                {step === 3 && (
                  <Button onClick={onSaveAccount} isLoading={saving} disabled={saving || !provider || !form.name}>Save</Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

