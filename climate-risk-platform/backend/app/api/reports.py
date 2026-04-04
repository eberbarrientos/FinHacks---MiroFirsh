"""API endpoints for executive report generation"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.services.reporting import ReportingService

router = APIRouter(prefix="/api/reports", tags=["reports"])
logger = logging.getLogger(__name__)


@router.get("/executive")
async def generate_executive_report(
    portfolio_id: str = Query(..., description="Portfolio UUID"),
    scenario_id: str = Query(..., description="Scenario UUID"),
    db: Session = Depends(get_db)
):
    """
    Generate and download executive PDF report.
    
    This endpoint generates a comprehensive executive report containing:
    - Portfolio summary and key metrics
    - Risk scores and distribution
    - Scenario analysis results
    - Top recommendations
    - Cascade insights (if available)
    - Charts and visualizations
    
    The report is generated on-demand and returned as a PDF file download.
    
    Args:
        portfolio_id: UUID of the portfolio to report on
        scenario_id: UUID of the scenario to analyze
        db: Database session
        
    Returns:
        PDF file as downloadable response
        
    Raises:
        HTTPException: 404 if portfolio or scenario not found
        HTTPException: 500 if report generation fails
    """
    logger.info(f"Generating executive report for portfolio {portfolio_id}, scenario {scenario_id}")
    
    try:
        # Initialize reporting service
        reporting_service = ReportingService(db)
        
        # Generate report
        pdf_bytes = reporting_service.generate_executive_report(
            portfolio_id=portfolio_id,
            scenario_id=scenario_id
        )
        
        # Return PDF as downloadable file
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=climate_risk_report_{portfolio_id[:8]}_{scenario_id[:8]}.pdf"
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error generating report: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error generating executive report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate executive report. Please try again later."
        )
