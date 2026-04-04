"""Unit tests for Financial Impact Engine"""

import pytest
from decimal import Decimal
from datetime import datetime

from app.engines.financial_impact import FinancialImpactEngine, ConcentrationMetrics
from app.schemas.holding import Holding
from app.schemas.scenario import Scenario
from app.schemas.enums import ScenarioType


@pytest.fixture
def engine():
    """Create a Financial Impact Engine instance"""
    return FinancialImpactEngine()


@pytest.fixture
def sample_holding():
    """Create a sample holding for testing"""
    return Holding(
        id="h1",
        portfolio_id="p1",
        asset_id="ASSET001",
        asset_name="Houston Office Complex",
        asset_type="Real Estate",
        issuer_name="Example REIT",
        sector="Real Estate",
        country="USA",
        state_region="Texas",
        latitude=29.7604,
        longitude=-95.3698,
        market_value=Decimal("5000000.00"),
        revenue_exposure_pct=Decimal("15.5"),
        carbon_intensity_proxy=Decimal("120.5"),
        insurance_dependency_score=Decimal("75.0"),
        supply_chain_dependency_score=Decimal("60.0"),
        created_at=datetime.now()
    )


@pytest.fixture
def high_risk_scenario():
    """Create a high severity hurricane scenario"""
    return Scenario(
        id="s1",
        name="Hurricane Category 5",
        scenario_type=ScenarioType.HURRICANE,
        severity="high",
        time_horizon="12m",
        parameters={"wind_speed_mph": 160},
        created_at=datetime.now()
    )


@pytest.fixture
def medium_risk_scenario():
    """Create a medium severity flood scenario"""
    return Scenario(
        id="s2",
        name="Coastal Flood",
        scenario_type=ScenarioType.FLOOD,
        severity="medium",
        time_horizon="12m",
        parameters={},
        created_at=datetime.now()
    )


class TestExpectedLossCalculation:
    """Tests for expected loss calculation"""
    
    def test_calculate_expected_loss_basic(self, engine, sample_holding, medium_risk_scenario):
        """Test basic expected loss calculation"""
        combined_risk_score = 50.0
        
        expected_loss = engine.calculate_expected_loss(
            sample_holding,
            combined_risk_score,
            medium_risk_scenario
        )
        
        # Expected loss should be positive and less than market value
        assert expected_loss > 0
        assert expected_loss < float(sample_holding.market_value)
    
    def test_calculate_expected_loss_high_risk(self, engine, sample_holding, high_risk_scenario):
        """Test expected loss with high risk score"""
        combined_risk_score = 85.0
        
        expected_loss = engine.calculate_expected_loss(
            sample_holding,
            combined_risk_score,
            high_risk_scenario
        )
        
        # High risk should result in higher loss
        assert expected_loss > 0
        # With high risk and high severity, loss should be substantial
        assert expected_loss > float(sample_holding.market_value) * 0.1
    
    def test_calculate_expected_loss_zero_risk(self, engine, sample_holding, medium_risk_scenario):
        """Test expected loss with zero risk score"""
        combined_risk_score = 0.0
        
        expected_loss = engine.calculate_expected_loss(
            sample_holding,
            combined_risk_score,
            medium_risk_scenario
        )
        
        # Zero risk should result in zero or minimal loss
        assert expected_loss >= 0
        assert expected_loss < float(sample_holding.market_value) * 0.01
    
    def test_calculate_expected_loss_no_insurance_score(self, engine, high_risk_scenario):
        """Test expected loss when insurance dependency score is missing"""
        holding = Holding(
            id="h2",
            portfolio_id="p1",
            asset_id="ASSET002",
            asset_name="Test Asset",
            asset_type="Equity",
            issuer_name="Test Corp",
            sector="Technology",
            country="USA",
            latitude=37.7749,
            longitude=-122.4194,
            market_value=Decimal("1000000.00"),
            insurance_dependency_score=None,  # Missing
            created_at=datetime.now()
        )
        
        combined_risk_score = 60.0
        expected_loss = engine.calculate_expected_loss(holding, combined_risk_score, high_risk_scenario)
        
        # Should still calculate loss with default insurance gap factor
        assert expected_loss > 0
    
    def test_damage_ratio_increases_with_severity(self, engine, sample_holding):
        """Test that damage ratio increases with scenario severity"""
        combined_risk_score = 70.0
        
        low_scenario = Scenario(
            id="s_low",
            name="Low Severity",
            scenario_type=ScenarioType.FLOOD,
            severity="low",
            time_horizon="12m",
            created_at=datetime.now()
        )
        
        high_scenario = Scenario(
            id="s_high",
            name="High Severity",
            scenario_type=ScenarioType.FLOOD,
            severity="high",
            time_horizon="12m",
            created_at=datetime.now()
        )
        
        loss_low = engine.calculate_expected_loss(sample_holding, combined_risk_score, low_scenario)
        loss_high = engine.calculate_expected_loss(sample_holding, combined_risk_score, high_scenario)
        
        # High severity should result in higher loss
        assert loss_high > loss_low


