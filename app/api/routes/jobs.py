import logging
from fastapi import APIRouter, Depends
from app.api.deps import get_discovery_service, get_processing_service, get_evaluation_service
from app.services.job_discovery_service import JobDiscoveryService
from app.services.job_processing_service import JobProcessingService
from app.services.job_evaluation_service import JobEvaluationService
from app.models.api import (
    ProcessJobRequest, ProcessJobResponse,
    SearchJobsRequest, SearchJobsResponse, JobSearchResult,
    EvaluationRequest, EvaluationResponse,
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
        job_id=str(request.job_id), job_url=str(request.job_url), profile_id=request.profile_id,
    )

    return ProcessJobResponse(**vars(result))


@router.post("/jobs/{job_hash}/evaluation", response_model=EvaluationResponse)
async def save_evaluation(
    job_hash: str,
    request: EvaluationRequest,
    service: JobEvaluationService = Depends(get_evaluation_service),
):
    
    record = service.evaluate(
        job_hash, score=request.score,
        status_recomendacao=request.status_recomendacao,
        justificativa_curta=request.justificativa_curta,
    )

    return EvaluationResponse(job_hash=job_hash, status=record.status, score=record.score)