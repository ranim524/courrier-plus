from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/api/config", tags=["config"])
settings = get_settings()


@router.get("")
def get_public_config() -> dict:
    return {"letter_price": settings.letter_price, "currency": settings.currency}