class TestPortfolioVaR:
    """Tests for portfolio climate VaR calculation"""
    
    def test_compute_portfolio_var_single_holding(self, engine, sample_holding, medium_risk_scenario):
        """Test portfolio VaR with single holding"""
        holdings = [sample_holding]
        risk_scores = {sample_holding.id: 50.0}
        
        portfolio_var = engine.compute_portfolio_var(holdings, risk_scores, medium_risk_scenario)
        
        # VaR should equal the expected loss of the single holding
        expected_loss = engine.calculate_expected_loss(sample_holding, 50.0, medium_risk_scenario)
        assert portfolio_var == expected_loss
    
    def test_compute_portfolio_var_multiple_holdings(self, engine, medium_risk_scenario):
        """Test portfolio VaR with multiple holdings"""
        holdings = [
            Holding(
                id="h1",
                portfolio_id="p1",
                asset_id="ASSET001",
                asset_name="Asset 1",
                asset_type="Real Estate",
                issuer_name="Issuer A",
                sector="Real Estate",
                country="USA",
                latitude=29.76,
                longitude=-95.37,
                market_value=Decimal("1000000.00"),
                insurance_dependency_score=Decimal("50.0"),
                created_at=datetime.now()
            ),
            Holding(
                id="h2",
                portfolio_id="p1",
                asset_id="ASSET002",
                asset_name="Asset 2",
                asset_type="Equity",
                issuer_name="Issuer B",
                sector="Technology",
                country="USA",
                latitude=37.77,
                longitude=-122.42,
                market_value=Decimal("2000000.00"),
                insurance_dependency_score=Decimal("30.0"),
                created_at=datetime.now()
            ),
        ]
        
        risk_scores = {"h1": 60.0, "h2": 40.0}
        
        portfolio_var = engine.compute_portfolio_var(holdings, risk_scores, medium_risk_scenario)
        
        # VaR should be sum of individual expected losses
        loss1 = engine.calculate_expected_loss(holdings[0], 60.0, medium_risk_scenario)
        loss2 = engine.calculate_expected_loss(holdings[1], 40.0, medium_risk_scenario)
        expected_total = loss1 + loss2
        
        assert portfolio_var == expected_total
    
    def test_compute_portfolio_var_empty_portfolio(self, engine, medium_risk_scenario):
        """Test portfolio VaR with empty portfolio"""
        holdings = []
        risk_scores = {}
        
        portfolio_var = engine.compute_portfolio_var(holdings, risk_scores, medium_risk_scenario)
        
        assert portfolio_var == 0.0


class TestStressedDrawdown:
    """Tests for stressed drawdown calculation"""
    
    def test_calculate_stressed_drawdown_basic(self, engine):
        """Test basic stressed drawdown calculation"""
        portfolio_var = 1000000.0
        total_value = 10000000.0
        
        drawdown = engine.calculate_stressed_drawdown(portfolio_var, total_value)
        
        # Should be 10%
        assert drawdown == 10.0
    
    def test_calculate_stressed_drawdown_high_loss(self, engine):
        """Test stressed drawdown with high loss"""
        portfolio_var = 5000000.0
        total_value = 10000000.0
        
        drawdown = engine.calculate_stressed_drawdown(portfolio_var, total_value)
        
        # Should be 50%
        assert drawdown == 50.0
    
    def test_calculate_stressed_drawdown_zero_portfolio(self, engine):
        """Test stressed drawdown with zero portfolio value"""
        portfolio_var = 1000000.0
        total_value = 0.0
        
        drawdown = engine.calculate_stressed_drawdown(portfolio_var, total_value)
        
        # Should return 0 to avoid division by zero
        assert drawdown == 0.0
    
    def test_calculate_stressed_drawdown_capped_at_100(self, engine):
        """Test that drawdown is capped at 100%"""
        portfolio_var = 15000000.0
        total_value = 10000000.0
        
        drawdown = engine.calculate_stressed_drawdown(portfolio_var, total_value)
        
        # Should be capped at 100%
        assert drawdown == 100.0


