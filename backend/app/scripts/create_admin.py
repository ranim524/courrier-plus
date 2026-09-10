"""Creates the first admin account for local development.

Usage:
    python -m app.scripts.create_admin

Reads FIRST_ADMIN_EMAIL / FIRST_ADMIN_PASSWORD from the environment (.env).
Never hard-codes credentials. Safe to run multiple times (no-op if the admin already exists).
"""

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.admin_service import create_admin_if_not_exists


def main() -> None:
    settings = get_settings()
    if not settings.first_admin_email or not settings.first_admin_password:
        raise SystemExit(
            "FIRST_ADMIN_EMAIL and FIRST_ADMIN_PASSWORD must be set in .env before running this script."
        )

    db = SessionLocal()
    try:
        admin = create_admin_if_not_exists(db, settings.first_admin_email, settings.first_admin_password)
        print(f"Admin ready: {admin.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
