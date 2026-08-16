from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.db.models import JobRecord, JobStatus, compute_job_hash, compute_content_fingerprint


class JobRepository:
    """Repository Pattern: Provides an abstraction layer for database operations related to job records."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_hash(self, job_hash: str) -> Optional[JobRecord]:
        return self.session.exec(select(JobRecord)
                                .where(JobRecord.job_hash == job_hash)
                                ).first()

    def exists(self, source_platform: str, job_id: str) -> bool:
        return self.get_by_hash(compute_job_hash(source_platform, job_id)) is not None

    def register_discovered(
        self, *, 
        source_platform: str, 
        job_id: str, 
        url: str,
        portal_url: Optional[str] = None,
        company: str, 
        title: str, 
        location: Optional[str] = None,
        profile_id: Optional[str] = None,
    ) -> JobRecord:
        
        """Idempotently registers a discovered job in the database. If the job already exists, it returns the existing record."""

        job_hash = compute_job_hash(source_platform, job_id)
        existing = self.get_by_hash(job_hash)

        if existing:
            return existing

        new_job_record = JobRecord(
            job_hash=job_hash,
            content_fingerprint=compute_content_fingerprint(title, company, location or ""),
            job_id=job_id,
            source_platform=source_platform,
            url=url,
            portal_url=portal_url,
            company=company,
            title=title,
            location=location,
            profile_id=profile_id,
            status=JobStatus.DISCOVERED,
        )

        self.session.add(new_job_record)
        self.session.commit()
        self.session.refresh(new_job_record)

        return new_job_record

    def mark_processed(self, job_hash: str) -> Optional[JobRecord]:
        job = self.get_by_hash(job_hash)

        if not job:
            return None
        
        job.status = JobStatus.PROCESSED
        job.updated_at = datetime.now(timezone.utc)
        
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)

        return job

    def save_evaluation(self, job_hash: str, *, score: int, status_recomendacao: str, justificativa_curta: Optional[str] = None,) -> Optional[JobRecord]:
        
        job_hash_record = self.get_by_hash(job_hash)

        if not job_hash_record:
            return None
        
        job_hash_record.score = score
        job_hash_record.status_recomendacao = status_recomendacao
        job_hash_record.justificativa_curta = justificativa_curta
        job_hash_record.status = JobStatus.EVALUATED
        job_hash_record.updated_at = datetime.now(timezone.utc)

        self.session.add(job_hash_record)
        self.session.commit()
        self.session.refresh(job_hash_record)

        return job_hash_record

    def list_jobs(self, *, 
                  status: Optional[str] = None,
                  profile_id: Optional[str] = None, 
                  limit: int = 50, ) -> List[JobRecord]:

        query = select(JobRecord)
        
        if status:
            query = query.where(JobRecord.status == status)

        if profile_id:
            query = query.where(JobRecord.profile_id == profile_id)

        query = query.order_by(JobRecord.created_at.desc()).limit(limit)

        return list(self.session.exec(query))