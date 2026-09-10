from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_token import AccessToken


def create(db: Session, token: AccessToken) -> AccessToken:
    db.add(token)
    db.flush()
    return token


def get_by_token_hash(db: Session, token_hash: str) -> AccessToken | None:
    stmt = select(AccessToken).where(AccessToken.token_hash == token_hash)
    return db.execute(stmt).scalar_one_or_none()


def get_active_for_letter(db: Session, letter_id: UUID) -> AccessToken | None:
    stmt = (
        select(AccessToken)
        .where(AccessToken.letter_id == letter_id, AccessToken.revoked_at.is_(None))
        .order_by(AccessToken.created_at.desc())
    )
    return db.execute(stmt).scalars().first()
