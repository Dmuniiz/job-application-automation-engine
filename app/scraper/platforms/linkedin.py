import logging
import random
import asyncio
import re
from typing import List, Optional
from datetime import datetime, timezone

from app.utils.http_retry import request_with_exponential_backoff
import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl

from app.scraper.base import BaseScraper
from app.models.job import RawJobDescription
from app.scraper.parser_html import JobParser
from fake_useragent import UserAgent


logger = logging.getLogger(__name__)

class PlaywrightLinkedInScraper(BaseScraper):
    """
    Scraper for LinkedIn job posts using Playwright for dynamic content rendering.
    Integrates with JobParser for structured data extraction.
    """

    BASE_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    BASE_JOB_URL = "https://www.linkedin.com/jobs/view"

    def __init__(self):
        # Gera dinamicamente um User-Agent de um navegador desktop real
        ua = UserAgent(browsers=['chrome', 'edge'], os=['windows', 'macos'])
        self.headers = {
            "User-Agent": ua.random,
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"'
        }

    async def _human_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Introduces a random delay to mimic human browsing behavior."""
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"Delaying for {delay:.2f} seconds to mimic human behavior.")
        await asyncio.sleep(delay)

    def _build_company_url(self, company_name: str) -> str:
        """
        Gera a URL da empresa como string pura.
        O Pydantic v2 fará a conversão para HttpUrl de forma nativa.
        """
        try:
            slug = re.sub(r'[^a-zA-Z0-9-]', '', company_name.replace(" ", "-").lower())
            if not slug:
                slug = "unknown"
            return f"https://www.linkedin.com/company/{slug}"
        except Exception:
            return "https://www.linkedin.com"

    async def fetch_job_details(self, job_id: str, job_url: str) -> Optional[RawJobDescription]:
        """Fetches detailed job information from a LinkedIn job posting page."""

        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=12.0) as client:
            try:
                response = await request_with_exponential_backoff(client=client, 
                    url=job_url, 
                    max_retries=3, 
                    base_delay=2.0)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch job details for {job_id}: Status {response.status_code}")
                    return None

                soup = BeautifulSoup(response.text, "html.parser")

                title_tag = soup.find("h1", class_="top-card-layout__title")
                company_tag = soup.find("a", class_="topcard__org-name-link")
                location_tag = soup.find("span", class_="topcard__flavor--bullet")
                description_tag = soup.find("div", class_="show-more-less-html__markup")

                raw_title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
                raw_company = company_tag.get_text(strip=True) if company_tag else "Unknown Company"
                raw_location = location_tag.get_text(strip=True) if location_tag else "Remote / Unspecified"

                raw_html_desc = str(description_tag) if description_tag else ""
                clean_description = JobParser.clean_text(raw_html_desc)

                raw_data = {
                    "title": raw_title,
                    "company": raw_company,
                    "location": raw_location,
                    "posting_date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
                }
                metadata = JobParser.build_metadata(raw_data, clean_description)


                return RawJobDescription(
                    job_id=job_id,
                    url=HttpUrl(job_url),
                    company_url=self._build_company_url(raw_company),
                    metadata=metadata,
                    source_platform="LinkedIn",
                    description_text=clean_description,
                    scraped_at=datetime.now(timezone.utc)
                )

            except Exception as e:
                logger.error(f"[LinkedIn Error] Error processing job {job_id}: {str(e)}")
                return None

    async def search_jobs(self, keywords: str, location: str, limit: int) -> List[RawJobDescription]:

        """
        Searches LinkedIn for job postings based on keywords and location.
        Returns a list of RawJobDescription objects containing job details.
        """

        logger.info(f"Searching LinkedIn for '{keywords}' in '{location}' (Limit: {limit})")
        jobs: List[RawJobDescription] = []
        start = 0

        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=12.0) as client:
            while len(jobs) < limit:
                params = {
                    "keywords": keywords,
                    "location": location,
                    "start": start
                }
                
                try:
                    response = await client.get(self.BASE_SEARCH_URL, params=params)
                    if response.status_code != 200:
                        logger.error(f"Error in LinkedIn search: Status {response.status_code}")
                        break

                    soup = BeautifulSoup(response.text, "html.parser")
                    job_cards = soup.find_all("li")

                    if not job_cards:
                        logger.info("No additional jobs found.")
                        break

                    for card in job_cards:
                        if len(jobs) >= limit:
                            break
                        
                        # Extract the unique ID of the job on LinkedIn
                        entity_urn = card.find("div", class_="base-card")
                        if entity_urn and "data-entity-urn" in entity_urn.attrs:
                            urn_str = entity_urn["data-entity-urn"]
                            job_id = urn_str.split(":")[-1]
                            job_url = f"{self.BASE_JOB_URL}/{job_id}"

                            # Fetch the complete details of the job
                            job_data = await self.fetch_job_details(job_id, job_url)
                            if job_data:
                                jobs.append(job_data)
                            await self._human_delay(2.0, 3.5)

                    start += 25  # LinkedIn pagina de 25 em 25 resultados
                    await self._human_delay(2.0, 3.5)

                except Exception as e:
                    logger.error(f"Error during search cycle: {str(e)}")
                    break

        logger.info(f"Search completed. Total jobs collected: {len(jobs)}")
        return jobs