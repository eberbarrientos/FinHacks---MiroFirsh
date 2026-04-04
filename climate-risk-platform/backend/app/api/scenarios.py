"""Scenario API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.database import get_db
from app.engines.scenario import ScenarioEngine
from app.services.risk_calculation import RiskCalculationService
from app.schemas.scenario import ScenarioCreate, Scenario
from app.config import settings
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


def get_redis_client():
    """Get Redis client for caching"""
    try:
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )
        return client
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        return None


@router.get("/templates", response_model=List[Dict[str, Any]])
def get_scenario_templates(db: Session = Depends(get_db)):
    """
    Get all predefined scenario templates
    
    Returns:
        List of scenario templates with descriptions and parameters
    
    **Validates: Requirements 4.1**
    """
    try:
        engine = ScenarioEngine(db)
        templates = engine.get_templates()
        return templates
    except Exception as e:
        logger.error(f"Error retrieving scenario templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scenario templates")


@router.post("", response_model=Scenario, status_code=201)
def create_scenario(
    scenario_data: ScenarioCreate,
    db: Session = Depends(get_db)
):
    """
    Create a custom scenario
    
    Args:
        scenario_data: Scenario creation data including name, type, severity, time_horizon, and parameters
    
    Returns:
        Created scenario with database ID
    
    **Validates: Requirements 4.2**
    """
    try:
        engine = ScenarioEngine(db)
        scenario = engine.create_scenario(scenario_data)
        logger.info(f"Created scenario {scenario.id}: {scenario.name}")
        return scenario
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating scenario: {e}")
        raise HTTPException(status_code=500, detail="Failed to create scenario")


@router.get("", response_model=List[Scenario])
def list_scenarios(db: Session = Depends(get_db)):
    """
    List all stored scenarios
    
    Returns:
        List of all scenarios ordered by creation date (newest first)
    """
    try:
        engine = ScenarioEngine(db)
        scenarios = engine.list_scenarios()
        return scenarios
    except Exception as e:
        logger.error(f"Error listing scenarios: {e}")
        raise HTTPException(status_code=500, detail="Failed to list scenarios")


@router.get("/{scenario_id}", response_model=Scenario)
def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific scenario by ID
    
    Args:
        scenario_id: Scenario UUID
    
    Returns:
        Scenario details
    """
    try:
        engine = ScenarioEngine(db)
        scenario = engine.get_scenario(scenario_id)
        
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
        
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scenario {scenario_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scenario")


@router.post("/{scenario_id}/stress-test", response_model=Dict[str, Any])
def stress_test_scenario(
    scenario_id: str,
    portfolio_id: str = Query(..., description="Portfolio UUID to stress test"),
    db: Session = Depends(get_db)
):
    """
    Apply a scenario to a portfolio and run stress test
    
    Args:
        scenario_id: Scenario UUID
        portfolio_id: Portfolio UUID
    
    Returns:
        Stress test results including risk metrics and scenario details
    
    **Validates: Requirements 4.3**
    """
    try:
        # Initialize engines and services
        scenario_engine = ScenarioEngine(db)
        redis_client = get_redis_client()
        risk_service = RiskCalculationService(db, redis_client)
        
        # Apply scenario and calculate risk
        results = scenario_engine.apply_scenario(
            portfolio_id=portfolio_id,
            scenario_id=scenario_id,
            risk_calculation_service=risk_service
        )
        
        logger.info(f"Stress test completed for portfolio {portfolio_id}, scenario {scenario_id}")
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running stress test: {e}")
        raise HTTPException(status_code=500, detail="Failed to run stress test")


@router.get("/compare", response_model=Dict[str, Any])
def compare_scenarios(
    portfolio_id: str = Query(..., description="Portfolio UUID"),
    scenario_ids: str = Query(..., description="Comma-separated list of scenario UUIDs (2-4 scenarios)"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple scenarios side-by-side for a portfolio
    
    Args:
        portfolio_id: Portfolio UUID
        scenario_ids: Comma-separated list of scenario UUIDs (2-4 scenarios)
    
    Returns:
        Comparison results with metrics for each scenario and delta calculations
    
    **Validates: Requirements 4.6**
    """
    try:
        # Parse scenario IDs
        scenario_id_list = [sid.strip() for sid in scenario_ids.split(",")]
        
        if len(scenario_id_list) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 scenarios required for comparison"
            )
        
        if len(scenario_id_list) > 4:
            raise HTTPException(
                status_code=400,
                detail="Maximum 4 scenarios can be compared simultaneously"
            )
        
        # Initialize engines and services
        scenario_engine = ScenarioEngine(db)
        redis_client = get_redis_client()
        risk_service = RiskCalculationService(db, redis_client)
        
        # Compare scenarios
        comparison = scenario_engine.compare_scenarios(
            portfolio_id=portfolio_id,
            scenario_ids=scenario_id_list,
            risk_calculation_service=risk_service
        )
        
        logger.info(f"Scenario comparison completed for portfolio {portfolio_id}")
        return comparison
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing scenarios: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare scenarios")
