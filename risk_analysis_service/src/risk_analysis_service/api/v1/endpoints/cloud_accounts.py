from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ....api.deps import get_current_active_user
from ....db.session import get_db
from ....db.models.organization import User
from ....schemas.cloud_account import (
    CloudAccountCreate,
    CloudAccountSummary,
)
from ....services.cloud_accounts import CloudAccountService


router = APIRouter(tags=["Cloud Accounts"])


@router.get(
    "/cloud-accounts",
    response_model=List[CloudAccountSummary],
    summary="List connected cloud accounts",
    description=(
        "Returns all cloud accounts connected to the authenticated user's organization. "
        "Sensitive credentials are never returned."
    ),
)
def list_cloud_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[CloudAccountSummary]:
    service = CloudAccountService(db)
    rows = service.list_cloud_accounts_for_user_org(current_user)
    return rows


@router.post(
    "/cloud-accounts",
    status_code=status.HTTP_201_CREATED,
    response_model=CloudAccountSummary,
    summary="Connect a new cloud account",
    description=(
        "Connect a new cloud account to the authenticated user's organization. "
        "Only admins can connect new accounts. Credentials are stored securely and "
        "are not returned in responses."
    ),
)
def connect_cloud_account(
    payload: CloudAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CloudAccountSummary:
    service = CloudAccountService(db)
    created = service.connect_new_account(current_user, payload)
    return created
