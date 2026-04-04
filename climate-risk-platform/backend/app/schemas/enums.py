"""Enumeration types for schemas"""

from enum import Enum


class ScenarioType(str, Enum):
    """Climate scenario types"""
    HURRICANE = "hurricane"
    WILDFIRE = "wildfire"
    DROUGHT = "drought"
    HEATWAVE = "heatwave"
    FLOOD = "flood"
    CARBON_TAX = "carbon_tax"
    EMISSIONS_REGULATION = "emissions_regulation"
    COMPOUND = "compound"


class RecommendationType(str, Enum):
    """Recommendation action types"""
    REBALANCE = "rebalance"
    DIVERSIFY = "diversify"
    HEDGE = "hedge"
    WATCHLIST = "watchlist"
    INSURANCE_REVIEW = "insurance_review"


class ConfidenceLevel(str, Enum):
    """Risk score confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
