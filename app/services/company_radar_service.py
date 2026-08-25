from typing import List
from app.db.repository import JobRepository
from app.models.api import RecurringCompany


class CompanyRadarService:
    """
    Somente leitura: agrega vagas já persistidas para identificar empresas
    que apareceram repetidamente com bom score. Não chama LLM — o valor
    aqui vem inteiramente do dado que já pagamos para coletar e avaliar.
    """

    def __init__(self, repository: JobRepository):
        self.repository = repository

    def find_recurring(
        self, *, 
        min_score: int = 70, 
        since_days: int = 28,
        min_occurrences: int = 2, 
        limit: int = 20,
    ) -> List[RecurringCompany]:
        
        rows = self.repository.find_recurring_companies(
            min_score=min_score, since_days=since_days,
            min_occurrences=min_occurrences, limit=limit,
        )
        return [RecurringCompany(**row) for row in rows]