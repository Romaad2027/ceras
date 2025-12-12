from __future__ import annotations

from typing import List
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ....api.deps import get_current_active_user
from ....db.models.organization import User
from ....db.models.user_invitation import UserInvitation, InvitationStatus
from ....db.session import get_db
from ....schemas.organization import (
    MemberResponse,
    InvitationResponse,
    UserWithOrganizationResponse,
)


router = APIRouter(tags=["Organization Members"])
logger = logging.getLogger("risk_analysis.api")


@router.get("/organization/members", response_model=List[MemberResponse])
def list_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[MemberResponse]:
    """
    List users in the current user's organization.
    """
    rows = (
        db.execute(
            select(User).where(User.organization_id == current_user.organization_id)
        )
        .scalars()
        .all()
    )
    return rows


@router.get("/organization/invitations", response_model=List[InvitationResponse])
def list_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[InvitationResponse]:
    """
    List pending invitations in the current user's organization.
    """
    rows = (
        db.execute(
            select(UserInvitation).where(
                UserInvitation.organization_id == current_user.organization_id,
                UserInvitation.status == InvitationStatus.PENDING,
            )
        )
        .scalars()
        .all()
    )
    return rows


@router.get(
    "/organization/users",
    response_model=List[UserWithOrganizationResponse],
    tags=["Organization Members"],
)
def list_users_with_organization(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[UserWithOrganizationResponse]:
    """
    List users in the current user's organization including their organization details.
    """
    rows = (
        db.execute(
            select(User)
            .where(User.organization_id == current_user.organization_id)
            .options(selectinload(User.organization))
        )
        .scalars()
        .all()
    )
    return rows
