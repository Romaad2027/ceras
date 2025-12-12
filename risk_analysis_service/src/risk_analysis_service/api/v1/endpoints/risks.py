from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from ....db.session import get_db
from ....services.analyzer_service import get_all_risks
from ....schemas.risk import Risk as RiskSchema


router = APIRouter(tags=["Risks"])
logger = logging.getLogger("risk_analysis.api")


@router.get("/risks", response_model=List[RiskSchema])
def list_risks(db: Session = Depends(get_db)):
    logger.info("GET /risks requested")
    risks = get_all_risks(db)
    logger.info("GET /risks success: count=%d", len(risks))
    return risks
