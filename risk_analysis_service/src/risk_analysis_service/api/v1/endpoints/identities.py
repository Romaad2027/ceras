from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ....api.deps import get_current_active_user
from ....db.models.cloud_identity import CloudIdentity
from ....db.models.entity_profile import EntityProfile
from ....db.models.organization import User
from ....db.session import get_db
from ....schemas.entity_profile import EntityProfileResponse
from ....schemas.identity import (
    IdentityDetailResponse,
    IdentityResponse,
    ProfileUpdate,
)

router = APIRouter(tags=["Identities"])
logger = logging.getLogger("risk_analysis.api")


@router.get("/identities", response_model=List[IdentityResponse])
def list_identities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[IdentityResponse]:
    """
    List cloud identities for the current user's organization.
    """
    logger.info("GET /identities skip=%s limit=%s", skip, limit)
    identities: List[CloudIdentity] = (
        db.execute(
            select(CloudIdentity)
            .where(CloudIdentity.organization_id == current_user.organization_id)
            .order_by(CloudIdentity.identity_name)
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return identities


@router.get("/identities/{identity_id}", response_model=IdentityDetailResponse)
def get_identity_detail(
    identity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> IdentityDetailResponse:
    """
    Get identity details; ensure an EntityProfile exists (create if missing).
    """
    logger.info("GET /identities/%s", identity_id)
    identity: Optional[CloudIdentity] = db.execute(
        select(CloudIdentity).where(
            and_(
                CloudIdentity.id == identity_id,
                CloudIdentity.organization_id == current_user.organization_id,
            )
        )
    ).scalar_one_or_none()
    if identity is None:
        raise HTTPException(status_code=404, detail="Identity not found")

    profile: Optional[EntityProfile] = db.execute(
        select(EntityProfile).where(
            and_(
                EntityProfile.cloud_identity_id == identity.id,
                EntityProfile.organization_id == current_user.organization_id,
            )
        )
    ).scalar_one_or_none()

    if profile is None:
                                                                        
        profile = db.execute(
            select(EntityProfile).where(
                and_(
                    EntityProfile.entity_id == identity.identity_arn,
                    EntityProfile.organization_id == current_user.organization_id,
                )
            )
        ).scalar_one_or_none()

    if profile is None:
                                                      
        profile = EntityProfile(
            entity_id=identity.identity_arn,
            organization_id=current_user.organization_id,
            cloud_identity_id=identity.id,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        logger.info("Created EntityProfile for identity %s", identity.id)
    else:
                               
        if getattr(profile, "cloud_identity_id", None) != identity.id:
            profile.cloud_identity_id = identity.id
            db.commit()
            db.refresh(profile)

    return IdentityDetailResponse(
        id=identity.id,
        identity_arn=identity.identity_arn,
        identity_name=identity.identity_name,
        identity_type=identity.identity_type,
        is_mfa_enabled=identity.is_mfa_enabled,
        created_at=identity.created_at,
        profile=profile,
    )


@router.patch("/identities/{identity_id}/profile", response_model=EntityProfileResponse)
def update_identity_profile(
    identity_id: uuid.UUID,
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EntityProfileResponse:
    """
    Update the profile linked to the specified identity.
    Ensures profile exists and updates whitelisted_cidrs, manual_allowed_actions,
    manual_forbidden_actions.
    """
    logger.info("PATCH /identities/%s/profile", identity_id)
    identity: Optional[CloudIdentity] = db.execute(
        select(CloudIdentity).where(
            and_(
                CloudIdentity.id == identity_id,
                CloudIdentity.organization_id == current_user.organization_id,
            )
        )
    ).scalar_one_or_none()
    if identity is None:
        raise HTTPException(status_code=404, detail="Identity not found")

    profile: Optional[EntityProfile] = db.execute(
        select(EntityProfile).where(
            and_(
                EntityProfile.cloud_identity_id == identity.id,
                EntityProfile.organization_id == current_user.organization_id,
            )
        )
    ).scalar_one_or_none()

    if profile is None:
                                                     
        profile = db.execute(
            select(EntityProfile).where(
                and_(
                    EntityProfile.entity_id == identity.identity_arn,
                    EntityProfile.organization_id == current_user.organization_id,
                )
            )
        ).scalar_one_or_none()

    if profile is None:
                           
        profile = EntityProfile(
            entity_id=identity.identity_arn,
            organization_id=current_user.organization_id,
            cloud_identity_id=identity.id,
        )
        db.add(profile)
        db.flush()

                   
    if payload.whitelisted_cidrs is not None:
        profile.whitelisted_cidrs = payload.whitelisted_cidrs
    if payload.manual_allowed_actions is not None:
        profile.manual_allowed_actions = payload.manual_allowed_actions
    if payload.manual_forbidden_actions is not None:
        profile.manual_forbidden_actions = payload.manual_forbidden_actions

    db.commit()
    db.refresh(profile)
    logger.info("PATCH /identities/%s/profile success", identity_id)
    return profile
