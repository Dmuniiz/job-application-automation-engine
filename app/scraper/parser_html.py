import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from app.models.job import JobMetadata

class JobParser:
    """
    Parses, cleans raw HTML, and extracts structured metadata.
    Handles missing attributes using robust bilingual (PT-BR / EN) regex heuristics.
    """

    @staticmethod
    def clean_text(raw_html: str) -> str:
        """
        Strips HTML tags while preserving line breaks for list items and paragraphs,
        ensuring clean markdown-friendly text for the Gemini LLM prompt.
        """
        if not raw_html:
            return ""
        
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # Insere quebras de linha em tags de bloco para manter a estrutura legível
        for block_tag in soup.find_all(['p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'tr']):
            block_tag.append("\n")
            
        text = soup.get_text()
        
        # Remove múltiplos espaços em branco por linha, mantendo as quebras de linha
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]
        return "\n".join([line for line in lines if line])

    @staticmethod
    def extract_heuristics(description_text: str) -> Dict[str, Optional[str]]:
        """
        Fallback parser when structural attributes (salary, employment_type, seniority)
        are missing. Supports both English and Portuguese terms.
        """
        heuristics: Dict[str, Optional[str]] = {
            "salary_range": None,
            "employment_type": None,
            "seniority_level": None
        }

        if not description_text:
            return heuristics

        # 1. Regex Multimoeda para Salários ($, R$, €, £, "k", "mil", /mês, /ano)
        salary_pattern = r'(?:(?:R\$|\$|€|£)\s*\d{1,3}(?:[.,]\d{3})*(?:\s*k)?(?:\s*-\s*(?:R\$|\$|€|£)?\s*\d{1,3}(?:[.,]\d{3})*(?:\s*k)?)?|\b\d{1,2}k\s*-\s*\d{1,2}k\b)'
        salary_match = re.search(salary_pattern, description_text, re.IGNORECASE)
        if salary_match:
            heuristics["salary_range"] = salary_match.group(0).strip()

        # 2. Heurística de Senioridade (EN + PT-BR)
        if re.search(r'\b(senior|sênior|sr\.?|lead|principal|head|especialista|specialist)\b', description_text, re.IGNORECASE):
            heuristics["seniority_level"] = "Senior"
        elif re.search(r'\b(pleno|mid-level|mid level|pl\.?)\b', description_text, re.IGNORECASE):
            heuristics["seniority_level"] = "Mid-Level"
        elif re.search(r'\b(junior|júnior|jr\.?|entry level|estágio|intern|trainee)\b', description_text, re.IGNORECASE):
            heuristics["seniority_level"] = "Entry Level"
        elif re.search(r'\b(director|diretor|vp|vice president|c-level|executive)\b', description_text, re.IGNORECASE):
            heuristics["seniority_level"] = "Executive"

        # 3. Heurística de Tipo de Contratação (EN + PT-BR)
        if re.search(r'\b(clt|efetivo|full-time|full time|tempo integral)\b', description_text, re.IGNORECASE):
            heuristics["employment_type"] = "Full-time (CLT)"
        elif re.search(r'\b(pj|p\.j\.|contract|contractor|prestador|freelance|pj/clt)\b', description_text, re.IGNORECASE):
            heuristics["employment_type"] = "Contract (PJ)"
        elif re.search(r'\b(part-time|part time|meio período)\b', description_text, re.IGNORECASE):
            heuristics["employment_type"] = "Part-time"
        elif re.search(r'\b(estágio|estagio|internship)\b', description_text, re.IGNORECASE):
            heuristics["employment_type"] = "Internship"

        return heuristics

    @classmethod
    def build_metadata(cls, raw_data: Dict[str, Any], description_text: str) -> JobMetadata:
        """
        Builds a JobMetadata object, falling back to heuristics when attributes are None or empty.
        """
        clean_desc = cls.clean_text(description_text)
        heuristics = cls.extract_heuristics(clean_desc)

        return JobMetadata(
            title=raw_data.get("title") or "Unknown Title",
            company=raw_data.get("company") or "Unknown Company",
            location=raw_data.get("location") or "Remote / Unspecified",
            employment_type=raw_data.get("employment_type") or heuristics["employment_type"] or "Full-time",
            seniority_level=raw_data.get("seniority_level") or heuristics["seniority_level"] or "Not Specified",
            salary_range=raw_data.get("salary_range") or heuristics["salary_range"] or "N/A",
            posting_date=raw_data.get("posting_date"),
            easy_apply=raw_data.get("easy_apply", False)
        )