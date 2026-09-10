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
