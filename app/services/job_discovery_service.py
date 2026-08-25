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
    portal_url: str
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

# discover -> bulk upsert jobs

    async def discover(self, keywords: str, location: str, limit_per_source: int) -> DiscoveryResult:
        
        raw_jobs = await self.aggregator.search_all(
            keywords=keywords, 
            location=location, 
            limit_per_source=limit_per_source
        )

        job_dicts = [
            {
                "job_id": job.job_id,
                "source_platform": getattr(job, "source_platform", "LinkedIn"),
                "url": str(job.job_url_api),
                "portal_url": str(job.portal_url),
                "company": job.metadata.company,
                "title": job.metadata.title,
                "location": job.metadata.location,
            }
            for job in raw_jobs
        ]

        # 1 única instrução SQL para o lote inteiro, em vez de N idas ao banco.
        bulk_result = self.repository.bulk_register_discovered(job_dicts)

        new_jobs = [
            DiscoveredJob(
                job_id=r.job_id, job_hash=r.job_hash, job_url=r.url,
                portal_url=r.portal_url,
                title=r.title, 
                company=r.company,
                source_platform=r.source_platform,
            )
            for r in bulk_result.new_records
        ]

        logger.info(
            f"[Discovery] new={len(new_jobs)} skipped_duplicates={bulk_result.skipped_duplicates}"
        )
        return DiscoveryResult(new_jobs=new_jobs, skipped_duplicates=bulk_result.skipped_duplicates)