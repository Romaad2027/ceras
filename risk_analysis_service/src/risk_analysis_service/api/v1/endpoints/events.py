from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
import logging

from ....db.session import get_db
from ....schemas.audit_event import GenericAuditEvent
from ....services.event_analyzer import EventAnalyzerService
from ....api.deps import get_current_active_user
from ....db.models.organization import User


router = APIRouter(tags=["Events"])
logger = logging.getLogger("risk_analysis.api")

                                                   
analyzer = EventAnalyzerService()


@router.post("/events/ingest")
def ingest_events(
    events: List[GenericAuditEvent],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
                                                  
    logger.info(
        "POST /events/ingest received: events_count=%d", len(events) if events else 0
    )
    created_alerts = analyzer.analyze_events(
        db, events, organization_id=current_user.organization_id
    )
    count = len(created_alerts)
    logger.info("POST /events/ingest success: alerts_created=%d", count)
    return {"alerts_created": count}


@router.post("/events/analyze-anomalies")
def analyze_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    hours: Optional[int] = Query(
        None, description="Lookback window in hours. Omit to use all records."
    ),
) -> dict:
                                                                                       
    logger.info(
        "POST /events/analyze-anomalies requested (deprecated), hours=%s", hours
    )
    return {"alerts_created": 0}
