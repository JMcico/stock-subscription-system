/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'
import { apiFetch } from '../api/client.js'

const STORAGE_ACCESS = 'stockapp_access'
const STORAGE_REFRESH = 'stockapp_refresh'
const STORAGE_USER = 'stockapp_user'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [access, setAccess] = useState(() =>
    localStorage.getItem(STORAGE_ACCESS),
  )
  const [refresh, setRefresh] = useState(() =>
    localStorage.getItem(STORAGE_REFRESH),
  )
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_USER)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })

  const persistSession = useCallback((a, r, u, opts = {}) => {
    const persist = opts.persist !== false
    if (persist) {
      if (a) localStorage.setItem(STORAGE_ACCESS, a)
      else localStorage.removeItem(STORAGE_ACCESS)
      if (r) localStorage.setItem(STORAGE_REFRESH, r)
      else localStorage.removeItem(STORAGE_REFRESH)
      if (u) localStorage.setItem(STORAGE_USER, JSON.stringify(u))
      else localStorage.removeItem(STORAGE_USER)
    } else {
      localStorage.removeItem(STORAGE_ACCESS)
      localStorage.removeItem(STORAGE_REFRESH)
      localStorage.removeItem(STORAGE_USER)
    }
    if (u) {
      setUser(u)
    } else {
      setUser(null)
    }
    setAccess(a || null)
    setRefresh(r || null)
  }, [])

  const login = useCallback(
    async (username, password) => {
      const res = await apiFetch('/api/auth/token/', {
        method: 'POST',
        body: JSON.stringify({
          username: (username || '').trim(),
          password,
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        let msg = 'Login failed'
        if (typeof data.detail === 'string') msg = data.detail
        else if (Array.isArray(data.detail)) msg = data.detail.map(String).join(' ')
        else if (data.non_field_errors?.length) msg = data.non_field_errors.join(' ')
        else if (typeof data === 'object') {
          const first = Object.values(data).flat()[0]
          if (typeof first === 'string') msg = first
        }
        throw new Error(msg)
      }
      const meRes = await apiFetch('/api/auth/me/', {
        headers: {
          Authorization: `Bearer ${data.access}`,
        },
      })
      const meData = await meRes.json().catch(() => ({}))
      const u = meRes.ok
        ? meData
        : {
            username: (username || '').trim(),
            email: (username || '').trim(),
            is_staff: false,
          }
      // Admin session is memory-only: do not persist tokens in browser storage.
      persistSession(data.access, data.refresh, u, {
        persist: !u?.is_staff,
      })
    },
    [persistSession],
  )

  const register = useCallback(
    async (email, password) => {
      const res = await apiFetch('/api/auth/register/', {
        method: 'POST',
        body: JSON.stringify({
          username: email.trim().toLowerCase(),
          password,
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const err = new Error('Registration failed')
        err.fieldErrors = data
        throw err
      }
      persistSession(data.access, data.refresh, data.user)
    },
    [persistSession],
  )

  const logout = useCallback(() => {
    persistSession(null, null, null)
  }, [persistSession])

  const value = useMemo(
    () => ({
      access,
      refresh,
      user,
      isAuthenticated: Boolean(access),
      login,
      register,
      logout,
    }),
    [access, refresh, user, login, register, logout],
  )

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
