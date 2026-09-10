from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PaymentStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Payment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    letter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("letters.id", ondelete="CASCADE"), nullable=False, index=True
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="mock")
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TND")
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.PENDING
    )

    letter = relationship("Letter", back_populates="payments")
