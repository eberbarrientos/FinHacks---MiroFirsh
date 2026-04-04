"""Scenario Engine for managing climate scenarios"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.scenario import Scenario as ScenarioModel
from app.schemas.scenario import ScenarioCreate, Scenario
from app.schemas.enums import ScenarioType


class ScenarioTemplate:
    """Predefined scenario template"""
    def __init__(
        self,
        name: str,
        scenario_type: ScenarioType,
        severity: str,
        time_horizon: str,
        description: str,
        parameters: Dict[str, Any]
    ):
        self.name = name
        self.scenario_type = scenario_type
        self.severity = severity
        self.time_horizon = time_horizon
        self.description = description
        self.parameters = parameters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "name": self.name,
            "scenario_type": self.scenario_type.value,
            "severity": self.severity,
            "time_horizon": self.time_horizon,
            "description": self.description,
            "parameters": self.parameters
        }


class ScenarioEngine:
    """Engine for managing climate scenarios and stress testing"""
    
    # Predefined scenario templates
    TEMPLATES = [
        ScenarioTemplate(
            name="Hurricane Category 5 - Gulf Coast",
            scenario_type=ScenarioType.HURRICANE,
            severity="high",
            time_horizon="12m",
            description="Major hurricane with 160+ mph winds impacting Gulf Coast region",
            parameters={
                "affected_regions": ["Texas Gulf", "Louisiana", "Florida"],
                "wind_speed_mph": 160,
                "storm_surge_ft": 15,
                "damage_multiplier": 2.5
            }
        ),
        ScenarioTemplate(
            name="Hurricane Category 3 - Atlantic Coast",
            scenario_type=ScenarioType.HURRICANE,
            severity="medium",
            time_horizon="12m",
            description="Moderate hurricane with 120 mph winds impacting Atlantic Coast",
            parameters={
                "affected_regions": ["North Carolina", "South Carolina", "Georgia"],
                "wind_speed_mph": 120,
                "storm_surge_ft": 10,
                "damage_multiplier": 1.5
            }
        ),
        ScenarioTemplate(
            name="Wildfire - California",
            scenario_type=ScenarioType.WILDFIRE,
            severity="high",
            time_horizon="6m",
            description="Severe wildfire season in California with widespread property damage",
            parameters={
                "affected_regions": ["California"],
                "acres_burned": 500000,
                "air_quality_index": 250,
                "damage_multiplier": 2.0
            }
        ),
        ScenarioTemplate(
            name="Wildfire - Western States",
            scenario_type=ScenarioType.WILDFIRE,
            severity="medium",
            time_horizon="6m",
            description="Moderate wildfire activity across Western states",
            parameters={
                "affected_regions": ["California", "Oregon", "Washington", "Colorado"],
                "acres_burned": 200000,
                "air_quality_index": 150,
                "damage_multiplier": 1.3
            }
        ),
        ScenarioTemplate(
            name="Drought - Southwest",
            scenario_type=ScenarioType.DROUGHT,
            severity="high",
            time_horizon="24m",
            description="Severe multi-year drought impacting Southwest agriculture and water supply",
            parameters={
                "affected_regions": ["Arizona", "New Mexico", "Nevada", "Southern California"],
                "precipitation_deficit_pct": 60,
                "water_shortage_level": "critical",
                "damage_multiplier": 1.8
            }
        ),
        ScenarioTemplate(
            name="Heatwave - Central US",
            scenario_type=ScenarioType.HEATWAVE,
            severity="high",
            time_horizon="3m",
            description="Extreme heat event with temperatures exceeding 110°F for extended periods",
            parameters={
                "affected_regions": ["Texas", "Oklahoma", "Kansas", "Missouri"],
                "max_temperature_f": 115,
                "duration_days": 30,
                "damage_multiplier": 1.4
            }
        ),
        ScenarioTemplate(
            name="Flood - Midwest",
            scenario_type=ScenarioType.FLOOD,
            severity="high",
            time_horizon="6m",
            description="Major flooding from heavy rainfall and river overflow",
            parameters={
                "affected_regions": ["Iowa", "Illinois", "Missouri", "Nebraska"],
                "rainfall_inches": 20,
                "river_crest_ft": 25,
                "damage_multiplier": 2.0
            }
        ),
        ScenarioTemplate(
            name="Flood - Coastal Storm Surge",
            scenario_type=ScenarioType.FLOOD,
            severity="medium",
            time_horizon="12m",
            description="Coastal flooding from storm surge and sea level rise",
            parameters={
                "affected_regions": ["Florida", "Louisiana", "Texas Gulf", "North Carolina"],
                "storm_surge_ft": 8,
                "sea_level_rise_inches": 6,
                "damage_multiplier": 1.6
            }
        ),
        ScenarioTemplate(
            name="Carbon Tax - $100/ton",
            scenario_type=ScenarioType.CARBON_TAX,
            severity="high",
            time_horizon="36m",
            description="Federal carbon tax of $100 per ton CO2 equivalent",
            parameters={
                "carbon_price_per_ton": 100,
                "affected_sectors": ["Utilities", "Energy", "Transportation", "Manufacturing"],
                "revenue_impact_pct": -15,
                "transition_multiplier": 2.5
            }
        ),
        ScenarioTemplate(
            name="Carbon Tax - $50/ton",
            scenario_type=ScenarioType.CARBON_TAX,
            severity="medium",
            time_horizon="36m",
            description="Federal carbon tax of $50 per ton CO2 equivalent",
            parameters={
                "carbon_price_per_ton": 50,
                "affected_sectors": ["Utilities", "Energy", "Transportation"],
                "revenue_impact_pct": -8,
                "transition_multiplier": 1.5
            }
        ),
        ScenarioTemplate(
            name="Emissions Regulation - Strict Standards",
            scenario_type=ScenarioType.EMISSIONS_REGULATION,
            severity="high",
            time_horizon="48m",
            description="Stringent emissions regulations requiring 50% reduction by 2030",
            parameters={
                "reduction_target_pct": 50,
                "compliance_deadline": "2030",
                "affected_sectors": ["Utilities", "Energy", "Transportation", "Manufacturing", "Agriculture"],
                "capex_increase_pct": 25,
                "transition_multiplier": 2.0
            }
        ),
        ScenarioTemplate(
            name="Emissions Regulation - Moderate Standards",
            scenario_type=ScenarioType.EMISSIONS_REGULATION,
            severity="medium",
            time_horizon="48m",
            description="Moderate emissions regulations requiring 30% reduction by 2035",
            parameters={
                "reduction_target_pct": 30,
                "compliance_deadline": "2035",
                "affected_sectors": ["Utilities", "Energy", "Transportation"],
                "capex_increase_pct": 15,
                "transition_multiplier": 1.3
            }
        )
    ]
    
    def __init__(self, db: Session):
        """Initialize scenario engine with database session"""
        self.db = db
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """
        Get all predefined scenario templates
        
        Returns:
            List of scenario template dictionaries
        
        **Validates: Requirements 4.1**
        """
        return [template.to_dict() for template in self.TEMPLATES]
    
    def create_scenario(self, scenario_data: ScenarioCreate) -> Scenario:
        """
        Create and store a custom scenario
        
        Args:
            scenario_data: Scenario creation data
        
        Returns:
            Created scenario with database ID
        
        **Validates: Requirements 4.2**
        """
        # Create database model
        db_scenario = ScenarioModel(
            name=scenario_data.name,
            scenario_type=scenario_data.scenario_type.value,
            severity=scenario_data.severity,
            time_horizon=scenario_data.time_horizon,
            parameters_json=scenario_data.parameters
        )
        
        # Save to database
        self.db.add(db_scenario)
        self.db.commit()
        self.db.refresh(db_scenario)
        
        # Convert to Pydantic schema
        return Scenario(
            id=str(db_scenario.id),
            name=db_scenario.name,
            scenario_type=ScenarioType(db_scenario.scenario_type),
            severity=db_scenario.severity,
            time_horizon=db_scenario.time_horizon,
            parameters=db_scenario.parameters_json,
            created_at=db_scenario.created_at
        )
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """
        Retrieve a scenario by ID
        
        Args:
            scenario_id: Scenario UUID
        
        Returns:
            Scenario if found, None otherwise
        """
        db_scenario = self.db.query(ScenarioModel).filter(
            ScenarioModel.id == scenario_id
        ).first()
        
        if not db_scenario:
            return None
        
        return Scenario(
            id=str(db_scenario.id),
            name=db_scenario.name,
            scenario_type=ScenarioType(db_scenario.scenario_type),
            severity=db_scenario.severity,
            time_horizon=db_scenario.time_horizon,
            parameters=db_scenario.parameters_json,
            created_at=db_scenario.created_at
        )
    
    def list_scenarios(self) -> List[Scenario]:
        """
        List all stored scenarios
        
        Returns:
            List of all scenarios
        """
        db_scenarios = self.db.query(ScenarioModel).order_by(
            ScenarioModel.created_at.desc()
        ).all()
        
        return [
            Scenario(
                id=str(s.id),
                name=s.name,
                scenario_type=ScenarioType(s.scenario_type),
                severity=s.severity,
                time_horizon=s.time_horizon,
                parameters=s.parameters_json,
                created_at=s.created_at
            )
            for s in db_scenarios
        ]
    
    def apply_scenario(
        self,
        portfolio_id: str,
        scenario_id: str,
        risk_calculation_service
    ) -> Dict[str, Any]:
        """
        Apply a scenario to a portfolio and trigger risk recalculation
        
        Args:
            portfolio_id: Portfolio UUID
            scenario_id: Scenario UUID
            risk_calculation_service: RiskCalculationService instance
        
        Returns:
            Risk calculation results with scenario-specific parameters applied
        
        **Validates: Requirements 4.3, 4.5**
        """
        # Verify scenario exists
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Trigger risk recalculation with scenario parameters
        # The risk calculation service will use scenario-specific severity and time_horizon
        results = risk_calculation_service.calculate_portfolio_risk(
            portfolio_id=portfolio_id,
            scenario_id=scenario_id
        )
        
        # Store scenario execution metadata
        # Results are already stored by risk_calculation_service
        
        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario.name,
            "scenario_type": scenario.scenario_type.value,
            "severity": scenario.severity,
            "time_horizon": scenario.time_horizon,
            "results": results
        }
    
    def compare_scenarios(
        self,
        portfolio_id: str,
        scenario_ids: List[str],
        risk_calculation_service
    ) -> Dict[str, Any]:
        """
        Compare multiple scenarios side-by-side for a portfolio
        
        Args:
            portfolio_id: Portfolio UUID
            scenario_ids: List of scenario UUIDs (max 4)
            risk_calculation_service: RiskCalculationService instance
        
        Returns:
            Comparison results with delta metrics between scenarios
        
        **Validates: Requirements 4.6**
        """
        if len(scenario_ids) > 4:
            raise ValueError("Maximum 4 scenarios can be compared simultaneously")
        
        if len(scenario_ids) < 2:
            raise ValueError("At least 2 scenarios required for comparison")
        
        # Retrieve results for each scenario
        scenario_results = []
        for scenario_id in scenario_ids:
            scenario = self.get_scenario(scenario_id)
            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            # Get or calculate risk results
            try:
                summary = risk_calculation_service.get_portfolio_summary(
                    portfolio_id=portfolio_id,
                    scenario_id=scenario_id
                )
            except ValueError:
                # Results don't exist, calculate them
                risk_calculation_service.calculate_portfolio_risk(
                    portfolio_id=portfolio_id,
                    scenario_id=scenario_id
                )
                summary = risk_calculation_service.get_portfolio_summary(
                    portfolio_id=portfolio_id,
                    scenario_id=scenario_id
                )
            
            scenario_results.append({
                "scenario_id": scenario_id,
                "scenario_name": scenario.name,
                "scenario_type": scenario.scenario_type.value,
                "severity": scenario.severity,
                "time_horizon": scenario.time_horizon,
                "portfolio_value": summary["portfolio_value"],
                "climate_var": summary["climate_var"],
                "stressed_drawdown": summary["stressed_drawdown"],
                "top_risks": summary["top_risks"]
            })
        
        # Calculate delta metrics between scenarios
        # Use first scenario as baseline
        baseline = scenario_results[0]
        deltas = []
        
        for i in range(1, len(scenario_results)):
            comparison = scenario_results[i]
            deltas.append({
                "from_scenario": baseline["scenario_name"],
                "to_scenario": comparison["scenario_name"],
                "climate_var_delta": comparison["climate_var"] - baseline["climate_var"],
                "climate_var_delta_pct": (
                    ((comparison["climate_var"] - baseline["climate_var"]) / baseline["climate_var"] * 100)
                    if baseline["climate_var"] > 0 else 0
                ),
                "stressed_drawdown_delta": comparison["stressed_drawdown"] - baseline["stressed_drawdown"],
                "stressed_drawdown_delta_pct": (
                    ((comparison["stressed_drawdown"] - baseline["stressed_drawdown"]) / baseline["stressed_drawdown"] * 100)
                    if baseline["stressed_drawdown"] > 0 else 0
                )
            })
        
        # Identify scenario with highest risk
        highest_risk_scenario = max(
            scenario_results,
            key=lambda s: s["climate_var"]
        )
        
        return {
            "portfolio_id": portfolio_id,
            "scenarios": scenario_results,
            "deltas": deltas,
            "highest_risk_scenario": {
                "scenario_id": highest_risk_scenario["scenario_id"],
                "scenario_name": highest_risk_scenario["scenario_name"],
                "climate_var": highest_risk_scenario["climate_var"]
            }
        }
