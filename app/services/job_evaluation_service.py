from app.core.exceptions import JobNotFoundError
from app.db.repository import JobRepository
from app.db.models import JobRecord


class JobEvaluationService:
    """save the evaluation scoring via n8n and persist it in the database."""

    def __init__(self, repository: JobRepository):
        self.repository = repository

    def evaluate(self, job_hash: str, *, score: int,status_recomendacao: str, justificativa_curta: str | None,) -> JobRecord:

        record = self.repository.save_evaluation(
            job_hash, score=score,
            status_recomendacao=status_recomendacao,
            justificativa_curta=justificativa_curta,
        )

        if not record:
            raise JobNotFoundError(f"No job found for hash={job_hash}")

        return record