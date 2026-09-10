---
name: resend-email
description: Resend email integration conventions and templates for Courrier+
---

# Resend Email

## Purpose
Send all transactional emails through Resend exclusively, with a safe dev/mock fallback.

## When to use it
Any time an event needs to notify a sender or recipient by email.

## Project conventions
- Single service: `app/services/email_service.py`, wrapping the Resend Python SDK (`resend` package).
- Env vars: `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `RESEND_FROM_NAME`. Read via `app/core/config.py`.
- If `RESEND_API_KEY` is empty/unset, the service runs in **mock mode**: it logs the would-be email (subject + recipient, never full body with tokens in production-style logs) and writes an `email_events` row with status `SENT` (mocked), so the rest of the app is fully testable without a real key.
- Every email send is recorded as an `email_events` row: `email_type`, `recipient`, `status` (`PENDING` → `SENT`/`FAILED`), `provider_message_id`, `error_message` (safe, no secrets).
- HTML templates live in `app/services/email_templates/` as simple Python functions returning HTML strings (Jinja2 optional but plain f-string/format templates are fine for this scale — avoid over-engineering).
- Five email types: `PAYMENT_CONFIRMATION` (sender), `RECIPIENT_NOTIFICATION` (recipient), `LETTER_OPENED` (sender), `RECEIPT_CONFIRMED` (sender), `SYSTEM_ERROR` (admin/internal, only for critical failures).

## Important rules
- Never hard-code an API key anywhere in source.
- Never put a full access token in an email log line, only in the actual email body sent to the legitimate recipient.
- Resend errors must not crash the request that triggered them — catch, log, record `FAILED` in `email_events`, and let the primary business operation (e.g. payment success) still succeed. Email is best-effort, not transactional with the core state change.
- Keep templates branded consistently: Courrier+ header, consistent color, footer disclaimer that this is not a certified legal registered mail (see legal disclaimer in README).

## Workflow to add a new email type
1. Add enum value to `EmailType` in `app/models/enums.py`.
2. Add a template function in `email_templates/`.
3. Add a `send_xxx_email()` function in `email_service.py` that renders the template, calls Resend (or mock), and writes the `email_events` row.
4. Call it from the relevant service (never from a route directly).
