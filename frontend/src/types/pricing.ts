export interface PricingBreakdown {
  page_count: number
  sheet_count: number
  printing_mode: string
  printing_sides: string
  paper_weight_g: string
  envelope_weight_g: string
  estimated_weight_g: string
  weight_bracket: string
  printing_cost: string
  paper_cost: string
  envelope_cost: string
  postal_postage: string
  registered_mail_fee: string
  acknowledgment_of_receipt: boolean
  acknowledgment_fee: string
  delivery_fee: string
  service_fee: string
  total: string
  currency: string
}
