import { useAuth } from '../context/AuthContext.jsx'

export default function HomePage() {
  const { user, logout } = useAuth()

  return (
    <div className="auth-shell">
      <div className="auth-card" style={{ maxWidth: '28rem' }}>
        <h1 className="auth-title">Stock Subscription</h1>
        <p className="auth-hint">
          Signed in as <strong>{user?.email || user?.username}</strong>
          {user?.is_staff ? (
            <span className="auth-badge"> Admin</span>
          ) : null}
        </p>
        <p className="auth-hint">
          Subscription UI will live here (Phase B+). You can sign out to test
          the login gate.
        </p>
        <button type="button" className="auth-submit" onClick={() => logout()}>
          Sign out
        </button>
      </div>
    </div>
  )
}
