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

### Recipient access (removed by design)
- The recipient has no digital access to a letter's content and no token of their own — no secure
  link, no online view, no email before physical delivery. The only thing that reaches them is the
  physical letter and, once an admin confirms it delivered, the delivery-confirmed email. This is a
  deliberate simplification, not an oversight: don't reintroduce a recipient-facing secret/token
  without the user explicitly asking for it back.
- `access_tokens`/`AccessToken` still exist as historical audit data only (see [[delivery]] and
  `docs/database.md`) — nothing creates or reads a new one.

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
- Recipient/sender flows never require login. The letter reference used for public tracking
  (`/api/track/{reference}`) is public/non-sensitive by design — there is no other recipient-facing
  surface to protect.
- Admin endpoints always check the JWT and role; never expose a letter/document to an unauthenticated request.
- Rate limit sensitive public endpoints (`/api/admin/login`, `/api/letters` creation, `/api/track/{reference}`) using `slowapi` or an in-memory limiter — see `app/core/rate_limit.py`.

### CORS
- Restrict `allow_origins` to `FRONTEND_URL` from env — never `*` alongside credentials.

### Logging
- Never log: passwords, JWT secret, full JWT, Resend API key, document contents, full request bodies containing sensitive data.
- Use the shared logger (`app/core/logging.py`); prefer structured log messages with safe context (letter reference, event type) over dumping objects.

### Error handling
- Never leak stack traces, SQL, or file paths to the client in a response. Use the global exception handler in `app/core/errors.py` to convert exceptions to `{"detail": "..."}`.

## Workflow
Before merging any feature touching auth/tokens/files, re-read this skill and check each rule above explicitly.
