# Database Schema — Courrier+

PostgreSQL, managed with SQLAlchemy models + Alembic migrations. All primary keys are UUIDs.
All tables have `created_at`/`updated_at` timestamptz columns.

## `admins`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | varchar(255) | unique, indexed |
| password_hash | varchar(255) | bcrypt |
| full_name | varchar(255) | nullable |

## `letters`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | internal identifier, never exposed publicly |
| reference | varchar(32) | unique, nullable until payment succeeds (e.g. `TN-2026-0001847`) |
| sender_first_name / last_name / email / phone | | captured per letter, no account |
| recipient_first_name / last_name / email / phone | | captured per letter, no account |
| subject | varchar(255) | |
| message | text | nullable — mutually exclusive with an attached document |
| content_type | enum | `TEXT_MESSAGE` \| `PDF_UPLOAD` |
| status | enum | see lifecycle below |
| page_count | integer | PDF page count (or 1 for a text-only letter), determined server-side |
| estimated_weight_g | integer | `page_count * ESTIMATED_GRAMS_PER_PAGE` (see `pricing_service.py`) |
| weight_bracket | varchar(20) | label of the matched tariff bracket, e.g. `20-100g` |
| base_postage | numeric(10,3) | postage for the matched weight bracket |
| registered_fee | numeric(10,3) | fixed registered-mail fee |
| acknowledgment_of_receipt | boolean | whether the sender requested an accusé de réception |
| acknowledgment_fee | numeric(10,3) | AR fee, `0` if not requested |
| total_amount / currency | numeric(10,3) / varchar(3) | full price snapshot at creation time |

**Status enum**: `DRAFT → PENDING_PAYMENT → PAID → SENT → DELIVERED → OPENED → RECEIVED`, with
exceptional states `FAILED`, `REFUSED`, `EXPIRED`, `CANCELLED`. Transitions are enforced in code
(`app/services/letter_state.py`), not by a DB trigger — kept simple and explicit.

**Pricing is a snapshot, not a live calculation.** `total_amount` and the rest of the pricing
breakdown are computed once by `app/services/pricing_service.py` at letter-creation time and
stored on the row. If the tariff configuration (brackets, fees, grams-per-page) changes later,
already-created letters keep the price they were created with — nothing is recomputed
retroactively. See `docs/api.md` for the pricing endpoints and `pricing_service.py` for the tariff
table itself.

## `documents`
One-to-one with `letters` (unique FK). Stores `original_filename` (display only),
`internal_filename` + `storage_path` (never derived from user input), `mime_type`, `size_bytes`,
and `sha256` (integrity hash of the actual file bytes).

## `payments`
| Column | Type | Notes |
|---|---|---|
| letter_id | UUID FK | indexed |
| provider | varchar(50) | `mock` for now |
| transaction_id | varchar(100) | unique — used as the idempotency key |
| amount / currency | | |
| status | enum | `PENDING`, `PAID`, `FAILED`, `REFUNDED` |

## `access_tokens`
| Column | Type | Notes |
|---|---|---|
| letter_id | UUID FK | indexed |
| token_hash | varchar(64) | SHA-256 of the raw token — the raw value is **never** stored |
| expires_at | timestamptz | default 30 days from issuance |
| revoked_at | timestamptz | nullable |
| last_used_at | timestamptz | nullable |

## `letter_events`
Append-only audit trail. `event_type` (enum), `actor_type` (`SENDER`/`RECIPIENT`/`ADMIN`/`SYSTEM`),
optional `ip_address`/`user_agent`, and a `event_metadata` JSONB column for extra context.

## `email_events`
One row per email attempt. `email_type` (enum), `recipient`, `status` (`PENDING`/`SENT`/`FAILED`),
`provider_message_id`, and a safe `error_message` (no secrets).

## Relationships

```
letters 1───1 documents
letters 1───N payments
letters 1───N access_tokens
letters 1───N letter_events
letters 1───N email_events
```

## Migrations

Generated with Alembic autogenerate against the SQLAlchemy models, then hand-reviewed:

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```
