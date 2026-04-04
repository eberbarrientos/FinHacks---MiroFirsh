"""Scenario schemas"""

from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
from datetime import datetime

from app.schemas.enums import ScenarioType


class ScenarioCreate(BaseModel):
    """Schema for creating a new scenario"""
    name: str
    scenario_type: ScenarioType
    severity: str = "medium"
    time_horizon: str = "12m"
    parameters: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Hurricane Category 5 - Gulf Coast",
                "scenario_type": "hurricane",
                "severity": "high",
                "time_horizon": "12m",
                "parameters": {
                    "affected_regions": ["Texas Gulf", "Louisiana", "Florida"],
                    "wind_speed_mph": 160,
                    "storm_surge_ft": 15
                }
            }
        }


class Scenario(ScenarioCreate):
    """Schema for scenario with database fields"""
    id: str
    created_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v):
        return str(v)

    class Config:
        from_attributes = True
