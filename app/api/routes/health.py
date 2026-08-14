from fastapi import APIRouter
from app.config.settings import settings

router = APIRouter(tags=["health"])
_is_mock_active = settings.USE_MOCK or (settings.ENVIRONMENT == "development")


@router.get("/health")
async def health_check():
    
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "use_mock": _is_mock_active,
        "database": settings.DATABASE_URL.split("://")[0],
    }