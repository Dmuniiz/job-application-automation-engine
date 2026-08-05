import logging
import httpx

from typing import List, Optional
from datetime import datetime
from playwright.async_api import async_playwright, BrowserContext
from pydantic import HttpUrl

from app.scraper.base import BaseScraper
from app.models.job import RawJobDescription
from app.models.job import JobMetadata
from app.config.settings import settings
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

class PlaywrightLinkedInScraper(BaseScraper):
    """
    Playwright-powered scraper for LinkedIn job posts.
    Configured with stealth headers to minimize blocking risk.
    """

    BASE_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    BASE_JOB_URL = "https://www.linkedin.com/jobs/view"

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def fetch_job_details(self, job_id: str, job_url: str) -> Optional[RawJobDescription]:
        """Extrai os detalhes completos de uma vaga individual."""
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=10.0) as client:
            try:
                response = await client.get(job_url)
                if response.status_code != 200:
                    logger.warning(f"Falha ao carregar vaga {job_id}: Status {response.status_code}")
                    return None

                soup = BeautifulSoup(response.text, "html.parser")

                # Extração de campos básicos via tags HTML do LinkedIn
                title_tag = soup.find("h1", class_="top-card-layout__title")
                company_tag = soup.find("a", class_="topcard__org-name-link")
                location_tag = soup.find("span", class_="topcard__flavor--bullet")
                description_tag = soup.find("div", class_="show-more-less-html__markup")

                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                company = company_tag.get_text(strip=True) if company_tag else "N/A"
                location = location_tag.get_text(strip=True) if location_tag else "Remote"
                description = description_tag.get_text(separator="\n", strip=True) if description_tag else ""

                return RawJobDescription(
                    job_id=job_id,
                    url=HttpUrl(job_url),
                    company_url=HttpUrl("https://www.linkedin.com/company/" + company.replace(" ", "-").lower(),),
                    metadata=JobMetadata(
                        title=title,
                        company=company,
                        location=location,
                        employment_type="Full-time",
                        seniority_level="Not Specified",
                        posting_date=datetime.utcnow().strftime("%Y-%m-%d"),
                        easy_apply=False
                    ),
                    description_text=description,
                    scraped_at=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Erro ao processar vaga {job_id}: {str(e)}")
                return None

    async def search_jobs(self, keywords: str, location: str, limit: int) -> List[RawJobDescription]:
        logger.info(f"Searching LinkedIn for '{keywords}' in '{location}' (Limit: {limit})")
        jobs: List[RawJobDescription] = []
        start = 0

        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=10.0) as client:
            while len(jobs) < limit:
                params = {
                    "keywords": keywords,
                    "location": location,
                    "start": start
                }
                
                try:
                    response = await client.get(self.BASE_SEARCH_URL, params=params)
                    if response.status_code != 200:
                        logger.error(f"Erro na busca do LinkedIn: Status {response.status_code}")
                        break

                    soup = BeautifulSoup(response.text, "html.parser")
                    job_cards = soup.find_all("li")

                    if not job_cards:
                        logger.info("Nenhuma vaga adicional encontrada.")
                        break

                    for card in job_cards:
                        if len(jobs) >= limit:
                            break
                        
                        # Extrai o ID único da vaga no LinkedIn
                        entity_urn = card.find("div", class_="base-card")
                        if entity_urn and "data-entity-urn" in entity_urn.attrs:
                            urn_str = entity_urn["data-entity-urn"]
                            job_id = urn_str.split(":")[-1]
                            job_url = f"{self.BASE_JOB_URL}/{job_id}"

                            # Busca os detalhes completos da vaga
                            job_data = await self.fetch_job_details(job_id, job_url)
                            if job_data:
                                jobs.append(job_data)

                    start += 25  # LinkedIn pagina de 25 em 25 resultados

                except Exception as e:
                    logger.error(f"Erro durante o ciclo de busca: {str(e)}")
                    break

        logger.info(f"Busca finalizada. Total de vagas coletadas: {len(jobs)}")
        return jobs