"""Tests for Climate Exposure Engine"""

import pytest
from decimal import Decimal
from datetime import datetime

from app.engines.exposure import ClimateExposureEngine
from app.schemas.holding import Holding
from app.schemas.scenario import Scenario
from app.schemas.enums import ScenarioType, ConfidenceLevel


@pytest.fixture
def engine():
    """Create ClimateExposureEngine instance."""
    return ClimateExposureEngine()


@pytest.fixture
def base_holding():
    """Create a base holding for testing."""
    return Holding(
        id="test-holding-1",
        portfolio_id="test-portfolio-1",
        asset_id="ASSET001",
        asset_name="Test Asset",
        asset_type="Real Estate",
        issuer_name="Test Issuer",
        sector="Real Estate",
        country="USA",
        state_region="Texas",
        latitude=29.7604,  # Houston
        longitude=-95.3698,
        market_value=Decimal("1000000.00"),
        created_at=datetime.now()
    )


@pytest.fixture
def complete_holding():
    """Create a holding with all optional fields."""
    return Holding(
        id="test-holding-2",
        portfolio_id="test-portfolio-1",
        asset_id="ASSET002",
        asset_name="Complete Asset",
        asset_type="Corporate Bond",
        issuer_name="Energy Corp",
        sector="Energy",
        country="USA",
        state_region="Texas",
        latitude=29.7604,
        longitude=-95.3698,
        market_value=Decimal("5000000.00"),
        revenue_exposure_pct=Decimal("25.5"),
        carbon_intensity_proxy=Decimal("250.0"),
        insurance_dependency_score=Decimal("75.0"),
        supply_chain_dependency_score=Decimal("60.0"),
        created_at=datetime.now()
    )


@pytest.fixture
def hurricane_scenario():
    """Create a hurricane scenario."""
    return Scenario(
        id="scenario-hurricane",
        name="Hurricane Category 5",
        scenario_type=ScenarioType.HURRICANE,
        severity="high",
        time_horizon="12m",
        parameters={"wind_speed_mph": 160},
        created_at=datetime.now()
    )


@pytest.fixture
def carbon_tax_scenario():
    """Create a carbon tax scenario."""
    return Scenario(
        id="scenario-carbon-tax",
        name="Carbon Tax $100/ton",
        scenario_type=ScenarioType.CARBON_TAX,
        severity="high",
        time_horizon="24m",
        parameters={"tax_per_ton": 100},
        created_at=datetime.now()
    )


@pytest.fixture
def wildfire_scenario():
    """Create a wildfire scenario."""
    return Scenario(
        id="scenario-wildfire",
        name="California Wildfire",
        scenario_type=ScenarioType.WILDFIRE,
        severity="high",
        time_horizon="12m",
        created_at=datetime.now()
    )


class TestPhysicalRiskScore:
    """Tests for physical risk score calculation."""
    
    def test_compute_physical_score_hurricane_coastal(self, engine, base_holding, hurricane_scenario):
        """Test physical score for hurricane scenario in coastal location."""
        # Houston is coastal and in hurricane zone
        score = engine.compute_physical_score(base_holding, hurricane_scenario)
        
        assert 0 <= score <= 100
        assert score > 50  # Should be high risk for Houston + hurricane
        assert isinstance(score, float)
    
    def test_compute_physical_score_wildfire_california(self, engine, wildfire_scenario):
        """Test physical score for wildfire scenario in California."""
        california_holding = Holding(
            id="test-ca",
            portfolio_id="test-portfolio",
            asset_id="CA001",
            asset_name="California Property",
            asset_type="Real Estate",
            issuer_name="Test",
            sector="Real Estate",
            country="USA",
            state_region="California",
            latitude=37.7749,  # San Francisco
            longitude=-122.4194,
            market_value=Decimal("2000000.00"),
            created_at=datetime.now()
        )
        
        score = engine.compute_physical_score(california_holding, wildfire_scenario)
        
        assert 0 <= score <= 100
        assert score > 40  # Should have elevated wildfire risk
    
    def test_compute_physical_score_severity_impact(self, engine, base_holding):
        """Test that severity affects physical score."""
        low_severity = Scenario(
            id="low",
            name="Low Hurricane",
            scenario_type=ScenarioType.HURRICANE,
            severity="low",
            time_horizon="12m",
            created_at=datetime.now()
        )
        
        high_severity = Scenario(
            id="high",
            name="High Hurricane",
            scenario_type=ScenarioType.HURRICANE,
            severity="high",
            time_horizon="12m",
            created_at=datetime.now()
        )
        
        low_score = engine.compute_physical_score(base_holding, low_severity)
        high_score = engine.compute_physical_score(base_holding, high_severity)
        
        assert high_score > low_score
    
    def test_compute_physical_score_normalized(self, engine, base_holding, hurricane_scenario):
        """Test that physical score is normalized to 0-100."""
        score = engine.compute_physical_score(base_holding, hurricane_scenario)
        
        assert 0 <= score <= 100
        assert score == round(score, 2)  # Should be rounded to 2 decimals
    
    def test_compute_physical_score_missing_coordinates(self, engine, hurricane_scenario):
        """Test physical score with default coordinates (0, 0)."""
        holding_default_coords = Holding(
            id="test-default-coords",
            portfolio_id="test-portfolio",
            asset_id="DEFCOORD",
            asset_name="Default Coordinates",
            asset_type="Bond",
            issuer_name="Test",
            sector="Financials",
            country="USA",
            latitude=0.0,  # Default coordinates
            longitude=0.0,
            market_value=Decimal("1000000.00"),
            created_at=datetime.now()
        )
        
        score = engine.compute_physical_score(holding_default_coords, hurricane_scenario)
        
        assert 0 <= score <= 100
        # Should still return a valid score even with default coordinates


