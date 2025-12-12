from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from ....db.session import get_db
from ....services.analyzer_service import analyze_and_save_risks
from ....schemas.cloud_resource import GenericCloudResource
from ....schemas.risk import Risk as RiskSchema


router = APIRouter(tags=["Analysis"])
logger = logging.getLogger("risk_analysis.api")


@router.post("/analyze/resource", response_model=List[RiskSchema])
async def analyze_resource_endpoint(
    resource: GenericCloudResource, db: Session = Depends(get_db)
):
    """
    Приймає дані про узагальнений хмарний ресурс і повертає список знайдених ризиків.
    """
    logger.info(
        "POST /analyze/resource received: id=%s type=%s",
        resource.resource_id,
        resource.resource_type,
    )
    risks = analyze_and_save_risks(db, resource)
    logger.info("POST /analyze/resource success: risks_saved=%d", len(risks))
    return risks
