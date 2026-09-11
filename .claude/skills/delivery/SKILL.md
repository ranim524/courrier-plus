---
name: delivery
description: Physical delivery system conventions for Courrier+ (delivery orders, couriers, state machine, proof of delivery)
---

# Physical Delivery

## Purpose
Manage the real physical delivery of a printed letter from Courrier+ to the recipient — separate from, but linked to, the digital access-link flow.

## When to use it
Any time you touch `app/models/delivery.py`, `app/services/delivery_service.py`, `app/services/delivery_state.py`, `app/services/delivery/`, `app/routes/delivery.py`, or the delivery-related fields on `TrackingRead`/`AccessLetterView`.

## Project conventions
- One `DeliveryOrder` per `Letter` (unique FK), auto-created by `delivery_service.create_delivery_order()` right after a letter reaches `SENT` (called from `payment_service.confirm_payment()`). It's immediately advanced to `READY_FOR_DISPATCH` — the prototype has no separate "printed"/"prepared" step to wait on.
- Detailed physical status lives on `DeliveryOrder.status` (`DeliveryStatus`, see `delivery_state.py` for the full transition graph). `Letter.status` only reflects the high-level `DELIVERED` milestone — reuses the enum member that already existed in `LetterStatus` (dormant before this module), rather than inventing a parallel state machine. See [[database]].
- Provider abstraction mirrors [[payment]]/document-management's storage pattern exactly: `app/services/delivery/base.py` (`BaseDeliveryProvider`), `app/services/delivery/manual_provider.py` (`ManualDeliveryProvider`, phase 1 — no external API, all status changes come from admin actions), `app/services/delivery/__init__.py` (factory keyed by `DeliveryProvider.code`). A real carrier is added later as a new provider class + DB row, never by hardcoding a company name into `delivery_service.py` or routes.
- Audit events reuse the existing `letter_events` table/`LetterEventType` enum (`DELIVERY_CREATED`, `DELIVERY_ASSIGNED`, ... `DELIVERY_CANCELLED`) — no separate `delivery_events` table, since every delivery event is already scoped to exactly one letter.
- Tracking number format `CP-2026-0001847` (`app/utils/tracking_number.py`), generated the same way as the letter reference (`app/utils/reference.py`): random, unique (DB constraint + retry loop), never the row's UUID.

## Important rules
- **Only `DeliveryStatus.DELIVERED` means the physical letter reached the recipient.** No earlier status (`ASSIGNED`, `PICKED_UP`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`) may trigger a "your letter was delivered" notification. `delivery_service.confirm_delivery()` is the *only* function that sends `DELIVERY_CONFIRMED_RECIPIENT`/`DELIVERY_CONFIRMED_SENDER` emails or creates a `ProofOfDelivery`.
- `confirm_delivery()` is idempotent: confirming an already-`DELIVERED` order is a no-op (checked before any state change) — never a second proof, event, or email. See [[testing]]'s critical email test.
- `DELIVERED` is terminal — no administrative "undo" transition exists (deliberate, not an oversight). All status changes go through `delivery_state.transition()`, same explicit-allow-list pattern as `letter_state.py`.
- Every mutating delivery endpoint lives under `/api/admin/deliveries/*` (or `/api/admin/delivery-agents/*`), behind `get_current_admin` — there is no sender/recipient-facing route that can change a delivery's status.
- No API credentials are ever stored on `DeliveryProvider` rows, even for a future external carrier with `api_enabled=True` — they belong in environment variables, referenced by the provider's `code`. See [[security]].
- Public views (`GET /api/track/{reference}`, `GET /api/access/{token}`) expose a `DeliveryPublicView` derived only from `DeliveryOrder`'s own timestamp columns — never courier name/phone, admin notes, or internal UUIDs. Built by `delivery_service.to_public_view()`.
- `DeliveryAttempt` rows are created only on failure (`mark_failed`); a successful delivery gets a `ProofOfDelivery`, not an attempt row.

## Workflow to add a new admin action
1. Add the transition to `ALLOWED_TRANSITIONS` in `delivery_state.py` if it's a new edge.
2. Add the function in `delivery_service.py`: call `delivery_state.transition()`, set the relevant timestamp column, record the matching `LetterEventType`, commit.
3. Add the route in `app/routes/delivery.py` (admin-only), calling the service function and returning `delivery_service.to_read()`.
4. Add a test in `tests/test_delivery.py` (service-level) and/or `tests/test_delivery_routes.py` (API-level).

## Testing gotcha
The test DB schema is built via `Base.metadata.create_all()` (see [[testing]]/conftest.py), not by running real Alembic migrations — so seed data a migration inserts (the `courrier_plus_internal` provider row) must also be seeded in `conftest.py`'s `_seed_reference_data()`. Similarly, adding a new Python-side enum member (`LetterEventType`, `EmailType`, `DeliveryStatus`, etc.) does **not** alter the actual Postgres enum type in a real deployment — that needs an explicit `ALTER TYPE ... ADD VALUE` migration (see `43aa24b4be43_add_delivery_event_and_email_enum_values.py`) even though `create_all` masks this gap in tests. This exact gap broke delivery event recording the first time it was tested live — always verify a new enum member against the real dev DB, not just the test suite, before considering it done.
