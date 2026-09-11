from pydantic import BaseModel

from app.services.pricing_service import DEFAULT_PRINTING_MODE, DEFAULT_PRINTING_SIDES


class PricingCalculateRequest(BaseModel):
    page_count: int
    printing_mode: str = DEFAULT_PRINTING_MODE
    printing_sides: str = DEFAULT_PRINTING_SIDES
    acknowledgment_of_receipt: bool = False


class PricingBreakdownRead(BaseModel):
    page_count: int
    sheet_count: int
    printing_mode: str
    printing_sides: str
    paper_weight_g: str
    envelope_weight_g: str
    estimated_weight_g: str
    weight_bracket: str
    printing_cost: str
    paper_cost: str
    envelope_cost: str
    postal_postage: str
    registered_mail_fee: str
    acknowledgment_of_receipt: bool
    acknowledgment_fee: str
    delivery_fee: str
    service_fee: str
    total: str
    currency: str
