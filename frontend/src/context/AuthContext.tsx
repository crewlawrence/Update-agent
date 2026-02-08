import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

type User = { userId: string; tenantId: string; email: string }
type AuthState = { user: User | null; token: string | null; loading: boolean }

const AuthContext = createContext<{
  state: AuthState
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string, tenantName: string) => Promise<void>
  logout: () => void
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
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setState({ user: null, token: null, loading: false })
  }, [])

  useEffect(() => {
    const t = localStorage.getItem(TOKEN_KEY)
    const u = localStorage.getItem(USER_KEY)
    if (t && u) {
      try {
        const user = JSON.parse(u) as User
        setState({ token: t, user, loading: false })
      } catch {
        setState({ token: null, user: null, loading: false })
      }
    } else {
      setState((s) => ({ ...s, loading: false }))
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const d = await res.json().catch(() => ({}))
      throw new Error(d.detail || 'Login failed')
    }
    const data = await res.json()
    const user: User = { userId: data.user_id, tenantId: data.tenant_id, email: data.email }
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    setState({ token: data.access_token, user, loading: false })
  }, [])

  const register = useCallback(
    async (email: string, password: string, fullName: string, tenantName: string) => {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName || null, tenant_name: tenantName }),
      })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail || 'Registration failed')
      }
      const data = await res.json()
      const user: User = { userId: data.user_id, tenantId: data.tenant_id, email: data.email }
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      setState({ token: data.access_token, user, loading: false })
    },
    [],
  )

  return (
    <AuthContext.Provider value={{ state, login, register, logout, setToken }}>
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
