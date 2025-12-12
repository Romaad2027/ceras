from __future__ import annotations

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from ....db.session import get_db
from ....db.models.cloud_resource import CloudResource, CloudResourceCriticality
from ....schemas.resource import (
    ResourceUpsertRequest,
    ResourceResponse,
    ResourceDetailResponse,
    ResourceConfigUpdate,
)
from ....api.deps import get_current_active_user
from ....db.models.organization import User

router = APIRouter(tags=["Resources"])
logger = logging.getLogger("risk_analysis.api")


@router.post("/resources/", response_model=ResourceResponse)
def upsert_resource(
    payload: ResourceUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResourceResponse:
    """Register or update a CloudResource and its criticality."""
    logger.info(
        "POST /resources/ received: id=%s type=%s criticality=%s",
        payload.resource_id,
        payload.resource_type,
        payload.criticality,
    )

    resource: Optional[CloudResource] = db.execute(
        select(CloudResource).where(
            and_(
                CloudResource.resource_id == payload.resource_id,
                CloudResource.organization_id == current_user.organization_id,
            )
        )
    ).scalar_one_or_none()
    if resource is None:
        resource = CloudResource(
            resource_id=payload.resource_id,
            resource_type=payload.resource_type,
            resource_name=payload.resource_name,
            criticality=payload.criticality,
            custom_rules=payload.custom_rules or {},
            organization_id=current_user.organization_id,
        )
        db.add(resource)
    else:
        resource.resource_type = payload.resource_type
        resource.resource_name = payload.resource_name
        resource.criticality = payload.criticality
        if payload.custom_rules is not None:
            resource.custom_rules = payload.custom_rules

    db.commit()
    db.refresh(resource)
    logger.info("POST /resources/ success: id=%s", resource.resource_id)
    return resource


@router.get("/resources/{resource_id}", response_model=ResourceDetailResponse)
def get_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResourceDetailResponse:
    """Retrieve full details of a CloudResource by its ID within current org."""
    logger.info("GET /resources/%s requested", resource_id)
    resource: Optional[CloudResource] = db.execute(
        select(CloudResource).where(
            and_(
                CloudResource.resource_id == resource_id,
                CloudResource.organization_id == current_user.organization_id,
            )
        )
    ).scalar_one_or_none()
    if resource is None:
        logger.info("GET /resources/%s not found", resource_id)
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.get("/resources", response_model=List[ResourceResponse])
def list_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[ResourceResponse]:
    """List all CloudResources for the current user's organization."""
    rows = (
        db.execute(
            select(CloudResource).where(
                CloudResource.organization_id == current_user.organization_id
            )
        )
        .scalars()
        .all()
    )
    return rows


@router.patch("/resources/{resource_id}", response_model=ResourceDetailResponse)
def update_resource(
    resource_id: str,
    payload: ResourceConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResourceDetailResponse:
    """Update resource configuration (criticality and/or security configuration)."""
    resource: Optional[CloudResource] = db.execute(
        select(CloudResource).where(
            and_(
                CloudResource.resource_id == resource_id,
                CloudResource.organization_id == current_user.organization_id,
            )
        )
    ).scalar_one_or_none()
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    if payload.criticality is not None:
        try:
            resource.criticality = CloudResourceCriticality(payload.criticality.upper())
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid criticality value")

    if payload.security_config is not None:
                                                      
        resource.custom_rules = payload.security_config

    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource
