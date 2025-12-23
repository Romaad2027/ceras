from typing import List

import logging
from sqlalchemy.orm import Session

from ..db.models.risk import Risk
from ..db.models.cloud_resource import CloudResource
from ..db.models.cloud_account import CloudAccount
from ..schemas import risk as risk_schemas
from ..schemas.cloud_resource import GenericCloudResource, ResourceType
from ..rules.s3_rules import STORAGE_BUCKET_RULES
from ..db.repositories.risk_repository import RiskRepository


logger = logging.getLogger("risk_analysis.services")


def get_all_risks(db: Session) -> List[Risk]:
    return RiskRepository(db).list_all()


def analyze_and_save_risks(db: Session, resource: GenericCloudResource) -> list[Risk]:
    """
    Аналізує ресурс за допомогою Rule Engine та зберігає знайдені ризики.
    Підтримувані типи:
    - STORAGE_BUCKET: застосовує правила з STORAGE_BUCKET_RULES
    """
    found_risks: list[risk_schemas.RiskCreate] = []

    resource_name = resource.configuration.get("bucket_name") or resource.resource_id

    logger.info(resource)
    db_cloud_resource = db.get(CloudResource, resource.resource_id)
    if db_cloud_resource is None:
        cloud_account = (
            db.query(CloudAccount)
            .filter(CloudAccount.id == resource.account_id)
            .first()
        )
        if cloud_account is None:
            raise ValueError(
                f"CloudResource not found and CloudAccount not resolvable for account_id={resource.account_id}"
            )
        if resource.resource_type == ResourceType.STORAGE_BUCKET:
            model_resource_type = "s3"
        else:
            model_resource_type = str(resource.resource_type).lower()
        db_cloud_resource = CloudResource(
            resource_id=resource.resource_id,
            organization_id=cloud_account.organization_id,
            cloud_account_id=cloud_account.id,
            resource_name=resource_name,
            resource_type=model_resource_type,
            custom_rules={},
        )
        db.add(db_cloud_resource)
        db.commit()
        db.refresh(db_cloud_resource)

    org_id = db_cloud_resource.organization_id

    if resource.resource_type == ResourceType.STORAGE_BUCKET:
        for rule in STORAGE_BUCKET_RULES:
            try:
                logger.debug(
                    "Evaluating rule %s for resource %s",
                    getattr(rule, "code", type(rule).__name__),
                    resource_name,
                )
                if rule.check(resource):
                    found_risks.append(
                        risk_schemas.RiskCreate(
                            resource_name=resource_name,
                            description=rule.description,
                            severity=rule.severity.value,
                            organization_id=org_id,
                            resource_id=resource.resource_id,
                        )
                    )
            except Exception as exc:
                logger.exception(
                    "Rule %s failed: %s",
                    getattr(rule, "code", type(rule).__name__),
                    exc,
                )

    saved_risks_models: list[Risk] = []
    repo = RiskRepository(db)
    saved_risks_models = repo.create_many(found_risks)
    logger.info(
        "Analysis result for %s: found=%d, saved_ids=%s",
        resource_name,
        len(found_risks),
        [r.id for r in saved_risks_models],
    )

    return saved_risks_models
