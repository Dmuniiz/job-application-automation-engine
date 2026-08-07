import asyncio
from typing import List
import logging
from app.models.job import RawJobDescription
from app.scraper.platforms.gupy import GupyScraper
from app.scraper.platforms.linkedin import PlaywrightLinkedInScraper  # Seu scraper atual do LinkedIn
from data.data_mock import MockLinkedInScraper  # Fallback/Mock


logger = logging.getLogger(__name__)

class JobAggregatorService:
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        if not self.use_mock:
            self.scrapers = [
                GupyScraper(),
                PlaywrightLinkedInScraper()
            ]
        else:
            self.scrapers = [MockLinkedInScraper()]

    async def search_all(self, keywords: str, location: str, limit_per_source: int = 5) -> List[RawJobDescription]:
        logger.info(f"[Aggregator] Initializing parallel search across platforms... {len(self.scrapers)}")
        
        tasks = [
            scraper.search_jobs(keywords=keywords, location=location, limit=limit_per_source)
            for scraper in self.scrapers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        consolidated_jobs: List[RawJobDescription] = []
        for res in results:
            if isinstance(res, list):
                consolidated_jobs.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"[Aggregator Exception] scrapers failed: {res}")

        logger.info(f"[Aggregator] Success. Aggregated jobs: {len(consolidated_jobs)}")
        return consolidated_jobs