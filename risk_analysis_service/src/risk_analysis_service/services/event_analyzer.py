from __future__ import annotations

from typing import List, Dict, Any, Tuple
import uuid
from datetime import datetime
from pathlib import Path
import warnings
import logging
import ipaddress
import asyncio

import pandas as pd
from joblib import load
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..schemas.audit_event import GenericAuditEvent
from ..db.models.security_alert import SecurityAlert
from ..db.models.entity_profile import EntityProfile
from ..db.models.cloud_resource import CloudResource, CloudResourceCriticality
from ..db.models.cloud_identity import CloudIdentity
from ..db.repositories.audit_event_repository import AuditEventRepository
from ..schemas.security_alert import SecurityAlertOut
from ..core.socket_manager import manager


logger = logging.getLogger("risk_analysis.services")


class EventAnalyzerService:
    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parent.parent / "ml_engine"
        self._model_path = base_dir / "model.pkl"
        self._scaler_path = base_dir / "scaler.pkl"

        self.model = None
        self.scaler = None

                        
        try:
            if self._scaler_path.exists():
                self.scaler = load(self._scaler_path)
                logger.info("Loaded scaler from %s", self._scaler_path)
            else:
                warnings.warn(f"Scaler not found at {self._scaler_path}")
        except Exception as exc:
            warnings.warn(f"Failed to load scaler: {exc}")

        try:
            if self._model_path.exists():
                self.model = load(self._model_path)
                logger.info("Loaded model from %s", self._model_path)
            else:
                warnings.warn(f"Model not found at {self._model_path}")
        except Exception as exc:
            warnings.warn(f"Failed to load model: {exc}")

    @staticmethod
    def _hybrid_entity_id(event: GenericAuditEvent) -> str:
        """
        Prefer non-empty, non-generic actor_identity; fallback to IP address.
        """
        invalid_identity_values = {"", "nan", "none", "anonymous", "unknown"}
        identity = (event.actor_identity or "").strip()
        if identity and identity.lower() not in invalid_identity_values:
            return identity
        return (event.actor_ip_address or "").strip()

    @staticmethod
    def _truncate_to_hour(dt: datetime) -> datetime:
        return dt.replace(minute=0, second=0, microsecond=0)

    @staticmethod
    def _ip_in_whitelisted_cidrs(ip_str: str, cidrs: list[str]) -> bool:
        """
        Return True if the provided IP belongs to any of the CIDRs.
        Invalid IP or CIDR entries are ignored gracefully.
        """
        if not ip_str or not cidrs:
            return False
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        for cidr in cidrs:
            try:
                network = ipaddress.ip_network(cidr, strict=False)
            except ValueError:
                continue
            if ip_obj in network:
                return True
        return False

    @staticmethod
    def _is_destructive_action(action_name: str) -> bool:
        """
        Heuristic to classify destructive actions (deletes/terminations/drops).
        """
        if not action_name:
            return False
        a = action_name.strip().lower()
        destructive_prefixes = (
            "delete",
            "terminate",
            "destroy",
            "drop",
            "purge",
            "revoke",
            "shutdown",
            "kill",
        )
        return a.startswith(destructive_prefixes)

    @staticmethod
    def _auto_profile_allows(
        event: GenericAuditEvent, profile: EntityProfile | None
    ) -> bool:
        """
        Return True if the event matches all available auto-profile attributes.
        If profile is None or no auto fields are configured, returns False (no allow).
        """
        if profile is None:
            return False
        hours = set(profile.auto_common_hours or [])
        ips = set(profile.auto_common_ips or [])
        actions = set(profile.auto_common_actions or [])
        has_any = bool(hours or ips or actions)
        if not has_any:
            return False
        hour_ok = (int(event.event_time.hour) in hours) if hours else True
        ip_ok = ((event.actor_ip_address or "") in ips) if ips else True
        action_ok = ((event.action_name or "") in actions) if actions else True
        return bool(hour_ok and ip_ok and action_ok)

    def _get_anomaly_summary(
        self, db: Session, entity_id: str, start_time: datetime, end_time: datetime
    ) -> dict:
        repo = AuditEventRepository(db)
        return repo.get_top_action_target_summary(
            entity_id=entity_id, start_time=start_time, end_time=end_time
        )

    def _prepare_features(self, events: List[GenericAuditEvent]) -> pd.DataFrame:
        """
        Convert raw events into hourly aggregated features matching training logic.
        Returns DataFrame indexed by (entity_id, time_window).
        """
        if not events:
            return pd.DataFrame(
                columns=[
                    "event_count",
                    "failure_ratio",
                    "unique_ips",
                    "critical_actions_count",
                    "is_night",
                ]
            )

        records: List[Dict[str, Any]] = []
        for e in events:
            records.append(
                {
                    "event_time": pd.to_datetime(
                        e.event_time, utc=True, errors="coerce"
                    ),
                    "actor_identity": (e.actor_identity or "").strip(),
                    "actor_ip_address": (e.actor_ip_address or "").strip(),
                    "action_name": (e.action_name or "").strip(),
                    "status": (
                        e.event_status.value
                        if hasattr(e.event_status, "value")
                        else str(e.event_status)
                    ).upper(),
                    "entity_id": self._hybrid_entity_id(e),
                }
            )

        df = pd.DataFrame.from_records(records)
        df = df.dropna(subset=["event_time"])

                        
        status_series = df["status"].astype(str).str.strip().str.upper()
        df["is_failure"] = status_series.eq("FAILURE")
        action_series = df["action_name"].astype(str).str.strip().str.lower()
        df["is_critical_action"] = action_series.str.startswith(("delete", "terminate"))

                     
        df["time_window"] = df["event_time"].dt.floor("h")

        grouped = df.groupby(["entity_id", "time_window"])
        features = grouped.agg(
            event_count=("event_time", "size"),
            failure_ratio=("is_failure", "mean"),
            unique_ips=("actor_ip_address", "nunique"),
            critical_actions_count=("is_critical_action", "sum"),
        )

        window_hours = features.index.get_level_values(1).hour
        is_night = ((window_hours <= 6) | (window_hours >= 21)).astype(int)
        features = features.assign(is_night=is_night)

                                    
        features = features.astype(
            {
                "event_count": "int64",
                "failure_ratio": "float64",
                "unique_ips": "int64",
                "critical_actions_count": "int64",
                "is_night": "int64",
            }
        )
        features.index.set_names(["entity_id", "time_window"], inplace=True)
        return features

    def analyze_events(
        self,
        db: Session,
        events: List[GenericAuditEvent],
        organization_id: uuid.UUID,
    ) -> List[SecurityAlert]:
        """
        Aggregated alerting per event:
          - Collect all violations for a single event instead of stopping at the first one.
          - Compute maximum severity over all detected violations.
          - Emit ONE SecurityAlert per event if there are any violations.
        """
        logger.info("Analyzing events batch: size=%d", len(events) if events else 0)
        created_alerts: List[SecurityAlert] = []
        if not events:
            return created_alerts

                                                                                               
        entity_ids = {self._hybrid_entity_id(e) for e in events}
        target_resource_ids = {e.target_resource for e in events if e.target_resource}
        actor_arns = {
            (e.actor_identity or "").strip()
            for e in events
            if (e.actor_identity or "").strip()
        }

        profiles_by_id: Dict[str, EntityProfile] = {}
        if entity_ids:
            stmt = select(EntityProfile).where(
                EntityProfile.entity_id.in_(list(entity_ids)),
                EntityProfile.organization_id == organization_id,
            )
            for prof in db.execute(stmt).scalars().all():
                profiles_by_id[str(prof.entity_id)] = prof

        identities_by_arn: Dict[str, CloudIdentity] = {}
        if actor_arns:
            istmt = select(CloudIdentity).where(
                CloudIdentity.identity_arn.in_(list(actor_arns)),
                CloudIdentity.organization_id == organization_id,
            )
            for ident in db.execute(istmt).scalars().all():
                identities_by_arn[str(ident.identity_arn)] = ident

        resources_by_id: Dict[str, CloudResource] = {}
        if target_resource_ids:
            rstmt = select(CloudResource).where(
                CloudResource.resource_id.in_(list(target_resource_ids)),
                CloudResource.organization_id == organization_id,
            )
            for res in db.execute(rstmt).scalars().all():
                resources_by_id[str(res.resource_id)] = res

                                                                   
        features_df = self._prepare_features(events)
        feature_columns = [
            "event_count",
            "failure_ratio",
            "unique_ips",
            "critical_actions_count",
            "is_night",
        ]

                               
        for event in events:
            entity_id = self._hybrid_entity_id(event)
            profile = profiles_by_id.get(str(entity_id))
            resource = resources_by_id.get(event.target_resource)
            actor_arn = (event.actor_identity or "").strip()
            cloud_identity = identities_by_arn.get(actor_arn) if actor_arn else None

                               
            violations: list[str] = []
            max_severity_val: int = 0
            skip_ml: bool = False

            def update_max_severity(tag: str) -> None:
                nonlocal max_severity_val
                severity_rank: dict[str, int] = {
                    "LOW": 1,
                    "MEDIUM": 2,
                    "HIGH": 3,
                    "CRITICAL": 4,
                }
                rank = severity_rank.get(tag, 0)
                if rank > max_severity_val:
                    max_severity_val = rank

                                                             
            if actor_arn:
                if cloud_identity:
                                                                    
                    if (
                        profile
                        and getattr(profile, "cloud_identity_id", None)
                        != cloud_identity.id
                    ):
                        profile.cloud_identity_id = cloud_identity.id
                        db.add(profile)
                else:
                                                                                 
                    violations.append("SHADOW_IDENTITY")
                    update_max_severity("MEDIUM")

                                   
            if profile and profile.whitelisted_cidrs:
                whitelisted = self._ip_in_whitelisted_cidrs(
                    (event.actor_ip_address or "").strip(), profile.whitelisted_cidrs
                )
                if not whitelisted:
                    violations.append("IP_VIOLATION")
                    update_max_severity("CRITICAL")

                                                       
            if resource and resource.criticality == CloudResourceCriticality.CRITICAL:
                if self._is_destructive_action(event.action_name or ""):
                    violations.append("CRITICAL_RESOURCE_TAMPERING")
                    update_max_severity("HIGH")

                                         
            if profile:
                if (event.action_name or "") in (
                    profile.manual_forbidden_actions or []
                ):
                    violations.append("FORBIDDEN_ACTION")
                    update_max_severity("MEDIUM")
                if (event.action_name or "") in (profile.manual_allowed_actions or []):
                    skip_ml = True

                                  
            should_run_ml = False
            if not skip_ml:
                if profile is None:
                    should_run_ml = True
                else:
                                                                               
                    should_run_ml = not self._auto_profile_allows(event, profile)

            if should_run_ml and self.model is not None and self.scaler is not None:
                window_start = self._truncate_to_hour(event.event_time)
                idx_key: Tuple[str, datetime] = (
                    str(entity_id),
                    pd.to_datetime(window_start, utc=True),
                )
                if features_df.empty or idx_key not in features_df.index:
                                                          
                    pass
                else:
                    row = features_df.loc[idx_key]
                    vector = row[feature_columns].fillna(0).values.reshape(1, -1)
                    try:
                        vector_scaled = self.scaler.transform(vector)
                        prediction = self.model.predict(vector_scaled)
                    except Exception as exc:
                        warnings.warn(f"ML inference failed: {exc}")
                        prediction = [None]
                    if prediction and prediction[0] == -1:
                        violations.append("ML_ANOMALY_DETECTED")
                        update_max_severity("HIGH")

                                         
            if violations:
                                                      
                val_to_label: dict[int, str] = {
                    1: "LOW",
                    2: "MEDIUM",
                    3: "HIGH",
                    4: "CRITICAL",
                }
                severity_label = val_to_label.get(max_severity_val, "LOW")

                                                                                      
                rule_code = (
                    "MULTIPLE_VIOLATIONS" if len(violations) > 1 else violations[0]
                )

                                              
                target_id = (
                    resource.resource_id
                    if resource
                    else (event.target_resource or "unknown")
                )
                description = (
                    f"Violations detected: {', '.join(violations)}. "
                    f"Details: action={event.action_name}, resource={target_id}, "
                    f"actor={entity_id}, ip={event.actor_ip_address}."
                )

                alert = SecurityAlert(
                    event_id=event.event_id,
                    rule_code=rule_code,
                    severity=severity_label,
                    description=description,
                    organization_id=organization_id,
                )
                                                       
                if cloud_identity:
                    alert.cloud_identity_id = cloud_identity.id
                created_alerts.append(alert)

        if created_alerts:
            logger.info(
                "DB insert pending: %d SecurityAlert alerts", len(created_alerts)
            )
            db.add_all(created_alerts)
            db.commit()
            for a in created_alerts:
                db.refresh(a)
            logger.info(
                "DB insert committed: SecurityAlert ids=%s",
                [a.id for a in created_alerts],
            )
                                                                               
            for a in created_alerts:
                try:
                    payload = SecurityAlertOut.model_validate(a).model_dump(mode="json")
                except Exception:
                                                                         
                    created_at_val = getattr(a, "created_at", None)
                    created_at_str = (
                        created_at_val.isoformat()
                        if hasattr(created_at_val, "isoformat")
                        else str(created_at_val)
                    )
                    payload = {
                        "id": getattr(a, "id", None),
                        "event_id": getattr(a, "event_id", "") or "",
                        "rule_code": getattr(a, "rule_code", "") or "",
                        "severity": getattr(a, "severity", "") or "",
                        "description": getattr(a, "description", "") or "",
                        "created_at": created_at_str,
                        "organization_id": str(getattr(a, "organization_id", "")) or "",
                        "cloud_identity_id": (
                            str(getattr(a, "cloud_identity_id"))
                            if getattr(a, "cloud_identity_id", None)
                            else None
                        ),
                        "cloud_account_id": (
                            str(getattr(a, "cloud_account_id"))
                            if getattr(a, "cloud_account_id", None)
                            else None
                        ),
                    }
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(manager.broadcast(payload, organization_id))
                except RuntimeError:
                                                                                             
                    try:
                        asyncio.run(manager.broadcast(payload, organization_id))
                    except RuntimeError:
                                                                                        
                        logger.debug("Skipping broadcast; no valid event loop context")
        else:
            logger.info("No alerts created for this batch")
        return created_alerts
