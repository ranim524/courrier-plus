---
name: deployment
description: Docker/Compose and environment conventions for running Courrier+ beyond local dev
---

# Deployment

## Purpose
Provide a reproducible way to run the whole stack locally (Docker Compose) and in production
(Cloudflare Pages, Render, Neon), while keeping plain local dev (no Docker) fully supported.

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
  builds `backend/Dockerfile` directly from `render.yaml` at the repo root) + Neon (PostgreSQL,
  also holds documents via `STORAGE_PROVIDER=database` — see [[document-management]]). Chosen
  because Cloudflare Workers don't run a Python/SQLAlchemy/psycopg2/bcrypt stack natively; this
  hybrid keeps the existing backend as-is. Documents live in Postgres rather than Cloudflare R2 by
  default because R2 requires a billing method on the Cloudflare account even for its free tier —
  `STORAGE_PROVIDER=r2` (`R2StorageProvider` is already implemented) is a config-only upgrade later
  if that becomes worth it.
- `render.yaml` lists every env var with `sync: false` for anything secret (Render prompts for it
  in the dashboard instead of storing it in the repo) — never put a real secret value in `render.yaml`.
- `backend/docker-entrypoint.sh` runs `alembic upgrade head` (and, if `FIRST_ADMIN_EMAIL`/
  `FIRST_ADMIN_PASSWORD` are set, the admin bootstrap script) before starting Uvicorn, on every
  container start. Both are idempotent, so this is safe to run repeatedly. This exists specifically
  because **Render's free plan has no Shell access** (paid-plan feature) — there would otherwise be
  no way to run one-off commands against the production database. Keep this pattern (auto-run
  idempotent startup tasks in the entrypoint) rather than assuming shell access will be available.

## Important rules
- Never commit a real `.env`; `docker-compose.yml` references `.env` via `env_file` and ships a matching `.env.example`.
- Database data persisted via a named volume, not bind-mounted into a random host path.
- Keep the Compose file simple — no orchestration beyond what these 3 services need (no k8s, no service mesh).
- `FRONTEND_URL` on the backend must exactly match the deployed Cloudflare Pages URL — CORS in `app/main.py` only allows that one origin.

## Workflow (local, Docker Compose)
1. `docker compose build`
2. `docker compose up` — the entrypoint runs migrations automatically once `db` is healthy.

## Workflow (production)
1. Push to GitHub.
2. Neon: create project, copy `DATABASE_URL`.
3. Render: New Blueprint from the repo (reads `render.yaml`), fill in the `sync: false` env vars, deploy. The entrypoint handles migrations + admin bootstrap automatically — check the Logs tab to confirm.
4. Cloudflare Pages: connect the repo, root directory `frontend`, build `npm run build`, output `dist`, set `VITE_API_URL` to the Render URL.
5. Set `FRONTEND_URL` on Render to the Pages URL and redeploy.
