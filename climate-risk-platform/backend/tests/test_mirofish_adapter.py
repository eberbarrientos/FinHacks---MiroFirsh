"""Tests for MiroFish adapter"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.adapters.mirofish import MiroFishAdapter, MiroFishError, MiroFishTimeoutError, MiroFishConnectionError


class TestMiroFishAdapter:
    """Test suite for MiroFish adapter"""
    
    def test_adapter_initialization(self):
        """Test adapter initializes with correct configuration"""
        adapter = MiroFishAdapter()
        
        assert adapter.api_url == "http://localhost:8080"
        assert adapter.timeout == 60
        assert adapter.retry_attempts == 3
        assert adapter.poll_interval == 5
        assert adapter.max_poll_attempts == 12
    
    def test_construct_scenario_packet(self):
        """Test scenario packet construction"""
        adapter = MiroFishAdapter()
        
        portfolio = {
            "id": "portfolio-1",
            "name": "Test Portfolio",
            "total_value": 1000000
        }
        
        scenario = {
            "id": "scenario-1",
            "scenario_type": "hurricane",
            "severity": "high",
            "time_horizon": "12m"
        }
        
        risk_results = [
            {
                "issuer_name": "Company A",
                "sector": "Energy",
                "state_region": "Texas",
                "country": "USA",
                "combined_score": 75.5,
                "expected_loss": 50000,
                "market_value": 500000,
                "insurance_dependency_score": 60,
                "supply_chain_dependency_score": 70
            },
            {
                "issuer_name": "Company B",
                "sector": "Utilities",
                "state_region": "Florida",
                "country": "USA",
                "combined_score": 82.3,
                "expected_loss": 75000,
                "market_value": 500000,
                "insurance_dependency_score": 55,
                "supply_chain_dependency_score": 45
            }
        ]
        
        packet = adapter.construct_scenario_packet(portfolio, scenario, risk_results)
        
        # Verify packet structure
        assert "scenario" in packet
        assert packet["scenario"]["type"] == "hurricane"
        assert packet["scenario"]["severity"] == "high"
        assert packet["scenario"]["time_horizon"] == "12m"
        
        assert "portfolio" in packet
        assert packet["portfolio"]["portfolio_id"] == "portfolio-1"
        assert packet["portfolio"]["value"] == 1000000
        
        assert "entities" in packet
        assert len(packet["entities"]) == 2
        
        # Verify entity data
        entity_a = next(e for e in packet["entities"] if e["issuer"] == "Company A")
        assert entity_a["sector"] == "Energy"
        assert entity_a["region"] == "Texas"
        assert entity_a["combined_score"] == 75.5
        assert entity_a["expected_loss"] == 50000
        assert "dependencies" in entity_a
        assert len(entity_a["dependencies"]) > 0
        
        assert "questions" in packet
        assert len(packet["questions"]) == 3
    
    def test_determine_dependencies_energy_sector(self):
        """Test dependency determination for energy sector"""
        adapter = MiroFishAdapter()
        
        risk_result = {
            "sector": "Energy",
            "insurance_dependency_score": 60,
            "supply_chain_dependency_score": 70
        }
        
        dependencies = adapter._determine_dependencies(risk_result)
        
        assert "insurers" in dependencies
        assert "suppliers" in dependencies
        assert "grid" in dependencies
        assert "regulators" in dependencies
    
    def test_determine_dependencies_financial_sector(self):
        """Test dependency determination for financial sector"""
        adapter = MiroFishAdapter()
        
        risk_result = {
            "sector": "Financial Services",
            "insurance_dependency_score": 30,
            "supply_chain_dependency_score": 40
        }
        
        dependencies = adapter._determine_dependencies(risk_result)
        
        assert "credit_markets" in dependencies
        assert "regulators" in dependencies
    
    def test_determine_dependencies_default(self):
        """Test default dependencies when no specific sector matches"""
        adapter = MiroFishAdapter()
        
        risk_result = {
            "sector": "Technology",
            "insurance_dependency_score": 20,
            "supply_chain_dependency_score": 30
        }
        
        dependencies = adapter._determine_dependencies(risk_result)
        
        # Should have default dependencies
        assert "suppliers" in dependencies
        assert "regulators" in dependencies
    
    @pytest.mark.asyncio
    async def test_submit_simulation_success(self):
        """Test successful simulation submission"""
        adapter = MiroFishAdapter()
        
        scenario_packet = {
            "scenario": {"type": "hurricane", "severity": "high"},
            "portfolio": {"portfolio_id": "p1", "value": 1000000},
            "entities": [],
            "questions": []
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"simulation_id": "sim_123"}
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            run_id = await adapter.submit_simulation(scenario_packet)
            
            assert run_id == "sim_123"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_simulation_failure(self):
        """Test simulation submission failure"""
        adapter = MiroFishAdapter()
        
        scenario_packet = {
            "scenario": {"type": "hurricane"},
            "portfolio": {"portfolio_id": "p1"},
            "entities": [],
            "questions": []
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error": "Invalid packet"
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(MiroFishError, match="Invalid packet"):
                await adapter.submit_simulation(scenario_packet)
    
    @pytest.mark.asyncio
    async def test_poll_simulation_completed(self):
        """Test polling for completed simulation"""
        adapter = MiroFishAdapter()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "status": "completed",
                "output_json": {
                    "cascade_events": [],
                    "dependency_narrative": "Test narrative"
                }
            }
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await adapter.poll_simulation("sim_123")
            
            assert result["status"] == "completed"
            assert "output_json" in result
    
    @pytest.mark.asyncio
    async def test_poll_simulation_failed(self):
        """Test polling for failed simulation"""
        adapter = MiroFishAdapter()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "status": "failed",
                "error": "Simulation error"
            }
        }
        
        with patch.object(adapter, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(MiroFishError, match="Simulation error"):
                await adapter.poll_simulation("sim_123")
    
    def test_parse_cascade_results(self):
        """Test parsing of cascade results"""
        adapter = MiroFishAdapter()
        
        simulation_data = {
            "status": "completed",
            "output_json": {
                "cascade_events": [
                    {"entity": "Company A", "loss": 10000},
                    {"entity": "Company B", "loss": 15000},
                    {"entity": "Company A", "loss": 5000}
                ],
                "dependency_narrative": "Test narrative about cascades"
            }
        }
        
        results = adapter.parse_cascade_results(simulation_data)
        
        assert results["cascade_events"] == simulation_data["output_json"]["cascade_events"]
        assert results["dependency_narrative"] == "Test narrative about cascades"
        assert results["propagated_loss"] == 30000  # 10000 + 15000 + 5000
        assert results["affected_entity_count"] == 2  # Company A and Company B
    
    def test_parse_cascade_results_no_events(self):
        """Test parsing when no cascade events"""
        adapter = MiroFishAdapter()
        
        simulation_data = {
            "status": "completed",
            "output_json": {
                "cascade_events": [],
                "dependency_narrative": "No cascades detected"
            }
        }
        
        results = adapter.parse_cascade_results(simulation_data)
        
        assert results["cascade_events"] == []
        assert results["dependency_narrative"] == "No cascades detected"
        assert results["propagated_loss"] == 0
        assert results["affected_entity_count"] == 0
    
    def test_parse_cascade_results_alternative_fields(self):
        """Test parsing with alternative field names"""
        adapter = MiroFishAdapter()
        
        simulation_data = {
            "status": "completed",
            "output_json": {
                "cascade_events": [
                    {"issuer": "Company A", "impact": 20000}
                ],
                "narrative": "Alternative narrative field"
            }
        }
        
        results = adapter.parse_cascade_results(simulation_data)
        
        assert results["dependency_narrative"] == "Alternative narrative field"
        assert results["propagated_loss"] == 20000
        assert results["affected_entity_count"] == 1
