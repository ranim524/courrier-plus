export type LetterStatus =
  | "DRAFT"
  | "PENDING_PAYMENT"
  | "PAID"
  | "SENT"
  | "DELIVERED"
  | "OPENED"
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
  price: number
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
  price: number
  currency: string
  created_at: string
}
