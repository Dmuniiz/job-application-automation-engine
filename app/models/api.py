from app.models.job import JobMetadata
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional


class ProcessJobRequest(BaseModel):
    job_url: HttpUrl = Field(..., description="Direct job application URL")
    job_id: str = Field(..., description="Unique job ID")
    profile_id: Optional[str] = Field(default="support_ops_engineer")

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
    status: str = Field(),
    score: Optional[int] = Field()
    status_recomendacao: Optional[str] = None
    justificativa_curta: Optional[str] = None

class UpdateJobStatusResponse(BaseModel):
    job_hash: str
    status: str
    score: Optional[int] = None