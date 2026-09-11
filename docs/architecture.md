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
ADMIN runs the physical delivery through to OUT_FOR_DELIVERY, then DEPOSITED
   (courier placed the letter in the mailbox -- Admin → Livraisons, or an
   external carrier's own platform via a webhook, see below)
   │
   ▼
delivery_service.mark_deposited() -- branches on acknowledgment_of_receipt:
   │
   ├─ NOT requested → no accusé de réception to collect: finalizes
   │  immediately, no recipient email at all, sender notified right away
   │  (same as force_confirm_delivery below, just automatic)
   │
   └─ requested (paid +2.500 TND) → single-use confirmation link emailed
      to the recipient; sender still gets nothing
      │
      ▼
      RECIPIENT clicks the link (POST /api/delivery-confirmation/{token}/confirm)
      -- or an admin force-confirms if the recipient never responds
   │
   ▼
delivery_service._finalize_delivery() → Letter → RECEIVED (if acknowledgment
   of receipt was requested) or DELIVERED (otherwise) — the only transition
   out of SENT. DELIVERY_CONFIRMED_SENDER email sent (sender only).
```

**The recipient never gets any digital access to the letter's content.** A letter *without* the paid
acknowledgment-of-receipt option gets the recipient zero emails, ever. A letter *with* it gets the
recipient exactly one email — the confirmation-request link above — which never shows the subject,
message, or PDF, just enough to recognize which letter this is and a confirm button. Every
transition is explicit and validated by `app/services/letter_state.py` — an invalid jump is rejected
with HTTP 409, never silently allowed.

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
ASSIGNED -> PICKED_UP -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DEPOSITED
   │                                         │                 │
   │                                         ▼                 ▼
   │                                  DELIVERY_FAILED    confirmation-request
   │                                   -> RETURNED_TO_SENDER    email to recipient
   ▼                                   (or retry: back to               │
  (cancel from an early status)         OUT_FOR_DELIVERY)                ▼
                                                            recipient confirms
                                                          (or admin force-confirms)
                                                                     │
                                                                     ▼
                                                                 DELIVERED
                                                              ProofOfDelivery
                                                         DELIVERY_CONFIRMED_SENDER
```

- **Deposit and confirmation are two separate steps for an AR letter, gated on
  `acknowledgment_of_receipt`.** `mark_deposited()` (called by an admin for the manual/internal
  provider, or an external carrier's own platform via `POST /api/webhooks/delivery/deposited`)
  means the letter was physically placed in the mailbox. Without the paid AR option there's no
  accusé de réception to collect, so it finalizes immediately -- no recipient email, sender
  notified right away. With it, it does **not** notify the sender yet: it emails the recipient a
  single-use confirmation link, and only once they click it (`confirm_delivery_by_recipient`), or
  an admin uses the `force-confirm` fallback if they never respond, does the delivery reach
  `DELIVERED` and the sender get notified. All three paths share the same idempotent
  `_finalize_delivery()` internals.
- **Two linked, not duplicated, state machines.** `DeliveryOrder.status` (`DeliveryStatus`) holds the
  detailed physical-delivery state; `Letter.status` only reflects the high-level outcome, moving
  from `SENT` straight to `DELIVERED` or `RECEIVED` (if the paid acknowledgment-of-receipt option
  was requested — this `ProofOfDelivery` *is* that accusé de réception) once the delivery is
  finalized. `SENT` never means delivered on its own.
- **The recipient's one and only digital touchpoint is the confirmation link**, and it never shows
  letter content — just enough to recognize which letter this is about (reference, sender name).
  No earlier status (`ASSIGNED`, `PICKED_UP`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`) sends anything to
  the recipient/sender, and the confirmation token is cleared the moment it's used — reusing it
  (double-submit, stale tab) 404s rather than duplicating anything.
- **Provider abstraction** (`app/services/delivery/`): `BaseDeliveryProvider` with
  `ManualDeliveryProvider` (phase 1 — no external API, admin drives every status change through
  Admin → Livraisons) as the only implementation today, selected by `DeliveryProvider.code`. A real
  carrier is a new provider class + DB row later, reporting deposits through the webhook above
  instead of the admin action — no change to `delivery_service.py`'s core logic. The UI labels the
  manual provider "suivi manuel" — it never implies real-time carrier tracking that doesn't exist yet.
- **Webhook authentication** (`app/routes/delivery_webhook.py`): a single shared secret
  (`DELIVERY_WEBHOOK_SECRET` env var, compared with `hmac.compare_digest`), not a per-provider DB
  credential — consistent with never storing carrier API keys on `DeliveryProvider` rows. An empty
  configured secret rejects every webhook call rather than silently accepting one.
- **Audit trail reuses `letter_events`** (no separate `delivery_events` table) — every delivery
  event is already scoped to one letter, so the existing `LetterEventType` enum gained
  `DELIVERY_CREATED` ... `DELIVERY_CANCELLED` (including `DELIVERY_DEPOSITED`) instead of a
  parallel table.
- **Public tracking view** (`GET /api/track/{reference}`) exposes a `DeliveryPublicView` derived
  only from `DeliveryOrder`'s own timestamp columns — never courier name/phone, admin notes, or
  internal database IDs. All delivery-mutating admin endpoints (`/api/admin/deliveries/*`,
  `/api/admin/delivery-agents/*`) require an admin JWT; the recipient confirmation route is scoped
  to a single-use token instead, and the webhook to its shared secret — neither can touch any
  delivery other than the one they were issued for.

See `.claude/skills/delivery/SKILL.md` and `docs/database.md` for the full schema.

## Admin vs. public surface

Senders track their letter by its public reference at `/track/{reference}` — no account, no
secret link. Administrators have accounts and JWT-based sessions, scoped to `/api/admin/*`. The
recipient's only credential of any kind is the single-use delivery-confirmation token, scoped to
exactly one delivery and cleared after one use. The `access_tokens` table and its model/repository
(from the now-removed content-viewing flow) remain in the codebase only to keep historical audit
data readable; nothing creates or reads a new one anymore (see `docs/database.md`).

## Legal note

Courrier+ is a **technical prototype**. It does not claim the same legal value as an official
Tunisian registered postal letter. See `docs/security.md` for the full disclaimer.
