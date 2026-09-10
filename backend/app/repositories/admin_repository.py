from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import Admin


def get_by_email(db: Session, email: str) -> Admin | None:
    stmt = select(Admin).where(Admin.email == email)
    return db.execute(stmt).scalar_one_or_none()


def create(db: Session, admin: Admin) -> Admin:
    db.add(admin)
    db.flush()
    return admin
