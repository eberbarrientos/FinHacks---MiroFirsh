"""Database connection and session management - supports SQLite and PostgreSQL"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
import logging
from app.config import settings

logger = logging.getLogger(__name__)

is_sqlite = settings.database_url.startswith("sqlite")

engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_recycle": settings.database_pool_recycle,
        "pool_timeout": 30,
    })

engine = create_engine(settings.database_url, **engine_kwargs)

# Enable foreign keys for SQLite
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist"""
    from app.models.base import Base
    # Import all models so they register with Base
    from app.models import Portfolio, Holding, Scenario, RiskResult, MiroFishRun, Recommendation  # noqa
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")


def check_database_health() -> bool:
    """Check if database connection is healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
