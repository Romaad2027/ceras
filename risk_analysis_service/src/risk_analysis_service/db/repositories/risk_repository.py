from __future__ import annotations

from typing import Iterable, List

from sqlalchemy.orm import Session
import logging

from ..models.risk import Risk
from ...schemas import risk as risk_schemas
from .base import BaseRepository


logger = logging.getLogger("risk_analysis.db")


class RiskRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_all(self) -> List[Risk]:
        return self.db.query(Risk).all()

    def create(self, data: risk_schemas.RiskCreate) -> Risk:
        db_obj = Risk(**data.model_dump())
        self.db.add(db_obj)
        logger.info(
            "DB insert pending: Risk(resource_name=%s, severity=%s)",
            db_obj.resource_name,
            db_obj.severity,
        )
        self.db.commit()
        self.db.refresh(db_obj)
        logger.info(
            "DB insert committed: Risk id=%s status=%s", db_obj.id, db_obj.status
        )
        return db_obj

    def create_many(self, items: Iterable[risk_schemas.RiskCreate]) -> List[Risk]:
        created: List[Risk] = []
        for item in items:
            created.append(Risk(**item.model_dump()))
        if not created:
            return []
        self.db.add_all(created)
        logger.info("DB bulk insert pending: %d Risk records", len(created))
        self.db.commit()
        for obj in created:
            self.db.refresh(obj)
        logger.info(
            "DB bulk insert committed: Risk ids=%s",
            [obj.id for obj in created],
        )
        return created
