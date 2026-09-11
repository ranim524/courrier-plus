# Security — Courrier+

## Legal / certification disclaimer

**Courrier+ is a technical prototype.** It does not, in its current state, provide a service with
the same legal value as an official Tunisian registered postal letter, nor does it claim
certification as a qualified electronic trust service. A real production deployment would need to
address, among other things: electronic signature and evidentiary requirements, identity
verification of senders/recipients, applicable personal-data-protection rules, payment
regulations, and postal-sector regulations under Tunisian law. None of these certifications are
claimed or implemented here.

## Implemented measures

### No digital access for the recipient
- The recipient never gets an email, a secure link, or any other digital access to a letter's
  content — the only thing that ever reaches them is the physical letter itself, plus the
  delivery-confirmed email once an admin confirms the physical delivery is complete (see
  "Physical delivery" below). This removes an entire class of risk (token leakage, link forwarding,
  expiry/revocation edge cases) by not having a recipient-facing secret at all.
- The `access_tokens` table that used to back this flow is retained only as historical audit data
  (see `docs/database.md`) — nothing creates or reads a new token anymore.

### Passwords & admin auth
- Admin passwords hashed with bcrypt (`passlib`).
- JWT (HS256) for admin sessions, separate secret from the app's general `SECRET_KEY`.
- All `/api/admin/*` routes (except login) require a valid JWT via the `get_current_admin`
  dependency.
- The first admin is created via `python -m app.scripts.create_admin`, reading credentials from
  environment variables — never hard-coded.
- An existing admin's password is changed via `python -m app.scripts.change_admin_password <email>`,
  which prompts for the new password interactively (hidden input, via `getpass`) — never as a
  command-line argument (would leak into shell history) and never logged.

### File uploads
- Only `application/pdf` is accepted, checked by extension, declared MIME type, **and** the
  file's actual magic bytes (`%PDF-`).
- Maximum size enforced (`MAX_UPLOAD_SIZE_MB`, default 10MB).
- Files are stored under a generated UUID filename; the original filename is kept only as
  display metadata, never used to build a filesystem path (prevents path traversal).
- SHA-256 of the actual bytes is computed and stored for integrity verification.
- Document downloads always go through an authorized route (admin JWT or a valid, unexpired
  recipient access token) — there is no static file mount serving `uploads/` directly.

### Payment idempotency
- Every payment has a unique `transaction_id`. Confirming an already-`PAID`/`FAILED` payment a
  second time is a no-op — it will not duplicate the letter's `SENT` transition, the recipient
  email, or any audit event.

### Transport & API
- CORS restricted to `FRONTEND_URL`, not `*`.
- Rate limiting (`slowapi`) on sensitive endpoints: letter creation, payment creation/confirmation,
  admin login, and all recipient access endpoints.
- Consistent error shape (`{"detail": "..."}`), no stack traces, SQL, or file paths ever returned
  to the client — enforced by a global exception handler.

### Logging
Never logged: passwords, JWT secret/tokens, full access tokens, the Resend API key, or document
contents. Structured log lines use safe context only (letter reference, event type, status).

### State machine
Letter status transitions are validated against an explicit allow-list
(`app/services/letter_state.py`). An out-of-order transition (e.g. confirming receipt before the
letter was opened) is rejected with HTTP 409, not silently accepted. The physical delivery state
machine (`app/services/delivery_state.py`) follows the same pattern independently.

### Physical delivery
- Every delivery-mutating endpoint (`/api/admin/deliveries/*`, `/api/admin/delivery-agents/*`)
  requires an admin JWT — enforced by the `get_current_admin` dependency on the backend, not by
  hiding buttons in the UI. There is no sender/recipient-facing route that can change a delivery's
  status.
- Public tracking (`/api/track/{reference}`) only ever exposes a `DeliveryPublicView` (tracking
  number, status, a timestamp-only timeline) — never courier name/phone, admin confirmation notes,
  or internal database IDs.
- `DeliveryOrder.confirm_delivery()` (the only path that can send a "your letter was delivered"
  email) is idempotent: a repeated confirmation never creates a duplicate `ProofOfDelivery`, audit
  event, or notification email — same idempotency discipline as payment confirmation above.
- No delivery-provider API credentials are stored in the database, even as the system becomes
  ready for a real external carrier (`DeliveryProvider.api_enabled`) — they belong in environment
  variables, referenced by the provider's `code`, following the same rule as every other secret in
  this project (never in source, never in Git, never logged).

## Privacy

Only the personal data required to operate the service is collected (sender/recipient name,
email, optional phone). IP address and user-agent are recorded on `letter_events` only for
security/audit purposes tied to a specific letter, not aggregated for tracking.
