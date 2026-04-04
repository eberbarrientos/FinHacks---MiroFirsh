"""MiroFish run database model"""

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Index, Text, func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, GUID, JSON


class MiroFishRun(Base):
    __tablename__ = "mirofish_runs"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    scenario_id = Column(GUID, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    portfolio_id = Column(GUID, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(String(50), nullable=False)
    input_json = Column(JSON)
    output_json = Column(JSON)
    cascade_events = Column(JSON)
    dependency_narrative = Column(Text)
    propagated_loss = Column(Numeric(20, 2))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    scenario = relationship("Scenario", back_populates="mirofish_runs")
    portfolio = relationship("Portfolio", back_populates="mirofish_runs")
    
    # Indexes
    __table_args__ = (
        Index("idx_mirofish_runs_scenario", "scenario_id"),
        Index("idx_mirofish_runs_portfolio", "portfolio_id"),
        Index("idx_mirofish_runs_status", "status"),
    )
