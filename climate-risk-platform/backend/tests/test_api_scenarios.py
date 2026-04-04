"""Tests for Scenario API endpoints"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_scenario_templates():
    """Test GET /api/scenarios/templates"""
    response = client.get("/api/scenarios/templates")
    
    assert response.status_code == 200
    templates = response.json()
    assert isinstance(templates, list)
    assert len(templates) > 0
    
    # Check template structure
    template = templates[0]
    assert "name" in template
    assert "scenario_type" in template
    assert "severity" in template
    assert "time_horizon" in template
    assert "description" in template
    assert "parameters" in template


def test_create_scenario():
    """Test POST /api/scenarios"""
    scenario_data = {
        "name": "Test API Hurricane",
        "scenario_type": "hurricane",
        "severity": "high",
        "time_horizon": "12m",
        "parameters": {
            "wind_speed_mph": 150,
            "affected_regions": ["Florida"]
        }
    }
    
    response = client.post("/api/scenarios", json=scenario_data)
    
    assert response.status_code == 201
    scenario = response.json()
    assert scenario["name"] == "Test API Hurricane"
    assert scenario["scenario_type"] == "hurricane"
    assert "id" in scenario
    assert "created_at" in scenario


def test_list_scenarios():
    """Test GET /api/scenarios"""
    response = client.get("/api/scenarios")
    
    assert response.status_code == 200
    scenarios = response.json()
    assert isinstance(scenarios, list)


def test_get_scenario_by_id():
    """Test GET /api/scenarios/{id}"""
    # First create a scenario
    scenario_data = {
        "name": "Test Get Scenario",
        "scenario_type": "wildfire",
        "severity": "medium",
        "time_horizon": "6m"
    }
    create_response = client.post("/api/scenarios", json=scenario_data)
    scenario_id = create_response.json()["id"]
    
    # Now get it
    response = client.get(f"/api/scenarios/{scenario_id}")
    
    assert response.status_code == 200
    scenario = response.json()
    assert scenario["id"] == scenario_id
    assert scenario["name"] == "Test Get Scenario"


def test_get_nonexistent_scenario():
    """Test GET /api/scenarios/{id} with invalid ID"""
    response = client.get("/api/scenarios/00000000-0000-0000-0000-000000000000")
    
    assert response.status_code == 404


def test_create_scenario_invalid_type():
    """Test POST /api/scenarios with invalid scenario type"""
    scenario_data = {
        "name": "Invalid Scenario",
        "scenario_type": "invalid_type",
        "severity": "high",
        "time_horizon": "12m"
    }
    
    response = client.post("/api/scenarios", json=scenario_data)
    
    # Should fail validation
    assert response.status_code == 422
