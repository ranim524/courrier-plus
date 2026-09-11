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
| sheet_count | integer | physical sheets to print: `page_count` (simplex) or `ceil(page_count/2)` (duplex) |
| printing_mode | varchar(20) | `black_and_white` or `color` |
| printing_sides | varchar(10) | `single` (recto) or `double` (recto-verso) |
| paper_weight_g | numeric(10,3) | `sheet_count * PAPER_WEIGHT_PER_SHEET_G` |
| envelope_weight_g | numeric(10,3) | fixed envelope weight |
| estimated_weight_g | numeric(10,3) | `paper_weight_g + envelope_weight_g` — an estimate, not a scale reading |
| weight_bracket | varchar(20) | label of the matched postal tariff bracket, e.g. `21-100g` |
| printing_cost | numeric(10,3) | `page_count * cost-per-page` for the chosen printing mode |
| paper_cost | numeric(10,3) | `sheet_count * PAPER_COST_PER_SHEET` |
| envelope_cost | numeric(10,3) | fixed envelope cost |
| postal_postage | numeric(10,3) | postage for the matched weight bracket |
| registered_mail_fee | numeric(10,3) | fixed registered-mail (recommandation) fee, mandatory |
| acknowledgment_of_receipt | boolean | whether the sender requested an accusé de réception |
| acknowledgment_fee | numeric(10,3) | AR fee, `0` if not requested |
| delivery_fee | numeric(10,3) | configurable delivery/logistics fee (currently `0`, included in postage) |
| service_fee | numeric(10,3) | Courrier+'s own platform/processing fee |
| total_amount / currency | numeric(10,3) / varchar(3) | full price snapshot at creation time (sum of all the above cost/fee columns) |

**Status enum**: `DRAFT → PENDING_PAYMENT → PAID → SENT → DELIVERED → OPENED → RECEIVED`, with
exceptional states `FAILED`, `REFUSED`, `EXPIRED`, `CANCELLED`. Transitions are enforced in code
(`app/services/letter_state.py`), not by a DB trigger — kept simple and explicit.

**Pricing is a snapshot, not a live calculation.** `total_amount` and the rest of the pricing
breakdown are computed once by `app/services/pricing_service.py` at letter-creation time and
stored on the row. If the tariff/printing configuration changes later, already-created letters
keep the price they were created with — nothing is recomputed retroactively. See `docs/api.md` for
the pricing endpoints and `pricing_service.py` for the tariff table itself.

## `documents`
One-to-one with `letters` (unique FK). Stores `original_filename` (display only),
`internal_filename` + `storage_path` (never derived from user input), `mime_type`, `size_bytes`,
and `sha256` (integrity hash of the actual file bytes). `storage_path` is a logical key interpreted
by whichever `StorageProvider` is active (`local`, `database`, or `r2`) — it's a filesystem path for
local, an S3 object key for R2, and the primary key of `document_blobs` for the database provider.

## `document_blobs`
Only populated when `STORAGE_PROVIDER=database`. Holds the actual file bytes when documents are
stored directly in Postgres instead of a separate object-storage service (see
`app/services/storage/database_provider.py` and `docs/deployment.md`).

| Column | Type | Notes |
|---|---|---|
| storage_path | varchar(500) PK | same value as `documents.storage_path` — a natural key, no surrogate UUID since this table is internal storage plumbing, never exposed via the API |
| data | bytea | raw file bytes |

Not linked to `documents` by a foreign key — same decoupling as the local-filesystem and R2
providers, where the storage layer never knows about the `documents` table.

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

## Physical delivery tables

See `docs/architecture.md`'s "Physical delivery system" section and `.claude/skills/delivery/SKILL.md`
for the full design rationale. `DeliveryOrder`'s detailed status is separate from, but linked to,
`letters.status` (which only reflects the high-level `DELIVERED` milestone).

### `delivery_providers`
| Column | Type | Notes |
|---|---|---|
| code | varchar(50) | unique, stable identifier (`courrier_plus_internal` is seeded by migration) |
| name | varchar(100) | display name, e.g. "Courrier+ Delivery" |
| provider_type | enum | `INTERNAL` \| `EXTERNAL_CARRIER` \| `POSTAL_SERVICE` |
| active | boolean | |
| api_enabled | boolean | `false` for the manual provider |
| api_base_url | varchar(255) | nullable — **never** a credential; a future carrier's API key lives in an env var, not here |

### `delivery_agents`
Couriers, admin-managed only (never exposed to senders/recipients). `provider_id` FK, `first_name`,
`last_name`, `phone`, `email` (nullable), `active`.

### `delivery_orders`
One-to-one with `letters` (unique FK). `tracking_number` (unique, e.g. `CP-2026-0001847` — never the
row's UUID), `provider_id` FK, `courier_id` FK (nullable until assigned), `status` (`DeliveryStatus`
enum, indexed), `attempt_count`, and a timestamp column per major milestone: `assigned_at`,
`picked_up_at`, `in_transit_at`, `out_for_delivery_at`, `delivered_at`, `failed_at`, `returned_at`
(plus `created_at`/`updated_at` from the standard mixin). These timestamps are also what
`delivery_service.to_public_view()` uses to build the public tracking timeline.

### `delivery_attempts`
One row per **failed** delivery attempt (a successful one gets a `proofs_of_delivery` row instead).
`delivery_id` FK, `attempt_number`, `attempted_at`, `courier_id` (nullable), `reason`
(`DeliveryFailureReason` enum), `notes` (nullable).

### `proofs_of_delivery`
One-to-one with `delivery_orders` (unique FK), created exactly once by the idempotent
`confirm_delivery()`. `delivered_at`, `delivered_by` (the confirming admin's email),
`recipient_name_if_provided` (nullable), `delivery_method` (nullable), `proof_type`
(`MANUAL_CONFIRMATION` for the current prototype — the column also supports `SIGNATURE`/`OTP`/
`PHOTO`/`EXTERNAL_PROVIDER_CONFIRMATION` for later, but only ever set to a type that was actually
captured), `proof_reference` (nullable, for a future signature/photo file reference), `notes`.

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
