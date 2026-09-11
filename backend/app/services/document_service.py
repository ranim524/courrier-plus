import io
from datetime import datetime, timezone
from uuid import UUID

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.models.document import Document
from app.repositories import document_repository
from app.services.storage import get_storage_provider
from app.utils.filenames import generate_internal_filename, sanitize_display_filename
from app.utils.hashing import sha256_of_bytes

settings = get_settings()

ALLOWED_MIME_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}
PDF_MAGIC_BYTES = b"%PDF-"


def validate_pdf(filename: str, content_type: str | None, data: bytes) -> None:
    if not data:
        raise ValidationAppError("The uploaded file is empty")

    if len(data) > settings.max_upload_size_bytes:
        raise ValidationAppError(
            f"File exceeds the maximum allowed size of {settings.max_upload_size_mb}MB"
        )

    lower_name = filename.lower()
    if not any(lower_name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise ValidationAppError("Only PDF files are allowed")

    if content_type not in ALLOWED_MIME_TYPES:
        raise ValidationAppError("Invalid file type: only application/pdf is accepted")

    if not data.startswith(PDF_MAGIC_BYTES):
        raise ValidationAppError("The file does not appear to be a valid PDF")


def count_pdf_pages(data: bytes) -> int:
    """Determines the exact page count of a PDF from its bytes. This is the
    source of truth for the Courrier+ pricing engine -- the page count is
    never accepted from the client."""
    try:
        reader = PdfReader(io.BytesIO(data))
        page_count = len(reader.pages)
    except PdfReadError as exc:
        raise ValidationAppError("Le fichier PDF est invalide ou illisible.") from exc

    if page_count < 1:
        raise ValidationAppError("Le document PDF ne contient aucune page.")

    return page_count


def store_document(db: Session, letter_id: UUID, filename: str, content_type: str, data: bytes) -> Document:
    validate_pdf(filename, content_type, data)

    file_hash = sha256_of_bytes(data)
    internal_name = generate_internal_filename(".pdf")
    year = datetime.now(timezone.utc).year
    relative_path = f"{year}/{internal_name}"

    storage = get_storage_provider()
    storage.save(data, relative_path)

    document = Document(
        letter_id=letter_id,
        original_filename=sanitize_display_filename(filename),
        internal_filename=internal_name,
        storage_path=relative_path,
        mime_type=content_type,
        size_bytes=len(data),
        sha256=file_hash,
    )
    return document_repository.create(db, document)


def read_document_bytes(document: Document) -> bytes:
    storage = get_storage_provider()
    return storage.read(document.storage_path)
