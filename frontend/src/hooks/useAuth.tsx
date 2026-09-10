import { createContext, useContext, useMemo, useState, type ReactNode } from "react"

const TOKEN_KEY = "courrier_admin_token"

interface AuthContextValue {
  isAuthenticated: boolean
  login: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: !!token,
      login: (newToken: string) => {
        localStorage.setItem(TOKEN_KEY, newToken)
        setToken(newToken)
      },
      logout: () => {
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
      },
    }),
    [token],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
