import httpx
from typing import List, Optional
import logging
from datetime import datetime, timezone
from app.scraper.base import BaseScraper
from app.models.job import RawJobDescription, JobMetadata
from app.scraper.parser_html import JobParser
from pydantic import BaseModel, HttpUrl
from fake_useragent import UserAgent
from app.utils.http_retry import request_with_exponential_backoff


logger = logging.getLogger(__name__)

class GupyScraper(BaseScraper):
    BASE_URL = "https://employability-portal.gupy.io/api/v1/jobs"

    def __init__(self):
            # Gera dinamicamente um User-Agent de um navegador desktop real
            ua = UserAgent(browsers=['chrome', 'edge'], os=['windows', 'macos'])
            self.headers = {
                "User-Agent": ua.random,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://portal.gupy.io/",
                "Origin": "https://portal.gupy.io",
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"'
            }

    async def fetch_job_details(self, job_id: str, job_url: str) -> Optional[RawJobDescription]:
        clean_id = str(job_id).replace("gupy-", "").strip()
        endpoint = f"{self.BASE_URL}/{clean_id}"

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client: 
            try:
                response = await request_with_exponential_backoff(client=client, 
                    url=endpoint, 
                    max_retries=3, 
                    base_delay=2.0)
                
                if response.status_code != 200:
                    logger.warning(f"[Gupy] Failed to fetch job details for {clean_id}: Status {response.status_code}")
                    return None

                data = response.json()
                portal_job = data.get("jobUrl")

                company_name = data.get("companyName") or "Gupy Partner"
                company_code = data.get("company", {}).get("code", "portal")
                
                raw_description = data.get("description", "")
                clean_description = JobParser.clean_text(raw_description)

                raw_data = {
                    "title": data.get("name", "Unknown Title"),
                    "company": company_name,
                    "location": data.get("workplaceType") or "Remote / Unspecified",
                    "posting_date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
                }
                metadata = JobParser.build_metadata(raw_data, clean_description)
                
                final_job_url = job_url if job_url and "gupy.io" in job_url else f"https://{company_code}.gupy.io/jobs/{clean_id}"
                company_url = f"https://{company_code}.gupy.io"

                return RawJobDescription(
                    job_id=f"gupy-{clean_id}",
                    job_url_api=final_job_url,
                    portal_url=portal_job,
                    company_url=company_url,
                    metadata=metadata,
                    description_text=clean_description,
                    source_platform="Gupy",
                    scraped_at=datetime.now(timezone.utc)
                )

            except Exception as e:
                logger.error(f"[Gupy Error] Error fetching details for {job_id}: {str(e)}")
                return None

    async def search_jobs(self, keywords: str, location: str, limit: int = 5) -> List[RawJobDescription]:
        logger.info(f"[Gupy Scraper] searching for '{keywords}'")
        jobs: List[RawJobDescription] = []
        
        # Prepare the search parameters for the Gupy API
        params = {
            "jobName": keywords,
            "offset": 0,
            "limit": limit
        }

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            try:
                response = await client.get(self.BASE_URL, params=params)

                if response.status_code != 200:
                    logger.error(f"[Gupy] Error in public search: Status {response.status_code}")
                    return jobs

                data = response.json().get("data", [])

                for item in data:
                    if len(jobs) >= limit:
                        break

                    job_id = str(item.get("id"))
                    company_code = item.get("company", {}).get("code", "portal")
                    job_url_api = f"https://{company_code}.gupy.io/jobs/{job_id}"
                    logger.info(f"[Gupy] Found job: {job_id} - {item.get('name')} at {company_code}")

                    job_details = await self.fetch_job_details(job_id, job_url_api)

                    if job_details:
                        jobs.append(job_details)

            except Exception as e:
                logger.error(f"[Gupy Error] Error in search cycle: {str(e)}")

        logger.info(f"[Gupy] Search completed. Total jobs collected: {len(jobs)}")
        return jobs