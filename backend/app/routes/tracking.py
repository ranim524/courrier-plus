from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.tracking import TrackingRead
from app.services import tracking_service

router = APIRouter(prefix="/api/track", tags=["tracking"])


@router.get("/{reference}", response_model=TrackingRead)
def get_tracking(reference: str, db: Session = Depends(get_db)) -> TrackingRead:
    return tracking_service.get_tracking(db, reference)
