import logging
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.models.api import ProcessJobRequest, ProcessJobResponse, SearchJobsRequest, SearchJobsResponse, JobSearchResult
from app.scraper.linkedin import PlaywrightLinkedInScraper
from app.scraper.data_mock import MockLinkedInScraper


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
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/api/v1/search-jobs", response_model=SearchJobsResponse)
async def search_jobs(request: SearchJobsRequest):
    """
    Automated Discovery Endpoint:
    Searches LinkedIn for target roles and returns a batch of fresh job URLs.
    """
    logger.info(f"Searching jobs for '{request.keywords}' in '{request.location}'")

    # Use Playwright in production or Mock in dev
    scraper = MockLinkedInScraper() if settings.ENVIRONMENT == "development" else PlaywrightLinkedInScraper()
    
    # Execute guest search query

    raw_jobs = await scraper.search_jobs(
        keywords=request.keywords,
        location=request.location,
        limit=request.limit
    )

    results = [
        JobSearchResult(
            job_id=job.job_id,
            job_url=str(job.url),
            title=job.metadata.title,
            company=job.metadata.company
        )
        for job in raw_jobs
    ]

    return SearchJobsResponse(count=len(results), jobs=results)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT, "default_profile": settings.DEFAULT_PROFILE_ID}

@app.post("/api/v1/process-job", response_model=ProcessJobResponse)
async def process_job(request: ProcessJobRequest):
    """
    End-to-End Endpoint:
    1. Scrapes LinkedIn Job URL
    2. Evaluates against locked Support & Ops Profile via Gemini
    3. Customizes Resume if Score >= Threshold
    4. Creates Google Doc & Logs to Google Sheets
    """

    profile_id = request.profile_id or settings.DEFAULT_PROFILE_ID

    # 1. Scrape Job Details (Swaps to Playwright in production)
    scraper = MockLinkedInScraper() if settings.ENVIRONMENT == "development" else PlaywrightLinkedInScraper()
    job = await scraper.fetch_job_details(str(request.job_id), str(request.job_url))
    
    if not job:
        raise HTTPException(status_code=400, detail="Failed to scrape or parse target job URL.")

    return ProcessJobResponse(
        job_id=job.job_id,
        job_url=str(job.url),
        company=job.metadata.company,
        title=job.metadata.title,
        description_text=job.description_text,
        company_url=str(job.company_url) if job.company_url else None,
        metadata=job.metadata
    )