---
name: testing
description: pytest conventions and required coverage for Courrier+ backend
---

# Testing

## Purpose
Ensure the critical business flows (letter lifecycle, payment, tokens, admin auth) are covered and regressions are caught.

## When to use it
After implementing or changing any backend behavior; before considering a phase "done".

## Project conventions
- `pytest` + FastAPI `TestClient`, tests in `backend/tests/`, one file per resource (`test_letters.py`, `test_payments.py`, `test_access.py`, `test_admin.py`, `test_tracking.py`, `test_e2e_happy_path.py`).
- Use a separate test database (`courrier_plus_test`) or a transactional rollback fixture per test — never run tests against the dev data you care about.
- Fixtures in `conftest.py`: `db_session`, `client`, `sample_letter`, `admin_token`.
- Mock the email service (Resend) in tests by default (dev/mock mode is already safe — assert on `email_events` rows rather than real network calls).

## Required coverage (do not consider testing "done" without these)
- Letter creation (valid + missing fields + invalid email + invalid PDF + oversized file).
- Reference generation format + uniqueness.
- SHA-256 correctness for a known file.
- Token generation randomness/format, invalid token access (404), expired token access (410/403), revoked token.
- Recipient access flow: open event recorded, receipt confirmation, invalid status transition rejected.
- Payment: success, failure, duplicate webhook/confirm call (idempotency — assert no duplicate letter/payment/email).
- Admin: login success/failure, unauthorized access to admin routes without token.
- Resend failure handling (simulate exception, assert graceful degradation + `email_events` FAILED row).
- End-to-end happy path per `docs/architecture.md` (create → pay → sent → opened → received → sender notified).
- **Physical delivery (see [[delivery]])**: full status walk (assign → pickup → in-transit → out-for-delivery → confirm), invalid transitions rejected, tracking number uniqueness. **Critical test**: no delivery-confirmed email at any status before `DELIVERED`, exactly one recipient + one sender email on confirm, no duplicate on a repeated confirm call (`test_delivery_routes.py::test_no_delivery_email_before_delivered_then_exactly_one_on_confirm`) — this is the single most important delivery test, don't skip or weaken it.

## Testing gotcha: Postgres enum values
The test DB is built via `Base.metadata.create_all()`, which creates every enum type fresh from
the current Python definition — this **masks** a real gap: adding a new Python-side enum member
(`LetterEventType`, `EmailType`, etc.) does not alter an already-migrated Postgres enum type in a
real deployment. Tests will pass even if you forgot the `ALTER TYPE ... ADD VALUE` migration; only
running the app live against the dev DB catches it. Always verify a new enum member against the
real dev DB (create a row using it), not just `pytest`, before considering it done.

## Workflow
1. Write/extend the test alongside the feature (not after everything is built).
2. Run `pytest -q` from `backend/`.
3. Fix failures before moving to the next phase.
4. For a new enum member, also verify live against the dev DB (see gotcha above).
