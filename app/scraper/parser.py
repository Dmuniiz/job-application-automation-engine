import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from app.models.job import JobMetadata

class JobParser:
    """
    Parses and cleans raw HTML into structured metadata.
    Handles missing/null attributes gracefully using heuristic regex fallbacks.
    """

    @staticmethod
    def clean_text(raw_html: str) -> str:
        """Strip HTML tags and normalize whitespace."""
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator=" ")
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def extract_heuristics(description_text: str) -> Dict[str, Optional[str]]:
        """
        Fallback parser when structural HTML tags are missing attributes like salary or employment type.
        """
        heuristics: Dict[str, Optional[str]] = {
            "salary_range": None,
            "employment_type": None,
            "seniority_level": None
        }

        # Regex for Salary Patterns (e.g., $120,000 - $150,000 or $80k-$100k)
        salary_match = re.search(r'(\$\d{2,3}(?:,\d{3})*(?:\s*-\s*\$\d{2,3}(?:,\d{3})*)?|\$\d{2,3}k\s*-\s*\$\d{2,3}k)', description_text, re.IGNORECASE)
        if salary_match:
            heuristics["salary_range"] = salary_match.group(0)

        # Seniority match heuristics
        if re.search(r'\b(senior|sr\.?|lead|principal)\b', description_text, re.IGNORECASE):
            heuristics["seniority_level"] = "Senior"
        elif re.search(r'\b(junior|jr\.?|entry level)\b', description_text, re.IGNORECASE):
            heuristics["seniority_level"] = "Entry Level"
        elif re.search(r'\b(director|vp|head of)\b', description_text, re.IGNORECASE):
            heuristics["seniority_level"] = "Executive"

        # Employment type heuristics
        if re.search(r'\b(full-time|full time)\b', description_text, re.IGNORECASE):
            heuristics["employment_type"] = "Full-time"
        elif re.search(r'\b(part-time|part time)\b', description_text, re.IGNORECASE):
            heuristics["employment_type"] = "Part-time"
        elif re.search(r'\b(contract|contractor|freelance)\b', description_text, re.IGNORECASE):
            heuristics["employment_type"] = "Contract"

        return heuristics

    @classmethod
    def build_metadata(cls, raw_data: Dict[str, Any], description_text: str) -> JobMetadata:
        """
        Builds a JobMetadata object, falling back to heuristics when attributes are None/empty.
        """
        heuristics = cls.extract_heuristics(description_text)

        return JobMetadata(
            title=raw_data.get("title") or "Unknown Title",
            company=raw_data.get("company") or "Unknown Company",
            location=raw_data.get("location") or "Remote / Unspecified",
            employment_type=raw_data.get("employment_type") or heuristics["employment_type"],
            seniority_level=raw_data.get("seniority_level") or heuristics["seniority_level"],
            salary_range=raw_data.get("salary_range") or heuristics["salary_range"],
            posting_date=raw_data.get("posting_date"),
            easy_apply=raw_data.get("easy_apply", False)
        )