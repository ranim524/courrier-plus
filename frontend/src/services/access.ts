import { apiClient } from "./apiClient"
import type { AccessLetterView } from "../types/tracking"

export async function viewLetterByToken(token: string): Promise<AccessLetterView> {
  const { data } = await apiClient.get<AccessLetterView>(`/api/access/${encodeURIComponent(token)}`)
  return data
}

export async function markOpened(token: string): Promise<AccessLetterView> {
  const { data } = await apiClient.post<AccessLetterView>(`/api/access/${encodeURIComponent(token)}/open`)
  return data
}

export async function confirmReceipt(token: string): Promise<AccessLetterView> {
  const { data } = await apiClient.post<AccessLetterView>(`/api/access/${encodeURIComponent(token)}/receive`)
  return data
}

export function getDocumentUrl(token: string): string {
  const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000"
  return `${base}/api/access/${encodeURIComponent(token)}/document`
}
