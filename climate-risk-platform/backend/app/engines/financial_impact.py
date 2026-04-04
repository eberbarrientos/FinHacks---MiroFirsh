"""Financial Impact Engine for calculating expected losses and portfolio metrics"""

from typing import List, Dict, Tuple, Optional
from decimal import Decimal

from app.schemas.holding import Holding
from app.schemas.scenario import Scenario
from app.schemas.enums import ScenarioType


class ConcentrationMetrics:
    """Container for concentration risk metrics"""
    def __init__(self):
        self.sector_concentration: Dict[str, float] = {}
        self.geography_concentration: Dict[str, float] = {}
        self.issuer_concentration: Dict[str, float] = {}
        self.sector_penalty: float = 0.0
        self.geography_penalty: float = 0.0
        self.issuer_penalty: float = 0.0
        self.total_penalty: float = 0.0


class FinancialImpactEngine:
    """
    Engine for computing financial impact metrics from climate risk scores.
    
    Calculates:
    - Expected loss for individual holdings
    - Portfolio-level climate VaR
    - Stressed drawdown percentages
    - Issuer-aggregated losses
    - Concentration risks and penalties
    """
    
    # Concentration thresholds
    SECTOR_CONCENTRATION_THRESHOLD = 0.25  # 25%
    GEOGRAPHY_CONCENTRATION_THRESHOLD = 0.15  # 15%
    ISSUER_CONCENTRATION_THRESHOLD = 0.05  # 5%
    
    # Concentration penalty factors
    SECTOR_PENALTY_FACTOR = 1.2
    GEOGRAPHY_PENALTY_FACTOR = 1.15
    ISSUER_PENALTY_FACTOR = 1.1
    
    # Business interruption factors by sector
    BUSINESS_INTERRUPTION_FACTORS = {
        "Utilities": 0.85,
        "Energy": 0.80,
        "Oil & Gas": 0.80,
        "Transportation": 0.75,
        "Materials": 0.70,
        "Industrials": 0.70,
        "Real Estate": 0.65,
        "Consumer Discretionary": 0.60,
        "Consumer Staples": 0.55,
        "Financials": 0.50,
        "Healthcare": 0.45,
        "Technology": 0.40,
        "Information Technology": 0.40,
        "Communication Services": 0.35,
        "Services": 0.35,
    }
    
    def calculate_expected_loss(
        self,
        holding: Holding,
        combined_risk_score: float,
        scenario: Scenario
    ) -> float:
        """
        Calculate expected loss for a holding.
        
        Formula: market_value * damage_ratio * business_interruption_factor * insurance_gap_factor
        
        Args:
            holding: The holding to assess
            combined_risk_score: The combined risk score (0-100)
            scenario: The climate scenario being applied
            
        Returns:
            Expected loss in monetary units
        """
        market_value = float(holding.market_value)
        
        # Calculate damage ratio based on combined risk score and scenario severity
        damage_ratio = self._calculate_damage_ratio(combined_risk_score, scenario)
        
        # Calculate business interruption factor based on sector and asset type
        business_interruption_factor = self._calculate_business_interruption_factor(
            holding.sector, holding.asset_type
        )
        
        # Calculate insurance gap factor
        insurance_gap_factor = self._calculate_insurance_gap_factor(
            holding.insurance_dependency_score
        )
        
        # Calculate expected loss
        expected_loss = (
            market_value * 
            damage_ratio * 
            business_interruption_factor * 
            insurance_gap_factor
        )
        
        return round(expected_loss, 2)
    
    def compute_portfolio_var(
        self,
        holdings: List[Holding],
        risk_scores: Dict[str, float],
        scenario: Scenario
    ) -> float:
        """
        Compute portfolio climate VaR as sum of expected losses across all holdings.
        
        Args:
            holdings: List of portfolio holdings
            risk_scores: Dictionary mapping holding_id to combined_risk_score
            scenario: The climate scenario being applied
            
        Returns:
            Portfolio climate VaR (total expected loss)
        """
        total_var = 0.0
        
        for holding in holdings:
            combined_score = risk_scores.get(holding.id, 0.0)
            expected_loss = self.calculate_expected_loss(holding, combined_score, scenario)
            total_var += expected_loss
        
        return round(total_var, 2)
    
    def calculate_stressed_drawdown(
        self,
        portfolio_climate_var: float,
        total_portfolio_value: float
    ) -> float:
        """
        Calculate stressed drawdown as percentage decline in portfolio value.
        
        Args:
            portfolio_climate_var: Total expected loss under scenario
            total_portfolio_value: Total market value of portfolio
            
        Returns:
            Stressed drawdown as percentage (0-100)
        """
        if total_portfolio_value <= 0:
            return 0.0
        
        drawdown_pct = (portfolio_climate_var / total_portfolio_value) * 100.0
        
        return round(min(100.0, drawdown_pct), 2)
    
    def aggregate_by_issuer(
        self,
        holdings: List[Holding],
        risk_scores: Dict[str, float],
        scenario: Scenario
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate losses by issuer to compute issuer-level risk.
        
        Args:
            holdings: List of portfolio holdings
            risk_scores: Dictionary mapping holding_id to combined_risk_score
            scenario: The climate scenario being applied
            
        Returns:
            Dictionary mapping issuer_name to aggregated metrics:
            {
                "issuer_name": {
                    "aggregated_loss": float,
                    "total_market_value": float,
                    "loss_percentage": float,
                    "holdings_count": int
                }
            }
        """
        issuer_data: Dict[str, Dict[str, any]] = {}
        
        for holding in holdings:
            issuer = holding.issuer_name
            combined_score = risk_scores.get(holding.id, 0.0)
            expected_loss = self.calculate_expected_loss(holding, combined_score, scenario)
            market_value = float(holding.market_value)
            
            if issuer not in issuer_data:
                issuer_data[issuer] = {
                    "aggregated_loss": 0.0,
                    "total_market_value": 0.0,
                    "holdings_count": 0
                }
            
            issuer_data[issuer]["aggregated_loss"] += expected_loss
            issuer_data[issuer]["total_market_value"] += market_value
            issuer_data[issuer]["holdings_count"] += 1
        
        # Calculate loss percentage for each issuer
        for issuer, data in issuer_data.items():
            if data["total_market_value"] > 0:
                data["loss_percentage"] = round(
                    (data["aggregated_loss"] / data["total_market_value"]) * 100.0,
                    2
                )
            else:
                data["loss_percentage"] = 0.0
            
            # Round aggregated values
            data["aggregated_loss"] = round(data["aggregated_loss"], 2)
            data["total_market_value"] = round(data["total_market_value"], 2)
        
        return issuer_data
    
    def compute_concentration_risk(
        self,
        holdings: List[Holding],
        total_portfolio_value: float
    ) -> ConcentrationMetrics:
        """
        Compute concentration risks across sectors, geographies, and issuers.
        
        Args:
            holdings: List of portfolio holdings
            total_portfolio_value: Total market value of portfolio
            
        Returns:
            ConcentrationMetrics object with concentration percentages and penalties
        """
        metrics = ConcentrationMetrics()
        
        if total_portfolio_value <= 0:
            return metrics
        
        # Calculate sector concentration
        sector_values: Dict[str, float] = {}
        for holding in holdings:
            sector = holding.sector or "Unknown"
            market_value = float(holding.market_value)
            sector_values[sector] = sector_values.get(sector, 0.0) + market_value
        
        for sector, value in sector_values.items():
            concentration_pct = (value / total_portfolio_value) * 100.0
            metrics.sector_concentration[sector] = round(concentration_pct, 2)
            
            # Apply penalty if threshold exceeded
            if concentration_pct > (self.SECTOR_CONCENTRATION_THRESHOLD * 100):
                metrics.sector_penalty += (
                    (concentration_pct / 100.0 - self.SECTOR_CONCENTRATION_THRESHOLD) * 
                    self.SECTOR_PENALTY_FACTOR
                )
        
        # Calculate geography concentration
        geography_values: Dict[str, float] = {}
        for holding in holdings:
            region = holding.state_region or holding.country or "Unknown"
            market_value = float(holding.market_value)
            geography_values[region] = geography_values.get(region, 0.0) + market_value
        
        for region, value in geography_values.items():
            concentration_pct = (value / total_portfolio_value) * 100.0
            metrics.geography_concentration[region] = round(concentration_pct, 2)
            
            # Apply penalty if threshold exceeded
            if concentration_pct > (self.GEOGRAPHY_CONCENTRATION_THRESHOLD * 100):
                metrics.geography_penalty += (
                    (concentration_pct / 100.0 - self.GEOGRAPHY_CONCENTRATION_THRESHOLD) * 
                    self.GEOGRAPHY_PENALTY_FACTOR
                )
        
        # Calculate issuer concentration
        issuer_values: Dict[str, float] = {}
        for holding in holdings:
            issuer = holding.issuer_name
            market_value = float(holding.market_value)
            issuer_values[issuer] = issuer_values.get(issuer, 0.0) + market_value
        
        for issuer, value in issuer_values.items():
            concentration_pct = (value / total_portfolio_value) * 100.0
            metrics.issuer_concentration[issuer] = round(concentration_pct, 2)
            
            # Apply penalty if threshold exceeded
            if concentration_pct > (self.ISSUER_CONCENTRATION_THRESHOLD * 100):
                metrics.issuer_penalty += (
                    (concentration_pct / 100.0 - self.ISSUER_CONCENTRATION_THRESHOLD) * 
                    self.ISSUER_PENALTY_FACTOR
                )
        
        # Calculate total penalty
        metrics.total_penalty = round(
            metrics.sector_penalty + metrics.geography_penalty + metrics.issuer_penalty,
            2
        )
        
        # Round penalty values
        metrics.sector_penalty = round(metrics.sector_penalty, 2)
        metrics.geography_penalty = round(metrics.geography_penalty, 2)
        metrics.issuer_penalty = round(metrics.issuer_penalty, 2)
        
        return metrics
    
    # Private helper methods
    
    def _calculate_damage_ratio(self, combined_risk_score: float, scenario: Scenario) -> float:
        """
        Calculate damage ratio based on combined risk score and scenario severity.
        
        Args:
            combined_risk_score: Combined risk score (0-100)
            scenario: The climate scenario
            
        Returns:
            Damage ratio (0.0-1.0)
        """
        # Base damage ratio from risk score (0-100 maps to 0.0-0.8)
        base_damage = (combined_risk_score / 100.0) * 0.8
        
        # Apply severity multiplier
        severity_multipliers = {
            "low": 0.6,
            "medium": 1.0,
            "high": 1.4,
            "extreme": 1.8,
        }
        severity_multiplier = severity_multipliers.get(scenario.severity.lower(), 1.0)
        
        # Calculate final damage ratio
        damage_ratio = base_damage * severity_multiplier
        
        # Cap at 1.0 (100% loss)
        return min(1.0, damage_ratio)
    
    def _calculate_business_interruption_factor(
        self,
        sector: str,
        asset_type: str
    ) -> float:
        """
        Calculate business interruption factor based on sector and asset type.
        
        Args:
            sector: The sector of the holding
            asset_type: The type of asset
            
        Returns:
            Business interruption factor (0.0-1.0)
        """
        # Get base factor from sector
        base_factor = self.BUSINESS_INTERRUPTION_FACTORS.get(sector, 0.50)
        
        # Adjust based on asset type
        asset_type_lower = asset_type.lower() if asset_type else ""
        
        if "infrastructure" in asset_type_lower or "utility" in asset_type_lower:
            # Infrastructure has higher interruption impact
            base_factor *= 1.2
        elif "real estate" in asset_type_lower or "property" in asset_type_lower:
            # Real estate has moderate interruption impact
            base_factor *= 1.0
        elif "equity" in asset_type_lower or "stock" in asset_type_lower:
            # Equities have lower direct interruption impact
            base_factor *= 0.8
        elif "bond" in asset_type_lower or "debt" in asset_type_lower:
            # Bonds have lower interruption impact
            base_factor *= 0.7
        
        # Cap at 1.0
        return min(1.0, base_factor)
    
    def _calculate_insurance_gap_factor(
        self,
        insurance_dependency_score: Optional[Decimal]
    ) -> float:
        """
        Calculate insurance gap factor from insurance dependency score.
        
        Higher insurance dependency with potential gaps increases loss exposure.
        
        Args:
            insurance_dependency_score: Insurance dependency score (0-100) or None
            
        Returns:
            Insurance gap factor (0.5-1.0)
        """
        if insurance_dependency_score is None:
            # Default to moderate gap if data missing
            return 0.75
        
        score = float(insurance_dependency_score)
        
        # Higher dependency means higher potential gap
        # Score 0 = 0.5 factor (50% loss exposure)
        # Score 100 = 1.0 factor (100% loss exposure)
        gap_factor = 0.5 + (score / 100.0) * 0.5
        
        return gap_factor
