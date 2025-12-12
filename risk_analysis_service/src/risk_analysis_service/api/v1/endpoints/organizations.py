from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import secrets

from ....api.deps import get_current_active_user
from ....db.models.organization import Organization, User, UserRole
from ....db.models.user_invitation import UserInvitation, InvitationStatus
from ....db.session import get_db
from ....schemas.organization import OrganizationUpdate
from ....schemas.auth import InviteRequest
from ....services.email import EmailService


router = APIRouter(tags=["Organizations"])


@router.patch("/organizations/me", status_code=status.HTTP_200_OK)
def update_my_organization(
    payload: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Deprecated: Organization no longer stores cloud credentials; use Cloud Accounts.
    """
    org = db.get(Organization, current_user.organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

                                                        
    return {"message": "No-op. Manage credentials via Cloud Accounts."}


@router.post("/organization/invites", status_code=status.HTTP_201_CREATED)
def create_invitation(
    payload: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Admins can invite users to their organization."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can send invitations")

                                  
    existing_user = db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    ).scalar_one_or_none()
    if existing_user is None:
        raise HTTPException(status_code=404, detail="Organization not found")

                                                   
    expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
    token = secrets.token_urlsafe(32)
    invitation = UserInvitation(
        email=payload.email,
        organization_id=current_user.organization_id,
        token=token,
        status=InvitationStatus.PENDING,
        expires_at=expires_at,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    invite_link = f"http://localhost:5173/join?token={token}"
    EmailService().send_invite(payload.email, invite_link)

    return {"message": "Invitation created"}
