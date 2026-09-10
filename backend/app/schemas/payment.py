from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import PaymentStatus


class PaymentCreateRequest(BaseModel):
    letter_id: UUID


class PaymentRead(BaseModel):
    id: UUID
    letter_id: UUID
    provider: str
    transaction_id: str
    amount: float
    currency: str
    status: PaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class MockPaymentConfirmRequest(BaseModel):
    transaction_id: str
    outcome: str = "success"  # "success" or "failure"
