from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, List


from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.db.models import (
    JobRecord, JobStatus, Skill, JobRecordSkill, SkillRelationType,
    compute_job_hash, compute_content_fingerprint, normalize_skill_name,
)

@dataclass
class BulkUpsertResult:
    """
    """
    new_records: List[JobRecord]
    skipped_duplicates: int


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
            status=JobStatus.DISCOVERED,
        )

        self.session.add(new_job_record)
        self.session.commit()
        self.session.refresh(new_job_record)

        return new_job_record

    def bulk_register_discovered(self, jobs: List[dict]) -> BulkUpsertResult:
        """
        
        """

        if not jobs:
            return BulkUpsertResult(new_records=[], skipped_duplicates=0)

        now = datetime.now(timezone.utc)
        rows_by_hash: dict[str, dict] = {}

        for j in jobs:
            job_hash = compute_job_hash(j["source_platform"], j["job_id"])

            if job_hash in rows_by_hash:
                continue
            
            rows_by_hash[job_hash] = {
                "job_hash": job_hash,
                "content_fingerprint": compute_content_fingerprint(
                    j["title"], j["company"], j.get("location") or ""
                ),
                "job_id": j["job_id"],
                "source_platform": j["source_platform"],
                "url": j["url"],
                "portal_url": j["portal_url"],
                "company": j["company"],
                "title": j["title"],
                "location": j.get("location"),
                "status": JobStatus.DISCOVERED,
                "score": None,
                "status_recomendacao": None,
                "justificativa_curta": None,
                "google_doc_url": None,
                "sheet_synced": False,
                "created_at": now,
                "updated_at": now,
            }

        rows = list(rows_by_hash.values())
        table = JobRecord.__table__

        dialect_name = self.session.get_bind().dialect.name
        insert_fn = pg_insert if dialect_name == "postgresql" else sqlite_insert

        stmt = (
            insert_fn(table)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["job_hash"])
            .returning(table)
        )

        result = self.session.execute(stmt)

        inserted_rows = result.mappings().all()
        self.session.commit()

        new_records = [JobRecord(**dict(row)) for row in inserted_rows]
        return BulkUpsertResult(
            new_records=new_records,
            skipped_duplicates=len(rows) - len(new_records),
        )

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

    def update_job(
        self, job_hash: str, *,
        status: Optional[str] = None,
        score: Optional[int] = None,
        status_recomendacao: Optional[str] = None,
        justificativa_curta: Optional[str] = None,
        industry_fit: Optional[str] = None,
        google_doc_url: Optional[str] = None,
        sheet_synced: Optional[bool] = None,
    ) -> Optional[JobRecord]:
        
        record = self.get_by_hash(job_hash)
        if not record:
            return None

        # status=None significa "não alterar" — é o que permite o sync-only call
        if status is not None:
            record.status = status
        if score is not None:
            record.score = score
        if status_recomendacao is not None:
            record.status_recomendacao = status_recomendacao
        if justificativa_curta is not None:
            record.justificativa_curta = justificativa_curta
        if industry_fit is not None:
            record.industry_fit = industry_fit
        if google_doc_url is not None:
            record.google_doc_url = google_doc_url
        if sheet_synced is not None:
            record.sheet_synced = sheet_synced

        record.updated_at = datetime.now(timezone.utc)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        
        return record  

    def list_jobs(self, *, 
                  status: Optional[str] = None,
                  limit: int = 50, ) -> List[JobRecord]:

        query = select(JobRecord)
        
        if status:
            query = query.where(JobRecord.status == status)
            
        query = query.order_by(JobRecord.created_at.desc()).limit(limit)

        return list(self.session.exec(query))


###

    def find_recurring_companies(
        self, *, min_score: int, since_days: int,
        min_occurrences: int, limit: int = 20,
    ) -> List[dict]:
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        table = JobRecord.__table__

        agg_stmt = (
            select(
                table.c.company,
                func.count(table.c.id).label("occurrences"),
                func.max(table.c.score).label("best_score"),
                func.max(table.c.created_at).label("last_seen_at"),
            )
            .where(table.c.score.isnot(None))
            .where(table.c.score >= min_score)
            .where(table.c.created_at >= cutoff)
            .group_by(table.c.company)
            .having(func.count(table.c.id) >= min_occurrences)
            .order_by(func.count(table.c.id).desc())
            .limit(limit)
        )
        agg_rows = self.session.execute(agg_stmt).mappings().all()

        results = []
        for row in agg_rows:

            # N+1 deliberado: o número de empresas recorrentes tende a ser
            # pequeno (dezenas, não milhares) — otimizar isso agora seria
            # resolver uma escala que ainda não existe, o mesmo raciocínio
            # que aplicamos para adiar Celery/Redis.

            latest = self.session.exec(
                select(JobRecord)
                .where(JobRecord.company == row["company"])
                .where(JobRecord.score >= min_score)
                .order_by(JobRecord.created_at.desc())
            ).first()

            results.append({
                "company": row["company"],
                "occurrences": row["occurrences"],
                "best_score": row["best_score"],
                "last_seen_at": row["last_seen_at"],
                "latest_job_title": latest.title if latest else "",
                "latest_job_url": latest.url if latest else "",
            })
        return results

    def replace_job_skills(
        self, job_record_id: int, *, relation_type: SkillRelationType, skill_names: List[str],
    ) -> None:
    
        """
        Substitui o conjunto de skills de um tipo (match/missing/transferable)
        para uma vaga. Idempotente: reexecutar com a mesma lista não duplica.
        """

        if not skill_names:
            return

        normalized_names = list({
            normalize_skill_name(n) for n in skill_names if n and n.strip()
        })

        if not normalized_names:
            return

        table = Skill.__table__
        dialect_name = self.session.get_bind().dialect.name
        insert_fn = pg_insert if dialect_name == "postgresql" else sqlite_insert

        #statement insert 
        stmt = (
            insert_fn(table)
            .values([{"name": n} for n in normalized_names])
            .on_conflict_do_nothing(index_elements=["name"])
        )

        self.session.execute(stmt)
        self.session.commit()

        skill_rows = self.session.exec(
            select(Skill)
            .where(Skill.name.in_(normalized_names))
        ).all()

        skill_id_by_name = {s.name: s.id for s in skill_rows}

        old_links = self.session.exec(
            select(JobRecordSkill)
            .where(JobRecordSkill.job_record_id == job_record_id)
            .where(JobRecordSkill.relation_type == relation_type.value)
        ).all()

        for link in old_links:
            self.session.delete(link)

        for name in normalized_names:
            self.session.add(JobRecordSkill(
                job_record_id=job_record_id,
                skill_id=skill_id_by_name[name],
                relation_type=relation_type.value,
            ))

        self.session.commit()