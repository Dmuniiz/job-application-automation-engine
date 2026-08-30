import logging
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_discovery_service, get_processing_service, get_status_service
from app.services.job_discovery_service import JobDiscoveryService
from app.services.job_processing_service import JobProcessingService
from app.services.job_status_service import JobStatusService

from app.models.api import RecurringCompaniesResponse
from app.services.company_radar_service import CompanyRadarService
from app.api.deps import get_company_radar_service

from app.models.api import (
    ProcessJobRequest, ProcessJobResponse,
    SearchJobsRequest, SearchJobsResponse, JobSearchResult,
    UpdateJobStatusRequest, UpdateJobStatusResponse
)

logger = logging.getLogger("job_automation")
router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.post("/search-jobs", response_model=SearchJobsResponse)
async def search_jobs(
    request: SearchJobsRequest,

    # Dependency injection for the JobDiscoveryService
    service: JobDiscoveryService = Depends(get_discovery_service),
):
    
    result = await service.discover(
        keywords=request.keywords, location=request.location, limit_per_source=request.limit,
    )

    return SearchJobsResponse(
        count=len(result.new_jobs),
        skipped_duplicates=result.skipped_duplicates,
        jobs=[JobSearchResult(**vars(j)) for j in result.new_jobs],
    )


@router.post("/process-job", response_model=ProcessJobResponse)
async def process_job(
    request: ProcessJobRequest,
    service: JobProcessingService = Depends(get_processing_service),
):

    result = await service.process(
        job_id=str(request.job_id), job_url=str(request.job_url),
    )

    return ProcessJobResponse(**vars(result))

@router.post("/jobs/{job_hash}/status", response_model=UpdateJobStatusResponse)
async def update_job_status(
    job_hash: str,
    request: UpdateJobStatusRequest,
    service: JobStatusService = Depends(get_status_service),
):
    record = service.update(
        job_hash, status=request.status, score=request.score,
        status_recomendacao=request.status_recomendacao,
        justificativa_curta=request.justificativa_curta,
        industry_fit=request.industry_fit,
        skills_match=request.skills_match,
        skills_missing=request.skills_missing,
        skills_transferable=request.skills_transferable,
        google_doc_url=request.google_doc_url,
        sheet_synced=request.sheet_synced,
    )
    return UpdateJobStatusResponse(job_hash=job_hash, status=record.status, score=record.score)

#reccuring companies query endpoint score >= 70

@router.get("/companies/recurring", response_model=RecurringCompaniesResponse)
async def get_recurring_companies(
    min_score: int = Query(default=70, ge=0, le=100),
    since_days: int = Query(default=28, ge=1, le=365),
    min_occurrences: int = Query(default=2, ge=2, le=50),
    limit: int = Query(default=20, ge=1, le=100),
    service: CompanyRadarService = Depends(get_company_radar_service),
):
    companies = service.find_recurring(
        min_score=min_score, since_days=since_days,
        min_occurrences=min_occurrences, limit=limit,
    )
    return RecurringCompaniesResponse(count=len(companies), companies=companies)