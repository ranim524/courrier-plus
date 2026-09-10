---
name: project-setup
description: Environment, directory layout, and local run conventions for Courrier+
---

# Project Setup

## Purpose
Defines how the Courrier+ modular monolith is laid out and how to get it running locally on Windows without Docker.

## When to use it
- Setting up the project for the first time on a machine.
- Adding a new top-level module/folder.
- Deciding where a new file belongs.

## Project conventions
- Architecture: **modular monolith**. One FastAPI app, one React app, one PostgreSQL database. No microservices.
- Backend lives in `backend/`, frontend in `frontend/`, docs in `docs/`, skills in `.claude/skills/`.
- Backend internal layering (top to bottom, each layer only calls downward):
  `routes/` (HTTP) → `services/` (business logic) → `repositories/` (DB access) → `models/` (SQLAlchemy ORM).
  `schemas/` (Pydantic) are used by routes for request/response validation, never by repositories.
  `core/` holds cross-cutting config: settings, security helpers, DB session, logging.
  `utils/` holds small stateless helpers (hashing, token generation, filename sanitizing).
- Frontend: pages compose components; `services/` holds API client calls (axios); `types/` holds shared TS interfaces; no business logic in components beyond form/UI state.

## Important rules
- Never put business logic directly in route handlers — call a service function.
- Never query the DB directly from a route or service — go through a repository.
- Do not introduce a new top-level dependency without checking it's justified by an explicit spec requirement.
- Real `.env` files are never committed. `.env.example` is always kept up to date when a new env var is introduced.

## Local run (no Docker required)
- PostgreSQL runs as a native Windows service (`postgresql-x64-18`).
- Backend: Python venv in `backend/.venv`, run with `uvicorn app.main:app --reload`.
- Frontend: `npm run dev` (Vite) in `frontend/`.
- Docker Compose is provided for convenience/deployment parity but is optional for day-to-day dev.

## Workflow for a new feature
1. Model/migration (if data shape changes) — see [[database]] skill.
2. Backend service + repository + route + schema — see [[backend-development]] skill.
3. Frontend page/component + API service call — see [[frontend-development]] skill.
4. Tests — see [[testing]] skill.
5. Update relevant doc in `docs/`.
