import { apiClient } from "./apiClient"
import type { DeliveryConfirmationView } from "../types/delivery"

export async function getDeliveryConfirmation(token: string): Promise<DeliveryConfirmationView> {
  const { data } = await apiClient.get<DeliveryConfirmationView>(`/api/delivery-confirmation/${encodeURIComponent(token)}`)
  return data
}

export async function confirmDeliveryReceipt(token: string): Promise<DeliveryConfirmationView> {
  const { data } = await apiClient.post<DeliveryConfirmationView>(
    `/api/delivery-confirmation/${encodeURIComponent(token)}/confirm`,
  )
  return data
}
