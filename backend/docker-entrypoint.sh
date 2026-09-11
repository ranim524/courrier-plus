#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

if [ -n "$FIRST_ADMIN_EMAIL" ] && [ -n "$FIRST_ADMIN_PASSWORD" ]; then
  echo "Ensuring first admin account exists..."
  python -m app.scripts.create_admin
else
  echo "FIRST_ADMIN_EMAIL/FIRST_ADMIN_PASSWORD not set, skipping admin bootstrap."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
