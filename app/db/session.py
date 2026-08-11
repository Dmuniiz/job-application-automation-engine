import logging
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from app.config.settings import settings


logger = logging.getLogger(__name__)


connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)


engine = create_engine(
    settings.DATABASE_URL, 
    echo=False, 
    connect_args=connect_args,
    pool_pre_ping=True
)


def create_db_and_tables() -> None:
    """
    Creates database tables automatically on startup if they do not exist.
    MVP: Alembic will be used for migrations in the future.
    """
    try:
        SQLModel.metadata.create_all(engine)
        logging.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"[Database Error] Failed to initialize database: {str(e)}")
        raise e


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency supplying transactional database sessions.
    one session per request, automatically closed after the request is completed.
    """
    with Session(engine) as session:
        yield session