from __future__ import annotations

import logging
from typing import Annotated
from typing import Tuple
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ....core.security import create_access_token, get_password_hash, verify_password
from ....db.models.organization import Organization, User, UserRole
from ....db.models.user_invitation import UserInvitation, InvitationStatus
from ....db.session import get_db
from ....schemas.auth import (
    Token,
    UserCreate,
    TenantRegisterRequest,
    InviteAcceptRequest,
)


logger = logging.getLogger("risk_analysis.api.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


async def _login_credentials(request: Request) -> Tuple[str, str]:
    """
    Extract login credentials from either JSON body or form data.

    Supports:
    - application/json with fields: {"email": "...", "password": "..."}
    - application/x-www-form-urlencoded with fields: username, password
    """
    content_type = request.headers.get("content-type", "").lower()
    try:
        if content_type.startswith("application/json"):
            data = await request.json()
            email = (data or {}).get("email") or (data or {}).get("username")
            password = (data or {}).get("password")
            if not email or not password:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Both 'email' (or 'username') and 'password' are required.",
                )
            return email, password
                                         
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Both 'username' and 'password' are required.",
            )
        return username, password
    except HTTPException:
        raise
    except Exception:
                                                     
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid login payload.",
        )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """Create a new organization and an admin user in a single transaction."""
                             
    existing_user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

                                                                              
    base_org_name: str = (
        payload.organization_name
        if payload.organization_name
        else payload.email.split("@")[0]
    )

                                                               
    org_name_candidate = base_org_name
    suffix = 1
    while db.execute(
        select(Organization).where(Organization.name == org_name_candidate)
    ).scalar_one_or_none():
        suffix += 1
        org_name_candidate = f"{base_org_name}-{suffix}"

    try:
        org = Organization(name=org_name_candidate)
        db.add(org)
        db.flush()                              

        user = User(
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            role=UserRole.ADMIN,
            organization_id=org.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        access_token = create_access_token(subject=str(user.id))
        return Token(access_token=access_token, token_type="bearer")
    except IntegrityError as exc:
        logger.exception("Failed to register user/org due to integrity error: %s", exc)
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Integrity error during registration"
        )


@router.post(
    "/register-tenant", response_model=Token, status_code=status.HTTP_201_CREATED
)
def register_tenant(
    payload: TenantRegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """Main tenant registration: creates Organization and an ADMIN User."""
    existing_user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

                                         
    base_org_name = payload.organization_name
    org_name_candidate = base_org_name
    suffix = 1
    while db.execute(
        select(Organization).where(Organization.name == org_name_candidate)
    ).scalar_one_or_none():
        suffix += 1
        org_name_candidate = f"{base_org_name}-{suffix}"

    try:
        org = Organization(name=org_name_candidate)
        db.add(org)
        db.flush()

        user = User(
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            role=UserRole.ADMIN,
            organization_id=org.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        access_token = create_access_token(subject=str(user.id))
        return Token(access_token=access_token, token_type="bearer")
    except IntegrityError as exc:
        logger.exception("Failed to register tenant due to integrity error: %s", exc)
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Integrity error during registration"
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(
    credentials: Annotated[Tuple[str, str], Depends(_login_credentials)],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """Validate credentials and return JWT access token."""
    username_or_email, password = credentials
    user = db.execute(
        select(User).where(User.email == username_or_email)
    ).scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token, token_type="bearer")


@router.post("/accept-invite", response_model=Token)
def accept_invite(
    payload: InviteAcceptRequest,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """Accept an invitation and create a user under the same organization."""
    invite: UserInvitation | None = db.execute(
        select(UserInvitation).where(UserInvitation.token == payload.token)
    ).scalar_one_or_none()
    if invite is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invite.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invitation is not pending")
    now = datetime.now(timezone.utc)
    if invite.expires_at is not None and invite.expires_at < now:
        raise HTTPException(status_code=400, detail="Invitation has expired")

                                       
    existing = db.execute(
        select(User).where(User.email == invite.email)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

    try:
        user = User(
            email=invite.email,
            hashed_password=get_password_hash(payload.password),
            role=UserRole.VIEWER,
            organization_id=invite.organization_id,
        )
        db.add(user)
        invite.status = InvitationStatus.ACCEPTED
        db.add(invite)
        db.commit()
        db.refresh(user)
        access_token = create_access_token(subject=str(user.id))
        return Token(access_token=access_token, token_type="bearer")
    except IntegrityError as exc:
        db.rollback()
        logger.exception("Accept invite failed: %s", exc)
        raise HTTPException(
            status_code=400, detail="Integrity error during accept-invite"
        )
