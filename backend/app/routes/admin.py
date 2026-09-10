from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.core.exceptions import NotFoundError
from app.core.rate_limit import limiter
from app.models.admin import Admin
from app.models.enums import ActorType, LetterEventType, LetterStatus
from app.repositories import (
    email_event_repository,
    letter_event_repository,
    letter_repository,
    payment_repository,
)
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse, DashboardStats
from app.schemas.common import Page
from app.schemas.event import EmailEventRead, LetterEventRead
from app.schemas.letter import LetterRead, LetterSummary
from app.schemas.payment import PaymentRead
from app.services import admin_service, audit_service, document_service, letter_service
from app.core.config import get_settings

router = APIRouter(prefix="/api/admin", tags=["admin"])
settings = get_settings()


@router.post("/login", response_model=AdminLoginResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: AdminLoginRequest, db: Session = Depends(get_db)) -> AdminLoginResponse:
    token = admin_service.authenticate_admin(db, payload.email, payload.password)
    return AdminLoginResponse(access_token=token, expires_in_minutes=settings.jwt_expiration_minutes)


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> DashboardStats:
    return admin_service.get_dashboard_stats(db)


@router.get("/letters", response_model=Page[LetterSummary])
def list_letters(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: LetterStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
) -> Page[LetterSummary]:
    items, total = letter_repository.list_letters(db, page, page_size, status, search)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return Page[LetterSummary](
        items=[LetterSummary.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/letters/{letter_id}", response_model=LetterRead)
def get_letter(
    letter_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)
) -> LetterRead:
    letter = letter_service.get_letter_or_404(db, letter_id)
    audit_service.record_event(db, letter.id, LetterEventType.ADMIN_VIEWED_LETTER, ActorType.ADMIN)
    db.commit()
    return LetterRead.model_validate(letter)


@router.get("/letters/{letter_id}/events", response_model=list[LetterEventRead])
def get_letter_events(
    letter_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)
) -> list[LetterEventRead]:
    events = letter_event_repository.list_for_letter(db, letter_id)
    return [LetterEventRead.model_validate(e) for e in events]


@router.get("/letters/{letter_id}/emails", response_model=list[EmailEventRead])
def get_letter_emails(
    letter_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)
) -> list[EmailEventRead]:
    events = email_event_repository.list_for_letter(db, letter_id)
    return [EmailEventRead.model_validate(e) for e in events]


@router.get("/letters/{letter_id}/document")
def download_letter_document(
    letter_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)
) -> Response:
    letter = letter_service.get_letter_or_404(db, letter_id)
    if letter.document is None:
        raise NotFoundError("No document attached to this letter")
    data = document_service.read_document_bytes(letter.document)
    return Response(content=data, media_type="application/pdf")


@router.get("/payments", response_model=Page[PaymentRead])
def list_payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
) -> Page[PaymentRead]:
    items, total = payment_repository.list_payments(db, page, page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return Page[PaymentRead](
        items=[PaymentRead.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/emails", response_model=Page[EmailEventRead])
def list_emails(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
) -> Page[EmailEventRead]:
    items, total = email_event_repository.list_all(db, page, page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return Page[EmailEventRead](
        items=[EmailEventRead.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
