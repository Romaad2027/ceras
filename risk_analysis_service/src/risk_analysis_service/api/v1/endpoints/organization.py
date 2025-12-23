from __future__ import annotations

from typing import List
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ....api.deps import get_current_active_user
from ....db.models.organization import User, UserRole
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


@router.delete("/organization/members/{user_id}", status_code=status.HTTP_200_OK)
def remove_member(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Remove a user from the organization.

    **Authorization:**
    - Only ADMIN users can remove members from the organization

    **Restrictions:**
    - Admins cannot remove themselves
    - The target user must belong to the same organization as the requester

    **Flow:**
    1. Verify the requesting user is an ADMIN
    2. Verify the target user exists and belongs to the same organization
    3. Prevent self-removal
    4. Delete the user from the database (cascading deletes will handle related records)

    **Path Parameters:**
    - `user_id` (UUID string): The unique identifier of the user to remove

    **Returns:**
    - Success message with the email of the removed user

    **Error Responses:**
    - `403 Forbidden`: If the requesting user is not an ADMIN
    - `403 Forbidden`: If attempting to remove oneself
    - `404 Not Found`: If the target user doesn't exist
    - `403 Forbidden`: If the target user belongs to a different organization
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can remove organization members",
        )

    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot remove yourself from the organization",
        )

    target_user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if target_user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only remove members from your own organization",
        )

    removed_email = target_user.email

    db.delete(target_user)
    db.commit()

    logger.info(
        f"User {removed_email} (ID: {user_id}) removed from organization "
        f"{current_user.organization_id} by admin {current_user.email}"
    )

    return {
        "message": f"User {removed_email} has been successfully removed from the organization"
    }
