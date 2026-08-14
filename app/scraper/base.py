from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.job import RawJobDescription

class BaseScraper(ABC):
    """
    Abstract Base Class for all Job Scrapers.
    Enforces a common contract regardless of the underlying extraction technology.
    """

    @abstractmethod
    async def fetch_job_details(self, *, job_id: str, job_url: str) -> Optional[RawJobDescription]:
        """Fetch and parse details for a single job listing."""
        pass
    
    @abstractmethod
    async def search_jobs(self, keywords: str, location: str, limit: int = 10) -> List[RawJobDescription]:
        """Search for job listings matching keywords and location."""
        pass