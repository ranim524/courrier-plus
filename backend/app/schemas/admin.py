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
    received_letters: int
    failed_letters: int
    total_payments: int
    total_revenue: float
    currency: str
    total_deliveries: int
    deliveries_ready_for_dispatch: int
    deliveries_assigned: int
    deliveries_in_transit: int
    deliveries_out_for_delivery: int
    deliveries_deposited: int
    deliveries_delivered: int
    deliveries_failed: int
    deliveries_returned: int
