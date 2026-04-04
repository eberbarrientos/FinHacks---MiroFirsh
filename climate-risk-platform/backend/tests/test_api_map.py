"""Tests for map API endpoints"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from app.main import app
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.scenario import Scenario
from app.models.risk_result import RiskResult

client = TestClient(app)


def test_get_map_holdings_success(db_session, sample_portfolio_with_risk_results):
    """Test successful retrieval of map holdings"""
    portfolio_id = sample_portfolio_with_risk_results["portfolio_id"]
    scenario_id = sample_portfolio_with_risk_results["scenario_id"]
    
    response = client.get(
        f"/api/map/holdings?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "portfolio_id" in data
    assert "scenario_id" in data
    assert "holdings_count" in data
    assert "holdings" in data
    assert len(data["holdings"]) > 0
    
    # Verify holding structure
    holding = data["holdings"][0]
    assert "holding_id" in holding
    assert "asset_name" in holding
    assert "issuer_name" in holding
    assert "sector" in holding
    assert "latitude" in holding
    assert "longitude" in holding
    assert "combined_score" in holding
    assert "expected_loss" in holding


def test_get_map_holdings_portfolio_not_found(db_session):
    """Test map holdings with non-existent portfolio"""
    fake_portfolio_id = str(uuid4())
    fake_scenario_id = str(uuid4())
    
    response = client.get(
        f"/api/map/holdings?portfolio_id={fake_portfolio_id}&scenario_id={fake_scenario_id}"
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_map_holdings_no_risk_data(db_session, sample_portfolio):
    """Test map holdings when no risk results exist"""
    portfolio_id = sample_portfolio["id"]
    fake_scenario_id = str(uuid4())
    
    response = client.get(
        f"/api/map/holdings?portfolio_id={portfolio_id}&scenario_id={fake_scenario_id}"
    )
    
    assert response.status_code == 404
    assert "no risk data" in response.json()["detail"].lower()


def test_get_hotspots_success(db_session, sample_portfolio_with_risk_results):
    """Test successful hotspot detection"""
    portfolio_id = sample_portfolio_with_risk_results["portfolio_id"]
    scenario_id = sample_portfolio_with_risk_results["scenario_id"]
    
    response = client.get(
        f"/api/map/hotspots?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "portfolio_id" in data
    assert "scenario_id" in data
    assert "threshold_score" in data
    assert "hotspots_count" in data
    assert "hotspots" in data
    
    # Verify hotspot structure if any exist
    if data["hotspots_count"] > 0:
        hotspot = data["hotspots"][0]
        assert "region" in hotspot
        assert "latitude" in hotspot
        assert "longitude" in hotspot
        assert "holding_count" in hotspot
        assert "total_expected_loss" in hotspot
        assert "avg_combined_score" in hotspot
        assert "max_combined_score" in hotspot


def test_get_hotspots_custom_threshold(db_session, sample_portfolio_with_risk_results):
    """Test hotspot detection with custom threshold"""
    portfolio_id = sample_portfolio_with_risk_results["portfolio_id"]
    scenario_id = sample_portfolio_with_risk_results["scenario_id"]
    
    response = client.get(
        f"/api/map/hotspots?portfolio_id={portfolio_id}&scenario_id={scenario_id}&threshold_score=80.0"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["threshold_score"] == 80.0


def test_get_hotspots_portfolio_not_found(db_session):
    """Test hotspots with non-existent portfolio"""
    fake_portfolio_id = str(uuid4())
    fake_scenario_id = str(uuid4())
    
    response = client.get(
        f"/api/map/hotspots?portfolio_id={fake_portfolio_id}&scenario_id={fake_scenario_id}"
    )
    
    assert response.status_code == 404


def test_hotspot_detection_algorithm():
    """Test the hotspot detection algorithm logic"""
    from app.api.map import detect_hotspots
    
    # Create test data with clustered high-risk holdings
    holdings_data = [
        # Cluster 1: High risk in Texas
        {"latitude": 29.7, "longitude": -95.3, "state_region": "Texas", "country": "USA", 
         "combined_score": 85.0, "expected_loss": 5000000},
        {"latitude": 29.8, "longitude": -95.4, "state_region": "Texas", "country": "USA",
         "combined_score": 80.0, "expected_loss": 4000000},
        {"latitude": 29.9, "longitude": -95.2, "state_region": "Texas", "country": "USA",
         "combined_score": 75.0, "expected_loss": 3000000},
        
        # Cluster 2: Low risk in California (should not be hotspot)
        {"latitude": 34.0, "longitude": -118.2, "state_region": "California", "country": "USA",
         "combined_score": 30.0, "expected_loss": 1000000},
        {"latitude": 34.1, "longitude": -118.3, "state_region": "California", "country": "USA",
         "combined_score": 35.0, "expected_loss": 1500000},
        
        # Single high-risk holding (should not be hotspot - needs at least 2)
        {"latitude": 40.7, "longitude": -74.0, "state_region": "New York", "country": "USA",
         "combined_score": 90.0, "expected_loss": 10000000},
    ]
    
    hotspots = detect_hotspots(holdings_data, threshold_score=70.0)
    
    # Should detect 1 hotspot (Texas cluster)
    assert len(hotspots) == 1
    assert hotspots[0]["region"] == "Texas"
    assert hotspots[0]["holding_count"] == 3
    assert hotspots[0]["avg_combined_score"] == 80.0
    assert hotspots[0]["total_expected_loss"] == 12000000


def test_hotspot_detection_empty_data():
    """Test hotspot detection with empty data"""
    from app.api.map import detect_hotspots
    
    hotspots = detect_hotspots([], threshold_score=70.0)
    assert len(hotspots) == 0


def test_hotspot_detection_no_clusters_above_threshold():
    """Test hotspot detection when no clusters exceed threshold"""
    from app.api.map import detect_hotspots
    
    holdings_data = [
        {"latitude": 29.7, "longitude": -95.3, "state_region": "Texas", "country": "USA",
         "combined_score": 50.0, "expected_loss": 1000000},
        {"latitude": 29.8, "longitude": -95.4, "state_region": "Texas", "country": "USA",
         "combined_score": 55.0, "expected_loss": 1500000},
    ]
    
    hotspots = detect_hotspots(holdings_data, threshold_score=70.0)
    assert len(hotspots) == 0
