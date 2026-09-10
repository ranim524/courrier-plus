from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import DocumentSourceType, LetterStatus


class SenderInfo(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)


class RecipientInfo(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)


class LetterCreate(BaseModel):
    sender: SenderInfo
    recipient: RecipientInfo
    subject: str = Field(min_length=1, max_length=255)
    message: str | None = Field(default=None, max_length=20000)
    acknowledgment_of_receipt: bool = False

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            return None
        return v


class DocumentRead(BaseModel):
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LetterRead(BaseModel):
    id: UUID
    reference: str | None
    sender_first_name: str
    sender_last_name: str
    sender_email: str
    recipient_first_name: str
    recipient_last_name: str
    recipient_email: str
    subject: str
    message: str | None
    content_type: DocumentSourceType
    status: LetterStatus
    page_count: int
    estimated_weight_g: int
    weight_bracket: str
    base_postage: float
    registered_fee: float
    acknowledgment_of_receipt: bool
    acknowledgment_fee: float
    total_amount: float
    currency: str
    created_at: datetime
    updated_at: datetime
    document: DocumentRead | None = None

    model_config = {"from_attributes": True}


class LetterSummary(BaseModel):
    id: UUID
    reference: str | None
    sender_first_name: str
    sender_last_name: str
    recipient_first_name: str
    recipient_last_name: str
    subject: str
    status: LetterStatus
    total_amount: float
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}
