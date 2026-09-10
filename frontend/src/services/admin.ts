import { apiClient } from "./apiClient"
import type { AdminLoginResponse, DashboardStats, EmailEventRead, LetterEventRead, Page } from "../types/admin"
import type { LetterRead, LetterStatus, LetterSummary } from "../types/letter"
import type { PaymentRead } from "../types/payment"

export async function adminLogin(email: string, password: string): Promise<AdminLoginResponse> {
  const { data } = await apiClient.post<AdminLoginResponse>("/api/admin/login", { email, password })
  return data
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/api/admin/dashboard")
  return data
}

export interface ListLettersParams {
  page?: number
  pageSize?: number
  status?: LetterStatus
  search?: string
}

export async function listLetters(params: ListLettersParams): Promise<Page<LetterSummary>> {
  const { data } = await apiClient.get<Page<LetterSummary>>("/api/admin/letters", {
    params: {
      page: params.page ?? 1,
      page_size: params.pageSize ?? 20,
      status: params.status,
      search: params.search,
    },
  })
  return data
}

export async function getLetterDetail(id: string): Promise<LetterRead> {
  const { data } = await apiClient.get<LetterRead>(`/api/admin/letters/${id}`)
  return data
}

export async function getLetterEvents(id: string): Promise<LetterEventRead[]> {
  const { data } = await apiClient.get<LetterEventRead[]>(`/api/admin/letters/${id}/events`)
  return data
}

export async function getLetterEmails(id: string): Promise<EmailEventRead[]> {
  const { data } = await apiClient.get<EmailEventRead[]>(`/api/admin/letters/${id}/emails`)
  return data
}

export async function listPayments(page = 1, pageSize = 20): Promise<Page<PaymentRead>> {
  const { data } = await apiClient.get<Page<PaymentRead>>("/api/admin/payments", {
    params: { page, page_size: pageSize },
  })
  return data
}

export async function listEmails(page = 1, pageSize = 20): Promise<Page<EmailEventRead>> {
  const { data } = await apiClient.get<Page<EmailEventRead>>("/api/admin/emails", {
    params: { page, page_size: pageSize },
  })
  return data
}

export function getLetterDocumentUrl(id: string): string {
  const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000"
  return `${base}/api/admin/letters/${id}/document`
}
