from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.schemas.tracking import AccessLetterView
from app.services import access_service, document_service
from app.repositories import letter_repository

router = APIRouter(prefix="/api/access", tags=["access"])


@router.get("/{token}", response_model=AccessLetterView)
@limiter.limit("30/minute")
def view_letter(request: Request, token: str, db: Session = Depends(get_db)) -> AccessLetterView:
    return access_service.view_letter(db, token, request.client.host if request.client else None, request.headers.get("user-agent"))


@router.post("/{token}/open", response_model=AccessLetterView)
@limiter.limit("30/minute")
def mark_opened(request: Request, token: str, db: Session = Depends(get_db)) -> AccessLetterView:
    return access_service.mark_opened(db, token, request.client.host if request.client else None, request.headers.get("user-agent"))


@router.post("/{token}/receive", response_model=AccessLetterView)
@limiter.limit("10/minute")
def confirm_receipt(request: Request, token: str, db: Session = Depends(get_db)) -> AccessLetterView:
    return access_service.confirm_receipt(db, token, request.client.host if request.client else None, request.headers.get("user-agent"))


@router.get("/{token}/document")
@limiter.limit("30/minute")
def download_document(request: Request, token: str, db: Session = Depends(get_db)) -> Response:
    letter = access_service.get_letter_for_token(db, token)
    document = letter_repository.get_by_id_with_document(db, letter.id).document
    if document is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("No document attached to this letter")

    data = document_service.read_document_bytes(document)
    return Response(content=data, media_type="application/pdf")
