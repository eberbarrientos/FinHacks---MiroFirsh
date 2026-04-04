"""Holding schemas"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class HoldingCreate(BaseModel):
    """Schema for creating a new holding"""
    asset_id: str
    asset_name: str
    asset_type: str
    issuer_name: str
    sector: str
    country: str
    state_region: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90, description="Latitude must be between -90 and 90")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude must be between -180 and 180")
    market_value: Decimal = Field(..., gt=0, description="Market value must be greater than 0")
    revenue_exposure_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    carbon_intensity_proxy: Optional[Decimal] = None
    insurance_dependency_score: Optional[Decimal] = Field(None, ge=0, le=100)
    supply_chain_dependency_score: Optional[Decimal] = Field(None, ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "asset_id": "ASSET001",
                "asset_name": "Houston Office Complex",
                "asset_type": "Real Estate",
                "issuer_name": "Example REIT",
                "sector": "Real Estate",
                "country": "USA",
                "state_region": "Texas",
                "latitude": 29.7604,
                "longitude": -95.3698,
                "market_value": 5000000.00,
                "revenue_exposure_pct": 15.5,
                "carbon_intensity_proxy": 120.5,
                "insurance_dependency_score": 75.0,
                "supply_chain_dependency_score": 60.0
            }
        }


class Holding(HoldingCreate):
    """Schema for holding with database fields"""
    id: str
    portfolio_id: str
    created_at: datetime

    class Config:
        from_attributes = True
