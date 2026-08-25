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
        self, job_hash: str, *, status: str,
        score: int | None = None,
        status_recomendacao: str | None = None,
        justificativa_curta: str | None = None,
        skills_match: str | None = None,      # JSON string ou CSV
        skills_missing: str | None = None,
        skills_transferable: str | None = None,
        industry_fit: str | None = None,
    ) -> JobRecord:

        if status not in JobStatus.ALL:
            raise InvalidStatusError(
                f"Status {status} invalid. Accepted Values: {sorted(JobStatus.ALL)}"
            )

        record = self.repository.update_job(
            job_hash, status=status, score=score,
            status_recomendacao=status_recomendacao,
            justificativa_curta=justificativa_curta,
            industry_fit=industry_fit,
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