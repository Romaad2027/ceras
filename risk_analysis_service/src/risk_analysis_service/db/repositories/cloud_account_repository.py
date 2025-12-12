from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.cloud_account import CloudAccount
from ...schemas.cloud_account import CloudAccountCreate
from .base import BaseRepository


class CloudAccountRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_by_organization(self, organization_id) -> List[CloudAccount]:
        stmt = select(CloudAccount).where(
            CloudAccount.organization_id == organization_id
        )
        return self.db.execute(stmt).scalars().all()

    def create_for_organization(
        self, organization_id, payload: CloudAccountCreate
    ) -> CloudAccount:
        db_obj = CloudAccount(
            organization_id=organization_id,
            name=payload.name,
            provider=payload.provider,
            credentials=payload.credentials,
            region=payload.region,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
