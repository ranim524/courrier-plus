import { apiClient } from "./apiClient"
import type { TrackingRead } from "../types/tracking"

export async function getTracking(reference: string): Promise<TrackingRead> {
  const { data } = await apiClient.get<TrackingRead>(`/api/track/${encodeURIComponent(reference)}`)
  return data
}
