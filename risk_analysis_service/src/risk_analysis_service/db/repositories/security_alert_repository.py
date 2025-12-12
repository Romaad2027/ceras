from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session
import logging

from ..models.security_alert import SecurityAlert
from .base import BaseRepository


logger = logging.getLogger("risk_analysis.db")


class SecurityAlertRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def create(
        self,
        *,
        event_id: str,
        rule_code: str,
        severity: str,
        description: str,
    ) -> SecurityAlert:
        alert = SecurityAlert(
            event_id=event_id,
            rule_code=rule_code,
            severity=severity,
            description=description,
        )
        self.db.add(alert)
        logger.info(
            "DB insert pending: SecurityAlert(event_id=%s, rule_code=%s, severity=%s)",
            event_id,
            rule_code,
            severity,
        )
        self.db.commit()
        self.db.refresh(alert)
        logger.info("DB insert committed: SecurityAlert id=%s", alert.id)
        return alert

    def create_many(self, alerts: List[SecurityAlert]) -> List[SecurityAlert]:
        if not alerts:
            return []
        self.db.add_all(alerts)
        logger.info("DB bulk insert pending: %d SecurityAlert records", len(alerts))
        self.db.commit()
        for a in alerts:
            self.db.refresh(a)
        logger.info(
            "DB bulk insert committed: SecurityAlert ids=%s", [a.id for a in alerts]
        )
        return alerts
