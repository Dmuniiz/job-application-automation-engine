from pydantic import BaseModel, Field
from typing import List

class SkillsMatch(BaseModel):
    matched: List[str] = Field(description="Exact skills matching candidate's profile")
    missing: List[str] = Field(description="Required/preferred skills candidate lacks")
    transferable: List[str] = Field(description="Skills candidate possesses that apply indirectly")

class JobEvaluation(BaseModel):
    overall_score: int = Field(..., ge=0, le=100, description="Overall candidate match percentage")
    recommendation: str = Field(..., description="'Apply', 'Consider', or 'Skip'")
    skills_match: SkillsMatch
    experience_alignment: str = Field(..., description="Assessment of years & depth of experience")
    industry_fit: str = Field(..., description="Relevance of candidate background to target domain")
    seniority_fit: str = Field(..., description="Assessment of target vs current seniority level")
    ats_keywords: List[str] = Field(description="Key ATS terms found in job posting to highlight")
    resume_improvements: List[str] = Field(description="Specific suggestions for optimization")
    red_flags: List[str] = Field(description="Potential issues like ambiguous responsibilities or low tenure")
    summary: str = Field(..., description="Executive summary of match feasibility")