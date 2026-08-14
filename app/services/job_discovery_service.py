import logging
from dataclasses import dataclass
from typing import List

from app.db.repository import JobRepository
from app.scraper.aggregator import JobAggregatorService

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredJob:
    job_id: str
    job_hash: str
    job_url: str
    title: str
    company: str
    source_platform: str


@dataclass
class DiscoveryResult:
    new_jobs: List[DiscoveredJob]
    skipped_duplicates: int

#/search-jobs
class JobDiscoveryService:


    def __init__(self, repository: JobRepository, aggregator: JobAggregatorService):
        self.repository = repository
        self.aggregator = aggregator

    async def discover(self, keywords: str, location: str, limit_per_source: int) -> DiscoveryResult:

        raw_jobs = await self.aggregator.search_all(
            keywords=keywords, location=location, limit_per_source=limit_per_source
        )

        new_jobs: List[DiscoveredJob] = []
        skipped = 0

        for job in raw_jobs:
            source = getattr(job, "source_platform", "LinkedIn")

            #check if the job already exists in the database
            if self.repository.exists(source, job.job_id):
                skipped += 1
                continue

            record = self.repository.register_discovered(
                source_platform=source,
                job_id=job.job_id,
                url=str(job.url),
                company=job.metadata.company,
                title=job.metadata.title,
                location=job.metadata.location,
            )


            # Add the newly discovered job to the list of new jobs -> json
            new_jobs.append(DiscoveredJob(
                job_id=job.job_id, job_hash=record.job_hash, job_url=str(job.url),
                title=job.metadata.title, company=job.metadata.company,
                source_platform=source,
            ))

        logger.info(f"[Discovery] new={len(new_jobs)} skipped_duplicates={skipped}")

        return DiscoveryResult(new_jobs=new_jobs, skipped_duplicates=skipped)