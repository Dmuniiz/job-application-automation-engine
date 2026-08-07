from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime

class JobMetadata(BaseModel):
    title: str = Field(..., description="Job Title")
    company: str = Field(..., description="Company Name")
    location: str = Field(..., description="Location of the job")
    employment_type: Optional[str] = Field(None, description="Full-time, Part-time, Contract, etc.")
    seniority_level: Optional[str] = Field(None, description="Entry, Mid, Senior, Lead, Executive")
    salary_range: Optional[str] = Field(None, description="Raw or parsed salary string")
    posting_date: Optional[str] = Field(None, description="Posting date string or ISO format")
    easy_apply: bool = Field(default=False)

class RawJobDescription(BaseModel):
    job_id: str = Field(..., description="Unique LinkedIn or Scraper Job ID")
    url: HttpUrl = Field(..., description="Direct Job Application URL")
    company_url: Optional[HttpUrl] = None
    metadata: JobMetadata
    description_text: str = Field(..., description="Full raw job description text")
    source_platform: str = Field(..., description="Source platform, e.g., LinkedIn, Indeed, etc.")
    scraped_at: datetime = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))