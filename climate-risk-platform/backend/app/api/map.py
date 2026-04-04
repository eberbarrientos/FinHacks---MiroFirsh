"""Map and geospatial API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Dict, Optional
from pydantic import BaseModel
from uuid import UUID
import logging
from collections import defaultdict

from app.database import get_db
from app.models.holding import Holding
from app.models.risk_result import RiskResult
from app.repositories.portfolio_repository import PortfolioRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/map", tags=["map"])


class HoldingMapData(BaseModel):
    """Schema for holding map data"""
    holding_id: str
    asset_name: str
    issuer_name: str
    sector: str
    latitude: float
    longitude: float
    combined_score: float
    expected_loss: float
    physical_score: Optional[float] = None
    transition_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class HotspotData(BaseModel):
    """Schema for geographic hotspot data"""
    region: str
    latitude: float
    longitude: float
    holding_count: int
    total_expected_loss: float
    avg_combined_score: float
    max_combined_score: float
    
    class Config:
        from_attributes = True


def detect_hotspots(holdings_data: List[Dict], threshold_score: float = 70.0) -> List[Dict]:
    """
    Detect geographic hotspots using clustering algorithm.
    
    Groups holdings by geographic proximity and high risk scores.
    A hotspot is defined as a region with:
    - Multiple holdings in close proximity (within ~50km)
    - Average combined score above threshold
    - Significant expected loss concentration
    
    Args:
        holdings_data: List of holdings with location and risk data
        threshold_score: Minimum average score to qualify as hotspot
        
    Returns:
        List of hotspot regions with aggregated metrics
    """
    if not holdings_data:
        return []
    
    # Simple grid-based clustering (0.5 degree grid ~ 50km at equator)
    grid_size = 0.5
    clusters = defaultdict(list)
    
    for holding in holdings_data:
        # Round coordinates to grid
        grid_lat = round(holding["latitude"] / grid_size) * grid_size
        grid_lon = round(holding["longitude"] / grid_size) * grid_size
        grid_key = (grid_lat, grid_lon)
        clusters[grid_key].append(holding)
    
    # Identify hotspots
    hotspots = []
    for (grid_lat, grid_lon), cluster_holdings in clusters.items():
        if len(cluster_holdings) < 2:  # Need at least 2 holdings
            continue
        
        total_loss = sum(h["expected_loss"] for h in cluster_holdings)
        avg_score = sum(h["combined_score"] for h in cluster_holdings) / len(cluster_holdings)
        max_score = max(h["combined_score"] for h in cluster_holdings)
        
        # Only include if average score exceeds threshold
        if avg_score >= threshold_score:
            # Determine region name from holdings
            regions = [h.get("state_region") or h.get("country") for h in cluster_holdings]
            region_name = max(set(regions), key=regions.count) if regions else f"Region {grid_lat},{grid_lon}"
            
            hotspots.append({
                "region": region_name,
                "latitude": grid_lat,
                "longitude": grid_lon,
                "holding_count": len(cluster_holdings),
                "total_expected_loss": total_loss,
                "avg_combined_score": avg_score,
                "max_combined_score": max_score
            })
    
    # Sort by total expected loss descending
    hotspots.sort(key=lambda x: x["total_expected_loss"], reverse=True)
    
    return hotspots


@router.get("/holdings", response_model=Dict)
async def get_map_holdings(
    portfolio_id: UUID,
    scenario_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get holdings with geospatial data for map visualization.
    
    Returns holdings with latitude, longitude, combined_score, and expected_loss
    for the specified portfolio and scenario.
    
    Args:
        portfolio_id: UUID of the portfolio
        scenario_id: UUID of the scenario
        db: Database session
        
    Returns:
        Holdings with geospatial and risk data
        
    Raises:
        HTTPException: If portfolio not found or no data available
    """
    # Verify portfolio exists
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Query holdings with risk results
    query = (
        db.query(
            Holding.id.label("holding_id"),
            Holding.asset_name,
            Holding.issuer_name,
            Holding.sector,
            Holding.latitude,
            Holding.longitude,
            Holding.state_region,
            Holding.country,
            RiskResult.combined_score,
            RiskResult.expected_loss,
            RiskResult.physical_score,
            RiskResult.transition_score
        )
        .join(RiskResult, Holding.id == RiskResult.holding_id)
        .filter(
            and_(
                Holding.portfolio_id == portfolio_id,
                RiskResult.scenario_id == scenario_id
            )
        )
    )
    
    results = query.all()
    
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk data found for portfolio {portfolio_id} and scenario {scenario_id}"
        )
    
    # Convert to dict format
    holdings_data = []
    for row in results:
        holdings_data.append({
            "holding_id": str(row.holding_id),
            "asset_name": row.asset_name,
            "issuer_name": row.issuer_name,
            "sector": row.sector,
            "latitude": float(row.latitude),
            "longitude": float(row.longitude),
            "state_region": row.state_region,
            "country": row.country,
            "combined_score": float(row.combined_score),
            "expected_loss": float(row.expected_loss),
            "physical_score": float(row.physical_score) if row.physical_score else None,
            "transition_score": float(row.transition_score) if row.transition_score else None
        })
    
    logger.info(f"Retrieved {len(holdings_data)} holdings for map visualization")
    
    return {
        "portfolio_id": str(portfolio_id),
        "scenario_id": str(scenario_id),
        "holdings_count": len(holdings_data),
        "holdings": holdings_data
    }


@router.get("/hotspots", response_model=Dict)
async def get_hotspots(
    portfolio_id: UUID,
    scenario_id: UUID,
    threshold_score: float = 70.0,
    db: Session = Depends(get_db)
):
    """
    Detect and return geographic hotspots with high climate risk concentration.
    
    Hotspots are identified using geographic clustering combined with risk scoring.
    A hotspot represents a region with multiple holdings showing elevated risk levels.
    
    Args:
        portfolio_id: UUID of the portfolio
        scenario_id: UUID of the scenario
        threshold_score: Minimum average combined score to qualify as hotspot (default: 70.0)
        db: Database session
        
    Returns:
        List of hotspots with aggregated risk metrics
        
    Raises:
        HTTPException: If portfolio not found or no data available
    """
    # Verify portfolio exists
    portfolio_repo = PortfolioRepository(db)
    portfolio = portfolio_repo.get_by_id(portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Query holdings with risk results
    query = (
        db.query(
            Holding.latitude,
            Holding.longitude,
            Holding.state_region,
            Holding.country,
            RiskResult.combined_score,
            RiskResult.expected_loss
        )
        .join(RiskResult, Holding.id == RiskResult.holding_id)
        .filter(
            and_(
                Holding.portfolio_id == portfolio_id,
                RiskResult.scenario_id == scenario_id
            )
        )
    )
    
    results = query.all()
    
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk data found for portfolio {portfolio_id} and scenario {scenario_id}"
        )
    
    # Convert to dict format for hotspot detection
    holdings_data = []
    for row in results:
        holdings_data.append({
            "latitude": float(row.latitude),
            "longitude": float(row.longitude),
            "state_region": row.state_region,
            "country": row.country,
            "combined_score": float(row.combined_score),
            "expected_loss": float(row.expected_loss)
        })
    
    # Detect hotspots
    hotspots = detect_hotspots(holdings_data, threshold_score)
    
    logger.info(f"Detected {len(hotspots)} hotspots for portfolio {portfolio_id}")
    
    return {
        "portfolio_id": str(portfolio_id),
        "scenario_id": str(scenario_id),
        "threshold_score": threshold_score,
        "hotspots_count": len(hotspots),
        "hotspots": hotspots
    }
