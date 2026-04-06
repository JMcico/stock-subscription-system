import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

function fmtPrice(v) {
  if (v === null || v === undefined || v === '') return '-'
  const n = Number(v)
  return Number.isFinite(n) ? `$${n.toFixed(4)}` : String(v)
}

function fmtTime(v) {
  if (!v) return 'Never'
  const d = new Date(v)
  return Number.isNaN(d.getTime()) ? '-' : d.toLocaleString()
}

export default function HomePage() {
  const { user, access, logout } = useAuth()
  const [ticker, setTicker] = useState('')
  const [rows, setRows] = useState([])
  const [users, setUsers] = useState([])
  const [searchUser, setSearchUser] = useState('')
  const [ownerDrafts, setOwnerDrafts] = useState({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [sendingAll, setSendingAll] = useState(false)
  const [sendingOwnerId, setSendingOwnerId] = useState(null)
  const [submittingOwnerId, setSubmittingOwnerId] = useState(null)
  const [deletingUserId, setDeletingUserId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError] = useState('')
  const [toast, setToast] = useState(null)

  const isAdmin = Boolean(user?.is_staff)
  const userEmail = user?.email || user?.username || ''

  const ownerGroups = useMemo(() => {
    const q = searchUser.trim().toLowerCase()
    if (!isAdmin) return []
    const subscriptionsByOwner = new Map()
    for (const row of rows) {
      const key = row.owner_id
      if (!subscriptionsByOwner.has(key)) subscriptionsByOwner.set(key, [])
      subscriptionsByOwner.get(key).push(row)
    }
    return users
      .filter((u) => {
        const label = (u.email || u.username || '').toLowerCase()
        return !q || label.includes(q)
      })
      .map((u) => ({
        owner: u.email || u.username,
        ownerId: u.id,
        ownerEmail: u.email || '',
        isStaff: Boolean(u.is_staff),
        subscriptions: subscriptionsByOwner.get(u.id) || [],
      }))
      .sort((a, b) => a.owner.localeCompare(b.owner))
  }, [isAdmin, rows, users, searchUser])

  const authHeaders = useMemo(
    () => ({
      Authorization: `Bearer ${access}`,
    }),
    [access],
  )

  useEffect(() => {
    let timer
    if (toast) {
      timer = setTimeout(() => setToast(null), 2400)
    }
    return () => {
      if (timer) clearTimeout(timer)
    }
  }, [toast])

  async function fetchRows() {
    setLoading(true)
    setError('')
    try {
      const tasks = [apiFetch('/api/subscriptions/', { headers: authHeaders })]
      if (isAdmin) tasks.push(apiFetch('/api/auth/users/', { headers: authHeaders }))
      const [subsRes, usersRes] = await Promise.all(tasks)

      const subsData = await subsRes.json().catch(() => [])
      if (!subsRes.ok) throw new Error('Failed to load subscriptions')
      setRows(Array.isArray(subsData) ? subsData : [])

      if (isAdmin) {
        const usersData = await usersRes.json().catch(() => [])
        if (!usersRes.ok) throw new Error('Failed to load users')
        setUsers(Array.isArray(usersData) ? usersData : [])
      } else {
        setUsers([])
      }
    } catch (e) {
      setError(e.message || 'Failed to load subscriptions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRows()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin])

  async function handleSubscribe(e) {
    e.preventDefault()
    setError('')
    const normalized = ticker.trim().toUpperCase()
    if (!normalized) return
    if (!userEmail) {
      setError('Cannot resolve your login email.')
      return
    }
    setSubmitting(true)
    try {
      const res = await apiFetch('/api/subscriptions/', {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          ticker: normalized,
          subscriber_email: userEmail.toLowerCase(),
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const first = Object.values(data || {}).flat?.()[0]
        throw new Error(typeof first === 'string' ? first : 'Subscribe failed')
      }
      setTicker('')
      setToast({ type: 'success', message: `${normalized} subscribed` })
      await fetchRows()
    } catch (e) {
      setError(e.message || 'Subscribe failed')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleSendNowAll() {
    setSendingAll(true)
    setError('')
    try {
      const res = await apiFetch('/api/subscriptions/send_now/', {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({}),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'Send failed')
      setToast({
        type: 'success',
        message: `Sent ${data.emails_sent || 0} email(s)`,
      })
      await fetchRows()
    } catch (e) {
      setError(e.message || 'Send failed')
      setToast({ type: 'error', message: e.message || 'Send failed' })
    } finally {
      setSendingAll(false)
    }
  }

  function setOwnerDraft(ownerId, value) {
    setOwnerDrafts((prev) => ({ ...prev, [ownerId]: value }))
  }

  async function handleOwnerSubscribe(ownerId, ownerEmail) {
    const normalized = (ownerDrafts[ownerId] || '').trim().toUpperCase()
    if (!normalized) return
    if (!ownerEmail || !ownerEmail.includes('@')) {
      setToast({ type: 'error', message: 'Owner email is missing or invalid' })
      return
    }
    setSubmittingOwnerId(ownerId)
    setError('')
    try {
      const res = await apiFetch('/api/subscriptions/', {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({
          target_owner_id: ownerId,
          ticker: normalized,
          subscriber_email: ownerEmail.toLowerCase(),
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const first = Object.values(data || {}).flat?.()[0]
        throw new Error(typeof first === 'string' ? first : 'Subscribe failed')
      }
      setOwnerDraft(ownerId, '')
      setToast({ type: 'success', message: `${normalized} added for ${ownerEmail}` })
      await fetchRows()
    } catch (e) {
      setError(e.message || 'Subscribe failed')
      setToast({ type: 'error', message: e.message || 'Subscribe failed' })
    } finally {
      setSubmittingOwnerId(null)
    }
  }

  async function handleDelete(id, tickerName) {
    const ok = window.confirm(`Delete subscription for ${tickerName}?`)
    if (!ok) return
    setDeletingId(id)
    setError('')
    try {
      const res = await apiFetch(`/api/subscriptions/${id}/`, {
        method: 'DELETE',
        headers: authHeaders,
      })
      if (!res.ok) throw new Error('Delete failed')
      setToast({ type: 'success', message: `${tickerName} deleted` })
      await fetchRows()
    } catch (e) {
      setError(e.message || 'Delete failed')
      setToast({ type: 'error', message: e.message || 'Delete failed' })
    } finally {
      setDeletingId(null)
    }
  }

  async function handleSendOwner(ownerId) {
    if (!ownerId) return
    setSendingOwnerId(ownerId)
    setError('')
    try {
      const res = await apiFetch(`/api/subscriptions/owners/${ownerId}/send_now/`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({}),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'Send failed')
      setToast({
        type: 'success',
        message: `Owner sent: ${data.emails_sent || 0} email(s)`,
      })
      await fetchRows()
    } catch (e) {
      setError(e.message || 'Send failed')
      setToast({ type: 'error', message: e.message || 'Send failed' })
    } finally {
      setSendingOwnerId(null)
    }
  }

  async function handleDeleteUser(ownerId, ownerLabel) {
    if (!ownerId) return
    const ok = window.confirm(
      `Delete user "${ownerLabel}" and all related subscriptions? This cannot be undone.`,
    )
    if (!ok) return
    setDeletingUserId(ownerId)
    setError('')
    try {
      const res = await apiFetch(`/api/auth/users/${ownerId}/`, {
        method: 'DELETE',
        headers: authHeaders,
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Delete user failed')
      }
      setToast({ type: 'success', message: `User ${ownerLabel} deleted` })
      await fetchRows()
    } catch (e) {
      setError(e.message || 'Delete user failed')
      setToast({ type: 'error', message: e.message || 'Delete user failed' })
    } finally {
      setDeletingUserId(null)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <div>
            <p className="text-sm font-medium text-blue-600">Stock Dashboard</p>
            <h1 className="text-lg font-semibold tracking-tight text-blue-700">Subscriptions</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-blue-50 px-3 py-1 text-sm text-blue-700">
              {userEmail}
              {isAdmin ? ' • Admin' : ''}
            </div>
            <button
              type="button"
              onClick={logout}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium hover:bg-slate-100"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6">
        {!isAdmin ? (
        <section className="mb-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
          <h2 className="mb-3 text-base font-semibold text-blue-700">New Subscription</h2>
          <form onSubmit={handleSubscribe} className="flex flex-col gap-3 sm:flex-row">
            <input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g. AAPL"
              required
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase outline-none ring-blue-500 placeholder:text-slate-400 focus:ring-2 sm:max-w-xs"
            />
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
            >
              {submitting ? (
                <span className="inline-flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                  Subscribing...
                </span>
              ) : (
                'Subscribe'
              )}
            </button>
          </form>
          <p className="mt-2 text-xs text-slate-500">
            Subscriber email is auto-bound to your account: {userEmail}
          </p>
          {error ? <p className="mt-2 text-sm text-rose-600">{error}</p> : null}
        </section>
        ) : null}

        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 sm:px-5">
            <h2 className="text-base font-semibold text-blue-700">Manage Subscriptions</h2>
            {!isAdmin ? (
              <button
                type="button"
                onClick={handleSendNowAll}
                disabled={sendingAll || rows.length === 0}
                className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {sendingAll ? 'Sending...' : 'Send Now'}
              </button>
            ) : null}
          </div>
          {isAdmin ? (
            <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-blue-700">User Management</h3>
                <span className="text-xs text-slate-500">
                  {ownerGroups.length} user(s) matched
                </span>
              </div>
              <input
                value={searchUser}
                onChange={(e) => setSearchUser(e.target.value)}
                placeholder="Search user by owner/email..."
                className="w-full max-w-sm rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none ring-blue-500 focus:ring-2"
              />
            </div>
          ) : null}
          {loading ? (
            <div className="space-y-3 p-4 sm:p-5">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-10 animate-pulse rounded-md bg-slate-100" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              {isAdmin ? (
                <div className="space-y-4 p-4 sm:p-5">
                  {ownerGroups.length === 0 ? (
                    <p className="py-8 text-center text-slate-500">
                      No users/subscriptions matched.
                    </p>
                  ) : (
                    ownerGroups.map((group) => (
                      <div key={`${group.owner}-${group.ownerId}`} className="rounded-lg border border-slate-200 bg-white">
                        <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2">
                          <p className="text-sm font-semibold text-blue-700">{group.owner}</p>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500">
                              {group.subscriptions.length} subscription(s)
                            </span>
                            <button
                              type="button"
                              onClick={() => handleSendOwner(group.ownerId)}
                              disabled={!group.ownerId || sendingOwnerId === group.ownerId}
                              className="rounded-md bg-blue-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
                            >
                              {sendingOwnerId === group.ownerId ? 'Sending...' : 'Send Now'}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteUser(group.ownerId, group.owner)}
                              disabled={
                                !group.ownerId ||
                                deletingUserId === group.ownerId ||
                                group.ownerId === user?.id
                              }
                              className="rounded-md border border-rose-300 px-2.5 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50 disabled:opacity-60"
                              title={group.ownerId === user?.id ? 'Cannot delete current admin user' : ''}
                            >
                              {deletingUserId === group.ownerId ? 'Deleting...' : 'Delete User'}
                            </button>
                          </div>
                        </div>
                        <div className="border-b border-slate-100 bg-slate-50 px-3 py-2">
                          <div className="flex flex-col gap-2 sm:flex-row">
                            <input
                              value={ownerDrafts[group.ownerId] || ''}
                              onChange={(e) =>
                                setOwnerDraft(group.ownerId, e.target.value.toUpperCase())
                              }
                              placeholder={`New subscription for ${group.owner}`}
                              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm uppercase outline-none ring-blue-500 focus:ring-2 sm:max-w-xs"
                            />
                            <button
                              type="button"
                              onClick={() =>
                                handleOwnerSubscribe(group.ownerId, group.ownerEmail)
                              }
                              disabled={submittingOwnerId === group.ownerId}
                              className="rounded-md bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
                            >
                              {submittingOwnerId === group.ownerId
                                ? 'Adding...'
                                : 'New Subscription'}
                            </button>
                          </div>
                        </div>
                        <table className="min-w-full text-left text-sm">
                          <thead className="bg-slate-50 text-slate-600">
                            <tr>
                              <th className="px-3 py-2 font-medium">Ticker</th>
                              <th className="px-3 py-2 font-medium">Current Price</th>
                              <th className="px-3 py-2 font-medium">Last Notified Price</th>
                              <th className="px-3 py-2 font-medium">Status/Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {group.subscriptions.map((row) => (
                              <tr key={row.id} className="border-t border-slate-100">
                                <td className="px-3 py-2 font-semibold text-slate-900">
                                  {row.ticker}
                                </td>
                                <td className="px-3 py-2">{fmtPrice(row.current_price)}</td>
                                <td className="px-3 py-2">{fmtPrice(row.last_notified_price)}</td>
                                <td className="px-3 py-2">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">
                                      {fmtTime(row.last_notified_time)}
                                    </span>
                                    <button
                                      type="button"
                                      onClick={() => handleDelete(row.id, row.ticker)}
                                      disabled={deletingId === row.id}
                                      className="rounded-md border border-rose-300 px-2.5 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 disabled:opacity-60"
                                    >
                                      Delete
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ))
                  )}
                </div>
              ) : null}
              {!isAdmin ? (
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Ticker</th>
                    <th className="px-4 py-3 font-medium">Current Price</th>
                    <th className="px-4 py-3 font-medium">Last Notified Price</th>
                    <th className="px-4 py-3 font-medium">Status/Action</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 ? (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-4 py-8 text-center text-slate-500"
                      >
                        No subscriptions yet.
                      </td>
                    </tr>
                  ) : (
                    rows.map((row) => (
                      <tr key={row.id} className="border-t border-slate-100">
                        <td className="px-4 py-3 font-semibold text-slate-900">{row.ticker}</td>
                        <td className="px-4 py-3">{fmtPrice(row.current_price)}</td>
                        <td className="px-4 py-3">{fmtPrice(row.last_notified_price)}</td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">
                              {fmtTime(row.last_notified_time)}
                            </span>
                            <button
                              type="button"
                              onClick={() => handleDelete(row.id, row.ticker)}
                              disabled={deletingId === row.id}
                              className="rounded-md border border-rose-300 px-2.5 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 disabled:opacity-60"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
              ) : null}
            </div>
          )}
        </section>
      </main>

      {toast ? (
        <div className="fixed bottom-4 right-4 z-50">
          <div
            className={`rounded-lg px-4 py-2 text-sm font-medium text-white shadow-lg ${
              toast.type === 'error' ? 'bg-rose-600' : 'bg-blue-600'
            }`}
          >
            {toast.message}
          </div>
        </div>
      ) : null}
    </div>
  )
}
