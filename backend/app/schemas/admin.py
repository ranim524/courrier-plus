from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class AdminRead(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_letters: int
    draft_letters: int
    pending_payment_letters: int
    paid_letters: int
    sent_letters: int
    opened_letters: int
    received_letters: int
    failed_letters: int
    total_payments: int
    total_revenue: float
    currency: str
