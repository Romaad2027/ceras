import { useEffect, useMemo, useState } from 'react'
import api, { organizationApi } from '../services/api.js'
import { Card, CardHeader, CardContent } from '../components/ui/Card.jsx'
import { Table } from '../components/ui/Table.jsx'
import { Button } from '../components/ui/Button.jsx'
import { Input } from '../components/ui/Input.jsx'
import { Badge } from '../components/ui/Badge.jsx'

const getInitials = (nameOrEmail) => {
  const s = (nameOrEmail || '').trim()
  if (!s) return '–'
  if (s.includes('@')) {
    const [local] = s.split('@')
    if (!local) return s.slice(0, 2).toUpperCase()
    const parts = local.split(/[.\-_ ]+/).filter(Boolean)
    return (parts[0]?.[0] || s[0] || '').toUpperCase() + (parts[1]?.[0] || '').toUpperCase()
  }
  const parts = s.split(/[ ]+/).filter(Boolean)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0]?.[0] || '').toUpperCase() + (parts[1]?.[0] || '').toUpperCase()
}

const colorClasses = [
  'bg-primary-container text-primary-container-foreground',
  'bg-secondary-container text-[var(--md-sys-color-on-secondary-container)]',
  'bg-tertiary-container text-[var(--md-sys-color-on-tertiary-container)]',
  'bg-surface-variant text-[var(--md-sys-color-on-surface-variant)]',
]
const pickColorClass = (seed) => {
  const str = (seed || '').toString()
  let hash = 0
  for (let i = 0; i < str.length; i += 1) {
    hash = (hash << 5) - hash + str.charCodeAt(i)
    hash |= 0
  }
  const idx = Math.abs(hash) % colorClasses.length
  return colorClasses[idx]
}

const formatDateTime = (value) => {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString()
}

const decodeJwt = (token) => {
  if (!token || typeof token !== 'string' || !token.includes('.')) return null
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64.padEnd(base64.length + (4 - (base64.length % 4)) % 4, '=')
    const json = atob(padded)
    return JSON.parse(json)
  } catch (_) {
    return null
  }
}

