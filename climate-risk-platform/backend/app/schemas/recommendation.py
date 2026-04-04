"""Recommendation schemas"""

from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from app.schemas.enums import RecommendationType


class Recommendation(BaseModel):
    """Schema for portfolio recommendation"""
    id: str
    portfolio_id: str
    scenario_id: str
    recommendation_type: RecommendationType
    priority: str
    message: str
    affected_holdings: Optional[List[str]] = None
    potential_impact: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440000",
                "portfolio_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_id": "660e8400-e29b-41d4-a716-446655440000",
                "recommendation_type": "rebalance",
                "priority": "high",
                "message": "Consider reducing exposure to coastal real estate holdings with combined risk score above 75",
                "affected_holdings": ["holding1", "holding2", "holding3"],
                "potential_impact": 2500000.00,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
