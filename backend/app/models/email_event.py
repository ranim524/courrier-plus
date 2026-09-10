from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import EmailStatus, EmailType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class EmailEvent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "email_events"

    letter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("letters.id", ondelete="CASCADE"), nullable=False, index=True
    )

    email_type: Mapped[EmailType] = mapped_column(SAEnum(EmailType, name="email_type"), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[EmailStatus] = mapped_column(
        SAEnum(EmailStatus, name="email_status"), nullable=False, default=EmailStatus.PENDING
    )
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    letter = relationship("Letter", back_populates="email_events")
