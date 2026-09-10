export interface PricingBreakdown {
  page_count: number
  estimated_weight_g: number
  weight_bracket: string
  base_postage: string
  registered_fee: string
  acknowledgment_of_receipt: boolean
  acknowledgment_fee: string
  total: string
  currency: string
}
