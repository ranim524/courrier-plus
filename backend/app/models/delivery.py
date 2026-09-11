from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    DeliveryFailureReason,
    DeliveryProviderType,
    DeliveryStatus,
    ProofOfDeliveryType,
)
from app.models.mixins import TimestampMixin, UUIDPKMixin


class DeliveryProvider(UUIDPKMixin, TimestampMixin, Base):
    """The company/system responsible for a physical delivery. Phase 1 ships
    a single seeded row ("Courrier+ Delivery", INTERNAL, manual). A real
    carrier is added later as another row + a new BaseDeliveryProvider
    implementation (see app/services/delivery/) -- never by hardcoding a
    specific company into this model or its callers.

    No API credentials are stored here even when api_enabled is later set for
    a real carrier: they belong in environment variables, referenced by the
    provider's `code`, never as a plaintext DB column.
    """

    __tablename__ = "delivery_providers"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_type: Mapped[DeliveryProviderType] = mapped_column(
        SAEnum(DeliveryProviderType, name="delivery_provider_type"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    api_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    api_base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    agents = relationship("DeliveryAgent", back_populates="provider")
    orders = relationship("DeliveryOrder", back_populates="provider")


class DeliveryAgent(UUIDPKMixin, TimestampMixin, Base):
    """A courier/delivery person. Admin-managed only -- never exposed to
    senders/recipients (see routes/delivery.py, all behind get_current_admin)."""

    __tablename__ = "delivery_agents"

    provider_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    provider = relationship("DeliveryProvider", back_populates="agents")
    orders = relationship("DeliveryOrder", back_populates="courier")


class DeliveryOrder(UUIDPKMixin, TimestampMixin, Base):
    """The physical delivery for exactly one letter. Detailed physical-
    delivery status lives here (DeliveryStatus); Letter.status only reflects
    the high-level DELIVERED milestone (see app/services/delivery_service.py
    and app/services/delivery_state.py) -- this table is the source of truth
    for everything in between."""

    __tablename__ = "delivery_orders"

    letter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("letters.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    tracking_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    provider_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_providers.id"), nullable=False, index=True
    )
    courier_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_agents.id"), nullable=True, index=True
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        SAEnum(DeliveryStatus, name="delivery_status"), nullable=False, default=DeliveryStatus.CREATED, index=True
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    in_transit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    out_for_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    letter = relationship("Letter", back_populates="delivery_order")
    provider = relationship("DeliveryProvider", back_populates="orders")
    courier = relationship("DeliveryAgent", back_populates="orders")
    attempts = relationship(
        "DeliveryAttempt", back_populates="delivery_order", cascade="all, delete-orphan", order_by="DeliveryAttempt.attempted_at"
    )
    proof = relationship("ProofOfDelivery", back_populates="delivery_order", uselist=False, cascade="all, delete-orphan")


class DeliveryAttempt(UUIDPKMixin, TimestampMixin, Base):
    """One record per failed delivery attempt (section 16). A successful
    delivery does not get an attempt row -- it gets a ProofOfDelivery."""

    __tablename__ = "delivery_attempts"

    delivery_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    courier_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("delivery_agents.id"), nullable=True)
    reason: Mapped[DeliveryFailureReason] = mapped_column(
        SAEnum(DeliveryFailureReason, name="delivery_failure_reason"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    delivery_order = relationship("DeliveryOrder", back_populates="attempts")


class ProofOfDelivery(UUIDPKMixin, TimestampMixin, Base):
    """Created exactly once, when a DeliveryOrder reaches DELIVERED (see
    delivery_service.confirm_delivery, which is idempotent and never creates
    a second one). proof_type is MANUAL_CONFIRMATION for the current
    prototype -- the model is shaped to support SIGNATURE/OTP/PHOTO later
    without a schema change, but never claim a proof type that wasn't
    actually captured."""

    __tablename__ = "proofs_of_delivery"

    delivery_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_orders.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_by: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_name_if_provided: Mapped[str | None] = mapped_column(String(200), nullable=True)
    delivery_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proof_type: Mapped[ProofOfDeliveryType] = mapped_column(
        SAEnum(ProofOfDeliveryType, name="proof_of_delivery_type"), nullable=False, default=ProofOfDeliveryType.MANUAL_CONFIRMATION
    )
    proof_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    delivery_order = relationship("DeliveryOrder", back_populates="proof")
