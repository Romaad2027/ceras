from __future__ import annotations

from .base import Rule, Severity
from ..schemas.cloud_resource import GenericCloudResource


class PublicAccessRule(Rule):
    code = "S3_PUBLIC_ACCESS"
    description = "Бакет є публічно доступним для всіх в Інтернеті."
    severity = Severity.High

    def check(self, resource: GenericCloudResource) -> bool:
        return bool(resource.configuration.get("is_public"))


class EncryptionDisabledRule(Rule):
    code = "S3_ENCRYPTION_DISABLED"
    description = "Шифрування даних 'at-rest' не налаштовано."
    severity = Severity.Medium

    def check(self, resource: GenericCloudResource) -> bool:
        return resource.configuration.get("encryption_type") == "NONE"


class VersioningDisabledRule(Rule):
    code = "S3_VERSIONING_DISABLED"
    description = "Версіонування об'єктів вимкнено."
    severity = Severity.Low

    def check(self, resource: GenericCloudResource) -> bool:
        return resource.configuration.get("versioning_enabled") is False


STORAGE_BUCKET_RULES: list[Rule] = [
    PublicAccessRule(),
    EncryptionDisabledRule(),
    VersioningDisabledRule(),
]
