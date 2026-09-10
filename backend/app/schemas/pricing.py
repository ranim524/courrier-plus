from pydantic import BaseModel


class PricingCalculateRequest(BaseModel):
    page_count: int
    acknowledgment_of_receipt: bool = False


class PricingBreakdownRead(BaseModel):
    page_count: int
    estimated_weight_g: int
    weight_bracket: str
    base_postage: str
    registered_fee: str
    acknowledgment_of_receipt: bool
    acknowledgment_fee: str
    total: str
    currency: str
