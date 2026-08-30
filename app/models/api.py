from app.models.job import JobMetadata
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime


class ProcessJobRequest(BaseModel):
    job_url: HttpUrl = Field(..., description="Direct job application URL")
    job_id: str = Field(..., description="Unique job ID")

class ProcessJobResponse(BaseModel):
    job_id: str
    job_hash: str
    job_url: str
    portal_url: Optional[str] = None
    company: str
    title: str
    description_text: str
    source_platform: str
    company_url: Optional[HttpUrl] = None
    metadata: JobMetadata

#models for job discovery

class SearchJobsRequest(BaseModel):
    keywords: str = Field(default="Technical Support")
    location: str = Field(default="Remote")
    limit: int = Field(default=5, ge=1, le=20)

class JobSearchResult(BaseModel):
    job_id: str
    job_hash: str
    job_url: str
    portal_url: Optional[str] = None
    title: str
    company: str
    source_platform: str

class SearchJobsResponse(BaseModel):
    count: int
    skipped_duplicates: int
    jobs: List[JobSearchResult]


#models for job evaluation 

class EvaluationRequest(BaseModel):
    """Gemini Evaluation Request Model"""
    score: int = Field(..., ge=0, le=100)
    status_recomendacao: str
    justificativa_curta: Optional[str] = None

class EvaluationResponse(BaseModel):
    job_hash: str
    status: str
    score: Optional[int] = None

#models to update job status

class UpdateJobStatusRequest(BaseModel):
    status: Optional[str] = Field(
        default=None,
        description="Novo status. Omitir para atualizar só outros campos (ex.: sync de Doc/Sheet) sem mudar o status.",
    )
    score: Optional[int] = Field(default=None, ge=0, le=100)
    status_recomendacao: Optional[str] = None
    justificativa_curta: Optional[str] = None
    industry_fit: Optional[str] = None
    skills_match: Optional[List[str]] = None
    skills_missing: Optional[List[str]] = None
    skills_transferable: Optional[List[str]] = None
    google_doc_url: Optional[str] = None
    sheet_synced: Optional[bool] = None

class UpdateJobStatusResponse(BaseModel):
    job_hash: str
    status: str
    score: Optional[int] = None


# models recurring company

class RecurringCompany(BaseModel):
    company: str
    occurrences: int
    best_score: int
    last_seen_at: datetime
    latest_job_title: str
    latest_job_url: str

class RecurringCompaniesResponse(BaseModel):
    count: int
    companies: List[RecurringCompany]