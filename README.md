# Courrier+

Digital registered mail platform for Tunisia — a technical prototype letting a sender deliver a
document or message to a recipient with a tracked lifecycle (payment → sent → opened → received),
without either party needing an account.

> **Legal notice**: Courrier+ is a technical prototype. It does not carry the same legal value as
> an official Tunisian registered postal letter. See [`docs/security.md`](docs/security.md) for
> details.

## Features

- No-account sender/recipient flow: write a message or upload a PDF, pay, and a secure link is
  emailed to the recipient.
- Unique public letter reference (`TN-2026-0001847`) generated only after successful payment.
- Cryptographically random, hashed, expiring recipient access tokens.
- Full lifecycle tracking (`DRAFT → PENDING_PAYMENT → PAID → SENT → OPENED → RECEIVED`, plus
  `FAILED`/`REFUSED`/`EXPIRED`/`CANCELLED`) with an explicit, validated state machine and full
  audit trail.
- SHA-256 integrity hash on every uploaded document.
- Transactional emails via Resend (payment confirmation, recipient notification, letter opened,
  receipt confirmed), with a safe mock mode when no API key is configured.
- Abstracted mock payment provider (idempotent), designed to be swapped for a real Tunisian
  provider later without touching the rest of the app.
- Admin dashboard: stats, letters (search/filter/paginate), letter detail with document hash and
  full event/email history, payments, email log.

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

Courrier+ prices each letter dynamically, modeled on the Tunisian Post's weight-based registered-mail
tariff:

```
TOTAL = postage (by estimated weight) + registered-mail fee (3.000 TND) + AR fee (2.500 TND, optional)
```

Since Courrier+ is digital, weight is **estimated** from the PDF's page count
(`ESTIMATED_GRAMS_PER_PAGE = 5`, configurable in `app/services/pricing_service.py`) — a
text-only letter is priced as a single page. The backend always determines the page count itself
from the uploaded PDF bytes; it never trusts a price, page count, or weight sent by the client.
Maximum document size accepted: 400 pages (2000g equivalent).

- `POST /api/pricing/preview` — live price preview used by the send-letter wizard as the sender
  uploads a PDF or toggles "Avec accusé de réception".
- `POST /api/pricing/calculate` — pure calculation from an already-known page count.

The computed breakdown (`page_count`, `estimated_weight_g`, `weight_bracket`, `base_postage`,
`registered_fee`, `acknowledgment_fee`, `total_amount`) is stored on the `letters` row as a
snapshot at creation time — see `docs/database.md`. If the tariff table changes later, letters
already created keep their original price.

> Courrier+'s page-based weight estimate is a pricing convention inspired by the Tunisian Post
> tariff table. It does not represent the actual physical weight of a printed document, and does
> not by itself establish legal equivalence with physical registered mail.

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
docker compose up -d db
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.scripts.create_admin
docker compose up
```
See [`docs/deployment.md`](docs/deployment.md) for details. Docker is optional — the app runs
fully locally without it.

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
document-management, payment, testing, deployment, code-review, documentation.
