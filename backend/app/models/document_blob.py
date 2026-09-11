from sqlalchemy import LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class DocumentBlob(TimestampMixin, Base):
    """Raw file bytes for DatabaseStorageProvider (STORAGE_PROVIDER=database).

    Keyed directly by storage_path (the same relative path used by the local
    and R2 providers) rather than a surrogate UUID -- this table is internal
    storage plumbing, never exposed via the API or referenced by a foreign
    key, so a natural key keeps it simple.
    """

    __tablename__ = "document_blobs"

    storage_path: Mapped[str] = mapped_column(String(500), primary_key=True)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
