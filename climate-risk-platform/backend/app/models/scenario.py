"""Scenario database model"""

from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, GUID, JSON


class Scenario(Base):
    __tablename__ = "scenarios"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    scenario_type = Column(String(100), nullable=False)
    severity = Column(String(50))
    time_horizon = Column(String(50))
    parameters_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    risk_results = relationship("RiskResult", back_populates="scenario", cascade="all, delete-orphan")
    mirofish_runs = relationship("MiroFishRun", back_populates="scenario", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="scenario", cascade="all, delete-orphan")
