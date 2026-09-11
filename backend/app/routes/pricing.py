from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.core.rate_limit import limiter
from app.schemas.pricing import PricingBreakdownRead, PricingCalculateRequest
from app.services import document_service, pricing_service
from app.services.pricing_service import DEFAULT_PRINTING_MODE, DEFAULT_PRINTING_SIDES

router = APIRouter(prefix="/api/pricing", tags=["pricing"])

# A text-message-only letter has no PDF to count pages from. It is priced as
# the minimum, single-page-equivalent weight bracket (see pricing_service).
TEXT_MESSAGE_PAGE_COUNT = 1


@router.post("/calculate", response_model=PricingBreakdownRead)
@limiter.limit("60/minute")
def calculate_price(request: Request, payload: PricingCalculateRequest) -> PricingBreakdownRead:
    """Pure pricing calculation from an already-known page count. Used
    internally/for testing; the sender-facing flow uses /preview instead,
    since the frontend must never determine the page count itself."""
    breakdown = pricing_service.calculate_letter_price(
        payload.page_count, payload.printing_mode, payload.printing_sides, payload.acknowledgment_of_receipt
    )
    return PricingBreakdownRead(**breakdown.to_dict())


@router.post("/preview", response_model=PricingBreakdownRead)
@limiter.limit("30/minute")
async def preview_price(
    request: Request,
    acknowledgment_of_receipt: bool = Form(default=False),
    printing_mode: str = Form(default=DEFAULT_PRINTING_MODE),
    printing_sides: str = Form(default=DEFAULT_PRINTING_SIDES),
    document: UploadFile | None = File(default=None),
) -> PricingBreakdownRead:
    """Live price preview for the send-letter wizard, called whenever the
    uploaded PDF or the acknowledgment-of-receipt option changes. The backend
    determines the page count itself from the uploaded file -- the frontend
    never computes or sends a page count or a price."""
    if document is not None and document.filename:
        file_bytes = await document.read()
        page_count = document_service.count_pdf_pages(file_bytes)
    else:
        page_count = TEXT_MESSAGE_PAGE_COUNT

    breakdown = pricing_service.calculate_letter_price(
        page_count, printing_mode, printing_sides, acknowledgment_of_receipt
    )
    return PricingBreakdownRead(**breakdown.to_dict())
