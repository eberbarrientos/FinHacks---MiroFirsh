"""Portfolio API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from app.database import get_db
from app.schemas.portfolio import Portfolio, PortfolioCreate
from app.schemas.holding import Holding, HoldingCreate
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.holding_repository import HoldingRepository
from app.services.ingestion import PortfolioIngestionService
from app.services.seed_data import SeedDataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


@router.post("", response_model=Portfolio, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new portfolio
    
    - **name**: Portfolio name
    - **base_currency**: Base currency (default: USD)
    """
    try:
        repo = PortfolioRepository(db)
        db_portfolio = repo.create(portfolio)
        logger.info(f"Created portfolio: {db_portfolio.id}")
        return db_portfolio
    except Exception as e:
        logger.error(f"Error creating portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portfolio"
        )


@router.get("/{portfolio_id}", response_model=dict)
async def get_portfolio(
    portfolio_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get portfolio metadata including holdings count and total value
    
    - **portfolio_id**: Portfolio UUID
    """
    repo = PortfolioRepository(db)
    portfolio_summary = repo.get_portfolio_summary(portfolio_id)
    
    if not portfolio_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    return portfolio_summary


@router.get("", response_model=List[Portfolio])
async def list_portfolios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all portfolios with pagination
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    repo = PortfolioRepository(db)
    portfolios = repo.get_all(skip=skip, limit=limit)
    return portfolios


@router.put("/{portfolio_id}", response_model=Portfolio)
async def update_portfolio(
    portfolio_id: UUID,
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """
    Update an existing portfolio
    
    - **portfolio_id**: Portfolio UUID
    - **name**: New portfolio name
    - **base_currency**: New base currency
    """
    repo = PortfolioRepository(db)
    updated_portfolio = repo.update(portfolio_id, portfolio)
    
    if not updated_portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    logger.info(f"Updated portfolio: {portfolio_id}")
    return updated_portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a portfolio and all its holdings
    
    - **portfolio_id**: Portfolio UUID
    """
    repo = PortfolioRepository(db)
    deleted = repo.delete(portfolio_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    logger.info(f"Deleted portfolio: {portfolio_id}")
    return None


@router.post("/{portfolio_id}/upload-holdings", response_model=dict)
async def upload_holdings(
    portfolio_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload holdings CSV file for a portfolio
    
    - **portfolio_id**: Portfolio UUID
    - **file**: CSV file with holdings data
    
    Returns holdings count and any validation errors
    """
    # Verify portfolio exists
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Validate CSV format
    ingestion_service = PortfolioIngestionService()
    is_valid, format_errors = ingestion_service.validate_csv(file)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "CSV validation failed",
                "errors": format_errors
            }
        )
    
    # Parse holdings
    holdings, validation_errors = ingestion_service.parse_holdings(file)
    
    if validation_errors:
        error_details = [error.to_dict() for error in validation_errors]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Holdings validation failed",
                "errors": error_details
            }
        )
    
    # Store holdings
    try:
        holding_repo = HoldingRepository(db)
        
        # Delete existing holdings for this portfolio
        holding_repo.delete_by_portfolio(portfolio_id)
        
        # Create new holdings
        db_holdings = holding_repo.create_bulk(portfolio_id, holdings)
        
        logger.info(f"Uploaded {len(db_holdings)} holdings to portfolio {portfolio_id}")
        
        return {
            "portfolio_id": str(portfolio_id),
            "holdings_count": len(db_holdings),
            "message": f"Successfully uploaded {len(db_holdings)} holdings"
        }
    except Exception as e:
        logger.error(f"Error storing holdings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store holdings"
        )


@router.get("/{portfolio_id}/holdings", response_model=dict)
async def get_holdings(
    portfolio_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get holdings for a portfolio with pagination
    
    - **portfolio_id**: Portfolio UUID
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    # Verify portfolio exists
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Get holdings
    holding_repo = HoldingRepository(db)
    holdings = holding_repo.get_by_portfolio(portfolio_id, skip=skip, limit=limit)
    total_count = holding_repo.get_count_by_portfolio(portfolio_id)
    
    return {
        "portfolio_id": str(portfolio_id),
        "holdings": holdings,
        "total_count": total_count,
        "skip": skip,
        "limit": limit
    }


@router.get("/sample/data", response_model=dict)
async def get_sample_portfolio_data():
    """
    Get sample portfolio data for demonstration purposes
    
    Returns a portfolio with 50+ diverse holdings across sectors and geographies
    """
    seed_service = SeedDataService()
    sample_data = seed_service.get_sample_portfolio()
    
    return {
        "portfolio": {
            "name": sample_data["name"],
            "base_currency": sample_data["base_currency"]
        },
        "holdings_count": len(sample_data["holdings"]),
        "holdings": sample_data["holdings"]
    }


@router.post("/sample/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_sample_portfolio(db: Session = Depends(get_db)):
    """
    Create a sample portfolio with holdings in the database
    
    Returns the created portfolio with all holdings
    """
    try:
        seed_service = SeedDataService()
        sample_data = seed_service.get_sample_portfolio()
        
        # Create portfolio
        portfolio_repo = PortfolioRepository(db)
        portfolio_create = PortfolioCreate(
            name=sample_data["name"],
            base_currency=sample_data["base_currency"]
        )
        db_portfolio = portfolio_repo.create(portfolio_create)
        
        # Create holdings
        holding_repo = HoldingRepository(db)
        holdings_create = [HoldingCreate(**h) for h in sample_data["holdings"]]
        db_holdings = holding_repo.create_bulk(db_portfolio.id, holdings_create)
        
        logger.info(f"Created sample portfolio {db_portfolio.id} with {len(db_holdings)} holdings")
        
        return {
            "portfolio_id": str(db_portfolio.id),
            "name": db_portfolio.name,
            "base_currency": db_portfolio.base_currency,
            "holdings_count": len(db_holdings),
            "message": f"Successfully created sample portfolio with {len(db_holdings)} holdings"
        }
    except Exception as e:
        logger.error(f"Error creating sample portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sample portfolio"
        )


@router.get("/{portfolio_id}/scenario-history", response_model=List[dict])
async def get_scenario_execution_history(
    portfolio_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get scenario execution history for a portfolio
    
    Returns all scenarios that have been executed for this portfolio,
    ordered by execution timestamp descending (most recent first)
    
    - **portfolio_id**: Portfolio UUID
    """
    # Verify portfolio exists
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    try:
        # Query risk_results table for unique scenario executions
        from app.models.risk_result import RiskResult
        from app.models.scenario import Scenario
        from sqlalchemy import func, desc
        
        # Get distinct scenarios with their latest execution time
        scenario_executions = (
            db.query(
                Scenario.id,
                Scenario.name,
                Scenario.scenario_type,
                Scenario.severity,
                Scenario.time_horizon,
                func.max(RiskResult.calculated_at).label('last_executed'),
                func.count(RiskResult.id).label('holdings_count')
            )
            .join(RiskResult, RiskResult.scenario_id == Scenario.id)
            .filter(RiskResult.portfolio_id == portfolio_id)
            .group_by(
                Scenario.id,
                Scenario.name,
                Scenario.scenario_type,
                Scenario.severity,
                Scenario.time_horizon
            )
            .order_by(desc('last_executed'))
            .all()
        )
        
        return [
            {
                "scenario_id": str(execution.id),
                "scenario_name": execution.name,
                "scenario_type": execution.scenario_type,
                "severity": execution.severity,
                "time_horizon": execution.time_horizon,
                "last_executed": execution.last_executed.isoformat() if execution.last_executed else None,
                "holdings_count": execution.holdings_count
            }
            for execution in scenario_executions
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving scenario history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scenario execution history"
        )
