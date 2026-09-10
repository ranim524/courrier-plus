import { apiClient } from "./apiClient"
import type { LetterRead, RecipientInfo, SenderInfo } from "../types/letter"

export interface CreateLetterInput {
  sender: SenderInfo
  recipient: RecipientInfo
  subject: string
  message?: string
  document?: File | null
  acknowledgmentOfReceipt: boolean
}

export async function createLetter(input: CreateLetterInput): Promise<LetterRead> {
  const form = new FormData()
  form.append("sender_first_name", input.sender.firstName)
  form.append("sender_last_name", input.sender.lastName)
  form.append("sender_email", input.sender.email)
  if (input.sender.phone) form.append("sender_phone", input.sender.phone)

  form.append("recipient_first_name", input.recipient.firstName)
  form.append("recipient_last_name", input.recipient.lastName)
  form.append("recipient_email", input.recipient.email)
  if (input.recipient.phone) form.append("recipient_phone", input.recipient.phone)

  form.append("subject", input.subject)
  if (input.message) form.append("message", input.message)
  if (input.document) form.append("document", input.document)
  form.append("acknowledgment_of_receipt", String(input.acknowledgmentOfReceipt))

  const { data } = await apiClient.post<LetterRead>("/api/letters", form, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return data
}
