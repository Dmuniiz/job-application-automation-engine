"""HTTP layer dependencies for the API endpoints
"""
from fastapi import Depends
from sqlmodel import Session

from app.db.session import get_session
from app.db.repository import JobRepository
from app.scraper.aggregator import JobAggregatorService
from app.services.job_discovery_service import JobDiscoveryService
from app.services.job_processing_service import JobProcessingService
from app.services.job_status_service import JobStatusService
from app.config.settings import settings

_is_mock_active = (settings.USE_MOCK) or (settings.ENVIRONMENT == "development")
_aggregator_service = JobAggregatorService(use_mock=_is_mock_active)


def get_job_repository(session: Session = Depends(get_session)) -> JobRepository:
    return JobRepository(session)


def get_discovery_service(repo: JobRepository = Depends(get_job_repository),) -> JobDiscoveryService:
    return JobDiscoveryService(repository=repo, aggregator=_aggregator_service)


def get_processing_service(repo: JobRepository = Depends(get_job_repository),) -> JobProcessingService:
    return JobProcessingService(repository=repo)

def get_status_service(
    repo: JobRepository = Depends(get_job_repository),
) -> JobStatusService:
    return JobStatusService(repository=repo)