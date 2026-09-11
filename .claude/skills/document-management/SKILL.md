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
- Storage abstraction: `app/services/storage/base.py` defines a `StorageProvider` interface (`save(bytes, filename) -> path`, `read(path) -> bytes`, `delete(path)`). Three implementations: `LocalStorageProvider` (`backend/uploads/`, local dev default), `DatabaseStorageProvider` (bytes in the `document_blobs` Postgres table, used in production — no object-storage account needed), and `R2StorageProvider` (Cloudflare R2 via `boto3`'s S3-compatible client, an available upgrade). Selected by `STORAGE_PROVIDER` env var (`local` / `database` / `r2`) via `app/services/storage/__init__.py::get_storage_provider()` — callers never import a concrete class directly. See [[deployment]].
- `DatabaseStorageProvider` opens its own session (via the app's `SessionLocal` by default, injectable for tests) rather than reusing a request-scoped session — it commits independently of the caller's transaction, same self-contained-resource pattern as the filesystem/S3 providers.
- Every uploaded document row (`documents` table) stores: `original_filename`, a generated safe/internal filename (UUID-based), `storage_path` (relative, never absolute/user-controlled), `mime_type`, `size`, `sha256`, `created_at`.
- SHA-256 computed via `app/utils/hashing.py::sha256_of_bytes(data: bytes) -> str`, computed from the actual uploaded bytes before writing to disk.
- Document retrieval always goes through an authorized route (admin JWT, or the letter's own recipient access token) — never a static file mount serving `backend/uploads/` directly.

## Pricing integration
- `document_service.count_pdf_pages(data: bytes) -> int` (via `pypdf`) is the sole source of truth for page count — never accept a page count from the client. `letter_service.create_letter()` calls it, then `pricing_service.calculate_letter_price()` to compute the physical-mail price snapshot (pages → sheets → paper/envelope weight → postal bracket → printing/paper/envelope/postage/fees). See [[payment]].
- A corrupt/unreadable PDF is rejected with a clear `ValidationAppError` before the file is ever stored. There is no fixed page-count cap: `calculate_letter_price()` rejects based on the *computed estimated weight* exceeding `MAX_WEIGHT_G` (2000g), which depends on `printing_sides` (duplex roughly doubles the page count that fits under the same weight) — never hard-code a page-count limit outside that calculation.

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
