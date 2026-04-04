"""Risk result schemas"""

from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from app.schemas.enums import ConfidenceLevel


class RiskResult(BaseModel):
    """Schema for risk calculation result"""
    holding_id: str
    scenario_id: str
    physical_score: Decimal
    transition_score: Decimal
    combined_score: Decimal
    expected_loss: Decimal
    stressed_return_delta: Decimal
    confidence: ConfidenceLevel

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "holding_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_id": "660e8400-e29b-41d4-a716-446655440000",
                "physical_score": 78.5,
                "transition_score": 45.2,
                "combined_score": 65.8,
                "expected_loss": 1250000.00,
                "stressed_return_delta": -12.5,
                "confidence": "high"
            }
        }
