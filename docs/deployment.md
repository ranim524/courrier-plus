# Deployment — Courrier+

## Local development (no Docker) — recommended for day-to-day work

### Prerequisites
- Python 3.11+
- Node.js 22+ / npm
- PostgreSQL running locally (a native Windows service works fine)

### Backend
```bash
cd backend
python -m venv .venv
./.venv/Scripts/pip install -r requirements.txt   # Windows
cp .env.example .env                              # then fill in real values
alembic upgrade head
python -m app.scripts.create_admin                # requires FIRST_ADMIN_EMAIL/PASSWORD in .env
uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
App: http://localhost:5173

### Tests
```bash
cd backend
pytest -q
```

## Docker Compose (convenience / production-parity)

```bash
docker compose build
docker compose up -d db
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.scripts.create_admin
docker compose up
```

- Backend: http://localhost:8000
- Frontend: http://localhost:4173
- Postgres (host-exposed for debugging): localhost:5433

Docker is optional — it exists for parity with a future server deployment, not as a requirement
for local development.

## Environment variables

See `backend/.env.example` and `frontend/.env.example` for the full list. Never commit a real
`.env` file — only `.env.example` is tracked in Git.

## Production deployment (Cloudflare Pages + R2, Render, Neon)

Cloudflare doesn't run a Python/FastAPI/PostgreSQL stack natively (Workers are JS/WASM-first), so
this is a **hybrid** topology: Cloudflare for what it's good at (static frontend hosting + object
storage), a normal container host for the FastAPI backend, and a managed serverless Postgres.

```
Browser ──▶ Cloudflare Pages (frontend, static build)
              │
              ▼
        Render (FastAPI backend, Docker)
              │              │
              ▼              ▼
      Neon (PostgreSQL)   Cloudflare R2 (PDF documents)
```

All four services have a free tier suitable for a prototype's traffic (see `README.md` for the
exact limits/caveats of each). None of this requires Docker locally — Render builds the existing
`backend/Dockerfile` directly from your Git repo.

### 0. Push the repo to GitHub

Render and Cloudflare Pages both deploy by connecting to a Git repository (GitHub or GitLab).
Create a repo on GitHub and push this project to it if you haven't already:
```bash
git remote add origin https://github.com/<you>/courrier-plus.git
git push -u origin master
```

### 1. Database — Neon (PostgreSQL)

1. Create a free account at https://neon.tech.
2. Create a new project (any region close to your users; Tunisia → Europe is usually closest).
3. Copy the connection string it gives you (starts with `postgresql://...`) — it already includes
   `?sslmode=require`, which Neon requires.
4. You'll set this as `DATABASE_URL` on Render in step 3. It should look like:
   `postgresql+psycopg2://<user>:<password>@<host>/<db>?sslmode=require`
   (Neon gives you a plain `postgresql://` URL — prefix it with `postgresql+psycopg2://` for
   SQLAlchemy, keeping everything after `://` unchanged.)

### 2. Object storage — Cloudflare R2

1. In the Cloudflare dashboard, go to **R2** → **Create bucket**. Name it e.g. `courrier-plus-docs`.
   Keep it private (default — do not enable public access).
2. Go to **R2** → **Manage API tokens** → **Create API token**. Scope: **Object Read & Write**,
   restricted to this bucket if possible. Copy the **Access Key ID** and **Secret Access Key** —
   the secret is shown only once.
3. Note your **Account ID** (shown on the R2 overview page, or the right sidebar of the Cloudflare
   dashboard).
4. You'll need: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`.

### 3. Backend — Render

1. Create a free account at https://render.com and connect your GitHub account.
2. **New** → **Blueprint**, point it at your `courrier-plus` repo. Render reads `render.yaml` at
   the repo root and creates the web service automatically (Docker build from `backend/Dockerfile`).
3. Render will prompt for every env var marked `sync: false` in `render.yaml`. Fill in:
   - `DATABASE_URL` — from Neon (step 1)
   - `SECRET_KEY`, `JWT_SECRET` — generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` (run this twice, once per key)
   - `FRONTEND_URL` — your Cloudflare Pages URL (step 4); you can fill this in after step 4 and redeploy
   - `BACKEND_URL` — Render gives you a URL like `https://courrier-plus-backend.onrender.com` once created; fill this in after the first deploy and redeploy
   - `RESEND_API_KEY`, `RESEND_FROM_EMAIL` — from your Resend account
   - `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` — from step 2
   - `FIRST_ADMIN_EMAIL`, `FIRST_ADMIN_PASSWORD` — your choice, used once by the admin bootstrap script
4. Deploy. Once it's live, open a shell on the Render service (dashboard → **Shell**) and run:
   ```bash
   alembic upgrade head
   python -m app.scripts.create_admin
   ```
5. **Free tier caveat**: a free Render web service spins down after 15 minutes of inactivity: the
   first request after a pause takes ~30-60s to wake it up. Fine for a prototype/demo, not for
   production traffic expecting instant responses.

### 4. Frontend — Cloudflare Pages

1. In the Cloudflare dashboard: **Workers & Pages** → **Create** → **Pages** → **Connect to Git**,
   select your repo.
2. Build settings:
   - **Root directory**: `frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
3. Environment variable: `VITE_API_URL` = your Render backend URL (from step 3.4).
4. Deploy. Cloudflare gives you a URL like `https://courrier-plus.pages.dev`.
5. Go back to Render and set `FRONTEND_URL` to this exact URL (needed for CORS — `app/main.py`
   only allows requests from `FRONTEND_URL`), then redeploy the backend.

`frontend/public/_redirects` (already in the repo) tells Pages to serve `index.html` for every
route, which React Router needs since Pages is a static host with no server-side routing.

### 5. Verify

- `https://<your-backend>.onrender.com/api/health` → `{"status": "ok", ...}`
- `https://<your-pages-site>.pages.dev` → the Courrier+ landing page, and a full send → pay →
  track flow should work end to end, with uploaded PDFs landing in the R2 bucket (visible in the
  Cloudflare dashboard under that bucket's **Objects** tab).
