"""Tests for risk calculation API endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal

from app.main import app
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.scenario import Scenario


@pytest.fixture
def test_scenario(db: Session) -> Scenario:
    """Create a test scenario"""
    scenario = Scenario(
        name="Test Hurricane Scenario",
        scenario_type="hurricane",
        severity="high",
        time_horizon="12m",
        parameters_json={"affected_regions": ["Texas Gulf"]}
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@pytest.fixture
def test_portfolio_with_holdings(db: Session) -> Portfolio:
    """Create a test portfolio with holdings"""
    # Create portfolio
    portfolio = Portfolio(
        name="Test Portfolio",
        base_currency="USD"
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    # Create holdings
    holdings = [
        Holding(
            portfolio_id=portfolio.id,
            asset_id="ASSET001",
            asset_name="Houston Energy Plant",
            asset_type="Infrastructure",
            issuer_name="Energy Corp",
            sector="Utilities",
            country="USA",
            state_region="Texas",
            latitude=Decimal("29.7604"),
            longitude=Decimal("-95.3698"),
            market_value=Decimal("10000000.00"),
            carbon_intensity_proxy=Decimal("450.0"),
            insurance_dependency_score=Decimal("75.0"),
        ),
        Holding(
            portfolio_id=portfolio.id,
            asset_id="ASSET002",
            asset_name="Miami Office Building",
            asset_type="Real Estate",
            issuer_name="Real Estate Co",
            sector="Real Estate",
            country="USA",
            state_region="Florida",
            latitude=Decimal("25.7617"),
            longitude=Decimal("-80.1918"),
            market_value=Decimal("5000000.00"),
            carbon_intensity_proxy=Decimal("120.0"),
            insurance_dependency_score=Decimal("60.0"),
        ),
    ]
    
    for holding in holdings:
        db.add(holding)
    
    db.commit()
    
    return portfolio


def test_trigger_risk_calculation(
    client: TestClient,
    test_portfolio_with_holdings: Portfolio,
    test_scenario: Scenario
):
    """Test triggering risk calculation"""
    response = client.post(
        "/api/risk/run",
        json={
            "portfolio_id": str(test_portfolio_with_holdings.id),
            "scenario_id": str(test_scenario.id)
        }
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] in ["queued", "processing"]
    assert "message" in data


def test_get_task_status(
    client: TestClient,
    test_portfolio_with_holdings: Portfolio,
    test_scenario: Scenario
):
    """Test getting task status"""
    # First trigger calculation
    response = client.post(
        "/api/risk/run",
        json={
            "portfolio_id": str(test_portfolio_with_holdings.id),
            "scenario_id": str(test_scenario.id)
        }
    )
    
    task_id = response.json()["task_id"]
    
    # Get task status
    response = client.get(f"/api/risk/task/{task_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert "status" in data
    assert data["portfolio_id"] == str(test_portfolio_with_holdings.id)
    assert data["scenario_id"] == str(test_scenario.id)


def test_get_task_status_not_found(client: TestClient):
    """Test getting status for non-existent task"""
    response = client.get("/api/risk/task/00000000-0000-0000-0000-000000000000")
    
    assert response.status_code == 404


def test_get_risk_results_not_found(client: TestClient):
    """Test getting results when none exist"""
    response = client.get(
        "/api/risk/results",
        params={
            "portfolio_id": "00000000-0000-0000-0000-000000000000",
            "scenario_id": "00000000-0000-0000-0000-000000000000"
        }
    )
    
    assert response.status_code == 404


def test_get_portfolio_summary_not_found(client: TestClient):
    """Test getting summary when no results exist"""
    response = client.get(
        "/api/risk/summary",
        params={
            "portfolio_id": "00000000-0000-0000-0000-000000000000",
            "scenario_id": "00000000-0000-0000-0000-000000000000"
        }
    )
    
    assert response.status_code == 404


def test_risk_calculation_invalid_portfolio(
    client: TestClient,
    test_scenario: Scenario
):
    """Test risk calculation with invalid portfolio ID"""
    response = client.post(
        "/api/risk/run",
        json={
            "portfolio_id": "00000000-0000-0000-0000-000000000000",
            "scenario_id": str(test_scenario.id)
        }
    )
    
    # Should accept the request but fail during processing
    assert response.status_code == 202
    
    task_id = response.json()["task_id"]
    
    # Wait a moment for processing
    import time
    time.sleep(1)
    
    # Check task status - should be failed
    response = client.get(f"/api/risk/task/{task_id}")
    data = response.json()
    
    # Task should eventually fail
    assert data["status"] in ["queued", "processing", "failed"]