class TestIssuerAggregation:
    """Tests for issuer-level loss aggregation"""
    
    def test_aggregate_by_issuer_single_issuer(self, engine, medium_risk_scenario):
        """Test aggregation with single issuer"""
        holdings = [
            Holding(
                id="h1",
                portfolio_id="p1",
                asset_id="ASSET001",
                asset_name="Asset 1",
                asset_type="Real Estate",
                issuer_name="Issuer A",
                sector="Real Estate",
                country="USA",
                latitude=29.76,
                longitude=-95.37,
                market_value=Decimal("1000000.00"),
                insurance_dependency_score=Decimal("50.0"),
                created_at=datetime.now()
            ),
        ]
        
        risk_scores = {"h1": 50.0}
        
        issuer_data = engine.aggregate_by_issuer(holdings, risk_scores, medium_risk_scenario)
        
        assert "Issuer A" in issuer_data
        assert issuer_data["Issuer A"]["holdings_count"] == 1
        assert issuer_data["Issuer A"]["total_market_value"] == 1000000.0
        assert issuer_data["Issuer A"]["aggregated_loss"] > 0
        assert issuer_data["Issuer A"]["loss_percentage"] > 0
    
    def test_aggregate_by_issuer_multiple_holdings_same_issuer(self, engine, medium_risk_scenario):
        """Test aggregation with multiple holdings from same issuer"""
        holdings = [
            Holding(
                id="h1",
                portfolio_id="p1",
                asset_id="ASSET001",
                asset_name="Asset 1",
                asset_type="Real Estate",
                issuer_name="Issuer A",
                sector="Real Estate",
                country="USA",
                latitude=29.76,
                longitude=-95.37,
                market_value=Decimal("1000000.00"),
                insurance_dependency_score=Decimal("50.0"),
                created_at=datetime.now()
            ),
            Holding(
                id="h2",
                portfolio_id="p1",
                asset_id="ASSET002",
                asset_name="Asset 2",
                asset_type="Real Estate",
                issuer_name="Issuer A",
                sector="Real Estate",
                country="USA",
                latitude=30.27,
                longitude=-97.74,
                market_value=Decimal("2000000.00"),
                insurance_dependency_score=Decimal("60.0"),
                created_at=datetime.now()
            ),
        ]
        
        risk_scores = {"h1": 50.0, "h2": 60.0}
        
        issuer_data = engine.aggregate_by_issuer(holdings, risk_scores, medium_risk_scenario)
        
        assert "Issuer A" in issuer_data
        assert issuer_data["Issuer A"]["holdings_count"] == 2
        assert issuer_data["Issuer A"]["total_market_value"] == 3000000.0
        
        # Aggregated loss should be sum of individual losses
        loss1 = engine.calculate_expected_loss(holdings[0], 50.0, medium_risk_scenario)
        loss2 = engine.calculate_expected_loss(holdings[1], 60.0, medium_risk_scenario)
        expected_total_loss = loss1 + loss2
        
        assert issuer_data["Issuer A"]["aggregated_loss"] == expected_total_loss
    
    def test_aggregate_by_issuer_multiple_issuers(self, engine, medium_risk_scenario):
        """Test aggregation with multiple issuers"""
        holdings = [
            Holding(
                id="h1",
                portfolio_id="p1",
                asset_id="ASSET001",
                asset_name="Asset 1",
                asset_type="Real Estate",
                issuer_name="Issuer A",
                sector="Real Estate",
                country="USA",
                latitude=29.76,
                longitude=-95.37,
                market_value=Decimal("1000000.00"),
                insurance_dependency_score=Decimal("50.0"),
                created_at=datetime.now()
            ),
            Holding(
                id="h2",
                portfolio_id="p1",
                asset_id="ASSET002",
                asset_name="Asset 2",
                asset_type="Equity",
                issuer_name="Issuer B",
                sector="Technology",
                country="USA",
                latitude=37.77,
                longitude=-122.42,
                market_value=Decimal("2000000.00"),
                insurance_dependency_score=Decimal("30.0"),
                created_at=datetime.now()
            ),
        ]
        
        risk_scores = {"h1": 50.0, "h2": 40.0}
        
        issuer_data = engine.aggregate_by_issuer(holdings, risk_scores, medium_risk_scenario)
        
        assert len(issuer_data) == 2
        assert "Issuer A" in issuer_data
        assert "Issuer B" in issuer_data
        assert issuer_data["Issuer A"]["holdings_count"] == 1
        assert issuer_data["Issuer B"]["holdings_count"] == 1


