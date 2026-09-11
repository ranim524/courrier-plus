import axios from "axios"

const TOKEN_KEY = "courrier_admin_token"

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// An admin JWT expires after JWT_EXPIRATION_MINUTES (60 min default) --
// without this, `isAuthenticated` in useAuth.tsx only checks that *a*
// token string exists, so ProtectedRoute keeps rendering the admin UI and
// every call just fails with a raw 401 in place instead of sending the
// admin back to log in again.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAdminRoute = window.location.pathname.startsWith("/admin")
    const isLoginPage = window.location.pathname === "/admin/login"
    if (axios.isAxiosError(error) && error.response?.status === 401 && isAdminRoute && !isLoginPage) {
      localStorage.removeItem(TOKEN_KEY)
      window.location.href = "/admin/login"
    }
    return Promise.reject(error)
  },
)

export interface ApiErrorShape {
  detail: string
}

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as ApiErrorShape | undefined)?.detail
    if (detail) return detail
    if (error.response?.status === 429) return "Trop de requêtes, veuillez réessayer dans un instant."
  }
  return "Une erreur inattendue est survenue. Veuillez réessayer."
}
