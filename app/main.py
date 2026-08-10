import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status

from app.config.settings import settings
from app.models.api import (
    ProcessJobRequest, 
    ProcessJobResponse, 
    SearchJobsRequest, 
    SearchJobsResponse, 
    JobSearchResult
)
from app.scraper.aggregator import JobAggregatorService
from app.scraper.platforms.linkedin import PlaywrightLinkedInScraper
from data.data_mock import MockLinkedInScraper
from app.scraper.platforms.gupy import GupyScraper


# Setup structured logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("job_automation")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure canonical profiles are loaded
    logger.info("Initializing application services...")
    yield
    logger.info("Shutting down application services...")

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="Automated Job Application System with LinkedIn Scraper, Gupy, and others platforms Integration",
    lifespan=lifespan
)

is_mock_active = settings.USE_MOCK or (settings.ENVIRONMENT == "development")
aggregator_service = JobAggregatorService(use_mock=is_mock_active)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "use_mock": is_mock_active,
        "default_profile": settings.DEFAULT_PROFILE_ID
    }

@app.post("/api/v1/search-jobs", response_model=SearchJobsResponse)
async def search_jobs(request: SearchJobsRequest):
    """
    Automated Discovery Endpoint multiplatform:
    1. Scrapes LinkedIn Job Listings (or Mock in dev)
    2. Scrapes Gupy Job Listings
    3. Consolidates and returns a list of RawJobDescription objects
    """
    logger.info(f"Searching jobs for '{request.keywords}' in '{request.location}'")

    try: 
        raw_jobs = await aggregator_service.search_all(
            keywords=request.keywords,
            location=request.location,
            limit_per_source=request.limit
        )

        results = [
            JobSearchResult(
                job_id=job.job_id,
                job_url=str(job.url),
                title=job.metadata.title if hasattr(job, 'metadata') else job.title,
                company=job.metadata.company if hasattr(job, 'metadata') else job.company,
                source_platform=getattr(job, 'source_platform', 'LinkedIn')
            )
            for job in raw_jobs
        ]

        return SearchJobsResponse(count=len(results), jobs=results)

    except Exception as e:
        logger.error(f"Error during multi-platform job search: {str(e)}")
        logger.error("".join(logging.traceback.format_exception(type(e), e, e.__traceback__)))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"Failed to search jobs": str(e)}
        )

@app.post("/api/v1/process-job", response_model=ProcessJobResponse)
async def process_job(request: ProcessJobRequest):
    """   
    Endpoint to process a specific job posting:
    receive the job_id and job_url, scrape the job details, and return a structured response.
    This endpoint can be used to fetch detailed job information for a specific job posting.
    Dinamic IP rotation and anti-bot measures.
    """

    logger.info(f"Processing job '{request.job_id}' for profile '{request.profile_id}'")
    #logger.info(f"Processing job '{request.job_id}' for profile '{request.profile_id or settings.DEFAULT_PROFILE_ID}'")

    job_url_str = str(request.job_url)
    job_id_str = str(request.job_id)

    try:
        # dinamic scrapers
        if is_mock_active:
            scraper = MockLinkedInScraper()
            job = await scraper.fetch_job_details(job_id_str, job_url_str)
        elif "gupy.io" in job_url_str or job_id_str.startswith("gupy-"):
            scraper = GupyScraper()
            job = await scraper.fetch_job_details(job_id_str, job_url_str)
        else:
            scraper = PlaywrightLinkedInScraper()
            job = await scraper.fetch_job_details(job_id_str, job_url_str)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Failed to fetch job details. The job may not exist or the URL is invalid."
            )

        return ProcessJobResponse(
            job_id=job.job_id,
            job_url=str(job.url),
            company=job.metadata.company,
            title=job.metadata.title,
            description_text=job.description_text,
            company_url=str(job.company_url) if job.company_url else None,
            metadata=job.metadata
        )
    
    except Exception as e:
        logger.error(f"Error processing job '{request.job_id}': {str(e)}")
        logger.error("".join(logging.traceback.format_exception(type(e), e, e.__traceback__)))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"Failed to process job": str(e)}
        )
