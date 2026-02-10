import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

type User = { userId: string; tenantId: string; email: string }
type AuthState = { user: User | null; token: string | null; loading: boolean }

const AuthContext = createContext<{
  state: AuthState
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string, tenantName: string) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<boolean>
  setToken: (token: string | null) => void
} | null>(null)

const TOKEN_KEY = 'agent_access_token'
const USER_KEY = 'agent_user'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    loading: true,
  })

  const setToken = useCallback((token: string | null) => {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
    setState((s) => ({ ...s, token }))
  }, [])

  const logout = useCallback(() => {
    fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => {})
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setState({ user: null, token: null, loading: false })
  }, [])

  // Restore session from HttpOnly refresh cookie only (no refresh token in localStorage)
  useEffect(() => {
    let cancelled = false
    fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' })
      .then((res) => {
        if (cancelled) return null
        if (!res.ok) {
          localStorage.removeItem(TOKEN_KEY)
          localStorage.removeItem(USER_KEY)
          setState({ user: null, token: null, loading: false })
          return null
        }
        return res.json()
      })
      .then((data) => {
        if (cancelled || !data?.access_token) return
        const user: User = { userId: data.user_id, tenantId: data.tenant_id, email: data.email }
        localStorage.setItem(TOKEN_KEY, data.access_token)
        localStorage.setItem(USER_KEY, JSON.stringify(user))
        setState({ token: data.access_token, user, loading: false })
      })
      .catch(() => setState((s) => ({ ...s, loading: false })))
      .finally(() => {
        if (!cancelled) setState((s) => ({ ...s, loading: false }))
      })
    return () => { cancelled = true }
  }, [])

  const refreshAccessToken = useCallback(async (): Promise<boolean> => {
    try {
      const res = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        logout()
        return false
      }
      const user: User = { userId: data.user_id, tenantId: data.tenant_id, email: data.email }
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      setState({ token: data.access_token, user, loading: false })
      return true
    } catch {
      return false
    }
  }, [logout])

  const login = useCallback(async (email: string, password: string) => {
    let res: Response
    try {
      res = await fetch('/api/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
    } catch {
      throw new Error('Cannot reach server. Is the backend running?')
    }
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const msg = Array.isArray(data.detail)
        ? (data.detail as { msg?: string }[]).map((e) => e.msg || '').filter(Boolean).join('. ') || 'Invalid input'
        : typeof data.detail === 'string'
          ? data.detail
          : 'Login failed'
      throw new Error(msg)
    }
    const user: User = { userId: data.user_id, tenantId: data.tenant_id, email: data.email }
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    setState({ token: data.access_token, user, loading: false })
  }, [])

  const register = useCallback(
    async (email: string, password: string, fullName: string, tenantName: string) => {
      let res: Response
      try {
        res = await fetch('/api/auth/register', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, full_name: fullName || null, tenant_name: tenantName }),
        })
      } catch {
        throw new Error('Cannot reach server. Is the backend running?')
      }
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const msg = Array.isArray(data.detail)
          ? (data.detail as { msg?: string }[]).map((e) => e.msg || '').filter(Boolean).join('. ') || 'Invalid input'
          : typeof data.detail === 'string'
            ? data.detail
            : 'Registration failed'
        throw new Error(msg)
      }
      const user: User = { userId: data.user_id, tenantId: data.tenant_id, email: data.email }
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      setState({ token: data.access_token, user, loading: false })
    },
    [],
  )

  return (
    <AuthContext.Provider value={{ state, login, register, logout, refreshAccessToken, setToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function authHeaders(): HeadersInit {
  const t = localStorage.getItem(TOKEN_KEY)
  return t ? { Authorization: `Bearer ${t}` } : {}
}
