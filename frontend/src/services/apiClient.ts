import axios from "axios"

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("courrier_admin_token")
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

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
