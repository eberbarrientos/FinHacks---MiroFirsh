"""Risk calculation API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel
import uuid
import logging

from app.database import get_db
from app.services.risk_calculation import RiskCalculationService
from app.utils.redis_client import get_redis_client
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/risk", tags=["risk"])

# In-memory task storage (in production, use Redis or database)
task_storage: Dict[str, Dict] = {}


class RiskCalculationRequest(BaseModel):
    """Request schema for risk calculation"""
    portfolio_id: str
    scenario_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_id": "660e8400-e29b-41d4-a716-446655440000"
            }
        }


class RiskCalculationResponse(BaseModel):
    """Response schema for risk calculation initiation"""
    task_id: str
    status: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "770e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "message": "Risk calculation started"
            }
        }


def get_risk_service(
    db: Session = Depends(get_db)
) -> RiskCalculationService:
    """Dependency to get risk calculation service"""
    redis_client = get_redis_client()
    return RiskCalculationService(db, redis_client)


def run_risk_calculation_task(
    task_id: str,
    portfolio_id: str,
    scenario_id: str,
    db: Session
):
    """Background task to run risk calculation"""
    try:
        # Update task status
        task_storage[task_id]["status"] = "processing"
        
        # Get Redis client
        redis_client = get_redis_client()
        
        # Create service and run calculation
        service = RiskCalculationService(db, redis_client)
        result = service.calculate_portfolio_risk(portfolio_id, scenario_id)
        
        # Update task with result
        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["result"] = result
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["error"] = str(e)


@router.post("/run", response_model=RiskCalculationResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_risk_calculation(
    request: RiskCalculationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger risk calculation for a portfolio and scenario.
    
    This endpoint initiates an asynchronous risk calculation and returns immediately
    with a task ID that can be used to check the status and retrieve results.
    
    Args:
        request: Risk calculation request with portfolio_id and scenario_id
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Task ID and status
        
    Raises:
        HTTPException: If portfolio or scenario not found
    """
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task storage
    task_storage[task_id] = {
        "status": "queued",
        "portfolio_id": request.portfolio_id,
        "scenario_id": request.scenario_id,
    }
    
    # Add background task
    background_tasks.add_task(
        run_risk_calculation_task,
        task_id,
        request.portfolio_id,
        request.scenario_id,
        db
    )
    
    logger.info(f"Risk calculation task {task_id} queued for portfolio {request.portfolio_id}")
    
    return RiskCalculationResponse(
        task_id=task_id,
        status="queued",
        message="Risk calculation started"
    )


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a risk calculation task.
    
    Args:
        task_id: UUID of the task
        
    Returns:
        Task status and result if completed
        
    Raises:
        HTTPException: If task not found
    """
    if task_id not in task_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    task = task_storage[task_id]
    
    response = {
        "task_id": task_id,
        "status": task["status"],
        "portfolio_id": task["portfolio_id"],
        "scenario_id": task["scenario_id"],
    }
    
    if task["status"] == "completed":
        response["result"] = task.get("result")
    elif task["status"] == "failed":
        response["error"] = task.get("error")
    
    return response


@router.get("/results")
async def get_risk_results(
    portfolio_id: str,
    scenario_id: str,
    service: RiskCalculationService = Depends(get_risk_service)
):
    """
    Retrieve risk calculation results for a portfolio and scenario.
    
    Args:
        portfolio_id: UUID of the portfolio
        scenario_id: UUID of the scenario
        service: Risk calculation service
        
    Returns:
        List of risk results with holding details
        
    Raises:
        HTTPException: If no results found
    """
    try:
        results = service.get_risk_results(portfolio_id, scenario_id)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No risk results found for portfolio {portfolio_id} and scenario {scenario_id}"
            )
        
        return {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "holdings": results
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving risk results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve risk results"
        )


@router.get("/summary")
async def get_portfolio_summary(
    portfolio_id: str,
    scenario_id: str,
    service: RiskCalculationService = Depends(get_risk_service)
):
    """
    Get portfolio-level summary metrics for a scenario.
    
    Args:
        portfolio_id: UUID of the portfolio
        scenario_id: UUID of the scenario
        service: Risk calculation service
        
    Returns:
        Portfolio summary with key metrics
        
    Raises:
        HTTPException: If no results found
    """
    try:
        summary = service.get_portfolio_summary(portfolio_id, scenario_id)
        
        return {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            **summary
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving portfolio summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio summary"
        )
