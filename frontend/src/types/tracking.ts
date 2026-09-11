import type { LetterStatus } from "./letter"
import type { DeliveryPublicView } from "./delivery"

export interface TrackingEvent {
  event_type: string
  actor_type: string
  created_at: string
}

export interface TrackingRead {
  reference: string
  status: LetterStatus
  subject: string
  sender_first_name: string
  sender_last_name: string
  recipient_first_name: string
  recipient_last_name: string
  created_at: string
  events: TrackingEvent[]
  delivery: DeliveryPublicView | null
}

export interface AccessLetterView {
  reference: string
  sender_first_name: string
  sender_last_name: string
  subject: string
  message: string | null
  status: LetterStatus
  has_document: boolean
  acknowledgment_of_receipt: boolean
  created_at: string
  delivery: DeliveryPublicView | null
}
