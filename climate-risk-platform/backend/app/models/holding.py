"""Holding database model"""

from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Index, func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, GUID


class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(GUID, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    # Required fields
    asset_id = Column(String(255), nullable=False)
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(100))
    issuer_name = Column(String(255))
    sector = Column(String(100))
    country = Column(String(100))
    state_region = Column(String(100))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    market_value = Column(Numeric(20, 2), nullable=False)
    
    # Optional fields
    revenue_exposure_pct = Column(Numeric(5, 2))
    carbon_intensity_proxy = Column(Numeric(10, 2))
    insurance_dependency_score = Column(Numeric(5, 2))
    supply_chain_dependency_score = Column(Numeric(5, 2))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    risk_results = relationship("RiskResult", back_populates="holding", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_holdings_portfolio", "portfolio_id"),
        Index("idx_holdings_issuer", "issuer_name"),
        Index("idx_holdings_sector", "sector"),
        Index("idx_holdings_location", "latitude", "longitude"),
    )
