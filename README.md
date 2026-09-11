# Courrier+

Digital registered mail platform for Tunisia — a technical prototype letting a sender deliver a
document or message to a recipient with a tracked lifecycle (payment → sent → opened → received),
without either party needing an account.

> **Legal notice**: Courrier+ is a technical prototype. It does not carry the same legal value as
> an official Tunisian registered postal letter. See [`docs/security.md`](docs/security.md) for
> details.

## Features

- No-account sender/recipient flow: write a message or upload a PDF, pay, and Courrier+ prints and
  physically delivers it. The recipient never gets an account, an email, or any digital access to
  the content — only the physical letter, and a confirmation email once it's actually delivered.
- Unique public letter reference (`TN-2026-0001847`) generated only after successful payment.
- Full lifecycle tracking (`DRAFT → PENDING_PAYMENT → PAID → SENT → DELIVERED`/`RECEIVED`, plus
  `FAILED`/`REFUSED`/`EXPIRED`/`CANCELLED`) with an explicit, validated state machine and full
  audit trail.
- SHA-256 integrity hash on every uploaded document.
- Transactional emails via Resend (payment confirmation to the sender, delivery-confirmed emails to
  both sender and recipient once physical delivery is confirmed), with a safe mock mode when no API
  key is configured.
- Abstracted mock payment provider (idempotent), designed to be swapped for a real Tunisian
  provider later without touching the rest of the app.
- Physical delivery system: Courrier+ prints and physically delivers the letter — delivery orders,
  couriers, a validated state machine (`ASSIGNED → PICKED_UP → IN_TRANSIT → OUT_FOR_DELIVERY →
  DELIVERED`), proof of delivery, and delivery-confirmed emails that only ever fire once the
  physical letter is actually confirmed delivered. See "Physical delivery" below.
- Admin dashboard: stats, letters (search/filter/paginate), letter detail with document hash and
  full event/email history, deliveries (assign/track/confirm), payments, email log.

## Architecture

Modular monolith: React + TypeScript (Vite, Tailwind) frontend, FastAPI + SQLAlchemy + Alembic
backend, PostgreSQL. See [`docs/architecture.md`](docs/architecture.md) for the full breakdown and
[`docs/database.md`](docs/database.md) for the schema.

## Technologies

**Frontend**: React, TypeScript, Vite, Tailwind CSS v4, React Router, Axios.
**Backend**: Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL, python-jose (JWT),
passlib/bcrypt, slowapi (rate limiting), Resend SDK.
**Testing**: pytest, FastAPI `TestClient`.
**DevOps**: Git, Docker/Docker Compose, `.env`-based configuration.

## Prerequisites

- Python 3.11+
- Node.js 22+ / npm
- PostgreSQL (running locally, or via Docker Compose)

## Quick start (local, no Docker)

### 1. Database
Create a dedicated role/database (see [`docs/deployment.md`](docs/deployment.md) if you need to
do this from scratch on Windows):
```sql
CREATE ROLE courrier_plus WITH LOGIN PASSWORD 'courrier_plus_dev_pw' CREATEDB;
CREATE DATABASE courrier_plus OWNER courrier_plus;
```

### 2. Backend
```bash
cd backend
python -m venv .venv
./.venv/Scripts/pip install -r requirements.txt
# .env is already provided for local dev; copy .env.example to adjust elsewhere
alembic upgrade head
python -m app.scripts.create_admin
uvicorn app.main:app --reload
```
Backend runs at http://localhost:8000 (interactive docs at `/docs`).

To change an existing admin's password later: `python -m app.scripts.change_admin_password <email>`
(prompts for the new password interactively — never pass it as a command-line argument).

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at http://localhost:5173.

### 4. Tests
```bash
cd backend
pytest -q
```

## Environment variables

See `backend/.env.example` and `frontend/.env.example`. Key ones:

