import re
import uuid

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_display_filename(filename: str) -> str:
    """Sanitizes a filename for display/storage as metadata only. Never used to build a filesystem path."""
    base = filename.strip().replace("\\", "_").replace("/", "_")
    base = _UNSAFE_CHARS.sub("_", base)
    return base[:255] if base else "document.pdf"


def generate_internal_filename(extension: str = ".pdf") -> str:
    return f"{uuid.uuid4().hex}{extension}"
