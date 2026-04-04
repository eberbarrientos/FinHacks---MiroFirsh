"""Portfolio schemas"""

from pydantic import BaseModel
from datetime import datetime


class PortfolioCreate(BaseModel):
    """Schema for creating a new portfolio"""
    name: str
    base_currency: str = "USD"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Global Equity Portfolio",
                "base_currency": "USD"
            }
        }


class Portfolio(PortfolioCreate):
    """Schema for portfolio with database fields"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
