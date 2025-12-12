from fastapi import APIRouter

from .v1.endpoints import aws, health
from .v1.endpoints import risks as risks_endpoints
from .v1.endpoints import events as events_endpoints
from .v1.endpoints import resources as resources_endpoints
from .v1.endpoints import profiles as profiles_endpoints
from .v1.endpoints import organizations as organizations_endpoints
from .v1.endpoints import organization as organization_members_endpoints
from .v1.endpoints import alerts as alerts_endpoints
from .v1.endpoints import cloud_accounts as cloud_accounts_endpoints


api_router = APIRouter()

                   
api_router.include_router(aws.router, prefix="/api/v1")
api_router.include_router(organizations_endpoints.router, prefix="/api/v1")
api_router.include_router(organization_members_endpoints.router, prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(risks_endpoints.router, prefix="/v1")
api_router.include_router(events_endpoints.router, prefix="/v1")
api_router.include_router(resources_endpoints.router, prefix="/v1")
api_router.include_router(resources_endpoints.router, prefix="/api/v1")
api_router.include_router(profiles_endpoints.router, prefix="/v1")
api_router.include_router(alerts_endpoints.router, prefix="/v1")
api_router.include_router(cloud_accounts_endpoints.router, prefix="/api/v1")
