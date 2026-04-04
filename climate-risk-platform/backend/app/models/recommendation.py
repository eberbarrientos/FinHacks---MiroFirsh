"""Recommendation database model"""

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Index, Text, func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, GUID, JSON


class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(GUID, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    scenario_id = Column(GUID, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    
    recommendation_type = Column(String(100), nullable=False)
    priority = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    affected_holdings = Column(JSON)
    potential_impact = Column(Numeric(20, 2))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="recommendations")
    scenario = relationship("Scenario", back_populates="recommendations")
    
    # Indexes
    __table_args__ = (
        Index("idx_recommendations_portfolio_scenario", "portfolio_id", "scenario_id"),
    )
