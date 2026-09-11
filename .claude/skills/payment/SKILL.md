---
name: payment
description: Payment abstraction and mock provider conventions for Courrier+
---

# Payment

## Purpose
Provide a payment abstraction so a real Tunisian payment provider can be plugged in later without rewriting the app.

## When to use it
Any time you touch payment creation, status, or webhook handling.

## Project conventions
- Interface: `app/services/payment/base.py` — `PaymentProvider.create_payment(amount, currency, letter_id) -> PaymentIntent` and `PaymentProvider.handle_webhook(payload, headers) -> PaymentResult`.
- `app/services/payment/mock_provider.py` implements it: `create_payment` returns a fake intent immediately payable via a `/api/payments/mock/confirm` dev-only endpoint, simulating SUCCESS or FAILED.
- Provider selection via `PAYMENT_PROVIDER` env var (`mock` for now), resolved in `app/services/payment/__init__.py::get_payment_provider()`.
- Payment states: `PENDING`, `PAID`, `FAILED`, `REFUNDED` — stored in `payments.status`, transitions only via `app/services/payment_service.py`.
- Amount is **not** a fixed config value: it comes from `app/services/pricing_service.py::calculate_letter_price()`, a physical-mail pricing pipeline (PDF page count → physical sheets → paper+envelope weight → postal tariff bracket, plus printing/paper/envelope/registered-mail/AR/delivery/Courrier+ service fees — see [[document-management]] for page counting). `CURRENCY=TND` is still a config scalar. `payment_service.create_payment()` always reads `letter.total_amount` (the snapshot stored at letter creation) — never a client-supplied amount, and never recomputed after the fact.
- Frontend never computes or sends a price: it calls `POST /api/pricing/preview` for a live display estimate, but the authoritative amount is whatever the backend stored on the letter at creation time.

## Important rules
- **Idempotency is mandatory.** Webhook/confirm handling must check current payment status before transitioning — a repeated call with the same `transaction_id` must not create a duplicate payment, letter activation, or email. Use the payment's unique `transaction_id` as the idempotency key and short-circuit if already processed.
- The letter is only finalized (reference generated, status moved to `PAID`) after the payment service confirms success — never before.
- No real payment credentials/API calls in this phase — mock only, clearly documented as such.

## Workflow
1. Sender reaches review step → frontend calls `POST /api/payments/create`.
2. Backend creates a `payments` row (`PENDING`) via the configured provider.
3. Frontend "pays" (mock UI action) → calls the mock confirm endpoint.
4. Backend verifies idempotently, updates payment to `PAID`/`FAILED`, and if `PAID`, calls `letter_service.mark_paid()` which generates the reference, moves the letter to `PAID` then `SENT`, creates events, and triggers the recipient email.
