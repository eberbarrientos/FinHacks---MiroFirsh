"""Tests for reports API endpoints"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal

from app.main import app
from app.models.portfolio import Portfolio as PortfolioModel
from app.models.holding import Holding as HoldingModel
from app.models.scenario import Scenario as ScenarioModel
from app.models.risk_result import RiskResult as RiskResultModel


client = TestClient(app)


class TestReportsAPI:
    """Test suite for reports API endpoints"""
    
    def test_generate_executive_report_success(self, db_session):
        """Test successful executive report generation"""
        # Create test data
        portfolio = PortfolioModel(
            id="test-portfolio-id",
            name="Test Portfolio",
            base_currency="USD"
        )
        db_session.add(portfolio)
        
        scenario = ScenarioModel(
            id="test-scenario-id",
            name="Test Scenario",
            scenario_type="hurricane",
            severity="high",
            time_horizon="12m"
        )
        db_session.add(scenario)
        
        holding = HoldingModel(
            id="test-holding-id",
            portfolio_id="test-portfolio-id",
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
            id="test-risk-id",
            portfolio_id="test-portfolio-id",
            holding_id="test-holding-id",
            scenario_id="test-scenario-id",
            physical_score=Decimal("75.5"),
            transition_score=Decimal("45.2"),
            combined_score=Decimal("65.0"),
            expected_loss=Decimal("50000.00"),
            stressed_return_delta=Decimal("0.0"),
            confidence="high"
        )
        db_session.add(risk_result)
        
        db_session.commit()
        
        # Make request
        response = client.get(
            "/api/reports/executive",
            params={
                "portfolio_id": "test-portfolio-id",
                "scenario_id": "test-scenario-id"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert len(response.content) > 0
    
    def test_generate_executive_report_missing_portfolio(self, db_session):
        """Test error handling for missing portfolio"""
        response = client.get(
            "/api/reports/executive",
            params={
                "portfolio_id": "nonexistent-id",
                "scenario_id": "scenario-id"
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_generate_executive_report_missing_scenario(self, db_session):
        """Test error handling for missing scenario"""
        # Create portfolio but not scenario
        portfolio = PortfolioModel(
            id="test-portfolio-id",
            name="Test Portfolio",
            base_currency="USD"
        )
        db_session.add(portfolio)
        db_session.commit()
        
        response = client.get(
            "/api/reports/executive",
            params={
                "portfolio_id": "test-portfolio-id",
                "scenario_id": "nonexistent-scenario-id"
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_generate_executive_report_missing_params(self):
        """Test error handling for missing query parameters"""
        # Missing scenario_id
        response = client.get(
            "/api/reports/executive",
            params={"portfolio_id": "test-id"}
        )
        assert response.status_code == 422
        
        # Missing portfolio_id
        response = client.get(
            "/api/reports/executive",
            params={"scenario_id": "test-id"}
        )
        assert response.status_code == 422
        
        # Missing both
        response = client.get("/api/reports/executive")
        assert response.status_code == 422
