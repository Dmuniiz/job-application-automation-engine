import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.core.exceptions import JobFetchError, JobNotFoundError, ScrapingSourceError
from app.db.session import create_db_and_tables
from app.api.routes import jobs, health

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("job_automation")
logging.getLogger("fake_useragent").setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing application services...")
    create_db_and_tables()
    yield
    logger.info("Shutting down application services...")


app = FastAPI(
    title=settings.APP_NAME,
    version="2.2.0",
    description="Automated Job Application System — layered architecture (API/Service/Repository)",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(jobs.router)


# --- Exception handlers globais: único lugar que traduz erro de domínio -> HTTP ---
# Isso elimina o try/except repetido que existia em cada endpoint.

@app.exception_handler(JobNotFoundError)
async def handle_not_found(request: Request, exc: JobNotFoundError):

    logger.warning(f"[404] {exc}")

    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(JobFetchError)
async def handle_fetch_error(request: Request, exc: JobFetchError):
    logger.warning(f"[400] {exc}")

    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ScrapingSourceError)
async def handle_scraping_error(request: Request, exc: ScrapingSourceError):
    logger.error(f"[502] {exc}")

    return JSONResponse(status_code=502, content={"detail": str(exc)})

# Any exception NOT mapped above propagates as FastAPI's default 500, with full traceback in the log — without masking by a generic except.
# Traceback 