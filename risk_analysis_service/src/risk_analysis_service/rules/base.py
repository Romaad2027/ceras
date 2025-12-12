from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from ..schemas.cloud_resource import GenericCloudResource


class Severity(str, Enum):
    High = "High"
    Medium = "Medium"
    Low = "Low"


class Rule(ABC):
    code: str
    description: str
    severity: Severity

    @abstractmethod
    def check(self, resource: GenericCloudResource) -> bool:
        """
        Return True if the rule detects a risk on the given resource.
        """
        raise NotImplementedError
