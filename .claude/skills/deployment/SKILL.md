---
name: deployment
description: Docker/Compose and environment conventions for running Courrier+ beyond local dev
---

# Deployment

## Purpose
Provide a reproducible way to run the whole stack locally (Docker Compose) and in production
(Cloudflare Pages + R2, Render, Neon), while keeping plain local dev (no Docker) fully supported.

## When to use it
When touching `docker-compose.yml`, Dockerfiles, `render.yaml`, `frontend/public/_redirects`, or
deployment-related env vars.

## Project conventions
- `docker-compose.yml` at repo root defines three services: `db` (postgres:18-alpine equivalent), `backend` (FastAPI + Uvicorn), `frontend` (Vite build served or dev server).
- `backend/Dockerfile` and `frontend/Dockerfile` are minimal, multi-stage where it helps (frontend: build then serve static via a lightweight server).
- All configuration via environment variables — no secrets baked into images.
- Resend is an external SaaS — never containerized.
- Local (non-Docker) dev remains the primary/simplest path for a student; Docker is offered as a convenience/production-parity option, not a requirement.
- **Production topology** (see `docs/deployment.md` for the full step-by-step): Cloudflare Pages
  (frontend, static build, reads `frontend/public/_redirects` for SPA routing) + Render (backend,
  builds `backend/Dockerfile` directly from `render.yaml` at the repo root) + Neon (PostgreSQL) +
  Cloudflare R2 (documents, via `STORAGE_PROVIDER=r2` — see [[document-management]]). Chosen because
  Cloudflare Workers don't run a Python/SQLAlchemy/psycopg2/bcrypt stack natively; this hybrid keeps
  the existing backend as-is.
- `render.yaml` lists every env var with `sync: false` for anything secret (Render prompts for it
  in the dashboard instead of storing it in the repo) — never put a real secret value in `render.yaml`.

## Important rules
- Never commit a real `.env`; `docker-compose.yml` references `.env` via `env_file` and ships a matching `.env.example`.
- Database data persisted via a named volume, not bind-mounted into a random host path.
- Keep the Compose file simple — no orchestration beyond what these 3 services need (no k8s, no service mesh).
- `FRONTEND_URL` on the backend must exactly match the deployed Cloudflare Pages URL — CORS in `app/main.py` only allows that one origin.

## Workflow (local, Docker Compose)
1. `docker compose build`
2. `docker compose up -d db` then run migrations (`docker compose run backend alembic upgrade head`)
3. `docker compose up`

## Workflow (production)
1. Push to GitHub.
2. Neon: create project, copy `DATABASE_URL`.
3. Cloudflare R2: create bucket + API token, note account ID/keys/bucket name.
4. Render: New Blueprint from the repo (reads `render.yaml`), fill in the `sync: false` env vars, deploy, then run `alembic upgrade head` and `python -m app.scripts.create_admin` from the Render shell.
5. Cloudflare Pages: connect the repo, root directory `frontend`, build `npm run build`, output `dist`, set `VITE_API_URL` to the Render URL.
6. Set `FRONTEND_URL` on Render to the Pages URL and redeploy.
