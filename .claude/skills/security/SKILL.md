---
name: security
description: Security rules for tokens, passwords, file uploads, auth, and logging in Courrier+
---

# Security

## Purpose
Centralize the security rules that apply across the whole platform (OWASP-conscious, no real payment/PII regulation certification implied).

## When to use it
Any time you: generate a token, handle a password, accept a file upload, write a log line, or add an endpoint that touches sensitive data.

## Project conventions & rules

### Tokens (recipient access)
- Generate with `secrets.token_urlsafe(32)` (or similar CSPRNG) — never sequential IDs, emails, or DB PKs.
- Store only `SHA-256(token)` in `access_tokens.token_hash`. The raw token is only ever in the URL sent by email; it is never persisted or logged in full.
- Every token has `expires_at`. Default expiration: 30 days from letter send (configurable via `ACCESS_TOKEN_EXPIRATION_DAYS`).
- Tokens can be revoked (`revoked_at`), checked on every access.
- Log only a short prefix of a token (e.g. first 8 chars) if logging is needed for debugging — never the full value.

### Passwords (admin only)
- Hashed with `passlib`'s bcrypt scheme. Never stored or logged in plaintext.
- First admin created via a CLI script (`backend/app/scripts/create_admin.py`) reading email/password from environment or interactive prompt — never hard-coded.

### JWT (admin auth)
- Signed with `JWT_SECRET` (separate from `SECRET_KEY`), short-lived access token (default 60 min, configurable).
- Verified via a FastAPI dependency (`get_current_admin`) on every `/api/admin/*` route except `/api/admin/login`.

### File uploads (documents)
- Only `application/pdf` MIME type and `.pdf` extension accepted — check both, don't trust either alone.
- Enforce a max size (`MAX_UPLOAD_SIZE_MB`, default 10MB).
- Generate a new random internal filename (UUID) for storage — never use the user-supplied filename on disk.
- Store the original filename separately in the DB for display only (never used to build a filesystem path).
- Compute SHA-256 of the file bytes and store it — see [[document-management]].
- Reject empty files.

### Auth & access control
- Recipient/sender flows never require login — access is entirely token-based (letter reference for tracking is public/non-sensitive by design; access token for viewing content is secret).
- Admin endpoints always check the JWT and role; never expose a letter/document to an unauthenticated request.
- Rate limit sensitive public endpoints (`/api/admin/login`, `/api/access/{token}/*`, `/api/letters` creation) using `slowapi` or an in-memory limiter — see `app/core/rate_limit.py`.

### CORS
- Restrict `allow_origins` to `FRONTEND_URL` from env — never `*` alongside credentials.

### Logging
- Never log: passwords, JWT secret, full JWT, full access tokens, Resend API key, document contents, full request bodies containing sensitive data.
- Use the shared logger (`app/core/logging.py`); prefer structured log messages with safe context (letter reference, event type) over dumping objects.

### Error handling
- Never leak stack traces, SQL, or file paths to the client in a response. Use the global exception handler in `app/core/errors.py` to convert exceptions to `{"detail": "..."}`.

## Workflow
Before merging any feature touching auth/tokens/files, re-read this skill and check each rule above explicitly.
