from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationAppError
from app.core.security import create_admin_jwt, hash_password, verify_password
from app.models.admin import Admin
from app.repositories import admin_repository, letter_repository, payment_repository
from app.schemas.admin import DashboardStats
from app.models.enums import LetterStatus

MIN_PASSWORD_LENGTH = 8


def authenticate_admin(db: Session, email: str, password: str) -> str:
    admin = admin_repository.get_by_email(db, email)
    if admin is None or not verify_password(password, admin.password_hash):
        raise UnauthorizedError("Invalid email or password")
    return create_admin_jwt(str(admin.id), admin.email)


def create_admin_if_not_exists(db: Session, email: str, password: str, full_name: str | None = None) -> Admin:
    existing = admin_repository.get_by_email(db, email)
    if existing is not None:
        return existing
    admin = Admin(email=email, password_hash=hash_password(password), full_name=full_name)
    admin = admin_repository.create(db, admin)
    db.commit()
    db.refresh(admin)
    return admin


def change_password(db: Session, email: str, new_password: str) -> Admin:
    admin = admin_repository.get_by_email(db, email)
    if admin is None:
        raise NotFoundError(f"No admin found with email: {email}")

    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValidationAppError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")

    admin.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(admin)
    return admin


def get_dashboard_stats(db: Session) -> DashboardStats:
    from app.core.config import get_settings

    settings = get_settings()

    return DashboardStats(
        total_letters=letter_repository.count_all(db),
        draft_letters=letter_repository.count_by_status(db, LetterStatus.DRAFT),
        pending_payment_letters=letter_repository.count_by_status(db, LetterStatus.PENDING_PAYMENT),
        paid_letters=letter_repository.count_by_status(db, LetterStatus.PAID),
        sent_letters=letter_repository.count_by_status(db, LetterStatus.SENT),
        opened_letters=letter_repository.count_by_status(db, LetterStatus.OPENED),
        received_letters=letter_repository.count_by_status(db, LetterStatus.RECEIVED),
        failed_letters=letter_repository.count_by_status(db, LetterStatus.FAILED),
        total_payments=payment_repository.count_all(db),
        total_revenue=payment_repository.sum_paid_amount(db),
        currency=settings.currency,
    )
