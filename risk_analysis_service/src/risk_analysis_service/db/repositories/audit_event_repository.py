from __future__ import annotations

from typing import Optional, List, Dict

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from .base import BaseRepository
from ..models.audit_event import AuditEvent
from datetime import datetime, timedelta, timezone


class AuditEventRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def fetch_events_df(self, hours: Optional[int] = None) -> pd.DataFrame:
        """
        Return a DataFrame of raw audit events used for UEBA feature engineering.
        Columns: event_time, actor_identity, actor_ip_address, action_name, status
        """
                                                           
        q = self.db.query(
            AuditEvent.event_time,
            AuditEvent.actor_identity,
            AuditEvent.actor_ip_address,
            AuditEvent.action_name,
            AuditEvent.event_status,
        ).order_by(AuditEvent.event_time.asc())

        if hours is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=int(hours))
            q = q.filter(AuditEvent.event_time >= cutoff)

        rows = q.all()
        if not rows:
            return pd.DataFrame(
                columns=[
                    "event_time",
                    "actor_identity",
                    "actor_ip_address",
                    "action_name",
                    "status",
                ]
            )

                                                                
        records: List[Dict] = []
        for (
            event_time,
            actor_identity,
            actor_ip_address,
            action_name,
            event_status,
        ) in rows:
            records.append(
                {
                    "event_time": event_time,
                    "actor_identity": actor_identity,
                    "actor_ip_address": actor_ip_address,
                    "action_name": action_name,
                    "status": event_status,
                }
            )

        return pd.DataFrame.from_records(records)

    def get_top_action_target_summary(
        self, entity_id: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, object]:
        """
        Return top (action_name, target_resource) with count for a given entity
        inside [start_time, end_time]. If nothing found, return {}.
        """
        q = (
            self.db.query(
                AuditEvent.action_name.label("action_name"),
                AuditEvent.target_resource.label("target_resource"),
                func.count(AuditEvent.id).label("cnt"),
            )
            .filter(
                or_(
                    AuditEvent.actor_identity == entity_id,
                    AuditEvent.actor_ip_address == entity_id,
                ),
                AuditEvent.event_time >= start_time,
                AuditEvent.event_time <= end_time,
            )
            .group_by(AuditEvent.action_name, AuditEvent.target_resource)
            .order_by(func.count(AuditEvent.id).desc())
        )
        top = q.first()
        if not top:
            return {}
        return {
            "top_action": top.action_name,
            "top_target": top.target_resource,
            "count": int(top.cnt) if top.cnt is not None else 0,
        }
