# Architecture — Courrier+

## Overview

Courrier+ is a **modular monolith**: one FastAPI backend, one React frontend, one PostgreSQL
database. There are no microservices, no message queues, no orchestration layer — the goal is a
codebase a single developer can hold in their head while still being cleanly separated by
responsibility.

```
┌─────────────┐      HTTPS/JSON       ┌──────────────────┐        SQL        ┌──────────────┐
│   React     │  ───────────────────▶ │   FastAPI app     │ ────────────────▶ │  PostgreSQL  │
│  (Vite/TS)  │ ◀─────────────────── │  (modular monolith)│ ◀──────────────── │              │
└─────────────┘                       └──────────────────┘                    └──────────────┘
                                              │
                                              ▼
                                        Resend (email)
```

## Backend layering

```
routes/         → HTTP layer: request parsing, status codes, no business logic
services/       → business rules, orchestration, calls repositories + other services
repositories/   → CRUD against the database via SQLAlchemy, no business rules
models/         → SQLAlchemy ORM entities
schemas/        → Pydantic request/response validation
core/           → cross-cutting config, DB session, security, logging, error handling
utils/          → small stateless helpers (hashing, filenames, reference generation)
```

A route never talks to a repository directly, and a repository never contains business logic.
This keeps each layer testable and replaceable independently (e.g. swapping the mock payment
provider for a real one only touches `services/payment/`).

## Main business flow

```
SENDER fills sender + recipient + subject + (message OR PDF)
   │
   ▼
POST /api/letters  → Letter created in DRAFT, document stored + SHA-256 computed if PDF
   │
   ▼
POST /api/payments/create → Letter → PENDING_PAYMENT, mock Payment created (PENDING)
   │
   ▼
POST /api/payments/mock/confirm (success) → idempotent:
   Payment → PAID
   Letter → PAID → SENT (unique public reference generated, e.g. TN-2026-0001847)
   Access token generated (random, hashed in DB)
   Emails sent: payment confirmation (sender), recipient notification (recipient)
   │
   ▼
RECIPIENT opens /access/{token} → RECIPIENT_LINK_ACCESSED event, then LETTER_OPENED
   → Letter → OPENED, sender notified by email
   │
   ▼
RECIPIENT confirms receipt → Letter → RECEIVED, RECEIPT_CONFIRMED event
   → sender notified by email
```

Every transition is explicit and validated by `app/services/letter_state.py` — an invalid jump
(e.g. RECEIVED before OPENED) is rejected with HTTP 409, never silently allowed.

## Payment & storage abstractions

- **Payment**: `PaymentProvider` interface (`app/services/payment/base.py`) with a `MockPaymentProvider`
  implementation. Selected via `PAYMENT_PROVIDER` env var. A real Tunisian provider can be added as
  a new class implementing the same interface without touching callers.
- **Storage**: `StorageProvider` interface (`app/services/storage/base.py`) with two implementations
  selected via `STORAGE_PROVIDER`: `LocalStorageProvider` (writes to `backend/uploads/`, the local
  dev default) and `R2StorageProvider` (Cloudflare R2, S3-compatible, used in production — see
  `docs/deployment.md`). Callers (`document_service.py`) only ever use the interface, never a
  concrete class directly.

## Admin vs. public surface

Senders and recipients never authenticate — they act through the letter creation form and
secret, single-purpose access tokens. Only administrators have accounts and JWT-based sessions,
scoped to `/api/admin/*`.

## Legal note

Courrier+ is a **technical prototype**. It does not claim the same legal value as an official
Tunisian registered postal letter. See `docs/security.md` for the full disclaimer.
