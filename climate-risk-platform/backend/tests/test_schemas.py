"""Tests for Pydantic schemas"""

import pytest
from pydantic import ValidationError

from app.schemas.holding import HoldingCreate
from app.schemas.portfolio import PortfolioCreate
from app.schemas.scenario import ScenarioCreate
from app.schemas.enums import ScenarioType, ConfidenceLevel


class TestHoldingSchema:
    """Test HoldingCreate schema validation"""
    
    def test_valid_holding(self):
        """Test creating a valid holding"""
        holding = HoldingCreate(
            asset_id="ASSET001",
            asset_name="Test Asset",
            asset_type="Real Estate",
            issuer_name="Test Corp",
            sector="Utilities",
            country="USA",
            state_region="Texas",
            latitude=29.7604,
            longitude=-95.3698,
            market_value=1000000.00
        )
        assert holding.asset_id == "ASSET001"
        assert holding.market_value == 1000000.00
    
    def test_latitude_validation(self):
        """Test latitude must be between -90 and 90"""
        with pytest.raises(ValidationError) as exc_info:
            HoldingCreate(
                asset_id="ASSET001",
                asset_name="Test Asset",
                asset_type="Real Estate",
                issuer_name="Test Corp",
                sector="Utilities",
                country="USA",
                latitude=100.0,  # Invalid
                longitude=-95.3698,
                market_value=1000000.00
            )
        assert "latitude" in str(exc_info.value).lower()
    
    def test_longitude_validation(self):
        """Test longitude must be between -180 and 180"""
        with pytest.raises(ValidationError) as exc_info:
            HoldingCreate(
                asset_id="ASSET001",
                asset_name="Test Asset",
                asset_type="Real Estate",
                issuer_name="Test Corp",
                sector="Utilities",
                country="USA",
                latitude=29.7604,
                longitude=200.0,  # Invalid
                market_value=1000000.00
            )
        assert "longitude" in str(exc_info.value).lower()
    
    def test_market_value_positive(self):
        """Test market value must be positive"""
        with pytest.raises(ValidationError) as exc_info:
            HoldingCreate(
                asset_id="ASSET001",
                asset_name="Test Asset",
                asset_type="Real Estate",
                issuer_name="Test Corp",
                sector="Utilities",
                country="USA",
                latitude=29.7604,
                longitude=-95.3698,
                market_value=-1000.00  # Invalid
            )
        assert "market_value" in str(exc_info.value).lower()
    
    def test_optional_fields(self):
        """Test optional fields can be None"""
        holding = HoldingCreate(
            asset_id="ASSET001",
            asset_name="Test Asset",
            asset_type="Real Estate",
            issuer_name="Test Corp",
            sector="Utilities",
            country="USA",
            latitude=29.7604,
            longitude=-95.3698,
            market_value=1000000.00,
            revenue_exposure_pct=None,
            carbon_intensity_proxy=None
        )
        assert holding.revenue_exposure_pct is None
        assert holding.carbon_intensity_proxy is None


class TestPortfolioSchema:
    """Test PortfolioCreate schema validation"""
    
    def test_valid_portfolio(self):
        """Test creating a valid portfolio"""
        portfolio = PortfolioCreate(
            name="Test Portfolio",
            base_currency="USD"
        )
        assert portfolio.name == "Test Portfolio"
        assert portfolio.base_currency == "USD"
    
    def test_default_currency(self):
        """Test default currency is USD"""
        portfolio = PortfolioCreate(name="Test Portfolio")
        assert portfolio.base_currency == "USD"


class TestScenarioSchema:
    """Test ScenarioCreate schema validation"""
    
    def test_valid_scenario(self):
        """Test creating a valid scenario"""
        scenario = ScenarioCreate(
            name="Hurricane Test",
            scenario_type=ScenarioType.HURRICANE,
            severity="high",
            time_horizon="12m"
        )
        assert scenario.name == "Hurricane Test"
        assert scenario.scenario_type == ScenarioType.HURRICANE
        assert scenario.severity == "high"
    
    def test_scenario_type_enum(self):
        """Test scenario type must be valid enum"""
        with pytest.raises(ValidationError):
            ScenarioCreate(
                name="Invalid Scenario",
                scenario_type="invalid_type",  # Invalid
                severity="high",
                time_horizon="12m"
            )
    
    def test_default_values(self):
        """Test default severity and time_horizon"""
        scenario = ScenarioCreate(
            name="Test Scenario",
            scenario_type=ScenarioType.FLOOD
        )
        assert scenario.severity == "medium"
        assert scenario.time_horizon == "12m"


class TestEnums:
    """Test enum definitions"""
    
    def test_scenario_types(self):
        """Test all scenario types are defined"""
        assert ScenarioType.HURRICANE == "hurricane"
        assert ScenarioType.WILDFIRE == "wildfire"
        assert ScenarioType.DROUGHT == "drought"
        assert ScenarioType.HEATWAVE == "heatwave"
        assert ScenarioType.FLOOD == "flood"
        assert ScenarioType.CARBON_TAX == "carbon_tax"
        assert ScenarioType.EMISSIONS_REGULATION == "emissions_regulation"
    
    def test_confidence_levels(self):
        """Test confidence level enum"""
        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.LOW == "low"
