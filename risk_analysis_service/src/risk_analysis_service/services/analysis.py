from sqlalchemy.orm import Session
from ..db.models import risk
from ..db.models.cloud_resource import CloudResource
from ..schemas.cloud_resource import GenericCloudResource
from ..schemas import risk as risk_schemas
import logging
from ..db.repositories.risk_repository import RiskRepository

logger = logging.getLogger("risk_analysis.services")


def analyze_and_save_risks(
    db: Session, resource: GenericCloudResource
) -> list[risk.Risk]:
    """
    Аналізує узагальнений хмарний ресурс (наприклад, S3 бакет), зберігає знайдені
    ризики в БД і повертає їх. Для S3 очікуються ключі в configuration:
    'is_public' та 'encryption_type' (вважається відсутнім шифрування, якщо значення 'NONE').
    """
    found_risks = []

    logger.info(
        "Analyze resource: id=%s type=%s", resource.resource_id, resource.resource_type
    )
    is_public = bool(resource.configuration.get("is_public"))
    logger.debug("Is public: %s", is_public)
    encryption_type = resource.configuration.get("encryption_type")

                                                                   
    resource_name = resource.configuration.get("bucket_name") or resource.resource_id

                                            
    db_cloud_resource = db.get(CloudResource, resource.resource_id)
    if db_cloud_resource is None:
        raise ValueError(f"CloudResource not found for id={resource.resource_id}")
    org_id = db_cloud_resource.organization_id

    if is_public:
        item = risk_schemas.RiskCreate(
            resource_name=resource_name,
            description="Бакет є публічно доступним для всіх в Інтернеті.",
            severity="High",
            organization_id=org_id,
            resource_id=resource.resource_id,
        )
        found_risks.append(item)

    if encryption_type == "NONE":
        item = risk_schemas.RiskCreate(
            resource_name=resource_name,
            description="Шифрування даних 'at-rest' не налаштовано.",
            severity="Medium",
            organization_id=org_id,
            resource_id=resource.resource_id,
        )
        found_risks.append(item)

    saved_risks_models = []
    repo = RiskRepository(db)
    saved_risks_models = repo.create_many(found_risks)
    logger.info(
        "Analysis result for %s: found=%d, saved_ids=%s",
        resource_name,
        len(found_risks),
        [r.id for r in saved_risks_models],
    )

    return saved_risks_models
