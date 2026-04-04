"""Tests for Scenario Engine"""

import pytest
from app.engines.scenario import ScenarioEngine, ScenarioTemplate
from app.schemas.scenario import ScenarioCreate
from app.schemas.enums import ScenarioType


def test_get_templates(db_session):
    """Test retrieving scenario templates"""
    engine = ScenarioEngine(db_session)
    templates = engine.get_templates()
    
    assert len(templates) > 0
    assert all(isinstance(t, dict) for t in templates)
    
    # Check that all required scenario types are present
    template_types = [t['scenario_type'] for t in templates]
    assert 'hurricane' in template_types
    assert 'wildfire' in template_types
    assert 'drought' in template_types
    assert 'heatwave' in template_types
    assert 'flood' in template_types
    assert 'carbon_tax' in template_types
    assert 'emissions_regulation' in template_types


def test_create_scenario(db_session):
    """Test creating a custom scenario"""
    engine = ScenarioEngine(db_session)
    
    scenario_data = ScenarioCreate(
        name="Test Hurricane Scenario",
        scenario_type=ScenarioType.HURRICANE,
        severity="high",
        time_horizon="12m",
        parameters={
            "affected_regions": ["Florida", "Texas"],
            "wind_speed_mph": 150
        }
    )
    
    scenario = engine.create_scenario(scenario_data)
    
    assert scenario.id is not None
    assert scenario.name == "Test Hurricane Scenario"
    assert scenario.scenario_type == ScenarioType.HURRICANE
    assert scenario.severity == "high"
    assert scenario.time_horizon == "12m"
    assert scenario.parameters is not None
    assert scenario.parameters["wind_speed_mph"] == 150


def test_get_scenario(db_session):
    """Test retrieving a scenario by ID"""
    engine = ScenarioEngine(db_session)
    
    # Create a scenario
    scenario_data = ScenarioCreate(
        name="Test Wildfire Scenario",
        scenario_type=ScenarioType.WILDFIRE,
        severity="medium",
        time_horizon="6m"
    )
    created_scenario = engine.create_scenario(scenario_data)
    
    # Retrieve it
    retrieved_scenario = engine.get_scenario(created_scenario.id)
    
    assert retrieved_scenario is not None
    assert retrieved_scenario.id == created_scenario.id
    assert retrieved_scenario.name == "Test Wildfire Scenario"


def test_list_scenarios(db_session):
    """Test listing all scenarios"""
    engine = ScenarioEngine(db_session)
    
    # Get initial count
    initial_scenarios = engine.list_scenarios()
    initial_count = len(initial_scenarios)
    
    # Create multiple scenarios
    created_names = []
    for i in range(3):
        scenario_data = ScenarioCreate(
            name=f"Test List Scenario {i}",
            scenario_type=ScenarioType.FLOOD,
            severity="medium",
            time_horizon="12m"
        )
        scenario = engine.create_scenario(scenario_data)
        created_names.append(scenario.name)
    
    # List scenarios
    scenarios = engine.list_scenarios()
    
    # Should have 3 more scenarios than before
    assert len(scenarios) == initial_count + 3
    
    # The most recently created scenarios should be at the top
    recent_names = [s.name for s in scenarios[:3]]
    assert created_names[-1] in recent_names  # Last created should be in top 3


def test_scenario_template_structure():
    """Test that scenario templates have correct structure"""
    engine = ScenarioEngine(None)  # Don't need DB for this test
    templates = engine.get_templates()
    
    for template in templates:
        assert 'name' in template
        assert 'scenario_type' in template
        assert 'severity' in template
        assert 'time_horizon' in template
        assert 'description' in template
        assert 'parameters' in template
        
        # Check severity values
        assert template['severity'] in ['low', 'medium', 'high']
        
        # Check parameters is a dict
        assert isinstance(template['parameters'], dict)
