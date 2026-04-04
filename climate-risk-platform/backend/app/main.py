"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.config import settings
from app.database import check_database_health, init_db, SessionLocal
from app.utils.redis_client import check_redis_health
from app.api import portfolios, risk, map, scenarios, mirofish, recommendations, reports
from app.api import simulate

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def seed_sample_data():
    """Seed sample portfolio + scenario if DB is empty"""
    from app.models.portfolio import Portfolio
    from app.models.scenario import Scenario
    from app.models.holding import Holding
    from app.schemas.portfolio import PortfolioCreate
    from app.schemas.holding import HoldingCreate
    from app.repositories.portfolio_repository import PortfolioRepository
    from app.repositories.holding_repository import HoldingRepository
    from app.services.seed_data import SeedDataService
    from app.engines.scenario import ScenarioEngine

    db = SessionLocal()
    try:
        # Only seed if no portfolios exist
        if db.query(Portfolio).count() > 0:
            logger.info("Database already has data, skipping seed")
            return

        logger.info("Seeding sample data...")

        # Create sample portfolio
        seed_service = SeedDataService()
        sample = seed_service.get_sample_portfolio()
        repo = PortfolioRepository(db)
        portfolio = repo.create(PortfolioCreate(name=sample["name"], base_currency=sample["base_currency"]))

        # Create holdings
        holding_repo = HoldingRepository(db)
        holdings = [HoldingCreate(**h) for h in sample["holdings"]]
        holding_repo.create_bulk(portfolio.id, holdings)

        # Create scenario templates as stored scenarios
        engine = ScenarioEngine(db)
        templates = engine.get_templates()
        for tmpl in templates[:4]:  # Seed first 4 templates
            from app.schemas.scenario import ScenarioCreate
            from app.schemas.enums import ScenarioType
            engine.create_scenario(ScenarioCreate(
                name=tmpl["name"],
                scenario_type=ScenarioType(tmpl["scenario_type"]),
                severity=tmpl["severity"],
                time_horizon=tmpl["time_horizon"],
                parameters=tmpl["parameters"],
            ))

        logger.info(f"Seeded portfolio '{portfolio.name}' with {len(holdings)} holdings and 4 scenarios")
    except Exception as e:
        logger.error(f"Seed failed: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    seed_sample_data()
    logger.info("Climate Risk Platform API started")
    yield
    # Shutdown
    logger.info("Shutting down")


app = FastAPI(
    title="Climate Risk Intelligence Platform API",
    description="API for climate risk assessment and portfolio analysis",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolios.router)
app.include_router(risk.router)
app.include_router(map.router)
app.include_router(scenarios.router)
app.include_router(mirofish.router)
app.include_router(recommendations.router)
app.include_router(reports.router)
app.include_router(simulate.router)


@app.get("/")
async def root():
    return {"status": "healthy", "service": "climate-risk-platform"}


@app.get("/health")
async def health():
    db_healthy = check_database_health()
    redis_healthy = check_redis_health()
    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": "0.1.0",
        "database": "connected" if db_healthy else "disconnected",
        "cache": "connected" if redis_healthy else "in-memory",
    }
