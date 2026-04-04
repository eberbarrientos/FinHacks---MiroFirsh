"""Portfolio database model"""

from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, GUID


class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    base_currency = Column(String(3), default="USD")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    risk_results = relationship("RiskResult", back_populates="portfolio", cascade="all, delete-orphan")
    mirofish_runs = relationship("MiroFishRun", back_populates="portfolio", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="portfolio", cascade="all, delete-orphan")