class TestConcentrationRisk:
    """Tests for concentration risk calculation"""
    
    def test_compute_concentration_risk_diversified(self, engine):
        """Test concentration risk with well-diversified portfolio"""
        # Create 20 holdings with good diversification
        holdings = [
            Holding(
                id=f"h{i}",
                portfolio_id="p1",
                asset_id=f"ASSET{i:03d}",
                asset_name=f"Asset {i}",
                asset_type="Equity",
                issuer_name=f"Issuer {i}",  # 20 different issuers (5% each)
                sector=f"Sector {i % 5}",  # 5 different sectors (20% each)
                country="USA",
                state_region=f"State {i % 10}",  # 10 different states (10% each)
                latitude=30.0 + i,
                longitude=-95.0 + i,
                market_value=Decimal("1000000.00"),
                created_at=datetime.now()
            )
            for i in range(20)
        ]
        
        total_value = 20000000.0
        
        metrics = engine.compute_concentration_risk(holdings, total_value)
        
        # Each sector should have 20% (4 holdings each)
        assert len(metrics.sector_concentration) == 5
        for sector, pct in metrics.sector_concentration.items():
            assert pct == 20.0
        
        # Each state should have 10% (2 holdings each)
        assert len(metrics.geography_concentration) == 10
        for state, pct in metrics.geography_concentration.items():
            assert pct == 10.0
        
        # Each issuer should have 5% (1 holding each)
        assert len(metrics.issuer_concentration) == 20
        for issuer, pct in metrics.issuer_concentration.items():
            assert pct == 5.0
        
        # No penalties should be applied (all at or below thresholds)
        assert metrics.sector_penalty == 0.0
        assert metrics.geography_penalty == 0.0
        assert metrics.issuer_penalty == 0.0
        assert metrics.total_penalty == 0.0
    
    def test_compute_concentration_risk_sector_concentration(self, engine):
        """Test concentration risk with high sector concentration"""
        holdings = [
            Holding(
                id=f"h{i}",
                portfolio_id="p1",
                asset_id=f"ASSET{i:03d}",
                asset_name=f"Asset {i}",
                asset_type="Equity",
                issuer_name=f"Issuer {i}",
                sector="Technology" if i < 7 else "Healthcare",  # 70% in Technology
                country="USA",
                state_region=f"State {i % 5}",
                latitude=30.0 + i,
                longitude=-95.0 + i,
                market_value=Decimal("1000000.00"),
                created_at=datetime.now()
            )
            for i in range(10)
        ]
        
        total_value = 10000000.0
        
        metrics = engine.compute_concentration_risk(holdings, total_value)
        
        # Technology should have 70% concentration
        assert metrics.sector_concentration["Technology"] == 70.0
        
        # Sector penalty should be applied (exceeds 25% threshold)
        assert metrics.sector_penalty > 0.0
        assert metrics.total_penalty > 0.0
    
    def test_compute_concentration_risk_geography_concentration(self, engine):
        """Test concentration risk with high geographic concentration"""
        holdings = [
            Holding(
                id=f"h{i}",
                portfolio_id="p1",
                asset_id=f"ASSET{i:03d}",
                asset_name=f"Asset {i}",
                asset_type="Equity",
                issuer_name=f"Issuer {i}",
                sector=f"Sector {i % 5}",
                country="USA",
                state_region="Texas" if i < 8 else "California",  # 80% in Texas
                latitude=29.76,
                longitude=-95.37,
                market_value=Decimal("1000000.00"),
                created_at=datetime.now()
            )
            for i in range(10)
        ]
        
        total_value = 10000000.0
        
        metrics = engine.compute_concentration_risk(holdings, total_value)
        
        # Texas should have 80% concentration
        assert metrics.geography_concentration["Texas"] == 80.0
        
        # Geography penalty should be applied (exceeds 15% threshold)
        assert metrics.geography_penalty > 0.0
        assert metrics.total_penalty > 0.0
    
    def test_compute_concentration_risk_issuer_concentration(self, engine):
        """Test concentration risk with high issuer concentration"""
        holdings = [
            Holding(
                id=f"h{i}",
                portfolio_id="p1",
                asset_id=f"ASSET{i:03d}",
                asset_name=f"Asset {i}",
                asset_type="Equity",
                issuer_name="Big Corp" if i < 6 else f"Small Corp {i}",  # 60% in Big Corp
                sector=f"Sector {i % 5}",
                country="USA",
                state_region=f"State {i % 5}",
                latitude=30.0 + i,
                longitude=-95.0 + i,
                market_value=Decimal("1000000.00"),
                created_at=datetime.now()
            )
            for i in range(10)
        ]
        
        total_value = 10000000.0
        
        metrics = engine.compute_concentration_risk(holdings, total_value)
        
        # Big Corp should have 60% concentration
        assert metrics.issuer_concentration["Big Corp"] == 60.0
        
        # Issuer penalty should be applied (exceeds 5% threshold)
        assert metrics.issuer_penalty > 0.0
        assert metrics.total_penalty > 0.0
    
    def test_compute_concentration_risk_zero_portfolio(self, engine):
        """Test concentration risk with zero portfolio value"""
        holdings = []
        total_value = 0.0
        
        metrics = engine.compute_concentration_risk(holdings, total_value)
        
        # Should return empty metrics with no penalties
        assert len(metrics.sector_concentration) == 0
        assert len(metrics.geography_concentration) == 0
        assert len(metrics.issuer_concentration) == 0
        assert metrics.total_penalty == 0.0


