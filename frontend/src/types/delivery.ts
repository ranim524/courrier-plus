export type DeliveryStatus =
  | "CREATED"
  | "READY_FOR_DISPATCH"
  | "ASSIGNED"
  | "PICKED_UP"
  | "IN_TRANSIT"
  | "OUT_FOR_DELIVERY"
  | "DEPOSITED"
  | "DELIVERED"
  | "DELIVERY_FAILED"
  | "RETURNED_TO_SENDER"
  | "CANCELLED"

export type DeliveryFailureReason =
  | "RECIPIENT_UNAVAILABLE"
  | "INCORRECT_ADDRESS"
  | "RECIPIENT_REFUSED"
  | "ADDRESS_INACCESSIBLE"
  | "OTHER"

export interface DeliveryProviderRead {
  id: string
  code: string
  name: string
  provider_type: "INTERNAL" | "EXTERNAL_CARRIER" | "POSTAL_SERVICE"
  active: boolean
  api_enabled: boolean
}

export interface DeliveryAgentRead {
  id: string
  provider_id: string
  first_name: string
  last_name: string
  phone: string
  email: string | null
  active: boolean
  created_at: string
}

export interface DeliveryAttemptRead {
  id: string
  attempt_number: number
  attempted_at: string
  courier_id: string | null
  reason: DeliveryFailureReason
  notes: string | null
}

export interface ProofOfDeliveryRead {
  delivered_at: string
  delivered_by: string
  recipient_name_if_provided: string | null
  delivery_method: string | null
  proof_type: string
  notes: string | null
}

export interface DeliveryOrderSummary {
  id: string
  tracking_number: string
  letter_reference: string | null
  recipient_name: string
  status: DeliveryStatus
  provider_name: string
  courier_name: string | null
  created_at: string
  updated_at: string
}

export interface DeliveryOrderRead {
  id: string
  letter_id: string
  letter_reference: string | null
  tracking_number: string
  status: DeliveryStatus
  provider: DeliveryProviderRead
  courier: DeliveryAgentRead | null
  attempt_count: number
  created_at: string
  assigned_at: string | null
  picked_up_at: string | null
  in_transit_at: string | null
  out_for_delivery_at: string | null
  deposited_at: string | null
  delivered_at: string | null
  failed_at: string | null
  returned_at: string | null
  updated_at: string
  attempts: DeliveryAttemptRead[]
  proof: ProofOfDeliveryRead | null
}

export interface DeliveryPublicEvent {
  label: string
  at: string
}

export interface DeliveryPublicView {
  tracking_number: string
  status: DeliveryStatus
  events: DeliveryPublicEvent[]
}

export interface DeliveryConfirmationView {
  reference: string
  tracking_number: string
  sender_first_name: string
  sender_last_name: string
  confirmed: boolean
}
