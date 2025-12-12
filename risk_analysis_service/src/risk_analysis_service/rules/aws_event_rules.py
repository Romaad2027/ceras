from __future__ import annotations

from .event_base import EventRule
from .base import Severity
from ..schemas.audit_event import GenericAuditEvent, EventStatus


class RootUsageRule(EventRule):
    code = "AWS_ROOT_USAGE"
    description = (
        "Використання root-користувача для повсякденних завдань є критичною "
        "вразливістю."
    )
    severity = Severity.High

    def check(self, event: GenericAuditEvent) -> bool:
        actor_identity = (event.actor_identity or "").lower()
        return "root" in actor_identity


class UnauthorizedAccessRule(EventRule):
    code = "AWS_UNAUTHORIZED_ACCESS"
    description = (
        "Неуспішна подія може свідчити про спробу підбору прав доступу "
        "(brute-force) або помилки конфігурації."
    )
    severity = Severity.Medium

    def check(self, event: GenericAuditEvent) -> bool:
        return event.event_status == EventStatus.FAILURE


class CriticalResourceDeletionRule(EventRule):
    code = "AWS_CRITICAL_RESOURCE_DELETION"
    description = (
        "Виявлено видалення критичного ресурсу (наприклад, bucket, db, instance). "
        "Це може бути саботаж або випадкове видалення інфраструктури."
    )
    severity = Severity.High

    def check(self, event: GenericAuditEvent) -> bool:
        action_name = (event.action_name or "").lower()
        if not action_name.startswith("delete"):
            return False

        target_resource = (event.target_resource or "").lower()
        critical_keywords = ("bucket", "db", "instance")
        return any(keyword in target_resource for keyword in critical_keywords)


AWS_EVENT_RULES = [
    RootUsageRule(),
    UnauthorizedAccessRule(),
    CriticalResourceDeletionRule(),
]
