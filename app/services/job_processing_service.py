from dataclasses import dataclass
import logging
from typing import Optional

from app.db.repository import JobRepository
from app.models import job
from app.models.api import JobMetadata
from app.scraper.factory import ScraperFactory
from app.core.exceptions import JobFetchError
from app.db.models import compute_job_hash


logger = logging.getLogger(__name__)

@dataclass
class ProcessedJob:
    job_id: str
    job_hash: str
    job_url: str
    company: str
    title: str
    description_text: str
    source_platform: str
    company_url: Optional[str]
    metadata: JobMetadata


class JobProcessingService:
    """process the job by scraping the job description and persisting it in the database."""

    def __init__(self, repository: JobRepository):
        self.repository = repository



    async def process(self, job_id: str, job_url: str, profile_id: Optional[str] = None) -> ProcessedJob:
        # Determine whether to use mock data based on the environment


        # Get the appropriate scraper and source name
        scraper, source_name = ScraperFactory.resolve_default(job_id, job_url)

        # Scrape the job description
        job_data = await scraper.fetch_job_details(job_id=job_id, job_url=job_url)

        if not job_data:
            raise JobFetchError(
                f"Failed to fetch job details for job_id={job_id} and job_url={job_url}"
                "The job may not exist, the URL is invalid, or the source blocked the request. " \
                "Please verify the job URL and try again."
            )


        job_hash = compute_job_hash(source_name, job_id)

        self.repository.register_discovered(
            source_platform=source_name, 
            job_id=job.job_id, url=str(job.url),
            company=job.metadata.company, 
            title=job.metadata.title,
            location=job.metadata.location, 
            profile_id=profile_id,
        )

        self.repository.mark_processed(job_hash)

        logger.info(f"[Processing] job_id={job_id} source={source_name} status=PROCESSED")


        return ProcessedJob(
            job_id=job.job_id, 
            job_hash=job_hash, 
            job_url=str(job.url),
            company=job.metadata.company, 
            title=job.metadata.title,
            description_text=job.description_text, 
            source_platform=source_name,
            company_url=str(job.company_url) if job.company_url else None,
            metadata=job.metadata,
        )