class TestTransitionRiskScore:
    """Tests for transition risk score calculation."""
    
    def test_compute_transition_score_high_carbon_sector(self, engine, complete_holding, carbon_tax_scenario):
        """Test transition score for high-carbon sector."""
        # Energy sector with high carbon intensity
        score = engine.compute_transition_score(complete_holding, carbon_tax_scenario)
        
        assert 0 <= score <= 100
        assert score > 50  # Should be high for Energy sector with carbon intensity
    
    def test_compute_transition_score_low_carbon_sector(self, engine, carbon_tax_scenario):
        """Test transition score for low-carbon sector."""
        tech_holding = Holding(
            id="test-tech",
            portfolio_id="test-portfolio",
            asset_id="TECH001",
            asset_name="Tech Company",
            asset_type="Equity",
            issuer_name="Tech Corp",
            sector="Technology",
            country="USA",
            latitude=37.7749,
            longitude=-122.4194,
            market_value=Decimal("3000000.00"),
            carbon_intensity_proxy=Decimal("10.0"),  # Low carbon
            created_at=datetime.now()
        )
        
        score = engine.compute_transition_score(tech_holding, carbon_tax_scenario)
        
        assert 0 <= score <= 100
        assert score < 40  # Should be lower for tech sector
    
    def test_compute_transition_score_missing_carbon_data(self, engine, base_holding, carbon_tax_scenario):
        """Test transition score with missing carbon intensity."""
        score = engine.compute_transition_score(base_holding, carbon_tax_scenario)
        
        assert 0 <= score <= 100
        # Should use default value
    
    def test_compute_transition_score_severity_amplification(self, engine, complete_holding):
        """Test that severity amplifies transition score for policy scenarios."""
        low_severity = Scenario(
            id="low-tax",
            name="Low Carbon Tax",
            scenario_type=ScenarioType.CARBON_TAX,
            severity="low",
            time_horizon="12m",
            created_at=datetime.now()
        )
        
        high_severity = Scenario(
            id="high-tax",
            name="High Carbon Tax",
            scenario_type=ScenarioType.CARBON_TAX,
            severity="high",
            time_horizon="12m",
            created_at=datetime.now()
        )
        
        low_score = engine.compute_transition_score(complete_holding, low_severity)
        high_score = engine.compute_transition_score(complete_holding, high_severity)
        
        assert high_score > low_score
    
    def test_compute_transition_score_normalized(self, engine, complete_holding, carbon_tax_scenario):
        """Test that transition score is normalized to 0-100."""
        score = engine.compute_transition_score(complete_holding, carbon_tax_scenario)
        
        assert 0 <= score <= 100
        assert score == round(score, 2)


class TestCombinedRiskScore:
    """Tests for combined risk score calculation."""
    
    def test_compute_combined_score_weights(self, engine):
        """Test that combined score uses correct weights."""
        physical = 80.0
        transition = 40.0
        
        combined = engine.compute_combined_score(physical, transition)
        
        # Expected: 0.65 * 80 + 0.35 * 40 = 52 + 14 = 66
        expected = 66.0
        assert combined == expected
    
    def test_compute_combined_score_high_physical(self, engine):
        """Test combined score with high physical risk."""
        combined = engine.compute_combined_score(100.0, 0.0)
        
        # Expected: 0.65 * 100 = 65
        assert combined == 65.0
    
    def test_compute_combined_score_high_transition(self, engine):
        """Test combined score with high transition risk."""
        combined = engine.compute_combined_score(0.0, 100.0)
        
        # Expected: 0.35 * 100 = 35
        assert combined == 35.0
    
    def test_compute_combined_score_balanced(self, engine):
        """Test combined score with balanced risks."""
        combined = engine.compute_combined_score(50.0, 50.0)
        
        # Expected: 0.65 * 50 + 0.35 * 50 = 32.5 + 17.5 = 50
        assert combined == 50.0
    
    def test_compute_combined_score_rounded(self, engine):
        """Test that combined score is rounded to 2 decimals."""
        combined = engine.compute_combined_score(33.333, 66.666)
        
        assert combined == round(combined, 2)


