"""
MiroFish API endpoints for cascade simulation
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.adapters import MiroFishAdapter, MiroFishError, MiroFishTimeoutError, MiroFishConnectionError
from app.models.mirofish_run import MiroFishRun
from app.models.portfolio import Portfolio
from app.models.scenario import Scenario
from app.models.risk_result import RiskResult


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mirofish", tags=["mirofish"])


class MiroFishRunRequest(BaseModel):
    """Request to trigger MiroFish cascade simulation"""
    portfolio_id: str
    scenario_id: str


class MiroFishRunResponse(BaseModel):
    """Response from MiroFish run creation"""
    run_id: str
    status: str
    message: Optional[str] = None


class MiroFishResultResponse(BaseModel):
    """Response with MiroFish simulation results"""
    run_id: str
    status: str
    cascade_events: Optional[list] = None
    dependency_narrative: Optional[str] = None
    propagated_loss: Optional[float] = None
    affected_entity_count: Optional[int] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@router.post("/run", response_model=MiroFishRunResponse)
async def trigger_cascade_simulation(
    request: MiroFishRunRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger MiroFish cascade simulation for a portfolio and scenario
    
    This endpoint:
    1. Retrieves portfolio and scenario data
    2. Fetches risk results for the portfolio/scenario combination
    3. Constructs a scenario packet
    4. Submits to MiroFish
    5. Polls for completion
    6. Stores results in database
    
    If MiroFish is unavailable, returns a fallback message.
    
    Args:
        request: Portfolio and scenario IDs
        db: Database session
        
    Returns:
        MiroFishRunResponse with run_id and status
        
    Raises:
        HTTPException: If portfolio/scenario not found or simulation fails
    """
    try:
        # Validate portfolio exists
        portfolio = db.query(Portfolio).filter(Portfolio.id == request.portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio {request.portfolio_id} not found")
        
        # Validate scenario exists
        scenario = db.query(Scenario).filter(Scenario.id == request.scenario_id).first()
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario {request.scenario_id} not found")
        
        # Get risk results for this portfolio/scenario
        risk_results = db.query(RiskResult).filter(
            RiskResult.portfolio_id == request.portfolio_id,
            RiskResult.scenario_id == request.scenario_id
        ).all()
        
        if not risk_results:
            raise HTTPException(
                status_code=400,
                detail="No risk results found. Please run risk calculation first."
            )
        
        # Calculate total portfolio value and prepare risk results data
        total_value = 0
        risk_results_data = []
        
        for r in risk_results:
            # Get holding details
            holding = r.holding
            if not holding:
                continue
            
            market_value = float(holding.market_value) if holding.market_value else 0
            total_value += market_value
            
            risk_results_data.append({
                "issuer_name": holding.issuer_name,
                "sector": holding.sector,
                "country": holding.country,
                "state_region": holding.state_region,
                "combined_score": float(r.combined_score) if r.combined_score else 0,
                "expected_loss": float(r.expected_loss) if r.expected_loss else 0,
                "market_value": market_value,
                "insurance_dependency_score": float(holding.insurance_dependency_score) if holding.insurance_dependency_score else 0,
                "supply_chain_dependency_score": float(holding.supply_chain_dependency_score) if holding.supply_chain_dependency_score else 0,
            })
        
        # Prepare data for adapter
        portfolio_data = {
            "id": str(portfolio.id),
            "name": portfolio.name,
            "total_value": total_value
        }
        
        scenario_data = {
            "id": str(scenario.id),
            "scenario_type": scenario.scenario_type,
            "severity": scenario.severity,
            "time_horizon": scenario.time_horizon
        }
        
        # Initialize MiroFish adapter
        adapter = MiroFishAdapter()
        
        # Construct scenario packet
        scenario_packet = adapter.construct_scenario_packet(
            portfolio=portfolio_data,
            scenario=scenario_data,
            risk_results=risk_results_data
        )
        
        # Create database record
        mirofish_run = MiroFishRun(
            scenario_id=request.scenario_id,
            portfolio_id=request.portfolio_id,
            status="pending",
            input_json=scenario_packet
        )
        db.add(mirofish_run)
        db.commit()
        db.refresh(mirofish_run)
        
        run_id = str(mirofish_run.id)
        
        try:
            # Submit to MiroFish
            mirofish_sim_id = await adapter.submit_simulation(scenario_packet)
            
            # Update status
            mirofish_run.status = "running"
            db.commit()
            
            # Poll for completion
            simulation_data = await adapter.poll_simulation(mirofish_sim_id)
            
            # Parse results
            cascade_results = adapter.parse_cascade_results(simulation_data)
            
            # Update database with results
            mirofish_run.status = "completed"
            mirofish_run.output_json = simulation_data
            mirofish_run.cascade_events = cascade_results["cascade_events"]
            mirofish_run.dependency_narrative = cascade_results["dependency_narrative"]
            mirofish_run.propagated_loss = cascade_results["propagated_loss"]
            mirofish_run.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"MiroFish simulation completed: run_id={run_id}")
            
            return MiroFishRunResponse(
                run_id=run_id,
                status="completed",
                message="Cascade simulation completed successfully"
            )
            
        except (MiroFishConnectionError, MiroFishTimeoutError) as e:
            # MiroFish unavailable - return fallback
            logger.warning(f"MiroFish unavailable: {e}")
            
            mirofish_run.status = "unavailable"
            mirofish_run.dependency_narrative = "Cascade analysis unavailable - showing direct risk only"
            db.commit()
            
            return MiroFishRunResponse(
                run_id=run_id,
                status="unavailable",
                message="Cascade analysis unavailable - showing direct risk only"
            )
            
        except MiroFishError as e:
            # MiroFish error
            logger.error(f"MiroFish simulation failed: {e}")
            
            mirofish_run.status = "failed"
            mirofish_run.dependency_narrative = f"Simulation failed: {str(e)}"
            db.commit()
            
            raise HTTPException(
                status_code=500,
                detail=f"MiroFish simulation failed: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering MiroFish simulation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger cascade simulation: {str(e)}"
        )


@router.get("/run/{run_id}", response_model=MiroFishResultResponse)
def get_simulation_results(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve MiroFish simulation results
    
    Args:
        run_id: MiroFish run identifier
        db: Database session
        
    Returns:
        MiroFishResultResponse with cascade results
        
    Raises:
        HTTPException: If run not found
    """
    try:
        # Query database for run
        mirofish_run = db.query(MiroFishRun).filter(MiroFishRun.id == run_id).first()
        
        if not mirofish_run:
            raise HTTPException(status_code=404, detail=f"MiroFish run {run_id} not found")
        
        # Build response
        response = MiroFishResultResponse(
            run_id=str(mirofish_run.id),
            status=mirofish_run.status,
            cascade_events=mirofish_run.cascade_events,
            dependency_narrative=mirofish_run.dependency_narrative,
            propagated_loss=float(mirofish_run.propagated_loss) if mirofish_run.propagated_loss else None,
            created_at=mirofish_run.created_at,
            completed_at=mirofish_run.completed_at
        )
        
        # Add affected entity count if cascade events exist
        if mirofish_run.cascade_events:
            entities = set()
            for event in mirofish_run.cascade_events:
                entity = event.get("entity") or event.get("issuer")
                if entity:
                    entities.add(entity)
            response.affected_entity_count = len(entities)
        
        # Add error message if failed or unavailable
        if mirofish_run.status in ["failed", "unavailable"]:
            response.error = mirofish_run.dependency_narrative
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving MiroFish results: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve simulation results: {str(e)}"
        )
