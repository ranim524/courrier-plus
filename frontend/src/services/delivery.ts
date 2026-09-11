import { apiClient } from "./apiClient"
import type { Page } from "../types/admin"
import type {
  DeliveryAgentRead,
  DeliveryFailureReason,
  DeliveryOrderRead,
  DeliveryOrderSummary,
  DeliveryProviderRead,
  DeliveryStatus,
} from "../types/delivery"

export interface ListDeliveriesParams {
  page?: number
  pageSize?: number
  status?: DeliveryStatus
  providerId?: string
  courierId?: string
  search?: string
}

export async function listDeliveries(params: ListDeliveriesParams): Promise<Page<DeliveryOrderSummary>> {
  const { data } = await apiClient.get<Page<DeliveryOrderSummary>>("/api/admin/deliveries", {
    params: {
      page: params.page ?? 1,
      page_size: params.pageSize ?? 20,
      status: params.status,
      provider_id: params.providerId,
      courier_id: params.courierId,
      search: params.search,
    },
  })
  return data
}

export async function getDelivery(id: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.get<DeliveryOrderRead>(`/api/admin/deliveries/${id}`)
  return data
}

export async function assignCourier(id: string, agentId: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.post<DeliveryOrderRead>(`/api/admin/deliveries/${id}/assign`, { agent_id: agentId })
  return data
}

export async function markPickedUp(id: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.post<DeliveryOrderRead>(`/api/admin/deliveries/${id}/pickup`)
  return data
}

export async function markInTransit(id: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.post<DeliveryOrderRead>(`/api/admin/deliveries/${id}/in-transit`)
  return data
}

export async function markOutForDelivery(id: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.post<DeliveryOrderRead>(`/api/admin/deliveries/${id}/out-for-delivery`)
  return data
}

export async function confirmDelivery(id: string, notes?: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.post<DeliveryOrderRead>(`/api/admin/deliveries/${id}/confirm-delivery`, { notes })
  return data
}

export async function markFailed(id: string, reason: DeliveryFailureReason, notes?: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.post<DeliveryOrderRead>(`/api/admin/deliveries/${id}/fail`, { reason, notes })
  return data
}

export async function retryDelivery(id: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.post<DeliveryOrderRead>(`/api/admin/deliveries/${id}/retry`)
  return data
}

export async function returnToSender(id: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.post<DeliveryOrderRead>(`/api/admin/deliveries/${id}/return`)
  return data
}

export async function cancelDelivery(id: string): Promise<DeliveryOrderRead> {
  const { data } = await apiClient.post<DeliveryOrderRead>(`/api/admin/deliveries/${id}/cancel`)
  return data
}

export async function listProviders(): Promise<DeliveryProviderRead[]> {
  const { data } = await apiClient.get<DeliveryProviderRead[]>("/api/admin/delivery-providers")
  return data
}

export async function listAgents(): Promise<DeliveryAgentRead[]> {
  const { data } = await apiClient.get<DeliveryAgentRead[]>("/api/admin/delivery-agents")
  return data
}

export interface CreateAgentInput {
  providerId: string
  firstName: string
  lastName: string
  phone: string
  email?: string
}

export async function createAgent(input: CreateAgentInput): Promise<DeliveryAgentRead> {
  const { data } = await apiClient.post<DeliveryAgentRead>("/api/admin/delivery-agents", {
    provider_id: input.providerId,
    first_name: input.firstName,
    last_name: input.lastName,
    phone: input.phone,
    email: input.email || undefined,
  })
  return data
}

export async function setAgentActive(id: string, active: boolean): Promise<DeliveryAgentRead> {
  const { data } = await apiClient.patch<DeliveryAgentRead>(`/api/admin/delivery-agents/${id}`, { active })
  return data
}
