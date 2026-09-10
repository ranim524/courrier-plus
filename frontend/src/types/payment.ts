export type PaymentStatus = "PENDING" | "PAID" | "FAILED" | "REFUNDED"

export interface PaymentRead {
  id: string
  letter_id: string
  provider: string
  transaction_id: string
  amount: number
  currency: string
  status: PaymentStatus
  created_at: string
}
