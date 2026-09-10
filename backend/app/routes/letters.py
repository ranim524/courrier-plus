from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ValidationAppError
from app.core.rate_limit import limiter
from app.schemas.letter import LetterCreate, LetterRead, RecipientInfo, SenderInfo
from app.services import letter_service

router = APIRouter(prefix="/api/letters", tags=["letters"])


@router.post("", response_model=LetterRead, status_code=201)
@limiter.limit("10/minute")
async def create_letter(
    request: Request,
    sender_first_name: str = Form(...),
    sender_last_name: str = Form(...),
    sender_email: str = Form(...),
    sender_phone: str | None = Form(default=None),
    recipient_first_name: str = Form(...),
    recipient_last_name: str = Form(...),
    recipient_email: str = Form(...),
    recipient_phone: str | None = Form(default=None),
    subject: str = Form(...),
    message: str | None = Form(default=None),
    document: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> LetterRead:
    try:
        payload = LetterCreate(
            sender=SenderInfo(
                first_name=sender_first_name, last_name=sender_last_name, email=sender_email, phone=sender_phone
            ),
            recipient=RecipientInfo(
                first_name=recipient_first_name,
                last_name=recipient_last_name,
                email=recipient_email,
                phone=recipient_phone,
            ),
            subject=subject,
            message=message,
        )
    except ValidationError as exc:
        first_error = exc.errors()[0]
        field = ".".join(str(loc) for loc in first_error["loc"])
        raise ValidationAppError(f"Invalid value for {field}: {first_error['msg']}") from exc

    file_bytes = None
    file_name = None
    file_content_type = None
    if document is not None and document.filename:
        file_bytes = await document.read()
        file_name = document.filename
        file_content_type = document.content_type

    letter = letter_service.create_letter(db, payload, file_bytes, file_name, file_content_type)
    return LetterRead.model_validate(letter)
