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
docker compose up
```

`backend/docker-entrypoint.sh` runs `alembic upgrade head` (and bootstraps the first admin, if
`FIRST_ADMIN_EMAIL`/`FIRST_ADMIN_PASSWORD` are set) automatically before starting Uvicorn, every
time the container starts. Both are idempotent, so this is safe on every restart -- no separate
`docker compose run` step needed.

- Backend: http://localhost:8000
- Frontend: http://localhost:4173
- Postgres (host-exposed for debugging): localhost:5433

Docker is optional — it exists for parity with a future server deployment, not as a requirement
for local development.

## Environment variables

See `backend/.env.example` and `frontend/.env.example` for the full list. Never commit a real
`.env` file — only `.env.example` is tracked in Git.

## Production deployment (Cloudflare Pages, Render, Neon)

Cloudflare doesn't run a Python/FastAPI/PostgreSQL stack natively (Workers are JS/WASM-first), so
this is a **hybrid** topology: Cloudflare Pages for the static frontend, a normal container host
for the FastAPI backend, and a managed serverless Postgres that also holds the uploaded PDFs.

```
Browser ──▶ Cloudflare Pages (frontend, static build)
              │
              ▼
        Render (FastAPI backend, Docker)
              │
              ▼
      Neon (PostgreSQL: app data + document_blobs)
```

Documents are stored as bytes in Postgres (`STORAGE_PROVIDER=database`, see
`app/services/storage/database_provider.py`) rather than in a separate object-storage service --
this avoids needing a third account/payment method (Cloudflare R2, for one, requires adding a
billing method even to stay within its free tier) for a prototype's document volumes. An
S3-compatible provider (`R2StorageProvider` is already implemented) is a one-env-var swap later if
volume grows past what's comfortable in the database.

All three services have a free tier suitable for a prototype's traffic (see `README.md` for the
exact limits/caveats of each). None of this requires Docker locally — Render builds the existing
`backend/Dockerfile` directly from your Git repo.

### 0. Push the repo to GitHub

Render and Cloudflare Pages both deploy by connecting to a Git repository (GitHub or GitLab).
Create a repo on GitHub and push this project to it if you haven't already:
```bash
git remote add origin https://github.com/<you>/courrier-plus.git
git push -u origin main
```

### 1. Database — Neon (PostgreSQL)

1. Create a free account at https://neon.tech.
2. Create a new project (any region close to your users; Tunisia → Europe is usually closest).
3. Copy the connection string it gives you (starts with `postgresql://...`) — it already includes
   `?sslmode=require`, which Neon requires.
4. You'll set this as `DATABASE_URL` on Render in step 2. It should look like:
   `postgresql+psycopg2://<user>:<password>@<host>/<db>?sslmode=require`
   (Neon gives you a plain `postgresql://` URL — prefix it with `postgresql+psycopg2://` for
   SQLAlchemy, keeping everything after `://` unchanged.)

### 2. Backend — Render

1. Create a free account at https://render.com and connect your GitHub account.
2. **New** → **Blueprint**, point it at your `courrier-plus` repo. Render reads `render.yaml` at
   the repo root and creates the web service automatically (Docker build from `backend/Dockerfile`).
3. Render will prompt for every env var marked `sync: false` in `render.yaml`. Fill in:
   - `DATABASE_URL` — from Neon (step 1)
   - `SECRET_KEY`, `JWT_SECRET` — generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` (run this twice, once per key)
   - `FRONTEND_URL` — your Cloudflare Pages URL (step 3); you can fill this in after step 3 and redeploy
   - `BACKEND_URL` — Render gives you a URL like `https://courrier-plus-backend.onrender.com` once created; fill this in after the first deploy and redeploy
   - `RESEND_API_KEY`, `RESEND_FROM_EMAIL` — from your Resend account
   - `FIRST_ADMIN_EMAIL`, `FIRST_ADMIN_PASSWORD` — your choice, used once by the admin bootstrap script
4. Deploy. `backend/docker-entrypoint.sh` runs `alembic upgrade head` and bootstraps the first
   admin (from `FIRST_ADMIN_EMAIL`/`FIRST_ADMIN_PASSWORD`) automatically on container startup --
   no manual step needed. This matters because **Render's free plan doesn't include Shell access**
   (that's a paid-plan feature), so there'd otherwise be no way to run one-off commands. Check the
   **Logs** tab to confirm you see `Running database migrations...` followed by a successful
   Uvicorn startup line.
5. **Free tier caveat**: a free Render web service spins down after 15 minutes of inactivity: the
   first request after a pause takes ~30-60s to wake it up. Fine for a prototype/demo, not for
   production traffic expecting instant responses.

### 3. Frontend — Cloudflare Pages

1. In the Cloudflare dashboard: **Workers & Pages** → **Create** → **Pages** → **Connect to Git**,
   select your repo.
2. Build settings:
   - **Root directory**: `frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
3. Environment variable: `VITE_API_URL` = your Render backend URL (from step 2.4).
4. Deploy. Cloudflare gives you a URL like `https://courrier-plus.pages.dev`.
5. Go back to Render and set `FRONTEND_URL` to this exact URL (needed for CORS — `app/main.py`
   only allows requests from `FRONTEND_URL`), then redeploy the backend.

`frontend/public/_redirects` (already in the repo) tells Pages to serve `index.html` for every
route, which React Router needs since Pages is a static host with no server-side routing.

### 4. Verify

- `https://<your-backend>.onrender.com/api/health` → `{"status": "ok", ...}`
- `https://<your-pages-site>.pages.dev` → the Courrier+ landing page, and a full send → pay →
  track flow should work end to end. Uploaded PDFs land in Neon's `document_blobs` table (you can
  confirm with `SELECT storage_path, length(data) FROM document_blobs;` from Neon's SQL editor).

### Optional: Cloudflare R2 instead of database storage

If document volume grows large enough that storing PDFs in Postgres becomes uncomfortable, switch
to Cloudflare R2 (S3-compatible, zero egress fees) without any code change:
1. Cloudflare dashboard → **R2 Object Storage** → add a billing method (required by Cloudflare even
   for the free tier) → **Create bucket**.
2. **Manage API tokens** → **Create API token**, scope **Object Read & Write**, restricted to that
   bucket. Note the Account ID, Access Key ID, and Secret Access Key (shown once).
3. On Render, set `STORAGE_PROVIDER=r2` and add `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`,
   `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`. Redeploy.
Existing documents already in `document_blobs` won't move automatically -- this only affects newly
uploaded documents unless you migrate the old rows yourself.
