import { apiClient } from "./apiClient"

export interface PublicConfig {
  currency: string
  registered_fee: string
  acknowledgment_fee: string
  estimated_grams_per_page: number
  max_pages: number
}

export async function getPublicConfig(): Promise<PublicConfig> {
  const { data } = await apiClient.get<PublicConfig>("/api/config")
  return data
}
