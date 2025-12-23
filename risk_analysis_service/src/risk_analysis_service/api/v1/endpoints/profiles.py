from __future__ import annotations

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from ....db.session import get_db
from ....db.models.entity_profile import EntityProfile
from ....schemas.entity_profile import EntityProfileUpdate, EntityProfileResponse
from ....api.deps import get_current_active_user
from ....db.models.organization import User

router = APIRouter(tags=["Profiles"])
logger = logging.getLogger("risk_analysis.api")


@router.get("/profiles", response_model=EntityProfileResponse)
def get_profile(
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EntityProfileResponse:
    """
    Get an entity's security profile.
    """
    logger.info(
        "GET /profiles?entity_id=%s received from user %s (org %s)",
        entity_id,
        current_user.email,
        current_user.organization_id,
    )

    profile: Optional[EntityProfile] = db.execute(
        select(EntityProfile).where(
            and_(
                EntityProfile.entity_id == entity_id,
                EntityProfile.organization_id == current_user.organization_id,
            )
        )
    ).scalar_one_or_none()

    if profile is None:
        logger.warning(
            "Profile not found: entity_id=%s, user_org=%s",
            entity_id,
            current_user.organization_id,
        )
        # Check if profile exists in another org
        other_profile = db.execute(
            select(EntityProfile).where(EntityProfile.entity_id == entity_id)
        ).scalar_one_or_none()
        if other_profile:
            logger.warning(
                "Profile exists but in different org: %s", other_profile.organization_id
            )
        raise HTTPException(
            status_code=404,
            detail=f"Entity profile not found for entity_id '{entity_id}' in your organization",
        )

    logger.info("GET /profiles?entity_id=%s success", entity_id)
    return profile


@router.patch("/profiles", response_model=EntityProfileResponse)
def update_profile(
    entity_id: str,
    payload: EntityProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EntityProfileResponse:
    """
    Update an entity's security settings.
    """
    logger.info(
        "PATCH /profiles?entity_id=%s received from user %s (org %s)",
        entity_id,
        current_user.email,
        current_user.organization_id,
        payload,
    )

    profile: Optional[EntityProfile] = db.execute(
        select(EntityProfile).where(
            and_(
                EntityProfile.entity_id == entity_id,
                EntityProfile.organization_id == current_user.organization_id,
            )
        )
    ).scalar_one_or_none()

    if profile is None:
        logger.warning(
            "Profile not found for update: entity_id=%s, user_org=%s",
            entity_id,
            current_user.organization_id,
        )
        raise HTTPException(
            status_code=404,
            detail=f"Entity profile not found for entity_id '{entity_id}' in your organization",
        )

    if payload.whitelisted_cidrs is not None:
        profile.whitelisted_cidrs = payload.whitelisted_cidrs
    if payload.manual_allowed_actions is not None:
        profile.manual_allowed_actions = payload.manual_allowed_actions
    if payload.profile_mode is not None:
        profile.profile_mode = payload.profile_mode

    db.commit()
    db.refresh(profile)
    logger.info("PATCH /profiles?entity_id=%s success", entity_id)
    return profile
