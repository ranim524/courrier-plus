---
name: deployment
description: Docker/Compose and environment conventions for running Courrier+ beyond local dev
---

# Deployment

## Purpose
Provide a reproducible way to run the whole stack (frontend, backend, PostgreSQL) via Docker Compose, while keeping plain local dev (no Docker) fully supported.

## When to use it
When touching `docker-compose.yml`, Dockerfiles, or deployment-related env vars.

## Project conventions
- `docker-compose.yml` at repo root defines three services: `db` (postgres:18-alpine equivalent), `backend` (FastAPI + Uvicorn), `frontend` (Vite build served or dev server).
- `backend/Dockerfile` and `frontend/Dockerfile` are minimal, multi-stage where it helps (frontend: build then serve static via a lightweight server).
- All configuration via environment variables — no secrets baked into images.
- Resend is an external SaaS — never containerized.
- Local (non-Docker) dev remains the primary/simplest path for a student; Docker is offered as a convenience/production-parity option, not a requirement.

## Important rules
- Never commit a real `.env`; `docker-compose.yml` references `.env` via `env_file` and ships a matching `.env.example`.
- Database data persisted via a named volume, not bind-mounted into a random host path.
- Keep the Compose file simple — no orchestration beyond what these 3 services need (no k8s, no service mesh).

## Workflow
1. `docker compose build`
2. `docker compose up -d db` then run migrations (`docker compose run backend alembic upgrade head`)
3. `docker compose up`
