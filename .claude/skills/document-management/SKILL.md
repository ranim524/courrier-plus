---
name: document-management
description: PDF upload, storage, and SHA-256 integrity conventions for Courrier+
---

# Document Management

## Purpose
Handle PDF uploads and letter documents/messages safely, with an abstract storage layer.

## When to use it
Any time you touch document upload, storage, retrieval, or hashing.

## Project conventions
- Storage abstraction: `app/services/storage/base.py` defines a `StorageProvider` interface (`save(bytes, filename) -> path`, `read(path) -> bytes`, `delete(path)`). Two implementations: `LocalStorageProvider` (`backend/uploads/`, local dev default) and `R2StorageProvider` (Cloudflare R2 via `boto3`'s S3-compatible client, used in production). Selected by `STORAGE_PROVIDER` env var via `app/services/storage/__init__.py::get_storage_provider()` — callers never import a concrete class directly. See [[deployment]].
- Every uploaded document row (`documents` table) stores: `original_filename`, a generated safe/internal filename (UUID-based), `storage_path` (relative, never absolute/user-controlled), `mime_type`, `size`, `sha256`, `created_at`.
- SHA-256 computed via `app/utils/hashing.py::sha256_of_bytes(data: bytes) -> str`, computed from the actual uploaded bytes before writing to disk.
- Document retrieval always goes through an authorized route (admin JWT, or the letter's own recipient access token) — never a static file mount serving `backend/uploads/` directly.

## Pricing integration
- `document_service.count_pdf_pages(data: bytes) -> int` (via `pypdf`) is the sole source of truth for page count — never accept a page count from the client. `letter_service.create_letter()` calls it, then `pricing_service.calculate_price()` to compute the price snapshot. See [[payment]].
- A corrupt/unreadable PDF or one exceeding 400 pages is rejected with a clear `ValidationAppError` before the file is ever stored.

## Important rules (see also [[security]])
- Validate extension AND MIME type AND that the content actually starts with `%PDF-` magic bytes — reject anything else.
- Enforce max size before reading the whole file into memory where practical (check `Content-Length` and re-check actual bytes length).
- Never build a filesystem path from user-supplied filename directly — always use the generated UUID filename; store the original only as metadata for display.
- Directory layout: `backend/uploads/<year>/<uuid>.pdf` to avoid one giant flat directory.

## Workflow
1. Route receives `UploadFile`.
2. Service validates (type, size, magic bytes).
3. Service computes SHA-256 from bytes.
4. Service calls `StorageProvider.save()`.
5. Repository persists the `documents` row.
6. Service emits a `LETTER_CREATED`/document-attached audit event as appropriate.
