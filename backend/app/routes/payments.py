from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.schemas.payment import MockPaymentConfirmRequest, PaymentCreateRequest, PaymentRead
from app.services import payment_service

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/create", response_model=PaymentRead, status_code=201)
@limiter.limit("10/minute")
def create_payment(request: Request, payload: PaymentCreateRequest, db: Session = Depends(get_db)) -> PaymentRead:
    payment = payment_service.create_payment(db, payload.letter_id)
    return PaymentRead.model_validate(payment)


@router.post("/mock/confirm", response_model=PaymentRead)
@limiter.limit("20/minute")
def confirm_mock_payment(
    request: Request, payload: MockPaymentConfirmRequest, db: Session = Depends(get_db)
) -> PaymentRead:
    """Dev-only endpoint simulating the mock payment provider's confirmation.
    Idempotent: repeated calls with the same transaction_id are safe."""
    payment = payment_service.confirm_payment(db, payload.transaction_id, payload.outcome)
    return PaymentRead.model_validate(payment)


@router.post("/webhook", response_model=PaymentRead)
def payment_webhook(payload: MockPaymentConfirmRequest, db: Session = Depends(get_db)) -> PaymentRead:
    """Generic webhook entry point for a future real payment provider.
    Kept idempotent the same way as the mock confirm endpoint."""
    payment = payment_service.confirm_payment(db, payload.transaction_id, payload.outcome)
    return PaymentRead.model_validate(payment)
