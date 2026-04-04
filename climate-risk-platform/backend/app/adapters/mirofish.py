"""
MiroFish Adapter for Dependency Cascade Simulation

This adapter integrates with the MiroFish backend to enable dependency cascade
simulation for climate risk analysis. It follows the same pattern as MiroFish's
simulation_manager for creating, submitting, and polling simulations.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings


logger = logging.getLogger(__name__)


class MiroFishError(Exception):
    """Base exception for MiroFish adapter errors"""
    pass


class MiroFishTimeoutError(MiroFishError):
    """Raised when MiroFish simulation times out"""
    pass


class MiroFishConnectionError(MiroFishError):
    """Raised when connection to MiroFish fails"""
    pass


class MiroFishAdapter:
    """
    Adapter for MiroFish dependency cascade simulation
    
    Provides methods to:
    - Construct scenario packets from risk results
    - Submit simulations to MiroFish
    - Poll for simulation completion
    - Parse cascade results
    
    Configuration:
    - API URL: settings.mirofish_api_url
    - Timeout: settings.mirofish_timeout (default 60s)
    - Retry attempts: settings.mirofish_retry_attempts (default 3)
    """
    
    def __init__(self):
        self.api_url = settings.mirofish_api_url
        self.timeout = settings.mirofish_timeout
        self.retry_attempts = settings.mirofish_retry_attempts
        self.poll_interval = 5  # Poll every 5 seconds
        self.max_poll_attempts = 12  # 12 attempts * 5 seconds = 60 seconds
        
        logger.info(
            f"MiroFishAdapter initialized: url={self.api_url}, "
            f"timeout={self.timeout}s, retry_attempts={self.retry_attempts}"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request to MiroFish with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request
            
        Returns:
            httpx.Response
            
        Raises:
            MiroFishConnectionError: If connection fails after retries
            MiroFishTimeoutError: If request times out
        """
        url = f"{self.api_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
        except httpx.ConnectError as e:
            logger.error(f"MiroFish connection error: {e}")
            raise MiroFishConnectionError(f"Failed to connect to MiroFish at {url}") from e
            
        except httpx.TimeoutException as e:
            logger.error(f"MiroFish timeout: {e}")
            raise MiroFishTimeoutError(f"Request to MiroFish timed out after {self.timeout}s") from e
            
        except httpx.HTTPStatusError as e:
            logger.error(f"MiroFish HTTP error: {e.response.status_code} - {e.response.text}")
            raise MiroFishError(
                f"MiroFish API error: {e.response.status_code} - {e.response.text}"
            ) from e
    
    def construct_scenario_packet(
        self,
        portfolio: Dict[str, Any],
        scenario: Dict[str, Any],
        risk_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Construct scenario packet for MiroFish submission
        
        The packet includes:
        - Scenario parameters (type, severity, time_horizon)
        - Portfolio summary (id, value)
        - Entity details (issuer, sector, region, risk scores, dependencies)
        - Analysis questions for MiroFish to answer
        
        Args:
            portfolio: Portfolio data with id, name, total_value
            scenario: Scenario data with type, severity, time_horizon
            risk_results: List of risk results with holding and risk data
            
        Returns:
            Scenario packet dictionary ready for MiroFish submission
        """
        # Calculate total portfolio value
        total_value = portfolio.get("total_value", 0)
        if not total_value and risk_results:
            total_value = sum(
                float(result.get("market_value", 0))
                for result in risk_results
            )
        
        # Build entities list from risk results
        # Group by issuer to avoid duplicate entities
        entities_by_issuer = {}
        
        for result in risk_results:
            issuer = result.get("issuer_name", "Unknown")
            
            if issuer not in entities_by_issuer:
                # Determine dependencies based on sector and risk profile
                dependencies = self._determine_dependencies(result)
                
                entities_by_issuer[issuer] = {
                    "issuer": issuer,
                    "sector": result.get("sector", "Unknown"),
                    "region": result.get("state_region") or result.get("country", "Unknown"),
                    "combined_score": float(result.get("combined_score", 0)),
                    "expected_loss": float(result.get("expected_loss", 0)),
                    "dependencies": dependencies
                }
            else:
                # Aggregate if issuer already exists
                existing = entities_by_issuer[issuer]
                existing["combined_score"] = max(
                    existing["combined_score"],
                    float(result.get("combined_score", 0))
                )
                existing["expected_loss"] += float(result.get("expected_loss", 0))
        
        entities = list(entities_by_issuer.values())
        
        # Construct the scenario packet
        packet = {
            "scenario": {
                "type": scenario.get("scenario_type", "unknown"),
                "severity": scenario.get("severity", "medium"),
                "time_horizon": scenario.get("time_horizon", "12m")
            },
            "portfolio": {
                "portfolio_id": portfolio.get("id", "unknown"),
                "value": float(total_value)
            },
            "entities": entities,
            "questions": [
                "What second-order cascades are likely?",
                "Which entities amplify portfolio loss?",
                "What mitigation actions matter most?"
            ]
        }
        
        logger.info(
            f"Constructed scenario packet: portfolio={portfolio.get('id')}, "
            f"scenario={scenario.get('id')}, entities={len(entities)}"
        )
        
        return packet
    
    def _determine_dependencies(self, risk_result: Dict[str, Any]) -> List[str]:
        """
        Determine dependency types for an entity based on its characteristics
        
        Args:
            risk_result: Risk result with holding and risk data
            
        Returns:
            List of dependency type strings
        """
        dependencies = []
        
        # Insurance dependencies
        insurance_score = risk_result.get("insurance_dependency_score", 0)
        if insurance_score and float(insurance_score) > 50:
            dependencies.append("insurers")
        
        # Supply chain dependencies
        supply_chain_score = risk_result.get("supply_chain_dependency_score", 0)
        if supply_chain_score and float(supply_chain_score) > 50:
            dependencies.append("suppliers")
        
        # Sector-specific dependencies
        sector = risk_result.get("sector", "").lower()
        if "utilit" in sector or "energy" in sector:
            dependencies.extend(["grid", "regulators"])
        elif "financ" in sector or "bank" in sector:
            dependencies.extend(["credit_markets", "regulators"])
        elif "real_estate" in sector or "reit" in sector:
            dependencies.extend(["construction", "financing"])
        elif "transport" in sector:
            dependencies.extend(["fuel_suppliers", "infrastructure"])
        
        # Default dependencies if none identified
        if not dependencies:
            dependencies = ["suppliers", "regulators"]
        
        return list(set(dependencies))  # Remove duplicates
    
    async def submit_simulation(
        self,
        scenario_packet: Dict[str, Any]
    ) -> str:
        """
        Submit scenario packet to MiroFish for cascade simulation
        
        Args:
            scenario_packet: Constructed scenario packet
            
        Returns:
            run_id: MiroFish simulation run identifier
            
        Raises:
            MiroFishError: If submission fails
        """
        try:
            response = await self._make_request(
                "POST",
                "/api/simulation/create",
                json=scenario_packet
            )
            
            data = response.json()
            
            if not data.get("success"):
                raise MiroFishError(f"MiroFish submission failed: {data.get('error')}")
            
            run_id = data.get("data", {}).get("simulation_id")
            
            if not run_id:
                raise MiroFishError("MiroFish did not return a simulation_id")
            
            logger.info(f"MiroFish simulation submitted: run_id={run_id}")
            
            return run_id
            
        except (MiroFishConnectionError, MiroFishTimeoutError):
            raise
        except Exception as e:
            logger.error(f"Failed to submit MiroFish simulation: {e}")
            raise MiroFishError(f"Simulation submission failed: {str(e)}") from e
    
    async def poll_simulation(
        self,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Poll MiroFish for simulation completion
        
        Polls every 5 seconds with maximum 12 attempts (60 second timeout)
        
        Args:
            run_id: MiroFish simulation run identifier
            
        Returns:
            Simulation status dictionary with status and results
            
        Raises:
            MiroFishTimeoutError: If simulation doesn't complete within timeout
            MiroFishError: If polling fails
        """
        for attempt in range(self.max_poll_attempts):
            try:
                response = await self._make_request(
                    "GET",
                    f"/api/simulation/{run_id}"
                )
                
                data = response.json()
                
                if not data.get("success"):
                    raise MiroFishError(f"Failed to get simulation status: {data.get('error')}")
                
                sim_data = data.get("data", {})
                status = sim_data.get("status", "unknown")
                
                logger.debug(
                    f"MiroFish poll attempt {attempt + 1}/{self.max_poll_attempts}: "
                    f"run_id={run_id}, status={status}"
                )
                
                # Check if simulation is complete
                if status in ["completed", "ready"]:
                    logger.info(f"MiroFish simulation completed: run_id={run_id}")
                    return sim_data
                
                elif status == "failed":
                    error = sim_data.get("error", "Unknown error")
                    raise MiroFishError(f"MiroFish simulation failed: {error}")
                
                # Wait before next poll
                if attempt < self.max_poll_attempts - 1:
                    await asyncio.sleep(self.poll_interval)
                
            except (MiroFishConnectionError, MiroFishTimeoutError):
                raise
            except MiroFishError:
                raise
            except Exception as e:
                logger.error(f"Error polling MiroFish simulation: {e}")
                raise MiroFishError(f"Polling failed: {str(e)}") from e
        
        # Timeout reached
        raise MiroFishTimeoutError(
            f"Simulation did not complete within {self.max_poll_attempts * self.poll_interval}s"
        )
    
    def parse_cascade_results(
        self,
        simulation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse MiroFish simulation output into structured cascade results
        
        Extracts:
        - cascade_events: List of cascade event objects
        - dependency_narrative: Text narrative of cascade propagation
        - propagated_loss: Total loss from cascade effects
        
        Args:
            simulation_data: Raw simulation data from MiroFish
            
        Returns:
            Parsed cascade results dictionary
        """
        # Extract output JSON
        output_json = simulation_data.get("output_json", {})
        
        # Parse cascade events
        cascade_events = output_json.get("cascade_events", [])
        
        # Parse dependency narrative
        dependency_narrative = output_json.get("dependency_narrative", "")
        if not dependency_narrative:
            # Try alternative field names
            dependency_narrative = output_json.get("narrative", "")
            if not dependency_narrative:
                dependency_narrative = "No cascade narrative available."
        
        # Calculate propagated loss from cascade events
        propagated_loss = 0.0
        for event in cascade_events:
            loss = event.get("loss", 0) or event.get("impact", 0)
            if loss:
                propagated_loss += float(loss)
        
        # If no cascade events but there's a total loss field, use that
        if propagated_loss == 0 and "total_propagated_loss" in output_json:
            propagated_loss = float(output_json["total_propagated_loss"])
        
        results = {
            "cascade_events": cascade_events,
            "dependency_narrative": dependency_narrative,
            "propagated_loss": propagated_loss,
            "affected_entity_count": len(set(
                event.get("entity") or event.get("issuer", "")
                for event in cascade_events
            ))
        }
        
        logger.info(
            f"Parsed cascade results: events={len(cascade_events)}, "
            f"propagated_loss={propagated_loss}, "
            f"affected_entities={results['affected_entity_count']}"
        )
        
        return results


# Import asyncio for sleep
import asyncio
