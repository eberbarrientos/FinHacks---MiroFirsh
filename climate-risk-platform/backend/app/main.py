"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.config import settings
from app.database import check_database_health
from app.utils.redis_client import check_redis_health
from app.api import portfolios, risk, map, scenarios, mirofish, recommendations, reports

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "%(name)s", "message": "%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%SZ'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Climate Risk Intelligence Platform API",
    description="API for climate risk assessment and portfolio analysis",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(portfolios.router)
app.include_router(risk.router)
app.include_router(map.router)
app.include_router(scenarios.router)
app.include_router(mirofish.router)
app.include_router(recommendations.router)
app.include_router(reports.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "climate-risk-platform"}


@app.get("/health")
async def health():
    """Detailed health check with database and Redis status"""
    db_healthy = check_database_health()
    redis_healthy = check_redis_health()
    
    overall_status = "healthy" if (db_healthy and redis_healthy) else "degraded"
    
    return {
        "status": overall_status,
        "version": "0.1.0",
        "database": "connected" if db_healthy else "disconnected",
        "redis": "connected" if redis_healthy else "disconnected",
        "services": {
            "database": db_healthy,
            "redis": redis_healthy
        }
    }

logger.info("Climate Risk Platform API started")
