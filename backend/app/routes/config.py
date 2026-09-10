from fastapi import APIRouter

from app.core.config import get_settings
from app.services.pricing_service import (
    ACKNOWLEDGMENT_OF_RECEIPT_FEE,
    ESTIMATED_GRAMS_PER_PAGE,
    MAX_PAGES,
    REGISTERED_MAIL_FEE,
)

router = APIRouter(prefix="/api/config", tags=["config"])
settings = get_settings()


@router.get("")
def get_public_config() -> dict:
    """Pricing is now dynamic (see /api/pricing/preview); this only exposes
    the currency and static tariff constants useful for display, never a
    fixed price."""
    return {
        "currency": settings.currency,
        "registered_fee": str(REGISTERED_MAIL_FEE),
        "acknowledgment_fee": str(ACKNOWLEDGMENT_OF_RECEIPT_FEE),
        "estimated_grams_per_page": ESTIMATED_GRAMS_PER_PAGE,
        "max_pages": MAX_PAGES,
    }