class TestBusinessInterruptionFactor:
    """Tests for business interruption factor calculation"""
    
    def test_business_interruption_high_impact_sector(self, engine):
        """Test business interruption for high-impact sectors"""
        factor = engine._calculate_business_interruption_factor("Utilities", "Infrastructure")
        
        # Utilities with infrastructure should have high factor
        assert factor > 0.8
    
    def test_business_interruption_low_impact_sector(self, engine):
        """Test business interruption for low-impact sectors"""
        factor = engine._calculate_business_interruption_factor("Technology", "Equity")
        
        # Technology with equity should have lower factor
        assert factor < 0.5
    
    def test_business_interruption_unknown_sector(self, engine):
        """Test business interruption for unknown sector"""
        factor = engine._calculate_business_interruption_factor("Unknown Sector", "Unknown Type")
        
        # Should return default moderate factor
        assert 0.4 <= factor <= 0.6


class TestInsuranceGapFactor:
    """Tests for insurance gap factor calculation"""
    
    def test_insurance_gap_high_dependency(self, engine):
        """Test insurance gap with high dependency score"""
        factor = engine._calculate_insurance_gap_factor(Decimal("90.0"))
        
        # High dependency should result in higher gap factor
        assert factor > 0.9
    
    def test_insurance_gap_low_dependency(self, engine):
        """Test insurance gap with low dependency score"""
        factor = engine._calculate_insurance_gap_factor(Decimal("10.0"))
        
        # Low dependency should result in lower gap factor
        assert factor < 0.6
    
    def test_insurance_gap_no_data(self, engine):
        """Test insurance gap with missing data"""
        factor = engine._calculate_insurance_gap_factor(None)
        
        # Should return default moderate factor
        assert factor == 0.75
