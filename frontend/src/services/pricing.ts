import { apiClient } from "./apiClient"
import type { PricingBreakdown } from "../types/pricing"

/**
 * Asks the backend for a live price preview. The backend determines the PDF
 * page count itself from the uploaded file (or treats a text-only letter as
 * a single page) -- the frontend never counts pages or computes a price
 * itself, it only displays what this call returns.
 */
export async function previewPrice(document: File | null, acknowledgmentOfReceipt: boolean): Promise<PricingBreakdown> {
  const form = new FormData()
  form.append("acknowledgment_of_receipt", String(acknowledgmentOfReceipt))
  if (document) form.append("document", document)

  const { data } = await apiClient.post<PricingBreakdown>("/api/pricing/preview", form, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return data
}
