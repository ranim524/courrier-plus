from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.schemas.delivery import DeliveryConfirmationView
from app.services import delivery_service

router = APIRouter(prefix="/api/delivery-confirmation", tags=["delivery-confirmation"])


def _to_view(order, confirmed: bool = False) -> DeliveryConfirmationView:
    letter = order.letter
    return DeliveryConfirmationView(
        reference=letter.reference or "",
        tracking_number=order.tracking_number,
        sender_first_name=letter.sender_first_name,
        sender_last_name=letter.sender_last_name,
        confirmed=confirmed,
    )


@router.get("/{token}", response_model=DeliveryConfirmationView)
@limiter.limit("30/minute")
def view_confirmation(request: Request, token: str, db: Session = Depends(get_db)) -> DeliveryConfirmationView:
    order = delivery_service.get_confirmation_view(db, token)
    return _to_view(order)


@router.post("/{token}/confirm", response_model=DeliveryConfirmationView)
@limiter.limit("10/minute")
def confirm(request: Request, token: str, db: Session = Depends(get_db)) -> DeliveryConfirmationView:
    order = delivery_service.confirm_delivery_by_recipient(db, token)
    return _to_view(order, confirmed=True)
