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
   DeliveryOrder auto-created (see "Physical delivery system" below)
   Email sent: payment confirmation (sender only)
   │
   ▼
ADMIN runs the physical delivery through to DELIVERED (Admin → Livraisons)
   │
   ▼
delivery_service.confirm_delivery() → Letter → RECEIVED (if acknowledgment of
   receipt was requested) or DELIVERED (otherwise) — the only transition out
   of SENT. DELIVERY_CONFIRMED_RECIPIENT + DELIVERY_CONFIRMED_SENDER emails sent.
```

**The recipient never gets an email or any digital access to the letter's content.** There is no
secure link, no online view, no digital "open"/"confirm receipt" action — the only thing that ever
reaches the recipient is the physical letter itself, and the only notification either side gets is
the delivery-confirmed email once an admin confirms the physical delivery
(`app/services/delivery_service.py::confirm_delivery`). Every transition is explicit and validated
by `app/services/letter_state.py` — an invalid jump is rejected with HTTP 409, never silently
allowed.

## Pricing model

Courrier+ physically prints the uploaded PDF, puts it in an envelope, and sends it as real
registered mail — the price reflects that physical service, computed entirely in
`app/services/pricing_service.py::calculate_letter_price()`:

```
PDF pages
   │  (server-side page count via pypdf — never trusted from the client)
   ▼
physical sheets            sheet_count = page_count (simplex) or ceil(page_count/2) (duplex)
   │
   ▼
paper weight + envelope weight   → estimated_weight_g ("poids estimé", not a scale reading)
   │
   ▼
postal weight bracket      → postal_postage (Tunisian internal-letter tariff, prototype defaults)
   │
   ▼
printing_cost + paper_cost + envelope_cost + postal_postage + registered_mail_fee
   + acknowledgment_fee (optional) + delivery_fee + service_fee
   =
total_amount
```

All the constants along this pipeline (`PRINTING_COST_BW_PER_PAGE`, `PAPER_WEIGHT_PER_SHEET_G`,
`ENVELOPE_COST`, `POSTAL_TARIFFS`, `COURRIER_PLUS_SERVICE_FEE`, etc.) are centralized at the top of
`pricing_service.py` — nowhere else in the codebase hard-codes a price. They are **initial
prototype defaults**, not verified official market prices; an admin settings screen to edit them
is the natural next step, documented as a TODO rather than built speculatively (see
`docs/deployment.md`).

The frontend only ever displays a breakdown returned by `POST /api/pricing/preview` — it never
computes a page count, weight, or price itself. `POST /api/letters` has no price/weight/page-count
field a client could set; the backend always re-derives everything from the actual uploaded PDF
bytes. See `docs/api.md` and `docs/database.md`.

## Payment & storage abstractions

- **Payment**: `PaymentProvider` interface (`app/services/payment/base.py`) with a `MockPaymentProvider`
  implementation. Selected via `PAYMENT_PROVIDER` env var. A real Tunisian provider can be added as
  a new class implementing the same interface without touching callers.
- **Storage**: `StorageProvider` interface (`app/services/storage/base.py`) with three implementations
  selected via `STORAGE_PROVIDER`: `LocalStorageProvider` (writes to `backend/uploads/`, the local
  dev default), `DatabaseStorageProvider` (stores file bytes in the `document_blobs` Postgres table,
  used in production — no object-storage account needed), and `R2StorageProvider` (Cloudflare R2,
  S3-compatible, an available upgrade if document volume grows — see `docs/deployment.md`). Callers
  (`document_service.py`) only ever use the interface, never a
  concrete class directly.

## Physical delivery system

Courrier+ actually prints the letter and delivers it physically — this is a distinct, linked
subsystem from the payment/tracking flow above:

```
Letter (SENT)
   │  auto-created by payment_service.confirm_payment()
   ▼
DeliveryOrder (CREATED -> READY_FOR_DISPATCH)
   │  admin actions, app/services/delivery_service.py
   ▼
ASSIGNED -> PICKED_UP -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED
   │                                         │
   │                                         ▼
   │                                  DELIVERY_FAILED -> RETURNED_TO_SENDER
   ▼                                         │
ProofOfDelivery                    (or back to OUT_FOR_DELIVERY for a retry)
   │
   ▼
DELIVERY_CONFIRMED_RECIPIENT / DELIVERY_CONFIRMED_SENDER emails
```

- **Two linked, not duplicated, state machines.** `DeliveryOrder.status` (`DeliveryStatus`) holds the
  detailed physical-delivery state; `Letter.status` only reflects the high-level outcome, moving
  from `SENT` straight to `DELIVERED` or `RECEIVED` (if the paid acknowledgment-of-receipt option
  was requested — this `ProofOfDelivery` *is* that accusé de réception) once
  `DeliveryOrder.confirm_delivery()` runs. `SENT` never means delivered on its own — only a
  confirmed `DeliveryOrder.DELIVERED` can move the letter there. There is no separate digital
  "opened" state: the recipient has no online access to react to in the first place.
- **Only `DELIVERED` triggers the "your letter was delivered" emails.** No earlier status
  (`ASSIGNED`, `PICKED_UP`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`) sends anything to the recipient/sender.
  `delivery_service.confirm_delivery()` is the single, idempotent entry point that creates the
  `ProofOfDelivery` and sends both emails exactly once.
- **Provider abstraction** (`app/services/delivery/`): `BaseDeliveryProvider` with
  `ManualDeliveryProvider` (phase 1 — no external API, every status change is a direct admin
  action) as the only implementation today, selected by `DeliveryProvider.code`. A real carrier is
  a new provider class + DB row later, with no change to `delivery_service.py` or the admin routes
  above it. The UI labels this "suivi manuel" — it never implies real-time carrier tracking that
  doesn't exist yet.
- **Audit trail reuses `letter_events`** (no separate `delivery_events` table) — every delivery
  event is already scoped to one letter, so the existing `LetterEventType` enum gained
  `DELIVERY_CREATED` ... `DELIVERY_CANCELLED` members instead of a parallel table.
- **Public tracking view** (`GET /api/track/{reference}`) exposes a `DeliveryPublicView` derived
  only from `DeliveryOrder`'s own timestamp columns — never courier name/phone, admin notes, or
  internal database IDs. All delivery-mutating endpoints (`/api/admin/deliveries/*`,
  `/api/admin/delivery-agents/*`) require an admin JWT; there is no sender/recipient-facing route
  that can change a delivery's status.

See `.claude/skills/delivery/SKILL.md` and `docs/database.md` for the full schema.

## Admin vs. public surface

Senders track their letter by its public reference at `/track/{reference}` — no account, no
secret link. Only administrators have accounts and JWT-based sessions, scoped to `/api/admin/*`.
The `access_tokens` table and its model/repository remain in the codebase only to keep historical
audit data readable; nothing creates or reads a new one anymore (see `docs/database.md`).

## Legal note

Courrier+ is a **technical prototype**. It does not claim the same legal value as an official
Tunisian registered postal letter. See `docs/security.md` for the full disclaimer.
