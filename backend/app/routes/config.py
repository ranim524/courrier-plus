from fastapi import APIRouter

from app.core.config import get_settings
from app.services.pricing_service import (
    ACKNOWLEDGMENT_FEE,
    DELIVERY_FEE,
    ENVELOPE_COST,
    PAPER_COST_PER_SHEET,
    PRINTING_COST_BW_PER_PAGE,
    REGISTERED_MAIL_FEE,
    COURRIER_PLUS_SERVICE_FEE,
    MAX_WEIGHT_G,
)

router = APIRouter(prefix="/api/config", tags=["config"])
settings = get_settings()


@router.get("")
def get_public_config() -> dict:
    """Pricing is dynamic (see /api/pricing/preview); this only exposes the
    currency and static tariff/service constants useful for display, never a
    fixed price."""
    return {
        "currency": settings.currency,
        "printing_cost_per_page": str(PRINTING_COST_BW_PER_PAGE),
        "paper_cost_per_sheet": str(PAPER_COST_PER_SHEET),
        "envelope_cost": str(ENVELOPE_COST),
        "registered_mail_fee": str(REGISTERED_MAIL_FEE),
        "acknowledgment_fee": str(ACKNOWLEDGMENT_FEE),
        "delivery_fee": str(DELIVERY_FEE),
        "service_fee": str(COURRIER_PLUS_SERVICE_FEE),
        "max_weight_g": str(MAX_WEIGHT_G),
    }
