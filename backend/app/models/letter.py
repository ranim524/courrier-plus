from sqlalchemy import Enum as SAEnum
from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DocumentSourceType, LetterStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Letter(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "letters"

    reference: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)

    # Sender info (no account — captured per letter)
    sender_first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sender_last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sender_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Recipient info
    recipient_first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient_last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    recipient_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[DocumentSourceType] = mapped_column(
        SAEnum(DocumentSourceType, name="document_source_type"), nullable=False
    )

    status: Mapped[LetterStatus] = mapped_column(
        SAEnum(LetterStatus, name="letter_status"), nullable=False, default=LetterStatus.DRAFT
    )

    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TND")

    document = relationship("Document", back_populates="letter", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="letter", cascade="all, delete-orphan")
    access_tokens = relationship("AccessToken", back_populates="letter", cascade="all, delete-orphan")
    events = relationship(
        "LetterEvent", back_populates="letter", cascade="all, delete-orphan", order_by="LetterEvent.created_at"
    )
    email_events = relationship("EmailEvent", back_populates="letter", cascade="all, delete-orphan")
