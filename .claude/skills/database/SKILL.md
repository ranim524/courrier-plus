---
name: database
description: PostgreSQL schema, SQLAlchemy models, and Alembic migration conventions for Courrier+
---

# Database

## Purpose
Keep the relational schema clean, consistent, and evolvable via Alembic.

## When to use it
Any time you add/change a SQLAlchemy model or need a migration.

## Project conventions
- PostgreSQL only. SQLAlchemy 2.0-style declarative models in `backend/app/models/`, one file per entity.
- Every table: `id` (UUID primary key, server default `gen_random_uuid()` via pgcrypto, or Python-side `uuid4`), `created_at` / `updated_at` (timestamptz, server defaults `now()`).
- Public-facing identifiers (letter reference, access tokens) are **never** the raw UUID PK — see [[security]].
- Foreign keys always indexed. Add explicit `UniqueConstraint`/`Index` where the spec implies uniqueness (letter reference, admin email, token hash).
- Enums (letter status, payment status, event type, email type) use Python `enum.Enum` + SQLAlchemy `Enum` type, defined in `app/models/enums.py` so both models and schemas share them.
- Migrations are generated with Alembic autogenerate, then hand-reviewed before applying — never hand-write a migration from scratch if autogenerate can produce it, but always check the diff.

## Important rules
- Never modify a table in place with raw SQL outside a migration.
- Never store plaintext recipient access tokens — store only `token_hash` (SHA-256). See [[security]].
- Letter status changes must be inserted as a `letter_events` row in the same transaction as the status update (handled by the service layer, not the DB, since we're not using triggers for this — keep it simple/explicit).
- Keep migrations reversible (`downgrade()` implemented) where feasible.

## Workflow
1. Edit/add model in `backend/app/models/`.
2. `alembic revision --autogenerate -m "description"`.
3. Read the generated migration file, fix anything autogenerate got wrong (enum creation order, server defaults).
4. `alembic upgrade head` against the local dev DB.
5. Verify with `psql` or a quick script.

## Core tables
`admins`, `letters`, `documents`, `payments`, `access_tokens`, `letter_events`, `email_events`.
See `docs/database.md` for the full column-level schema and rationale.
