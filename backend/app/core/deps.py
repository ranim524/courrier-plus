from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_admin_jwt
from app.models.admin import Admin
from app.repositories import admin_repository


def get_current_admin(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> Admin:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or invalid authorization header")

    token = authorization.split(" ", 1)[1]
    payload = decode_admin_jwt(token)

    admin = admin_repository.get_by_email(db, payload.get("email", ""))
    if admin is None:
        raise UnauthorizedError("Admin not found")
    return admin


def get_client_ip(x_forwarded_for: str | None = Header(default=None)) -> str | None:
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return None
