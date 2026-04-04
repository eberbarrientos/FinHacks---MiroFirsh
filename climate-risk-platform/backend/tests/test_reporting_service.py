"""Tests for reporting service"""

import pytest
import uuid
from unittest.mock import Mock, MagicMock
from decimal import Decimal
from datetime import datetime

from app.services.reporting import ReportingService
from app.models.portfolio import Portfolio as PortfolioModel
from app.models.holding import Holding as HoldingModel
from app.models.scenario import Scenario as ScenarioModel
from app.models.risk_result import RiskResult as RiskResultModel
from app.models.recommendation import Recommendation as RecommendationModel


class TestReportingService:
    """Test suite for ReportingService"""
    
    def test_gather_report_data(self, db_session):
        """Test gathering report data from database"""
        # Generate proper UUIDs
        portfolio_id = str(uuid.uuid4())
        scenario_id = str(uuid.uuid4())
        holding_id = str(uuid.uuid4())
        risk_id = str(uuid.uuid4())
        
        # Create test data
        portfolio = PortfolioModel(
            id=portfolio_id,
            name="Test Portfolio",
            base_currency="USD"
        )
        db_session.add(portfolio)
        
        scenario = ScenarioModel(
            id=scenario_id,
            name="Test Scenario",
            scenario_type="hurricane",
            severity="high",
            time_horizon="12m"
        )
        db_session.add(scenario)
        
        holding = HoldingModel(
            id=holding_id,
            portfolio_id=portfolio_id,
            asset_id="ASSET001",
            asset_name="Test Asset",
            asset_type="Real Estate",
            issuer_name="Test Issuer",
            sector="Real Estate",
            country="USA",
            latitude=29.7604,
            longitude=-95.3698,
            market_value=Decimal("1000000.00")
        )
        db_session.add(holding)
        
        risk_result = RiskResultModel(
            id=risk_id,
            portfolio_id=portfolio_id,
            holding_id=holding_id,
            scenario_id=scenario_id,
            physical_score=Decimal("75.5"),
            transition_score=Decimal("45.2"),
            combined_score=Decimal("65.0"),
            expected_loss=Decimal("50000.00"),
            stressed_return_delta=Decimal("0.0"),
            confidence="high"
        )
        db_session.add(risk_result)
        
        db_session.commit()
        
        # Test gathering data
        service = ReportingService(db_session)
        report_data = service._gather_report_data(portfolio_id, scenario_id)
        
        # Verify metadata
        assert report_data["metadata"]["portfolio_name"] == "Test Portfolio"
        assert report_data["metadata"]["scenario_name"] == "Test Scenario"
        assert "generation_date" in report_data["metadata"]
        
        # Verify portfolio summary
        assert report_data["portfolio_summary"]["total_value"] == 1000000.0
        assert report_data["portfolio_summary"]["holdings_count"] == 1
        assert report_data["portfolio_summary"]["climate_var"] == 50000.0
        
        # Verify risk scores
        assert report_data["risk_scores"]["average_combined_score"] == 65.0
        
        # Verify holdings
        assert len(report_data["holdings"]) == 1
        assert report_data["holdings"][0]["asset_name"] == "Test Asset"
    
    def test_calculate_sector_breakdown(self, db_session):
        """Test sector breakdown calculation"""
        # Create test holdings
        holdings = [
            HoldingModel(
                id="h1",
                portfolio_id="p1",
                asset_id="A1",
                asset_name="Asset 1",
                asset_type="Real Estate",
                issuer_name="Issuer 1",
                sector="Utilities",
                country="USA",
                latitude=29.7604,
                longitude=-95.3698,
                market_value=Decimal("1000000.00")
            ),
            HoldingModel(
                id="h2",
                portfolio_id="p1",
                asset_id="A2",
                asset_name="Asset 2",
                asset_type="Real Estate",
                issuer_name="Issuer 2",
                sector="Utilities",
                country="USA",
                latitude=29.7604,
                longitude=-95.3698,
                market_value=Decimal("2000000.00")
            ),
        ]
        
        risk_results = [
            RiskResultModel(
                id="r1",
                portfolio_id="p1",
                holding_id="h1",
                scenario_id="s1",
                physical_score=Decimal("75.0"),
                transition_score=Decimal("45.0"),
                combined_score=Decimal("65.0"),
                expected_loss=Decimal("50000.00"),
                stressed_return_delta=Decimal("0.0"),
                confidence="high"
            ),
            RiskResultModel(
                id="r2",
                portfolio_id="p1",
                holding_id="h2",
                scenario_id="s1",
                physical_score=Decimal("80.0"),
                transition_score=Decimal("50.0"),
                combined_score=Decimal("70.0"),
                expected_loss=Decimal("100000.00"),
                stressed_return_delta=Decimal("0.0"),
                confidence="high"
            ),
        ]
        
        service = ReportingService(db_session)
        sector_breakdown = service._calculate_sector_breakdown(holdings, risk_results)
        
        # Verify sector aggregation
        assert "Utilities" in sector_breakdown
        assert sector_breakdown["Utilities"]["total_value"] == 3000000.0
        assert sector_breakdown["Utilities"]["holdings_count"] == 2
        assert sector_breakdown["Utilities"]["total_loss"] == 150000.0
        assert sector_breakdown["Utilities"]["avg_risk_score"] == 67.5  # (65 + 70) / 2
    
    def test_render_charts_without_matplotlib(self, db_session):
        """Test chart rendering gracefully handles missing matplotlib"""
        service = ReportingService(db_session)
        
        report_data = {
            "sector_breakdown": {},
            "risk_scores": {},
            "geographic_breakdown": {}
        }
        
        # Should return empty dict if matplotlib not available
        charts = service.render_charts(report_data)
        assert isinstance(charts, dict)
    
    def test_generate_executive_report_missing_portfolio(self, db_session):
        """Test error handling for missing portfolio"""
        service = ReportingService(db_session)
        
        # Use proper UUID format
        nonexistent_portfolio_id = str(uuid.uuid4())
        nonexistent_scenario_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="Portfolio .* not found"):
            service.generate_executive_report(nonexistent_portfolio_id, nonexistent_scenario_id)
    
    def test_generate_executive_report_missing_scenario(self, db_session):
        """Test error handling for missing scenario"""
        # Generate proper UUIDs
        portfolio_id = str(uuid.uuid4())
        nonexistent_scenario_id = str(uuid.uuid4())
        
        # Create portfolio but not scenario
        portfolio = PortfolioModel(
            id=portfolio_id,
            name="Test Portfolio",
            base_currency="USD"
        )
        db_session.add(portfolio)
        db_session.commit()
        
        service = ReportingService(db_session)
        
        with pytest.raises(ValueError, match="Scenario .* not found"):
            service.generate_executive_report(portfolio_id, nonexistent_scenario_id)
