"""Portfolio schemas"""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Any


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

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: Any) -> str:
        return str(v)

    class Config:
        from_attributes = True
