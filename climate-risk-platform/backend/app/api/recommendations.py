"""Recommendation API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app.engines.recommendation import RecommendationEngine
from app.models.recommendation import Recommendation as RecommendationModel
from app.schemas.recommendation import Recommendation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def get_recommendation_engine(db: Session = Depends(get_db)) -> RecommendationEngine:
    """Dependency to get recommendation engine"""
    return RecommendationEngine(db)


@router.get("", response_model=List[Recommendation])
async def get_recommendations(
    portfolio_id: str,
    scenario_id: str,
    db: Session = Depends(get_db)
):
    """
    Get recommendations for a portfolio and scenario.
    
    Returns recommendations sorted by priority (critical > high > medium > low)
    and then by potential impact (descending).
    
    Args:
        portfolio_id: UUID of the portfolio
        scenario_id: UUID of the scenario
        db: Database session
        
    Returns:
        List of recommendations sorted by priority and impact
        
    Raises:
        HTTPException: If portfolio or scenario not found, or no recommendations exist
    """
    try:
        # Query existing recommendations
        recommendations = db.query(RecommendationModel).filter(
            RecommendationModel.portfolio_id == portfolio_id,
            RecommendationModel.scenario_id == scenario_id
        ).all()
        
        # If no recommendations exist, generate them
        if not recommendations:
            logger.info(f"No existing recommendations found, generating for portfolio {portfolio_id}, scenario {scenario_id}")
            engine = RecommendationEngine(db)
            recommendations = engine.generate_recommendations(portfolio_id, scenario_id)
        
        # Sort by priority and potential impact
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        sorted_recommendations = sorted(
            recommendations,
            key=lambda r: (
                priority_order.get(r.priority, 4),
                -(float(r.potential_impact) if r.potential_impact else 0)
            )
        )
        
        logger.info(f"Returning {len(sorted_recommendations)} recommendations")
        
        # Convert to Pydantic models with string UUIDs
        return [
            Recommendation(
                id=str(r.id),
                portfolio_id=str(r.portfolio_id),
                scenario_id=str(r.scenario_id),
                recommendation_type=r.recommendation_type,
                priority=r.priority,
                message=r.message,
                affected_holdings=r.affected_holdings,
                potential_impact=r.potential_impact,
                created_at=r.created_at
            )
            for r in sorted_recommendations
        ]
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recommendations"
        )


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_recommendations(
    portfolio_id: str,
    scenario_id: str,
    engine: RecommendationEngine = Depends(get_recommendation_engine)
):
    """
    Generate new recommendations for a portfolio and scenario.
    
    This endpoint forces regeneration of recommendations even if they already exist.
    Useful when risk results have been updated.
    
    Args:
        portfolio_id: UUID of the portfolio
        scenario_id: UUID of the scenario
        engine: Recommendation engine
        
    Returns:
        Success message with count of generated recommendations
        
    Raises:
        HTTPException: If portfolio or scenario not found, or generation fails
    """
    try:
        # Delete existing recommendations
        engine.db.query(RecommendationModel).filter(
            RecommendationModel.portfolio_id == portfolio_id,
            RecommendationModel.scenario_id == scenario_id
        ).delete()
        engine.db.commit()
        
        # Generate new recommendations
        recommendations = engine.generate_recommendations(portfolio_id, scenario_id)
        
        return {
            "message": "Recommendations generated successfully",
            "count": len(recommendations),
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )
