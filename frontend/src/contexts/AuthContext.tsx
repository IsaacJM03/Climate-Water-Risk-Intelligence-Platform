import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../api/client'
import type { DecodedToken } from '../types'

const TOKEN_KEY = 'cwrip_token'

function decodeToken(token: string): DecodedToken | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return {
      userId: payload.sub,
      orgId: payload.org,
      role: payload.role,
    }
  } catch {
    return null
  }
}

interface AuthContextValue {
  user: DecodedToken | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<DecodedToken | null>(() => {
    const t = localStorage.getItem(TOKEN_KEY)
    return t ? decodeToken(t) : null
  })
  const navigate = useNavigate()

  useEffect(() => {
    if (token) {
      setUser(decodeToken(token))
    }
  }, [token])

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.login(email, password)
      localStorage.setItem(TOKEN_KEY, response.access_token)
      setToken(response.access_token)
      setUser(decodeToken(response.access_token))
      navigate('/dashboard')
    },
    [navigate],
  )

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
    navigate('/login')
  }, [navigate])

  return (
    <AuthContext.Provider
      value={{ user, token, isAuthenticated: !!token, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
