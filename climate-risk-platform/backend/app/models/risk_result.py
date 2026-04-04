"""Risk result database model"""

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, GUID


class RiskResult(Base):
    __tablename__ = "risk_results"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(GUID, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    holding_id = Column(GUID, ForeignKey("holdings.id", ondelete="CASCADE"), nullable=False)
    scenario_id = Column(GUID, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    
    physical_score = Column(Numeric(5, 2))
    transition_score = Column(Numeric(5, 2))
    combined_score = Column(Numeric(5, 2))
    expected_loss = Column(Numeric(20, 2))
    stressed_return_delta = Column(Numeric(5, 2))
    confidence = Column(String(50))
    
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="risk_results")
    holding = relationship("Holding", back_populates="risk_results")
    scenario = relationship("Scenario", back_populates="risk_results")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("holding_id", "scenario_id", name="uq_holding_scenario"),
        Index("idx_risk_results_portfolio_scenario", "portfolio_id", "scenario_id"),
        Index("idx_risk_results_scenario", "scenario_id"),
        Index("idx_risk_results_combined_score", "combined_score"),
    )
