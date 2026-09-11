export interface AdminLoginResponse {
  access_token: string
  token_type: string
  expires_in_minutes: number
}

export interface DashboardStats {
  total_letters: number
  draft_letters: number
  pending_payment_letters: number
  paid_letters: number
  sent_letters: number
  received_letters: number
  failed_letters: number
  total_payments: number
  total_revenue: number
  currency: string
  total_deliveries: number
  deliveries_ready_for_dispatch: number
  deliveries_assigned: number
  deliveries_in_transit: number
  deliveries_out_for_delivery: number
  deliveries_deposited: number
  deliveries_delivered: number
  deliveries_failed: number
  deliveries_returned: number
}

export interface LetterEventRead {
  id: string
  event_type: string
  actor_type: string
  ip_address: string | null
  user_agent: string | null
  event_metadata: Record<string, unknown> | null
  created_at: string
}

export interface EmailEventRead {
  id: string
  email_type: string
  recipient: string
  status: string
  provider_message_id: string | null
  error_message: string | null
  created_at: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
