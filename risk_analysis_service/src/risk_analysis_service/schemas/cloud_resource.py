from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, field_validator


class CloudProvider(str, Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"


class ResourceType(str, Enum):
    STORAGE_BUCKET = "STORAGE_BUCKET"
    VIRTUAL_MACHINE = "VIRTUAL_MACHINE"
    DATABASE = "DATABASE"


class GenericCloudResource(BaseModel):
    resource_id: str
    resource_type: ResourceType
    cloud_provider: CloudProvider
    account_id: str
    configuration: Dict[str, Any]

                                                                                       
    @field_validator("resource_type", mode="before")
    def _normalize_resource_type(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return ResourceType(value.upper())
            except ValueError:
                return value
        return value

    @field_validator("cloud_provider", mode="before")
    def _normalize_cloud_provider(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return CloudProvider(value.upper())
            except ValueError:
                return value
        return value


if __name__ == "__main__":
    s3_bucket = GenericCloudResource(
        resource_id="arn:aws:s3:::example-bucket",
        resource_type=ResourceType.STORAGE_BUCKET,
        cloud_provider=CloudProvider.AWS,
        account_id="123456789012",
        configuration={
            "is_public": False,
            "encryption_enabled": True,
        },
    )
    print(s3_bucket.model_dump_json(indent=2))
