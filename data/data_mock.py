from typing import List, Optional
from datetime import datetime
from pydantic import HttpUrl

from app.scraper.base import BaseScraper
from app.models.job import RawJobDescription, JobMetadata

class MockScraper(BaseScraper):
    """
    Offline Mock Scraper for testing downstream AI evaluation and integration loops
    without hitting web rate limits or browser drivers.
    """

    async def fetch_job_details(self, job_id: str, job_url: str) -> Optional[RawJobDescription]:
            return RawJobDescription(
            job_id=job_id,
            url=HttpUrl(job_url),
            company_url=HttpUrl("https://linkedin.com/company/cloudscale-tech"),
            metadata=JobMetadata(
                title="Senior Support & Operations Engineer (L4)",
                company="CloudScale Technologies",
                location="Remote - Brasil / US",
                employment_type="Full-time",
                seniority_level="Senior",
                salary_range="$80,000 - $110,000 / ano",
                posting_date="2026-08-01",
                easy_apply=True
            ),
            description_text=(
                "A CloudScale Technologies está em busca de um Engenheiro de Suporte e Operações L4 "
                "para liderar a resolução de incidentes críticos em ambiente Cloud e automação de processos.\n\n"
                "Requisitos Principais:\n"
                "- Experiência sólida em suporte técnico avançado (L3/L4), troubleshooting de sistemas e análise de logs.\n"
                "- Domínio de linguagem Python e criação de microserviços/APIs REST com FastAPI.\n"
                "- Experiência prática com automação de pipelines de integração usando n8n ou motores similares.\n"
                "- Conhecimentos avançados em Linux, containers Docker e consultas/otimização em bancos de dados SQL.\n\n"
                "Responsabilidades:\n"
                "- Automatizar fluxos de ingestão e triagem de dados entre APIs.\n"
                "- Investigar falhas operacionais e criar scripts de correção contínua.\n"
                "- Manter a infraestrutura de suporte operando com alta disponibilidade."
            ),
            source_platform="LinkedIn",
            scraped_at=datetime.utcnow()
        )

    async def search_jobs(self, keywords: str, location: str, limit: int = 10) -> List[RawJobDescription]:

        single = await self.fetch_job_details("mock-job-99887766", "https://www.linkedin.com/jobs/view/99887766")

        return [single] if single else []