from pydantic import BaseModel, Field
from typing import List, Optional

class WorkExperience(BaseModel):
    company: str
    role_title: str
    dates: str
    location: Optional[str] = None
    highlights: List[str] = Field(description="Factual achievements and core duties")

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    graduation_year: Optional[str] = None

class ResumeProfile(BaseModel):
    profile_id: str = Field(..., description="Unique identifier, e.g., 'ai_architect' or 'engineering_manager'")
    target_role_category: str = Field(..., description="Primary focus area of this version")
    full_name: str
    email: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    summary: str
    core_skills: List[str]
    experiences: List[WorkExperience]
    education: List[Education]
    certifications: List[str] = Field(default_factory=list)