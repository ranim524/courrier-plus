from sqlalchemy.orm import Session, sessionmaker

from app.core.database import SessionLocal
from app.models.document_blob import DocumentBlob
from app.services.storage.base import StorageProvider


class DatabaseStorageProvider(StorageProvider):
    """Stores documents as bytes in PostgreSQL (the `document_blobs` table)
    instead of a separate object-storage service. No third-party account,
    API key, or payment method needed -- it reuses the same database the
    rest of the app already runs on (e.g. Neon in production).

    Fine for a prototype's document volumes (uploads capped at
    MAX_UPLOAD_SIZE_MB); a real S3-compatible provider (see r2_provider.py)
    is a straightforward swap later via STORAGE_PROVIDER if usage grows.
    """

    def __init__(self, session_factory: sessionmaker[Session] | None = None):
        self._session_factory = session_factory or SessionLocal

    def save(self, data: bytes, relative_path: str) -> str:
        db = self._session_factory()
        try:
            existing = db.get(DocumentBlob, relative_path)
            if existing is not None:
                existing.data = data
            else:
                db.add(DocumentBlob(storage_path=relative_path, data=data))
            db.commit()
        finally:
            db.close()
        return relative_path

    def read(self, storage_path: str) -> bytes:
        db = self._session_factory()
        try:
            blob = db.get(DocumentBlob, storage_path)
            if blob is None:
                raise FileNotFoundError(f"No document blob stored at {storage_path}")
            return blob.data
        finally:
            db.close()

    def delete(self, storage_path: str) -> None:
        db = self._session_factory()
        try:
            blob = db.get(DocumentBlob, storage_path)
            if blob is not None:
                db.delete(blob)
                db.commit()
        finally:
            db.close()
