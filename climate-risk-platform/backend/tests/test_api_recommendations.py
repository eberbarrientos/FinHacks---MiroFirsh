"""Tests for recommendation API endpoints"""

import pytest
from decimal import Decimal
from app.models.holding import Holding
from app.models.risk_result import RiskResult


def test_get_recommendations_generates_if_not_exist(client, sample_portfolio_with_risk_results):
    """Test that GET endpoint generates recommendations if they don't exist"""
    portfolio_id = str(sample_portfolio_with_risk_results["portfolio_id"])
    scenario_id = str(sample_portfolio_with_risk_results["scenario_id"])
    
    response = client.get(
        f"/api/recommendations?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Verify recommendation structure
    rec = data[0]
    assert "id" in rec
    assert "portfolio_id" in rec
    assert "scenario_id" in rec
    assert "recommendation_type" in rec
    assert "priority" in rec
    assert "message" in rec
    assert rec["priority"] in ["critical", "high", "medium", "low"]


def test_get_recommendations_sorted_by_priority(client, sample_portfolio_with_risk_results):
    """Test that recommendations are sorted by priority and impact"""
    portfolio_id = str(sample_portfolio_with_risk_results["portfolio_id"])
    scenario_id = str(sample_portfolio_with_risk_results["scenario_id"])
    
    response = client.get(
        f"/api/recommendations?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify sorting
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    
    for i in range(len(data) - 1):
        current_priority = priority_order[data[i]["priority"]]
        next_priority = priority_order[data[i + 1]["priority"]]
        
        # Current should be <= next (higher priority first)
        assert current_priority <= next_priority


def test_get_recommendations_not_found(client):
    """Test 404 when portfolio or scenario doesn't exist"""
    response = client.get(
        "/api/recommendations?portfolio_id=00000000-0000-0000-0000-000000000000&scenario_id=00000000-0000-0000-0000-000000000000"
    )
    
    assert response.status_code == 404


def test_generate_recommendations_endpoint(client, sample_portfolio_with_risk_results):
    """Test POST endpoint to force regeneration of recommendations"""
    portfolio_id = str(sample_portfolio_with_risk_results["portfolio_id"])
    scenario_id = str(sample_portfolio_with_risk_results["scenario_id"])
    
    response = client.post(
        f"/api/recommendations/generate?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["message"] == "Recommendations generated successfully"
    assert data["count"] > 0
    assert data["portfolio_id"] == portfolio_id
    assert data["scenario_id"] == scenario_id


def test_generate_recommendations_replaces_existing(client, sample_portfolio_with_risk_results, db_session):
    """Test that regeneration replaces existing recommendations"""
    portfolio_id = str(sample_portfolio_with_risk_results["portfolio_id"])
    scenario_id = str(sample_portfolio_with_risk_results["scenario_id"])
    
    # Generate first time
    response1 = client.post(
        f"/api/recommendations/generate?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    assert response1.status_code == 201
    count1 = response1.json()["count"]
    
    # Get recommendations
    response2 = client.get(
        f"/api/recommendations?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    assert response2.status_code == 200
    recs_before = response2.json()
    
    # Generate again
    response3 = client.post(
        f"/api/recommendations/generate?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    assert response3.status_code == 201
    
    # Get recommendations again
    response4 = client.get(
        f"/api/recommendations?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    assert response4.status_code == 200
    recs_after = response4.json()
    
    # Should have new IDs (regenerated)
    assert len(recs_after) > 0
    if len(recs_before) > 0 and len(recs_after) > 0:
        # IDs should be different (new recommendations)
        assert recs_before[0]["id"] != recs_after[0]["id"]


def test_recommendations_include_affected_holdings(client, sample_portfolio_with_risk_results):
    """Test that recommendations include affected holdings list"""
    portfolio_id = str(sample_portfolio_with_risk_results["portfolio_id"])
    scenario_id = str(sample_portfolio_with_risk_results["scenario_id"])
    
    response = client.get(
        f"/api/recommendations?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # At least one recommendation should have affected holdings
    has_affected_holdings = any(
        rec.get("affected_holdings") is not None and len(rec["affected_holdings"]) > 0
        for rec in data
    )
    assert has_affected_holdings


def test_recommendations_include_potential_impact(client, sample_portfolio_with_risk_results):
    """Test that recommendations include potential impact values"""
    portfolio_id = str(sample_portfolio_with_risk_results["portfolio_id"])
    scenario_id = str(sample_portfolio_with_risk_results["scenario_id"])
    
    response = client.get(
        f"/api/recommendations?portfolio_id={portfolio_id}&scenario_id={scenario_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # At least one recommendation should have potential impact
    has_potential_impact = any(
        rec.get("potential_impact") is not None and float(rec["potential_impact"]) > 0
        for rec in data
    )
    assert has_potential_impact
