from venv import logger

from app.config.settings import settings
from app.scraper.base import BaseScraper
from app.scraper.platforms.gupy import GupyScraper
from app.scraper.platforms.linkedin import PlaywrightLinkedInScraper
from data.data_mock import MockScraper


class ScraperFactory:

    @staticmethod
    def get_scraper(job_id: str, job_url: str, use_mock: bool) -> tuple[BaseScraper, str]:
        """
        Factory method to get the appropriate scraper based on the job URL.
        Returns a tuple of (scraper_instance, source_name).
        """

        if use_mock:
            return MockScraper(), "Mock"
        
        if "gupy.io" in job_url or job_id.startswith("gupy-"):
            return GupyScraper(), "Gupy"
    
        return PlaywrightLinkedInScraper(), "LinkedIn"

    @classmethod
    def resolve_default(cls, job_id: str, job_url: str) -> tuple[BaseScraper, str]:

        is_mock_active = (settings.USE_MOCK) or (settings.ENVIRONMENT == "development")

        return cls.get_scraper(job_id, job_url, is_mock_active)