from __future__ import annotations

from sqlalchemy.orm import Session

from ..db.repositories.cloud_account_repository import CloudAccountRepository
from ..db.models.organization import User, UserRole
from ..schemas.cloud_account import CloudAccountCreate
from fastapi import HTTPException, status


class CloudAccountService:
    """Business logic for managing cloud accounts."""

    def __init__(self, db: Session) -> None:
        self.repo = CloudAccountRepository(db)

    def list_cloud_accounts_for_user_org(self, current_user: User):
        return self.repo.list_by_organization(current_user.organization_id)

    def connect_new_account(self, current_user: User, payload: CloudAccountCreate):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can connect cloud accounts",
            )

        return self.repo.create_for_organization(current_user.organization_id, payload)
