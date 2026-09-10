---
name: code-review
description: Self-review checklist to apply before considering a Courrier+ phase complete
---

# Code Review

## Purpose
A consistent checklist applied at the end of each development phase, and at the final review (Phase 25).

## When to use it
Before marking any phase "done", and as a final pass over the whole codebase.

## Checklist
- **Layering**: routes contain no business logic; services contain no raw SQL; repositories contain no business rules.
- **Security** (cross-check against [[security]]): no plaintext tokens/passwords anywhere, uploads validated, admin routes protected, CORS restricted, no secrets in source.
- **Consistency**: error responses use `{"detail": ...}`; status codes correct; enums shared between models/schemas.
- **No dead code / no premature abstraction**: no unused files, no speculative interfaces beyond what's specified (payment/storage abstraction is explicitly required — don't add more).
- **Frontend**: no `any` without justification, responsive at mobile width, loading/error states present, no raw HTML injection.
- **Tests**: required coverage from [[testing]] present and passing.
- **Docs**: `docs/*.md` reflect the current state of what was actually built, not just the plan.
- **Env**: every new env var appears in `.env.example` with a comment.

## Workflow
1. Re-read the diff/feature against this checklist.
2. Fix anything failing before moving on.
3. At the final review (end of build), run the full checklist against the entire repo once more and record findings/fixes in the final report.
