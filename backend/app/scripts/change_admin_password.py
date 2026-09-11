"""Changes an existing admin's password.

Usage:
    python -m app.scripts.change_admin_password admin@courrierplus.tn

The new password is entered interactively via a hidden prompt (getpass) --
it is never accepted as a command-line argument (which would leak into shell
history / process lists) and never logged anywhere.
"""

import getpass
import sys

from app.core.database import SessionLocal
from app.core.exceptions import AppError
from app.services.admin_service import change_password


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m app.scripts.change_admin_password <admin-email>")

    email = sys.argv[1]

    new_password = getpass.getpass("New password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    if new_password != confirm_password:
        raise SystemExit("Passwords do not match.")

    db = SessionLocal()
    try:
        admin = change_password(db, email, new_password)
        print(f"Password updated for {admin.email}")
    except AppError as exc:
        raise SystemExit(str(exc)) from exc
    finally:
        db.close()


if __name__ == "__main__":
    main()
