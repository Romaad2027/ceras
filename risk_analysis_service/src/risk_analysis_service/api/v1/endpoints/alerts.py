from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
import logging

from ....db.session import get_db
from ....api.deps import get_current_active_user
from ....db.models.organization import User
from ....db.models.security_alert import SecurityAlert
from ....schemas.security_alert import (
    SecurityAlertOut,
    PaginatedSecurityAlerts,
)


router = APIRouter(tags=["Alerts"])
logger = logging.getLogger("risk_analysis.api")


@router.get(
    "/alerts",
    response_model=PaginatedSecurityAlerts,
)
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    rule_code: Optional[str] = Query(None, description="Filter by rule code"),
    cloud_account_id: Optional[uuid.UUID] = Query(None),
    cloud_identity_id: Optional[uuid.UUID] = Query(None),
    created_from: Optional[datetime] = Query(None),
    created_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None, description="Search in description"),
) -> PaginatedSecurityAlerts:
    logger.info(
        "GET /alerts requested page=%d size=%d severity=%s rule_code=%s",
        page,
        page_size,
        severity,
        rule_code,
    )

    filters = [SecurityAlert.organization_id == current_user.organization_id]
    if severity:
        filters.append(SecurityAlert.severity == severity)
    if rule_code:
        filters.append(SecurityAlert.rule_code == rule_code)
    if cloud_account_id:
        filters.append(SecurityAlert.cloud_account_id == cloud_account_id)
    if cloud_identity_id:
        filters.append(SecurityAlert.cloud_identity_id == cloud_identity_id)
    if created_from:
        filters.append(SecurityAlert.created_at >= created_from)
    if created_to:
        filters.append(SecurityAlert.created_at <= created_to)
    if search:
                                            
        filters.append(SecurityAlert.description.ilike(f"%{search}%"))

    where_clause = and_(*filters) if filters else None

                 
    total = db.execute(
        select(func.count()).select_from(SecurityAlert).where(where_clause)
    ).scalar_one()

                
    stmt = (
        select(SecurityAlert)
        .where(where_clause)
        .order_by(SecurityAlert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.execute(stmt).scalars().all()

    logger.info("GET /alerts success: total=%d returned=%d", total, len(items))
    return PaginatedSecurityAlerts(
        total=total,
        page=page,
        page_size=page_size,
        items=items,                                       
    )
