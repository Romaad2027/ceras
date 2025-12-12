from __future__ import annotations

from abc import ABC, abstractmethod

from .base import Severity
from ..schemas.audit_event import GenericAuditEvent


class EventRule(ABC):
    code: str
    description: str
    severity: Severity

    @abstractmethod
    def check(self, event: GenericAuditEvent) -> bool:
        """
        Return True if the audit event violates this rule.
        """
        raise NotImplementedError
