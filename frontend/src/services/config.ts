import { apiClient } from "./apiClient"

export interface PublicConfig {
  letter_price: number
  currency: string
}

export async function getPublicConfig(): Promise<PublicConfig> {
  const { data } = await apiClient.get<PublicConfig>("/api/config")
  return data
}
