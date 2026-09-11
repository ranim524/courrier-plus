export type LetterStatus =
  | "DRAFT"
  | "PENDING_PAYMENT"
  | "PAID"
  | "SENT"
  | "DELIVERED"
  | "RECEIVED"
  | "FAILED"
  | "REFUSED"
  | "EXPIRED"
  | "CANCELLED"

export type ContentType = "TEXT_MESSAGE" | "PDF_UPLOAD"

export interface SenderInfo {
  firstName: string
  lastName: string
  email: string
  phone?: string
}

export interface RecipientInfo {
  firstName: string
  lastName: string
  email: string
  phone?: string
}

export interface DocumentRead {
  original_filename: string
  mime_type: string
  size_bytes: number
  sha256: string
  created_at: string
}

export interface LetterRead {
  id: string
  reference: string | null
  sender_first_name: string
  sender_last_name: string
  sender_email: string
  recipient_first_name: string
  recipient_last_name: string
  recipient_email: string
  subject: string
  message: string | null
  content_type: ContentType
  status: LetterStatus
  page_count: number
  sheet_count: number
  printing_mode: string
  printing_sides: string
  paper_weight_g: number
  envelope_weight_g: number
  estimated_weight_g: number
  weight_bracket: string
  printing_cost: number
  paper_cost: number
  envelope_cost: number
  postal_postage: number
  registered_mail_fee: number
  acknowledgment_of_receipt: boolean
  acknowledgment_fee: number
  delivery_fee: number
  service_fee: number
  total_amount: number
  currency: string
  created_at: string
  updated_at: string
  document?: DocumentRead | null
}

export interface LetterSummary {
  id: string
  reference: string | null
  sender_first_name: string
  sender_last_name: string
  recipient_first_name: string
  recipient_last_name: string
  subject: string
  status: LetterStatus
  total_amount: number
  currency: string
  created_at: string
}
