from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ActorType, LetterEventType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class LetterEvent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "letter_events"

    letter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("letters.id", ondelete="CASCADE"), nullable=False, index=True
    )

    event_type: Mapped[LetterEventType] = mapped_column(
        SAEnum(LetterEventType, name="letter_event_type"), nullable=False
    )
    actor_type: Mapped[ActorType] = mapped_column(SAEnum(ActorType, name="actor_type"), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    letter = relationship("Letter", back_populates="events")
