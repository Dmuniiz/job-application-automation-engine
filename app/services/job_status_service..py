"""
Validate status response and persist
"""

from app.core.exceptions import JobNotFoundError, InvalidStatusError
from app.db.repository import JobRepository
from app.db.models import JobRecord, JobStatus

class JobStatusService:

    def __init__(self, repository: JobRepository):
        self.repository = repository

    def update(
        self, job_hash: str, *, status: str,
        score: int | None = None,
        status_recomendacao: str | None = None,
        justificativa_curta: str | None = None,
    ) -> JobRecord:

        if status not in JobStatus.ALL:
            raise InvalidStatusError(
                f"Status {status} invalid. Accepted Values: {sorted(JobStatus.ALL)}"
            )

        record = self.repository.update_job(
            job_hash, status=status, score=score,
            status_recomendacao=status_recomendacao,
            justificativa_curta=justificativa_curta,
        )

        if not record:
            raise JobNotFoundError(f"No job found for hash={job_hash}")
        return record