- `DATABASE_URL` — PostgreSQL connection string.
- `SECRET_KEY` / `JWT_SECRET` — generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- `RESEND_API_KEY` — leave empty for development; the app runs in a safe mock email mode and logs
  what would have been sent. Get a real key at https://resend.com when ready for real delivery.
- `PAYMENT_PROVIDER=mock` — the only provider implemented so far; see `docs/architecture.md` for
  how to add a real one.
- `CURRENCY=TND` — currency shown throughout the app and emails. There is no fixed price env var:
  pricing is dynamic (see below).

## Pricing

Courrier+ actually prints the uploaded PDF, puts it in an envelope, and sends it as physical
registered mail — the price reflects that real physical service:

```
TOTAL = printing cost + paper cost + envelope cost + postage (by estimated weight)
        + registered-mail fee (3.000 TND) + AR fee (2.500 TND, optional)
        + delivery fee + Courrier+ service fee
```

The backend determines everything server-side and never trusts a price, page count, sheet count,
or weight sent by the client:

1. Count the PDF's pages (`pypdf`, never from the client).
2. Convert pages to physical sheets — `sheet_count = page_count` (simplex, default) or
   `ceil(page_count / 2)` (duplex).
3. Estimate the physical weight — `sheet_count × 5g (paper) + 10g (envelope)` ("poids estimé", not
   a scale reading).
4. Match the Tunisian Post internal-letter weight bracket for postage.
5. Sum printing (`0.150 TND/page`), paper (`0.050 TND/sheet`), envelope (`0.500 TND`), postage,
   the mandatory registered-mail fee, optional AR fee, delivery fee (currently `0`, included in
   postage), and the Courrier+ service fee (`1.000 TND`).

Maximum document weight accepted: 2000g (~398 pages simplex, ~796 duplex — the limit is on weight,
not a fixed page count, since duplex fits roughly twice as many pages per envelope).

- `POST /api/pricing/preview` — live price preview used by the send-letter wizard as the sender
  uploads a PDF or toggles "Avec accusé de réception".
- `POST /api/pricing/calculate` — pure calculation from an already-known page count.

All constants (printing/paper/envelope costs, postal tariff table, service fee, etc.) are
centralized in `app/services/pricing_service.py` — **initial prototype defaults, not verified
market prices**. The full breakdown is stored on the `letters` row as a snapshot at creation time
— see `docs/database.md`. If the tariff/printing configuration changes later, letters already
created keep their original price.

> Courrier+'s paper/envelope weight model is an estimate ("poids estimé"), not the letter's actual
> weighed mass, and the postal tariff values are prototype defaults inspired by the Tunisian Post
> tariff table — verify them before real production use. Courrier+ digitizes the ordering,
> tracking and notification experience around a real physical mailing; it does not by itself
> establish legal equivalence with an official La Poste Tunisienne registered letter.

## Physical delivery

Courrier+ prints the uploaded PDF and physically delivers it — this is tracked as a `DeliveryOrder`,
separate from (but linked to) the letter's own lifecycle:

```
Letter SENT (auto-creates the DeliveryOrder)
  → READY_FOR_DISPATCH → ASSIGNED → PICKED_UP → IN_TRANSIT → OUT_FOR_DELIVERY
  → DEPOSITED (letter physically placed in the mailbox — admin action, or an
               external carrier's own platform via a webhook)
      → recipient emailed a single-use link to confirm receipt
  → DELIVERED (recipient confirms, or an admin force-confirms as a fallback)
      → proof of delivery + delivery-confirmed email to the sender
      → Letter.status becomes RECEIVED (if acknowledgment of receipt was paid for)
        or DELIVERED (otherwise) — the only way a letter ever leaves SENT
```
or, on a failed attempt: `OUT_FOR_DELIVERY → DELIVERY_FAILED → (retry) or RETURNED_TO_SENDER`.

