import { apiClient } from "./apiClient"
import type { PaymentRead } from "../types/payment"

export async function createPayment(letterId: string): Promise<PaymentRead> {
  const { data } = await apiClient.post<PaymentRead>("/api/payments/create", { letter_id: letterId })
  return data
}

export async function confirmMockPayment(
  transactionId: string,
  outcome: "success" | "failure",
): Promise<PaymentRead> {
  const { data } = await apiClient.post<PaymentRead>("/api/payments/mock/confirm", {
    transaction_id: transactionId,
    outcome,
  })
  return data
}
