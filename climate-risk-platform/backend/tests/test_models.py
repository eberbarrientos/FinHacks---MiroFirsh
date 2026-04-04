"""Tests for database models"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.scenario import Scenario
from app.schemas.enums import ScenarioType


class TestPortfolioModel:
    """Test Portfolio database model"""
    
    def test_create_portfolio(self, db_session):
        """Test creating a portfolio"""
        portfolio = Portfolio(
            name="Test Portfolio",
            base_currency="USD"
        )
        db_session.add(portfolio)
        db_session.commit()
        db_session.refresh(portfolio)
        
        assert portfolio.id is not None
        assert portfolio.name == "Test Portfolio"
        assert portfolio.base_currency == "USD"
        assert portfolio.created_at is not None
    
    def test_portfolio_name_required(self, db_session):
        """Test portfolio name is required"""
        portfolio = Portfolio(base_currency="USD")
        db_session.add(portfolio)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_portfolio_default_currency(self, db_session):
        """Test default currency is USD"""
        portfolio = Portfolio(name="Test Portfolio")
        db_session.add(portfolio)
        db_session.commit()
        db_session.refresh(portfolio)
        
        assert portfolio.base_currency == "USD"


class TestHoldingModel:
    """Test Holding database model"""
    
    def test_create_holding(self, db_session):
        """Test creating a holding"""
        # Create portfolio first
        portfolio = Portfolio(name="Test Portfolio")
        db_session.add(portfolio)
        db_session.commit()
        
        # Create holding
        holding = Holding(
            portfolio_id=portfolio.id,
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
        db_session.add(holding)
        db_session.commit()
        db_session.refresh(holding)
        
        assert holding.id is not None
        assert holding.portfolio_id == portfolio.id
        assert holding.asset_id == "ASSET001"
        assert holding.market_value == 1000000.00
    
    def test_holding_portfolio_relationship(self, db_session):
        """Test holding-portfolio relationship"""
        portfolio = Portfolio(name="Test Portfolio")
        db_session.add(portfolio)
        db_session.commit()
        
        holding = Holding(
            portfolio_id=portfolio.id,
            asset_id="ASSET001",
            asset_name="Test Asset",
            issuer_name="Test Corp",
            sector="Utilities",
            country="USA",
            market_value=1000000.00
        )
        db_session.add(holding)
        db_session.commit()
        
        # Test relationship
        assert holding.portfolio.id == portfolio.id
        assert len(portfolio.holdings) == 1
        assert portfolio.holdings[0].id == holding.id
    
    def test_cascade_delete(self, db_session):
        """Test holdings are deleted when portfolio is deleted"""
        portfolio = Portfolio(name="Test Portfolio")
        db_session.add(portfolio)
        db_session.commit()
        
        holding = Holding(
            portfolio_id=portfolio.id,
            asset_id="ASSET001",
            asset_name="Test Asset",
            issuer_name="Test Corp",
            sector="Utilities",
            country="USA",
            market_value=1000000.00
        )
        db_session.add(holding)
        db_session.commit()
        
        holding_id = holding.id
        
        # Delete portfolio
        db_session.delete(portfolio)
        db_session.commit()
        
        # Verify holding is also deleted
        deleted_holding = db_session.query(Holding).filter(Holding.id == holding_id).first()
        assert deleted_holding is None


class TestScenarioModel:
    """Test Scenario database model"""
    
    def test_create_scenario(self, db_session):
        """Test creating a scenario"""
        scenario = Scenario(
            name="Hurricane Test",
            scenario_type=ScenarioType.HURRICANE.value,
            severity="high",
            time_horizon="12m"
        )
        db_session.add(scenario)
        db_session.commit()
        db_session.refresh(scenario)
        
        assert scenario.id is not None
        assert scenario.name == "Hurricane Test"
        assert scenario.scenario_type == "hurricane"
        assert scenario.severity == "high"
    
    def test_scenario_with_parameters(self, db_session):
        """Test scenario with JSON parameters"""
        scenario = Scenario(
            name="Custom Scenario",
            scenario_type=ScenarioType.COMPOUND.value,
            severity="high",
            time_horizon="24m",
            parameters_json={"wind_speed": 150, "affected_regions": ["Gulf Coast"]}
        )
        db_session.add(scenario)
        db_session.commit()
        db_session.refresh(scenario)
        
        assert scenario.parameters_json["wind_speed"] == 150
        assert "Gulf Coast" in scenario.parameters_json["affected_regions"]
