from app.models.job import JobMetadata
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional

class ProcessJobRequest(BaseModel):
    job_url: HttpUrl = Field(..., description="Direct LinkedIn job application URL")
    job_id: str = Field(..., description="Unique LinkedIn job ID")
    profile_id: Optional[str] = Field(default="support_ops_engineer", description="Defaults to Support & Ops profile")

class ProcessJobResponse(BaseModel):
    job_id: str
    job_url: str
    company: str
    title: str
    description_text: str
    company_url: Optional[HttpUrl] = None
    metadata: JobMetadata

class SearchJobsRequest(BaseModel):
    keywords: str = Field(default="Technical Support", description="Job search keywords")
    location: str = Field(default="Remote", description="Job search location")
    limit: int = Field(default=5, ge=1, le=20, description="Number of job links to retrieve")

class JobSearchResult(BaseModel):
    job_id: str
    job_url: str
    title: str
    company: str

class SearchJobsResponse(BaseModel):
    count: int
    jobs: List[JobSearchResult]