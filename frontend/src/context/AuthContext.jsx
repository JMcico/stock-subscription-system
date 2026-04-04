import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'

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

  const persistSession = useCallback((a, r, u) => {
    if (a) localStorage.setItem(STORAGE_ACCESS, a)
    else localStorage.removeItem(STORAGE_ACCESS)
    if (r) localStorage.setItem(STORAGE_REFRESH, r)
    else localStorage.removeItem(STORAGE_REFRESH)
    if (u) {
      localStorage.setItem(STORAGE_USER, JSON.stringify(u))
      setUser(u)
    } else {
      localStorage.removeItem(STORAGE_USER)
      setUser(null)
    }
    setAccess(a || null)
    setRefresh(r || null)
  }, [])

  const login = useCallback(
    async (email, password) => {
      const { apiFetch } = await import('../api/client.js')
      const res = await apiFetch('/api/auth/token/', {
        method: 'POST',
        body: JSON.stringify({
          username: email.trim().toLowerCase(),
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
      const u = {
        username: email.trim().toLowerCase(),
        email: email.trim().toLowerCase(),
      }
      persistSession(data.access, data.refresh, u)
    },
    [persistSession],
  )

  const register = useCallback(
    async (email, password) => {
      const { apiFetch } = await import('../api/client.js')
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
