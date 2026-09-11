import { apiClient } from "./apiClient"

export interface PublicConfig {
  currency: string
  printing_cost_per_page: string
  paper_cost_per_sheet: string
  envelope_cost: string
  registered_mail_fee: string
  acknowledgment_fee: string
  delivery_fee: string
  service_fee: string
  max_weight_g: string
}

export async function getPublicConfig(): Promise<PublicConfig> {
  const { data } = await apiClient.get<PublicConfig>("/api/config")
  return data
}
