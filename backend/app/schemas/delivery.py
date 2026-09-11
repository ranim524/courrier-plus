from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    DeliveryFailureReason,
    DeliveryProviderType,
    DeliveryStatus,
    ProofOfDeliveryType,
)


class DeliveryProviderRead(BaseModel):
    id: UUID
    code: str
    name: str
    provider_type: DeliveryProviderType
    active: bool
    api_enabled: bool

    model_config = {"from_attributes": True}


class DeliveryAgentCreate(BaseModel):
    provider_id: UUID
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)
    email: str | None = None


class DeliveryAgentUpdate(BaseModel):
    active: bool


class DeliveryAgentRead(BaseModel):
    id: UUID
    provider_id: UUID
    first_name: str
    last_name: str
    phone: str
    email: str | None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DeliveryAttemptRead(BaseModel):
    id: UUID
    attempt_number: int
    attempted_at: datetime
    courier_id: UUID | None
    reason: DeliveryFailureReason
    notes: str | None

    model_config = {"from_attributes": True}


class ProofOfDeliveryRead(BaseModel):
    delivered_at: datetime
    delivered_by: str
    recipient_name_if_provided: str | None
    delivery_method: str | None
    proof_type: ProofOfDeliveryType
    notes: str | None

    model_config = {"from_attributes": True}


class DeliveryOrderSummary(BaseModel):
    id: UUID
    tracking_number: str
    letter_reference: str | None
    recipient_name: str
    status: DeliveryStatus
    provider_name: str
    courier_name: str | None
    created_at: datetime
    updated_at: datetime


class DeliveryOrderRead(BaseModel):
    id: UUID
    letter_id: UUID
    letter_reference: str | None
    tracking_number: str
    status: DeliveryStatus
    acknowledgment_of_receipt: bool
    provider: DeliveryProviderRead
    courier: DeliveryAgentRead | None
    attempt_count: int
    created_at: datetime
    assigned_at: datetime | None
    picked_up_at: datetime | None
    in_transit_at: datetime | None
    out_for_delivery_at: datetime | None
    deposited_at: datetime | None
    delivered_at: datetime | None
    failed_at: datetime | None
    returned_at: datetime | None
    updated_at: datetime
    attempts: list[DeliveryAttemptRead]
    proof: ProofOfDeliveryRead | None


class AssignCourierRequest(BaseModel):
    agent_id: UUID


class DeliveryFailureRequest(BaseModel):
    reason: DeliveryFailureReason
    notes: str | None = Field(default=None, max_length=2000)


class DeliveryConfirmRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class DeliveryPublicEvent(BaseModel):
    label: str
    at: datetime


class DeliveryPublicView(BaseModel):
    """Safe subset shown on the public tracking page -- no courier personal
    info, no admin notes, no internal IDs (spec section 27)."""

    tracking_number: str
    status: DeliveryStatus
    events: list[DeliveryPublicEvent]


class DeliveryConfirmationView(BaseModel):
    """What the recipient sees at /confirm-delivery/{token} before they
    confirm -- deliberately minimal: no letter content (subject/message/PDF),
    just enough to recognize which letter this is about."""

    reference: str
    tracking_number: str
    sender_first_name: str
    sender_last_name: str
    confirmed: bool = False


class DeliveryWebhookRequest(BaseModel):
    """Payload an external carrier's own platform sends to report that its
    courier placed the letter in the recipient's mailbox. Authenticated via
    the X-Webhook-Secret header (app/core/config.py's delivery_webhook_secret),
    not a field here -- never trust a secret sent in the body."""

    provider_code: str
    tracking_number: str
