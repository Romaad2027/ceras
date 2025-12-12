import asyncio
import os
import json
import logging
from typing import Optional, Any, Dict, List, Tuple
from uuid import uuid4, UUID
from datetime import datetime
import time

from aiokafka import AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient
from aiokafka.admin.new_topic import NewTopic
from aiokafka.errors import (
    TopicAlreadyExistsError,
    KafkaConnectionError,
    KafkaError,
)

from ..db.session import SessionLocal
from ..schemas.audit_event import GenericAuditEvent
from ..services.event_analyzer import EventAnalyzerService
from ..db.models.audit_event import AuditEvent
from ..db.models.cloud_identity import CloudIdentity, IdentityType


logger = logging.getLogger(__name__)


class EventConsumer:
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "cloud_audit_events",
        group_id: str = "risk-analysis-service",
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True,
    ) -> None:
        """
        Initialize Kafka consumer for audit events and cloud identities.
        """
                                     
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", bootstrap_servers)
        audit_topic = os.getenv("KAFKA_TOPIC", topic)
        identities_topic = os.getenv("KAFKA_IDENTITIES_TOPIC", "cloud_identities")
        group_id = os.getenv("KAFKA_GROUP_ID", group_id)

        self._audit_topic = audit_topic
        self._identities_topic = identities_topic
        self._topics: tuple[str, str] = (audit_topic, identities_topic)
        self._bootstrap_servers = bootstrap_servers
        self._consumer: Optional[AIOKafkaConsumer] = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
        )
                                                                     
        self._analyzer = EventAnalyzerService()
        self._running = False
                                   
                                                        
        self.batch: List[Tuple[UUID, GenericAuditEvent]] = []
        self.BATCH_SIZE: int = 50
        self.FLUSH_INTERVAL: float = 5.0
        self._last_flush_time: float = time.monotonic()

    async def _ensure_topic_exists(self) -> None:
        """
        Ensure the consumer topic exists. Try to create if missing.
        """
        admin = AIOKafkaAdminClient(bootstrap_servers=self._bootstrap_servers)
        try:
            await admin.start()
            try:
                existing_topics = set(await admin.list_topics())
                to_create = [t for t in self._topics if t not in existing_topics]
                if to_create:
                    await admin.create_topics(
                        [
                            NewTopic(name=t, num_partitions=1, replication_factor=1)
                            for t in to_create
                        ]
                    )
                    logger.info("Created Kafka topics %s", to_create)
            except TopicAlreadyExistsError:
                                                                     
                logger.debug("Topic(s) already exist")
            except (KafkaConnectionError, KafkaError) as exc:
                logger.warning(
                    "Could not verify/create topics %s: %s", self._topics, exc
                )
            except Exception as exc:
                logger.warning(
                    "Unexpected error ensuring topics %s: %s", self._topics, exc
                )
        finally:
            try:
                await admin.close()
            except Exception:
                pass

    def _msg_ctx(self, msg: Any) -> Dict[str, Any]:
        """
        Provide a consistent set of message metadata for logging.
        """
        return {
            "topic": getattr(msg, "topic", ",".join(self._topics)),
            "partition": getattr(msg, "partition", "?"),
            "offset": getattr(msg, "offset", "?"),
        }

    def _normalize_raw(self, raw: Any, msg: Any) -> Optional[Any]:
        """
        Normalize raw Kafka value: handle None, bytes, and strings.
        Returns normalized raw (str or dict) or None to skip.
        """
        ctx = self._msg_ctx(msg)
        if raw is None:
            logger.warning(
                "Received null message on %s partition %s offset %s; skipping",
                ctx["topic"],
                ctx["partition"],
                ctx["offset"],
            )
            return None

        if isinstance(raw, (bytes, bytearray)):
            if len(raw) == 0:
                logger.warning(
                    "Received empty bytes payload on %s partition %s offset %s; skipping",
                    ctx["topic"],
                    ctx["partition"],
                    ctx["offset"],
                )
                return None
            try:
                raw = raw.decode("utf-8")
            except Exception:
                raw = raw.decode("utf-8", errors="replace")

        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                logger.warning(
                    "Received blank string payload on %s partition %s offset %s; skipping",
                    ctx["topic"],
                    ctx["partition"],
                    ctx["offset"],
                )
                return None

        return raw

    def _parse_payload(self, raw: Any, msg: Any) -> Optional[Dict[str, Any]]:
        """
        Convert normalized raw into a dict payload. Returns None to skip.
        May raise json.JSONDecodeError for invalid JSON strings.
        """
        ctx = self._msg_ctx(msg)
        logger.info("Parsing payload: %r", raw)
        payload = raw if isinstance(raw, dict) else json.loads(raw)
        logger.info("Parsed payload: %r", payload)
        if not isinstance(payload, dict):
            logger.warning(
                "Ignoring non-object JSON payload on %s partition %s offset %s: %r",
                ctx["topic"],
                ctx["partition"],
                ctx["offset"],
                payload,
            )
            return None
        return payload

    def _upsert_cloud_identity(self, payload: Dict[str, Any]) -> None:
        """
        Upsert CloudIdentity for the given organization and identity ARN.
        Expected payload keys:
          - organization_id (UUID or str)
          - identity_arn (str)
          - identity_name (str, optional)
          - identity_type (str: IAM_USER|IAM_ROLE|ROOT, optional)
          - is_mfa_enabled (bool, optional)
          - created_at (ISO datetime or epoch seconds, optional)
        """
        org_raw = payload.get("organization_id")
        identity_arn = (payload.get("identity_arn") or "").strip()
        if not org_raw or not identity_arn:
            logger.warning(
                "Skipping cloud identity upsert: missing organization_id or identity_arn"
            )
            return
        try:
            org_id: UUID = UUID(str(org_raw))
        except Exception:
            logger.warning("Invalid organization_id in identity payload: %r", org_raw)
            return

        identity_name = (payload.get("identity_name") or "").strip() or identity_arn
        type_raw = (payload.get("identity_type") or "IAM_USER").strip().upper()
        try:
            identity_type = IdentityType[type_raw]
        except Exception:
                                             
            identity_type = IdentityType.IAM_USER
        is_mfa_enabled = bool(payload.get("is_mfa_enabled", False))

        created_at_val = payload.get("created_at")
        created_at_dt: Optional[datetime] = None
        if created_at_val:
            try:
                if isinstance(created_at_val, (int, float)):
                    created_at_dt = datetime.utcfromtimestamp(float(created_at_val))
                else:
                    created_at_dt = datetime.fromisoformat(
                        str(created_at_val).replace("Z", "+00:00")
                    )
            except Exception:
                created_at_dt = None

        db = SessionLocal()
        try:
                                                                  
            from sqlalchemy import select

            stmt = select(CloudIdentity).where(
                CloudIdentity.organization_id == org_id,
                CloudIdentity.identity_arn == identity_arn,
            )
            existing = db.execute(stmt).scalars().first()
            if existing:
                existing.identity_name = identity_name
                existing.identity_type = identity_type
                existing.is_mfa_enabled = is_mfa_enabled
                                                                    
                if created_at_dt and existing.created_at is None:
                    existing.created_at = created_at_dt
                db.add(existing)
                logger.info(
                    "Updated CloudIdentity for org=%s arn=%s", org_id, identity_arn
                )
            else:
                obj = CloudIdentity(
                    organization_id=org_id,
                    identity_arn=identity_arn,
                    identity_name=identity_name,
                    identity_type=identity_type,
                    is_mfa_enabled=is_mfa_enabled,
                    created_at=created_at_dt,
                )
                db.add(obj)
                logger.info(
                    "Inserted CloudIdentity for org=%s arn=%s", org_id, identity_arn
                )
            db.commit()
        except Exception as exc:
            logger.exception("Upsert CloudIdentity failed: %s", exc)
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception:
                pass

    def _process_payload(self, db: Any, payload: Dict[str, Any]) -> None:
        """
        Validate payload into domain model and buffer it for batch processing.
        """
                                                                                                 
        org_raw = payload.get("organization_id")
        if not org_raw:
            logger.warning("Dropping payload without organization_id: %r", payload)
            return
        try:
            org_id: UUID = UUID(str(org_raw))
        except Exception:
            logger.warning(
                "Dropping payload with invalid organization_id %r: %r", org_raw, payload
            )
            return
        event_dict = self._to_generic_event_payload(payload)
        event = GenericAuditEvent.model_validate(event_dict)
                                                                                                         
        self.batch.append((org_id, event))

    def _to_generic_event_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt various incoming payload shapes (e.g., AWS CloudTrail-like under 'raw')
        into the GenericAuditEvent dict expected by validation.
        """
                                                                      
        raw = payload.get("raw") if isinstance(payload, dict) else None
        raw = raw if isinstance(raw, dict) else payload

                                                
        def _get_event_time() -> Any:
                                              
            v = (
                payload.get("event_time")
                or raw.get("event_time")
                or raw.get("eventTime")
            )
            return v

        def _get_actor_identity() -> Optional[str]:
            v = (
                payload.get("actor_identity")
                or raw.get("actor_identity")
                or (raw.get("userIdentity") or {}).get("userName")
                or (raw.get("userIdentity") or {}).get("arn")
                or raw.get("AccessKeyId")
            )
            return v

        def _get_actor_ip() -> Optional[str]:
            v = (
                payload.get("actor_ip_address")
                or raw.get("actor_ip_address")
                or raw.get("sourceIPAddress")
                or payload.get("ip")
            )
            return v

        def _get_action_name() -> Optional[str]:
            v = (
                payload.get("action_name")
                or raw.get("action_name")
                or raw.get("eventName")
            )
            return v

        def _get_target_resource() -> Optional[str]:
            if "target_resource" in payload:
                return payload.get("target_resource")
            if "target_resource" in raw:
                return raw.get("target_resource")
            req = raw.get("requestParameters") or {}
                                   
            bucket = req.get("bucketName") or req.get("bucket") or req.get("name")
            key = req.get("key") or req.get("objectKey")
            instance = (
                req.get("instanceId") or req.get("instanceIds") or req.get("imageId")
            )
            resource = None
            if bucket and key:
                resource = f"s3://{bucket}/{key}"
            elif bucket:
                resource = f"s3://{bucket}"
            elif instance:
                resource = str(instance)
                                                           
            if not resource:
                resource = (
                    raw.get("eventSource") or req.get("resource") or req.get("groupId")
                )
            return resource

        def _get_event_status() -> str:
            v = payload.get("event_status") or raw.get("event_status")
            if v:
                return str(v)
                                           
            if raw.get("errorCode") or raw.get("errorMessage"):
                return "FAILURE"
                                                                    
            if "responseElements" in raw and raw.get("responseElements") is None:
                return "FAILURE"
            return "SUCCESS"

        def _get_cloud_provider() -> str:
            v = payload.get("cloud_provider") or raw.get("cloud_provider")
            if v:
                return str(v)
                                                        
            aws_hints = (
                "awsRegion",
                "eventSource",
                "eventName",
                "userIdentity",
                "AccessKeyId",
            )
            if any(h in raw for h in aws_hints):
                return "AWS"
            return "AWS"           

        def _get_event_id() -> str:
            return (
                payload.get("event_id")
                or raw.get("event_id")
                or raw.get("eventID")
                or str(uuid4())
            )

                                                     
        normalized: Dict[str, Any] = {
            "event_id": _get_event_id(),
            "event_time": _get_event_time(),
            "actor_identity": _get_actor_identity() or "",
            "actor_ip_address": _get_actor_ip() or "",
            "action_name": _get_action_name() or "",
            "target_resource": _get_target_resource() or "",
            "event_status": _get_event_status(),
                                         
            "organization_id": payload.get("organization_id"),
            "cloud_provider": _get_cloud_provider(),
            "raw_log": raw if isinstance(raw, dict) else {"raw": raw},
        }

                                                                                           
        et = normalized.get("event_time")
        if isinstance(et, (int, float)):
            try:
                normalized["event_time"] = (
                    datetime.utcfromtimestamp(float(et)).isoformat() + "Z"
                )
            except Exception:
                pass

        logger.debug("Normalized event for validation: %r", normalized)
        return normalized

    def _flush(self) -> None:
        """
        Persist buffered events and run analysis in a single DB transaction.
        """
        if not self.batch:
            return
        db = SessionLocal()
        try:
                                                                          
            orm_events: List[AuditEvent] = []
            for org_id, e in self.batch:
                orm_events.append(
                    AuditEvent(
                        event_time=e.event_time,
                        actor_identity=e.actor_identity or None,
                        action_name=e.action_name or None,
                        target_resource=e.target_resource or None,
                        actor_ip_address=e.actor_ip_address or None,
                        event_status=str(
                            e.event_status.value
                            if hasattr(e.event_status, "value")
                            else e.event_status
                        ),
                        organization_id=org_id,
                    )
                )
            if orm_events:
                db.bulk_save_objects(orm_events)

                                                       
            org_to_events: Dict[UUID, List[GenericAuditEvent]] = {}
            for org_id, e in self.batch:
                org_to_events.setdefault(org_id, []).append(e)
            for org_id, events in org_to_events.items():
                try:
                    self._analyzer.analyze_events(db, events, organization_id=org_id)
                except Exception as exc:
                    logger.exception(
                        "Analyzer failed for org %s batch of %d events: %s",
                        org_id,
                        len(events),
                        exc,
                    )

                            
            db.commit()
            logger.info(
                "Flushed %d events to audit_events and committed.", len(self.batch)
            )
        except Exception as exc:
            logger.exception("Failed during batch flush: %s", exc)
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception:
                pass
                                             
        self.batch.clear()
        self._last_flush_time = time.monotonic()

    async def start(self) -> None:
                                                                      
        try:
            await self._ensure_topic_exists()
        except Exception as exc:
                                                                                              
            logger.debug("Continuing without ensuring topic due to: %s", exc)
        await self._consumer.start()
        self._running = True
        logger.info("Kafka consumer started for topics %s", self._topics)

    async def stop(self) -> None:
        self._running = False
        await self._consumer.stop()
        logger.info("Kafka consumer stopped for topics %s", self._topics)

    async def consume_loop(self) -> None:
        """
        Batch consuming loop with time-based flushing.
        """
        if not self._running:
            logger.warning("consume_loop called before start(); starting consumer now.")
            await self.start()

        try:
            while True:
                try:
                                                                      
                    messages_map = await self._consumer.getmany(timeout_ms=1000)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.exception("Error fetching messages from Kafka: %s", exc)
                    await asyncio.sleep(1.0)
                    continue

                                          
                total_received = 0
                for tp, messages in messages_map.items():
                    for msg in messages:
                        total_received += 1
                        try:
                            raw = msg.value
                            raw = self._normalize_raw(raw, msg)
                            if raw is None:
                                continue
                            payload = self._parse_payload(raw, msg)
                            if payload is None:
                                continue
                            if getattr(msg, "topic", "") == self._identities_topic:
                                                                            
                                self._upsert_cloud_identity(payload)
                            else:
                                              
                                self._process_payload(None, payload)
                        except json.JSONDecodeError as exc:
                            logger.warning(
                                "Invalid JSON received on topic %s: %s",
                                getattr(msg, "topic", ",".join(self._topics)),
                                exc,
                            )
                        except Exception as exc:
                            logger.exception("Failed to process message: %s", exc)

                                                    
                now = time.monotonic()
                if (
                    len(self.batch) >= self.BATCH_SIZE
                    or (now - self._last_flush_time) >= self.FLUSH_INTERVAL
                ):
                    self._flush()
                                                                                                      
                elif (
                    total_received == 0
                    and self.batch
                    and (now - self._last_flush_time) >= self.FLUSH_INTERVAL
                ):
                    self._flush()
        except asyncio.CancelledError:
            logger.info("consume_loop cancelled; stopping consumer.")
                                             
            try:
                self._flush()
            except Exception:
                pass
            await self.stop()
        except Exception as exc:
            logger.exception("Fatal error in consume_loop: %s", exc)
                                     
            try:
                self._flush()
            except Exception:
                pass
            await self.stop()
