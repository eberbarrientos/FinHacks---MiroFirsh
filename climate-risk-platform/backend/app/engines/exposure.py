"""Climate Exposure Engine for calculating physical and transition risk scores"""

import math
from typing import Optional
from decimal import Decimal

from app.schemas.holding import Holding
from app.schemas.scenario import Scenario
from app.schemas.enums import ScenarioType, ConfidenceLevel


class ClimateExposureEngine:
    """
    Engine for computing climate risk exposure scores.
    
    Calculates:
    - Physical risk scores based on geographic hazard exposure
    - Transition risk scores based on carbon intensity and sector policy exposure
    - Combined risk scores
    - Confidence levels based on data completeness
    """
    
    # Hazard weights for physical risk calculation
    HAZARD_WEIGHTS = {
        "flood": 0.25,
        "hurricane": 0.20,
        "wildfire": 0.20,
        "heatwave": 0.15,
        "drought": 0.10,
        "storm": 0.10,
    }
    
    # Sector policy exposure weights for transition risk
    SECTOR_POLICY_WEIGHTS = {
        # High exposure sectors
        "Utilities": 0.90,
        "Energy": 0.85,
        "Oil & Gas": 0.85,
        "Transportation": 0.75,
        "Materials": 0.70,
        "Industrials": 0.65,
        
        # Medium exposure sectors
        "Real Estate": 0.50,
        "Consumer Discretionary": 0.45,
        "Consumer Staples": 0.40,
        "Financials": 0.35,
        
        # Low exposure sectors
        "Healthcare": 0.25,
        "Technology": 0.20,
        "Information Technology": 0.20,
        "Communication Services": 0.20,
        "Services": 0.15,
    }
    
    # Physical risk score weights
    PHYSICAL_WEIGHT = 0.65
    TRANSITION_WEIGHT = 0.35
    
    def compute_physical_score(self, holding: Holding, scenario: Scenario) -> float:
        """
        Compute physical risk score based on geographic hazard exposure.
        
        Args:
            holding: The holding to assess
            scenario: The climate scenario to apply
            
        Returns:
            Physical risk score normalized to 0-100 range
        """
        latitude = float(holding.latitude) if holding.latitude else 0.0
        longitude = float(holding.longitude) if holding.longitude else 0.0
        
        # Calculate individual hazard intensities based on location
        hazard_scores = {
            "flood": self._calculate_flood_intensity(latitude, longitude, scenario),
            "hurricane": self._calculate_hurricane_intensity(latitude, longitude, scenario),
            "wildfire": self._calculate_wildfire_intensity(latitude, longitude, scenario),
            "heatwave": self._calculate_heatwave_intensity(latitude, longitude, scenario),
            "drought": self._calculate_drought_intensity(latitude, longitude, scenario),
            "storm": self._calculate_storm_intensity(latitude, longitude, scenario),
        }
        
        # Apply scenario-specific amplification
        severity_multiplier = self._get_severity_multiplier(scenario.severity)
        
        # Calculate weighted sum
        weighted_score = sum(
            hazard_scores[hazard] * weight * severity_multiplier
            for hazard, weight in self.HAZARD_WEIGHTS.items()
        )
        
        # Normalize to 0-100 range
        normalized_score = min(100.0, max(0.0, weighted_score))
        
        return round(normalized_score, 2)
    
    def compute_transition_score(self, holding: Holding, scenario: Scenario) -> float:
        """
        Compute transition risk score based on carbon intensity, sector policy exposure,
        and regulatory vulnerability.
        
        Args:
            holding: The holding to assess
            scenario: The climate scenario to apply
            
        Returns:
            Transition risk score normalized to 0-100 range
        """
        # Carbon intensity component (0-40 points)
        carbon_score = self._calculate_carbon_score(holding)
        
        # Sector policy exposure component (0-40 points)
        sector_score = self._calculate_sector_policy_score(holding)
        
        # Regulatory vulnerability component (0-20 points)
        regulatory_score = self._calculate_regulatory_score(holding, scenario)
        
        # Apply scenario-specific amplification for transition scenarios
        if scenario.scenario_type in [ScenarioType.CARBON_TAX, ScenarioType.EMISSIONS_REGULATION]:
            severity_multiplier = self._get_severity_multiplier(scenario.severity)
        else:
            severity_multiplier = 1.0
        
        # Calculate total transition score
        total_score = (carbon_score + sector_score + regulatory_score) * severity_multiplier
        
        # Normalize to 0-100 range
        normalized_score = min(100.0, max(0.0, total_score))
        
        return round(normalized_score, 2)
    
    def compute_combined_score(self, physical_score: float, transition_score: float) -> float:
        """
        Compute combined risk score as weighted average of physical and transition scores.
        
        Args:
            physical_score: Physical risk score (0-100)
            transition_score: Transition risk score (0-100)
            
        Returns:
            Combined risk score (0-100)
        """
        combined = (self.PHYSICAL_WEIGHT * physical_score + 
                   self.TRANSITION_WEIGHT * transition_score)
        
        return round(combined, 2)
    
    def assign_confidence(self, holding: Holding) -> ConfidenceLevel:
        """
        Assign confidence level based on data completeness.
        
        Args:
            holding: The holding to assess
            
        Returns:
            Confidence level (HIGH, MEDIUM, or LOW)
        """
        # Count optional fields that are present
        optional_fields = [
            holding.revenue_exposure_pct,
            holding.carbon_intensity_proxy,
            holding.insurance_dependency_score,
            holding.supply_chain_dependency_score,
        ]
        
        present_count = sum(1 for field in optional_fields if field is not None)
        total_optional = len(optional_fields)
        
        # Assign confidence based on completeness
        if present_count == total_optional:
            return ConfidenceLevel.HIGH
        elif present_count >= total_optional / 2:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    # Private helper methods for hazard intensity calculations
    
    def _calculate_flood_intensity(self, latitude: float, longitude: float, scenario: Scenario) -> float:
        """Calculate flood hazard intensity based on location."""
        # Coastal regions and river valleys have higher flood risk
        # Simplified model: higher risk near coasts and low latitudes
        coastal_proximity = self._estimate_coastal_proximity(latitude, longitude)
        base_intensity = 30.0 + (coastal_proximity * 40.0)
        
        # Amplify for flood scenarios
        if scenario.scenario_type == ScenarioType.FLOOD:
            base_intensity *= 1.5
        
        return min(100.0, base_intensity)
    
    def _calculate_hurricane_intensity(self, latitude: float, longitude: float, scenario: Scenario) -> float:
        """Calculate hurricane hazard intensity based on location."""
        # Hurricane risk concentrated in tropical/subtropical coastal regions
        # Peak risk: 10-40 degrees latitude, coastal areas
        lat_risk = 0.0
        if 10 <= abs(latitude) <= 40:
            # Peak risk around 20-30 degrees
            lat_risk = 100.0 - abs(abs(latitude) - 25) * 3.0
        
        coastal_proximity = self._estimate_coastal_proximity(latitude, longitude)
        base_intensity = lat_risk * coastal_proximity
        
        # Amplify for hurricane scenarios
        if scenario.scenario_type == ScenarioType.HURRICANE:
            base_intensity *= 1.8
        
        return min(100.0, max(0.0, base_intensity))
    
    def _calculate_wildfire_intensity(self, latitude: float, longitude: float, scenario: Scenario) -> float:
        """Calculate wildfire hazard intensity based on location."""
        # Wildfire risk higher in dry, temperate regions
        # Western US, Mediterranean climates, Australia
        lat_risk = 0.0
        if 25 <= abs(latitude) <= 50:
            lat_risk = 60.0
        elif 15 <= abs(latitude) < 25:
            lat_risk = 40.0
        
        # Simplified longitude-based risk (Western regions)
        lon_risk = 30.0
        if -125 <= longitude <= -100:  # Western US
            lon_risk = 70.0
        elif 110 <= longitude <= 155:  # Australia
            lon_risk = 65.0
        
        base_intensity = (lat_risk + lon_risk) / 2
        
        # Amplify for wildfire scenarios
        if scenario.scenario_type == ScenarioType.WILDFIRE:
            base_intensity *= 1.7
        
        return min(100.0, base_intensity)
    
    def _calculate_heatwave_intensity(self, latitude: float, longitude: float, scenario: Scenario) -> float:
        """Calculate heatwave hazard intensity based on location."""
        # Heatwave risk higher in lower latitudes and continental interiors
        lat_risk = max(0.0, 70.0 - abs(latitude) * 1.5)
        
        base_intensity = lat_risk
        
        # Amplify for heatwave scenarios
        if scenario.scenario_type == ScenarioType.HEATWAVE:
            base_intensity *= 1.6
        
        return min(100.0, base_intensity)
    
    def _calculate_drought_intensity(self, latitude: float, longitude: float, scenario: Scenario) -> float:
        """Calculate drought hazard intensity based on location."""
        # Drought risk varies by climate zone
        # Higher in semi-arid regions (20-40 degrees latitude)
        lat_risk = 0.0
        if 20 <= abs(latitude) <= 40:
            lat_risk = 60.0
        elif 10 <= abs(latitude) < 20 or 40 < abs(latitude) <= 50:
            lat_risk = 40.0
        else:
            lat_risk = 20.0
        
        base_intensity = lat_risk
        
        # Amplify for drought scenarios
        if scenario.scenario_type == ScenarioType.DROUGHT:
            base_intensity *= 1.5
        
        return min(100.0, base_intensity)
    
    def _calculate_storm_intensity(self, latitude: float, longitude: float, scenario: Scenario) -> float:
        """Calculate storm hazard intensity based on location."""
        # Storm risk present globally but varies by latitude
        # Mid-latitudes have higher storm frequency
        lat_risk = 40.0
        if 30 <= abs(latitude) <= 60:
            lat_risk = 60.0
        
        base_intensity = lat_risk
        
        return min(100.0, base_intensity)
    
    def _calculate_carbon_score(self, holding: Holding) -> float:
        """Calculate carbon intensity component of transition risk (0-40 points)."""
        if holding.carbon_intensity_proxy is None:
            # Default moderate score if data missing
            return 20.0
        
        carbon_intensity = float(holding.carbon_intensity_proxy)
        
        # Normalize carbon intensity to 0-40 scale
        # Assume carbon intensity range: 0-500 tons CO2e per unit
        normalized = min(40.0, (carbon_intensity / 500.0) * 40.0)
        
        return normalized
    
    def _calculate_sector_policy_score(self, holding: Holding) -> float:
        """Calculate sector policy exposure component (0-40 points)."""
        sector = holding.sector or "Unknown"
        
        # Get sector weight, default to medium exposure
        sector_weight = self.SECTOR_POLICY_WEIGHTS.get(sector, 0.50)
        
        # Scale to 0-40 points
        return sector_weight * 40.0
    
    def _calculate_regulatory_score(self, holding: Holding, scenario: Scenario) -> float:
        """Calculate regulatory vulnerability component (0-20 points)."""
        # Base regulatory risk
        base_risk = 10.0
        
        # Increase for high-carbon sectors
        sector = holding.sector or "Unknown"
        if sector in ["Utilities", "Energy", "Oil & Gas", "Transportation"]:
            base_risk = 15.0
        
        # Increase if supply chain dependencies are high
        if holding.supply_chain_dependency_score:
            supply_chain_factor = float(holding.supply_chain_dependency_score) / 100.0
            base_risk += supply_chain_factor * 5.0
        
        return min(20.0, base_risk)
    
    def _estimate_coastal_proximity(self, latitude: float, longitude: float) -> float:
        """
        Estimate proximity to coast (0.0 = inland, 1.0 = coastal).
        Simplified heuristic based on known coastal coordinates.
        """
        # Known coastal regions (simplified)
        coastal_regions = [
            # US East Coast
            (25, 45, -85, -65),
            # US West Coast
            (30, 50, -125, -115),
            # US Gulf Coast
            (25, 32, -100, -80),
            # European coasts
            (35, 70, -10, 30),
            # Asian coasts
            (20, 45, 100, 145),
        ]
        
        for lat_min, lat_max, lon_min, lon_max in coastal_regions:
            if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
                return 0.8
        
        # Default to moderate coastal proximity
        return 0.4
    
    def _get_severity_multiplier(self, severity: str) -> float:
        """Get multiplier based on scenario severity."""
        severity_map = {
            "low": 0.7,
            "medium": 1.0,
            "high": 1.5,
            "extreme": 2.0,
        }
        return severity_map.get(severity.lower(), 1.0)
