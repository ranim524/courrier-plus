---
name: documentation
description: Documentation structure and conventions for Courrier+
---

# Documentation

## Purpose
Keep `README.md` and `docs/` accurate, beginner-friendly, and useful as the single source of truth for running and understanding the project.

## When to use it
Whenever a feature, endpoint, table, or env var is added/changed — update the relevant doc in the same session, not "later".

## Structure
- `README.md`: project description, features, quick start (install/run/test), env vars overview, links to `docs/`.
- `docs/architecture.md`: modular monolith overview, layering diagram (text), main business flow.
- `docs/database.md`: full schema (tables, columns, types, constraints, relationships) and rationale.
- `docs/api.md`: endpoint list with method, path, auth requirement, request/response shape (kept in sync with FastAPI's auto-generated OpenAPI docs at `/docs`, but written for humans).
- `docs/security.md`: concrete list of implemented security measures + the legal/certification disclaimer.
- `docs/deployment.md`: local run (no Docker) and Docker Compose run instructions.

## Important rules
- Write for a CS student audience: clear, concrete, no marketing fluff.
- Never claim legal/certification value beyond what's actually implemented (see disclaimer requirement in the top-level spec).
- Keep examples runnable/copy-pasteable (real commands, real paths for this repo).
