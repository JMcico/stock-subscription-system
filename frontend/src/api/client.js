/**
 * API base: empty string uses Vite dev proxy (`/api` → Django). Override with VITE_API_BASE_URL.
 */
export function getApiBase() {
  const base = import.meta.env.VITE_API_BASE_URL
  return base === undefined || base === '' ? '' : base.replace(/\/$/, '')
}

export async function apiFetch(path, options = {}) {
  const base = getApiBase()
  const url = `${base}${path.startsWith('/') ? path : `/${path}`}`
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  return fetch(url, { ...options, headers })
}