export const MembersPage = () => {
  const [members, setMembers] = useState([])
  const [invites, setInvites] = useState([])
  const [loadingMembers, setLoadingMembers] = useState(false)
  const [loadingInvites, setLoadingInvites] = useState(false)
  const [errorMembers, setErrorMembers] = useState('')
  const [errorInvites, setErrorInvites] = useState('')
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('member')
  const [sendingInvite, setSendingInvite] = useState(false)
  const [revokingId, setRevokingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [toast, setToast] = useState(null)

  const showToast = (type, message) => {
    setToast({ type, message })
    window.clearTimeout(showToast._t)
    showToast._t = window.setTimeout(() => setToast(null), 2200)
  }

  const token = (typeof window !== 'undefined' && window.localStorage && localStorage.getItem('token')) || ''
  const claims = useMemo(() => decodeJwt(token), [token])
  const currentUserId = claims?.sub || claims?.user_id || claims?.uid || null
  const currentUserEmail = claims?.email || claims?.preferred_username || null
  const you = useMemo(() => {
    if (!members || members.length === 0) return null
    const byId = members.find(
      (m) => String(m?.id || m?.user_id || '') && String(m?.id || m?.user_id) === String(currentUserId || '')
    )
    if (byId) return byId
    if (currentUserEmail) {
      const emailLc = String(currentUserEmail).toLowerCase()
      return members.find((m) => String(m?.email || '').toLowerCase() === emailLc) || null
    }
    return null
  }, [members, currentUserId, currentUserEmail])
  const isAdmin = useMemo(() => {
    const role = (you?.role || you?.user_role || '').toString().toLowerCase()
    return role === 'admin'
  }, [you])

  const fetchMembers = async () => {
    try {
      setLoadingMembers(true)
      setErrorMembers('')
      const data = await organizationApi.listUsers()
      const items = Array.isArray(data) ? data : data?.members || data?.items || []
      setMembers(items)
    } catch (err) {
      setErrorMembers(err?.response?.data?.detail || err?.response?.data?.message || 'Failed to fetch members.')
    } finally {
      setLoadingMembers(false)
    }
  }

  const fetchInvites = async () => {
    try {
      setLoadingInvites(true)
      setErrorInvites('')
      const data = await organizationApi.listInvitations()
      const items = Array.isArray(data) ? data : data?.invitations || data?.items || []
      setInvites(items)
    } catch (err) {
      setErrorInvites(err?.response?.data?.detail || err?.response?.data?.message || 'Failed to fetch invitations.')
    } finally {
      setLoadingInvites(false)
    }
  }

  const handleSendInvite = async (e) => {
    e?.preventDefault?.()
    if (!inviteEmail) return
    try {
      setSendingInvite(true)
      await api.post('/organization/invites', {
        email: inviteEmail,
        role: inviteRole,
      })
      showToast('success', 'Invitation sent')
      setInviteEmail('')
      await fetchInvites()
      setShowInviteForm(false)
    } catch (err) {
      showToast('error', err?.response?.data?.message || 'Failed to send invite')
    } finally {
      setSendingInvite(false)
    }
  }

  const handleRevokeInvite = async (invite) => {
    const id = invite?.id || invite?.invite_id
    if (!id) return
    try {
      setRevokingId(id)
      await api.delete(`/organization/invites/${id}`)
      showToast('success', 'Invitation revoked')
      await fetchInvites()
    } catch (err) {
      showToast('error', err?.response?.data?.message || 'Failed to revoke invite')
    } finally {
      setRevokingId(null)
    }
  }

  const handleDeleteMember = async (member) => {
    const id = member?.id || member?.user_id
    if (!id) {
      showToast('error', 'User ID not found.')
      return
    }
    // prevent self-removal in UI as well
    const isSelf =
      (currentUserId && String(id) === String(currentUserId)) ||
      (!!currentUserEmail &&
        String(member?.email || '').toLowerCase() === String(currentUserEmail).toLowerCase())
    if (isSelf) {
      showToast('error', 'You cannot remove yourself.')
      return
    }
    const label = member?.email || member?.name || 'this user'
    const ok = window.confirm(`Remove ${label} from the organization?`)
    if (!ok) return
    try {
      setDeletingId(id)
      await organizationApi.removeUser(id)
      showToast('success', `Removed ${member?.email || 'user'}`)
      await fetchMembers()
    } catch (err) {
      showToast('error', err?.response?.data?.detail || err?.response?.data?.message || 'Failed to remove user.')
    } finally {
      setDeletingId(null)
    }
  }

  useEffect(() => {
    let cancelled = false
    const init = async () => {
      try {
        await Promise.all([fetchMembers(), fetchInvites()])
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

  const memberColumns = useMemo(
    () => [
      {
        header: 'Name',
        accessor: (row) => row.name || row.full_name || row.display_name || row.email || '—',
        cell: (value, row) => {
          const email = row?.email || ''
          const initials = getInitials(row?.name || email)
          const color = pickColorClass(row?.name || email)
          return (
            <div className="flex items-center gap-3">
              <div
                className={[
                  'h-8 w-8 rounded-full flex items-center justify-center text-xs font-semibold',
                  color,
                ].join(' ')}
                title={value}
              >
                {initials}
              </div>
              <div className="flex flex-col">
                <span className="font-medium text-surface-foreground">{value}</span>
                <span className="text-xs text-[var(--md-sys-color-on-surface-variant)]">{email}</span>
              </div>
            </div>
          )
        },
      },
      {
        header: 'Email',
        accessor: (row) => row.email || '—',
      },
      {
        header: 'Role',
        accessor: (row) => row.role || row.user_role || 'member',
        cell: (val) => <Badge variant="default">{(val || '').toString().toUpperCase()}</Badge>,
      },
      {
        header: 'Status',
        accessor: (row) => (row.active || row.enabled || row.is_active ? 'Active' : 'Inactive'),
        cell: (val) => (
          <Badge variant={val === 'Active' ? 'success' : 'default'}>{val}</Badge>
        ),
      },
      {
        header: 'Actions',
        accessor: () => '',
        cell: (_v, row) => {
          const id = row?.id || row?.user_id
          const isSelf =
            (currentUserId && String(id) === String(currentUserId)) ||
            (!!currentUserEmail &&
              String(row?.email || '').toLowerCase() === String(currentUserEmail).toLowerCase())
          const canDelete = isAdmin && !!id && !isSelf
          return (
            <div className="flex items-center gap-2">
              <Button
                variant="danger"
                size="sm"
                disabled={!canDelete}
                isLoading={deletingId === id}
                onClick={() => handleDeleteMember(row)}
                title={
                  !id
                    ? 'Delete not available'
                    : !isAdmin
                    ? 'Only admins can delete members'
                    : isSelf
                    ? 'You cannot remove yourself'
                    : 'Remove user'
                }
              >
                Delete
              </Button>
            </div>
          )
        },
      },
    ],
    [deletingId, isAdmin, currentUserId, currentUserEmail]
  )

  const inviteColumns = useMemo(
    () => [
      {
        header: 'Email',
        accessor: (row) => row.email || row.invitee_email || '—',
      },
      {
        header: 'Sent At',
        accessor: (row) => row.sent_at || row.created_at || row.created || null,
        cell: (val) => <span>{formatDateTime(val)}</span>,
      },
      {
        header: 'Status',
        accessor: (row) => row.status || 'PENDING',
        cell: (val) => <Badge variant="warning">{(val || 'PENDING').toString().toUpperCase()}</Badge>,
      },
      {
        header: 'Actions',
        accessor: () => '',
        cell: (_v, row) => {
          const id = row?.id || row?.invite_id
          return (
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={!id}
                isLoading={revokingId === id}
                onClick={() => handleRevokeInvite(row)}
                title={id ? 'Revoke invitation' : 'Revoke not available'}
              >
                Revoke
              </Button>
            </div>
          )
        },
      },
    ],
    [revokingId]
  )

  return (
    <div className="space-y-6">
      <Card className="shadow-md">
        <CardHeader className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-surface-foreground">Team Members</h2>
          <Button variant="primary" onClick={() => setShowInviteForm((v) => !v)}>
            {showInviteForm ? 'Close' : 'Invite New Member'}
          </Button>
        </CardHeader>
        {showInviteForm && (
          <CardContent>
            <form className="grid grid-cols-1 gap-4 sm:grid-cols-3 items-end" onSubmit={handleSendInvite}>
              <Input
                label="Email"
                type="email"
                placeholder="user@example.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                required
              />
              <div className="w-full">
                <label className="mb-1 block text-sm font-medium text-surface-foreground">Role</label>
                <select
                  className={[
                    'w-full rounded-lg bg-surface-variant text-surface-foreground',
                    'border border-transparent focus:border-primary focus:ring-2 focus:ring-outline-variant focus:outline-none',
                    'px-3 py-2 transition-shadow',
                  ].join(' ')}
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                >
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-2">
                <Button type="submit" variant="primary" isLoading={sendingInvite}>
                  Send Invite
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowInviteForm(false)}
                  disabled={sendingInvite}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        )}
      </Card>

      {toast && (
        <div
          className={[
            'rounded-lg px-4 py-2 text-sm border',
            toast.type === 'success'
              ? 'bg-primary-container text-primary-container-foreground border-outline-variant'
              : 'bg-error-container text-[var(--md-sys-color-on-error-container)] border-outline-variant',
          ].join(' ')}
        >
          {toast.message}
        </div>
      )}

      <Card className="shadow-md">
        <CardHeader>
          <h3 className="text-base font-semibold text-surface-foreground">Active Members</h3>
        </CardHeader>
        <CardContent>
          {loadingMembers && members.length === 0 ? (
            <div className="space-y-3">
              <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
              <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
              <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
            </div>
          ) : (
            <Table
              zebra
              stickyHeader
              columns={memberColumns}
              data={members}
              rowKey={(row, i) => row?.id || row?.user_id || row?.email || i}
              emptyMessage={errorMembers || 'No active members.'}
            />
          )}
        </CardContent>
      </Card>

      <Card className="shadow-md">
        <CardHeader>
          <h3 className="text-base font-semibold text-surface-foreground">Pending Invitations</h3>
        </CardHeader>
        <CardContent>
          {loadingInvites && invites.length === 0 ? (
            <div className="space-y-3">
              <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
              <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
              <div className="h-10 w-full animate-pulse rounded-md bg-[var(--md-sys-color-surface-container-high)]" />
            </div>
          ) : (
            <Table
              zebra
              stickyHeader
              columns={inviteColumns}
              data={invites}
              rowKey={(row, i) => row?.id || row?.invite_id || row?.email || i}
              emptyMessage={errorInvites || 'No pending invitations.'}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default MembersPage


