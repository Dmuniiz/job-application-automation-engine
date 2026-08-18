import hashlib
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
import re

# Define the JobStatus class to represent the various statuses a job can have
class JobStatus:
    DISCOVERED = "discovered"
    PROCESSED = "processed"
    AUTO_APPROVED = "auto_approved"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"          # timeout do Send-and-Wait sem resposta
    FAILED = "failed"

    ALL = {
        DISCOVERED,
        PROCESSED,
        AUTO_APPROVED,
        PENDING_REVIEW,
        APPROVED,
        REJECTED,
        EXPIRED,
        FAILED
    }

class JobRecord(SQLModel, table=True):
    __tablename__ = "job_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_hash: str = Field(index=True, unique=True)
    job_id: str
    source_platform: str
    url: str
    portal_url: Optional[str] = None
    company: str
    title: str
    location: Optional[str] = None
    profile_id: Optional[str] = None

    status: str = Field(default=JobStatus.DISCOVERED, index=True)

    score: Optional[int] = None
    status_recomendacao: Optional[str] = None
    justificativa_curta: Optional[str] = None

    google_doc_url: Optional[str] = None
    sheet_synced: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

def compute_job_hash(source_platform: str, job_id: str) -> str:
    """Compute a unique hash for a job based on its source platform and job ID."""

    raw = f"{source_platform.strip().lower()}:{job_id.strip().lower()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def clean_text(text: str) -> str:
    if not text:
        return ""
    
    # regex to remove extra whitespace, newlines, and convert to lowercase
    return re.sub(r"\s+", " ", text.strip().lower())


# Implement a function to compute a unique hash for a job based on its source platform and job ID
def compute_content_fingerprint(title: str, company: str, location: str) -> str:
    parts = [clean_text(p) for p in (title, company, location)]

    normalized = "|".join(parts)

    return hashlib.md5(normalized.encode("utf-8")).hexdigest()