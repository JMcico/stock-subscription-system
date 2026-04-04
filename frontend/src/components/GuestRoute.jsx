import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

/** Login / register — redirect to app home if already signed in. */
export default function GuestRoute({ children }) {
  const { isAuthenticated } = useAuth()
  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }
  return children
}
