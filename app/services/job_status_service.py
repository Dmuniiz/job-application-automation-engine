"""
Validate status response and persist
"""

from app.core.exceptions import JobNotFoundError, InvalidStatusError
from app.db.repository import JobRepository
from app.db.models import JobRecord, JobStatus, SkillRelationType

class JobStatusService:

    def __init__(self, repository: JobRepository):
        self.repository = repository

    def update(
        self, job_hash: str, *,
        status: str | None = None,
        score: int | None = None,
        status_recomendacao: str | None = None,
        justificativa_curta: str | None = None,
        industry_fit: str | None = None,
        skills_match: list[str] | None = None,
        skills_missing: list[str] | None = None,
        skills_transferable: list[str] | None = None,
        google_doc_url: str | None = None,
        sheet_synced: bool | None = None,
    ) -> JobRecord:
        
        if status is not None and status not in JobStatus.ALL:
            raise InvalidStatusError(
                f"Status '{status}' inválido. Valores aceitos: {sorted(JobStatus.ALL)}"
            )

        record = self.repository.update_job(
            job_hash, status=status, score=score,
            status_recomendacao=status_recomendacao,
            justificativa_curta=justificativa_curta,
            industry_fit=industry_fit,
            google_doc_url=google_doc_url,
            sheet_synced=sheet_synced,
        )
        if not record:
            raise JobNotFoundError(f"No job found for hash={job_hash}")

        for names, relation in [
            (skills_match, SkillRelationType.MATCH),
            (skills_missing, SkillRelationType.MISSING),
            (skills_transferable, SkillRelationType.TRANSFERABLE),
        ]:
            if names:
                self.repository.replace_job_skills(record.id, relation_type=relation, skill_names=names)

        return record