**Deposit and confirmation are two separate steps.** Placing the letter in the mailbox doesn't
notify anyone by itself — it emails the recipient a single-use link asking them to confirm receipt,
and only that confirmation (or an admin's manual override, if the recipient never responds) notifies
the sender. This is the recipient's *only* digital touchpoint: the link never shows the letter's
content, just enough to recognize which letter it's about, and it's single-use (reusing it 404s
rather than duplicating anything). Admins manage the whole flow from **Admin → Livraisons** (assign
a courier, advance status, mark deposited, force-confirm) and **Admin → Livreurs**
(add/deactivate couriers). The public tracking page shows the delivery status/timeline, without any
courier or admin-only details.

A real external carrier reports a deposit through `POST /api/webhooks/delivery/deposited`
(authenticated by `DELIVERY_WEBHOOK_SECRET`) instead of the admin clicking a button — same
underlying `mark_deposited()` call, no change anywhere else.

Phase 1 ships one seeded provider, "Courrier+ Delivery" (manual/internal — every status change is
a direct admin action, labeled "suivi manuel" in the UI since there's no real-time carrier feed).
The provider is abstracted (`app/services/delivery/`, `BaseDeliveryProvider`) so a real external
carrier can be added later as a new provider class + DB row without touching the delivery service,
routes, or admin UI above it. See `docs/architecture.md` and `.claude/skills/delivery/SKILL.md`.

## Resend setup

1. Create a Resend account and a verified sending domain.
2. Set `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `RESEND_FROM_NAME` in `backend/.env`.
3. Restart the backend — emails will now be sent for real instead of logged in mock mode.

## Mock payment

`PAYMENT_PROVIDER=mock` is the default. The send-letter flow calls `POST /api/payments/create`
(amount = the letter's computed `total_amount`), then `POST /api/payments/mock/confirm` to simulate
success or failure — no real payment account or credentials are involved. See
`docs/architecture.md` for how a real Tunisian provider would plug into the same `PaymentProvider`
interface.

## Docker

```bash
docker compose build
docker compose up
```
The backend's entrypoint (`backend/docker-entrypoint.sh`) runs `alembic upgrade head` and, if
`FIRST_ADMIN_EMAIL`/`FIRST_ADMIN_PASSWORD` are set, bootstraps the first admin automatically on
every container start — no separate `docker compose run` step needed (safe to run repeatedly:
migrations no-op once applied, admin bootstrap no-ops once the account exists).

See [`docs/deployment.md`](docs/deployment.md) for details. Docker is optional — the app runs
fully locally without it.

## Production deployment (Cloudflare)

- **Frontend** → Cloudflare Pages (static build, free)
- **Backend** → Render (Docker, free tier — sleeps after 15min inactivity)
- **Database** → Neon (serverless PostgreSQL, free tier)
- **Documents** → stored as bytes in that same Postgres database
  (`STORAGE_PROVIDER=database`, see `app/services/storage/database_provider.py`) — no third-party
  object-storage account needed. The storage layer is abstracted (`app/services/storage/`), so an
  S3-compatible provider like Cloudflare R2 (`STORAGE_PROVIDER=r2`, already implemented) is a
  config-only swap later if document volume grows past what's comfortable in the database. R2
  itself requires adding a billing method even for its free tier, which is why it isn't the default.

Full step-by-step instructions (account creation, env vars, `render.yaml`, CORS, DNS) are in
[`docs/deployment.md`](docs/deployment.md#production-deployment-cloudflare-pages-render-neon).

## Security

See [`docs/security.md`](docs/security.md) for the full list of implemented measures (token
hashing/expiration, password hashing, JWT auth, file validation, rate limiting, audit logging,
idempotent payments, and the legal/certification disclaimer).

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/database.md`](docs/database.md)
- [`docs/api.md`](docs/api.md)
- [`docs/security.md`](docs/security.md)
- [`docs/deployment.md`](docs/deployment.md)

## Claude Code Skills

Project-specific Skills used throughout development live in `.claude/skills/`: project-setup,
backend-development, database, frontend-development, security, resend-email,
document-management, payment, delivery, testing, deployment, code-review, documentation.