class TestConfidenceAssignment:
    """Tests for confidence level assignment."""
    
    def test_assign_confidence_high(self, engine, complete_holding):
        """Test high confidence when all optional fields present."""
        confidence = engine.assign_confidence(complete_holding)
        
        assert confidence == ConfidenceLevel.HIGH
    
    def test_assign_confidence_low(self, engine, base_holding):
        """Test low confidence when no optional fields present."""
        confidence = engine.assign_confidence(base_holding)
        
        assert confidence == ConfidenceLevel.LOW
    
    def test_assign_confidence_medium(self, engine):
        """Test medium confidence when some optional fields present."""
        partial_holding = Holding(
            id="test-partial",
            portfolio_id="test-portfolio",
            asset_id="PARTIAL",
            asset_name="Partial Data",
            asset_type="Bond",
            issuer_name="Test",
            sector="Financials",
            country="USA",
            latitude=40.7128,
            longitude=-74.0060,
            market_value=Decimal("2000000.00"),
            carbon_intensity_proxy=Decimal("100.0"),
            insurance_dependency_score=Decimal("50.0"),
            # Missing: revenue_exposure_pct, supply_chain_dependency_score
            created_at=datetime.now()
        )
        
        confidence = engine.assign_confidence(partial_holding)
        
        assert confidence == ConfidenceLevel.MEDIUM


class TestIntegration:
    """Integration tests for complete risk assessment workflow."""
    
    def test_complete_risk_assessment_hurricane(self, engine, complete_holding, hurricane_scenario):
        """Test complete risk assessment for hurricane scenario."""
        physical = engine.compute_physical_score(complete_holding, hurricane_scenario)
        transition = engine.compute_transition_score(complete_holding, hurricane_scenario)
        combined = engine.compute_combined_score(physical, transition)
        confidence = engine.assign_confidence(complete_holding)
        
        assert 0 <= physical <= 100
        assert 0 <= transition <= 100
        assert 0 <= combined <= 100
        assert confidence == ConfidenceLevel.HIGH
        
        # Combined should be weighted average
        expected_combined = round(0.65 * physical + 0.35 * transition, 2)
        assert combined == expected_combined
    
    def test_complete_risk_assessment_carbon_tax(self, engine, complete_holding, carbon_tax_scenario):
        """Test complete risk assessment for carbon tax scenario."""
        physical = engine.compute_physical_score(complete_holding, carbon_tax_scenario)
        transition = engine.compute_transition_score(complete_holding, carbon_tax_scenario)
        combined = engine.compute_combined_score(physical, transition)
        confidence = engine.assign_confidence(complete_holding)
        
        # For carbon tax, transition risk should be significant
        assert transition > 40
        assert confidence == ConfidenceLevel.HIGH
    
    def test_sector_comparison(self, engine, carbon_tax_scenario):
        """Test that different sectors produce different transition scores."""
        energy_holding = Holding(
            id="energy",
            portfolio_id="test",
            asset_id="E001",
            asset_name="Energy Asset",
            asset_type="Equity",
            issuer_name="Energy Corp",
            sector="Energy",
            country="USA",
            latitude=30.0,
            longitude=-95.0,
            market_value=Decimal("1000000.00"),
            carbon_intensity_proxy=Decimal("300.0"),
            created_at=datetime.now()
        )
        
        tech_holding = Holding(
            id="tech",
            portfolio_id="test",
            asset_id="T001",
            asset_name="Tech Asset",
            asset_type="Equity",
            issuer_name="Tech Corp",
            sector="Technology",
            country="USA",
            latitude=37.7749,
            longitude=-122.4194,
            market_value=Decimal("1000000.00"),
            carbon_intensity_proxy=Decimal("20.0"),
            created_at=datetime.now()
        )
        
        energy_score = engine.compute_transition_score(energy_holding, carbon_tax_scenario)
        tech_score = engine.compute_transition_score(tech_holding, carbon_tax_scenario)
        
        assert energy_score > tech_score
