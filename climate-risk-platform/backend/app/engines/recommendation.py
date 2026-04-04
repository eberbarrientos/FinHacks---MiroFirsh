"""Recommendation Engine for portfolio optimization suggestions"""

from typing import List, Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.holding import Holding
from app.models.risk_result import RiskResult
from app.models.recommendation import Recommendation
from app.models.portfolio import Portfolio
from app.schemas.enums import RecommendationType

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Engine for generating portfolio optimization recommendations based on risk analysis.
    
    Analyzes risk results to identify:
    - High-risk holdings requiring rebalancing
    - Geographic concentration hotspots
    - Sector concentration requiring diversification
    - Issuers requiring watchlist monitoring
    - Insurance coverage gaps
    """
    
    def __init__(self, db: Session):
        """
        Initialize recommendation engine.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def generate_recommendations(
        self,
        portfolio_id: str,
        scenario_id: str
    ) -> List[Recommendation]:
        """
        Generate all recommendations for a portfolio under a scenario.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            
        Returns:
            List of Recommendation objects
        """
        logger.info(f"Generating recommendations for portfolio {portfolio_id}, scenario {scenario_id}")
        
        # Get portfolio and risk results
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        risk_results = self.db.query(RiskResult).filter(
            RiskResult.portfolio_id == portfolio_id,
            RiskResult.scenario_id == scenario_id
        ).all()
        
        if not risk_results:
            raise ValueError(f"No risk results found for portfolio {portfolio_id} and scenario {scenario_id}")
        
        # Get holdings with risk results
        holdings_with_risk = self._get_holdings_with_risk(risk_results)
        
        # Calculate total portfolio value
        total_value = sum(h["market_value"] for h in holdings_with_risk)
        
        recommendations = []
        
        # Generate rebalancing recommendations
        recommendations.extend(self._generate_rebalancing_recommendations(
            portfolio_id, scenario_id, holdings_with_risk, total_value
        ))
        
        # Identify geographic hotspots
        recommendations.extend(self._identify_geographic_hotspots(
            portfolio_id, scenario_id, holdings_with_risk, total_value
        ))
        
        # Check sector concentration
        recommendations.extend(self._check_sector_concentration(
            portfolio_id, scenario_id, holdings_with_risk, total_value
        ))
        
        # Flag watchlist issuers
        recommendations.extend(self._flag_watchlist_issuers(
            portfolio_id, scenario_id, holdings_with_risk
        ))
        
        # Check insurance coverage
        recommendations.extend(self._check_insurance_coverage(
            portfolio_id, scenario_id, holdings_with_risk
        ))
        
        # Ensure at least one recommendation
        if not recommendations:
            recommendations.append(self._create_default_recommendation(
                portfolio_id, scenario_id, total_value
            ))
        
        # Store recommendations in database
        for rec in recommendations:
            self.db.add(rec)
        
        self.db.commit()
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        
        return recommendations
    
    def _get_holdings_with_risk(self, risk_results: List[RiskResult]) -> List[Dict]:
        """
        Combine holdings with their risk results.
        
        Args:
            risk_results: List of RiskResult objects
            
        Returns:
            List of dictionaries with holding and risk data
        """
        holdings_with_risk = []
        
        for risk_result in risk_results:
            holding = self.db.query(Holding).filter(Holding.id == risk_result.holding_id).first()
            if holding:
                holdings_with_risk.append({
                    "holding_id": str(holding.id),
                    "asset_name": holding.asset_name,
                    "issuer_name": holding.issuer_name,
                    "sector": holding.sector,
                    "country": holding.country,
                    "state_region": holding.state_region,
                    "market_value": float(holding.market_value),
                    "combined_score": float(risk_result.combined_score),
                    "expected_loss": float(risk_result.expected_loss),
                    "insurance_dependency_score": float(holding.insurance_dependency_score) if holding.insurance_dependency_score else 0.0,
                })
        
        return holdings_with_risk
    
    def _generate_rebalancing_recommendations(
        self,
        portfolio_id: str,
        scenario_id: str,
        holdings_with_risk: List[Dict],
        total_value: float
    ) -> List[Recommendation]:
        """
        Generate rebalancing suggestions for high-risk holdings.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            holdings_with_risk: List of holdings with risk data
            total_value: Total portfolio value
            
        Returns:
            List of rebalancing recommendations
        """
        recommendations = []
        
        # Find holdings with combined_score > 75
        high_risk_holdings = [h for h in holdings_with_risk if h["combined_score"] > 75]
        
        if high_risk_holdings:
            # Sort by combined score descending
            high_risk_holdings.sort(key=lambda x: x["combined_score"], reverse=True)
            
            # Calculate total exposure and potential impact
            total_exposure = sum(h["market_value"] for h in high_risk_holdings)
            total_expected_loss = sum(h["expected_loss"] for h in high_risk_holdings)
            
            # Determine priority based on portfolio impact
            impact_pct = (total_exposure / total_value) * 100
            priority = self._calculate_priority(impact_pct)
            
            # Create recommendation
            affected_holding_ids = [h["holding_id"] for h in high_risk_holdings[:10]]  # Top 10
            
            message = (
                f"Consider rebalancing {len(high_risk_holdings)} holdings with combined risk scores above 75. "
                f"These holdings represent {impact_pct:.1f}% of portfolio value "
                f"with expected losses of ${total_expected_loss:,.0f}. "
                f"Top holdings: {', '.join([h['asset_name'] for h in high_risk_holdings[:3]])}."
            )
            
            rec = Recommendation(
                portfolio_id=portfolio_id,
                scenario_id=scenario_id,
                recommendation_type=RecommendationType.REBALANCE,
                priority=priority,
                message=message,
                affected_holdings=affected_holding_ids,
                potential_impact=Decimal(str(total_expected_loss))
            )
            
            recommendations.append(rec)
        
        return recommendations
    
    def _identify_geographic_hotspots(
        self,
        portfolio_id: str,
        scenario_id: str,
        holdings_with_risk: List[Dict],
        total_value: float
    ) -> List[Recommendation]:
        """
        Identify geographic regions with high concentration.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            holdings_with_risk: List of holdings with risk data
            total_value: Total portfolio value
            
        Returns:
            List of geographic hotspot recommendations
        """
        recommendations = []
        
        # Group by state/region
        region_exposure = {}
        region_loss = {}
        region_holdings = {}
        
        for holding in holdings_with_risk:
            region = holding.get("state_region") or holding.get("country") or "Unknown"
            
            if region not in region_exposure:
                region_exposure[region] = 0.0
                region_loss[region] = 0.0
                region_holdings[region] = []
            
            region_exposure[region] += holding["market_value"]
            region_loss[region] += holding["expected_loss"]
            region_holdings[region].append(holding)
        
        # Find regions exceeding 15% threshold
        hotspot_regions = []
        for region, exposure in region_exposure.items():
            exposure_pct = (exposure / total_value) * 100
            if exposure_pct > 15:
                hotspot_regions.append({
                    "region": region,
                    "exposure": exposure,
                    "exposure_pct": exposure_pct,
                    "expected_loss": region_loss[region],
                    "holdings": region_holdings[region]
                })
        
        # Create recommendations for each hotspot
        for hotspot in hotspot_regions:
            priority = self._calculate_priority(hotspot["exposure_pct"])
            
            affected_holding_ids = [h["holding_id"] for h in hotspot["holdings"][:10]]
            
            message = (
                f"Geographic concentration in {hotspot['region']} represents {hotspot['exposure_pct']:.1f}% "
                f"of portfolio value (${hotspot['exposure']:,.0f}). "
                f"Expected losses in this region: ${hotspot['expected_loss']:,.0f}. "
                f"Consider diversifying exposure across multiple regions."
            )
            
            rec = Recommendation(
                portfolio_id=portfolio_id,
                scenario_id=scenario_id,
                recommendation_type=RecommendationType.DIVERSIFY,
                priority=priority,
                message=message,
                affected_holdings=affected_holding_ids,
                potential_impact=Decimal(str(hotspot["expected_loss"]))
            )
            
            recommendations.append(rec)
        
        return recommendations
    
    def _check_sector_concentration(
        self,
        portfolio_id: str,
        scenario_id: str,
        holdings_with_risk: List[Dict],
        total_value: float
    ) -> List[Recommendation]:
        """
        Check for sector concentration requiring diversification.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            holdings_with_risk: List of holdings with risk data
            total_value: Total portfolio value
            
        Returns:
            List of sector diversification recommendations
        """
        recommendations = []
        
        # Group by sector
        sector_exposure = {}
        sector_loss = {}
        sector_holdings = {}
        
        for holding in holdings_with_risk:
            sector = holding.get("sector") or "Unknown"
            
            if sector not in sector_exposure:
                sector_exposure[sector] = 0.0
                sector_loss[sector] = 0.0
                sector_holdings[sector] = []
            
            sector_exposure[sector] += holding["market_value"]
            sector_loss[sector] += holding["expected_loss"]
            sector_holdings[sector].append(holding)
        
        # Find sectors exceeding 25% threshold
        concentrated_sectors = []
        for sector, exposure in sector_exposure.items():
            exposure_pct = (exposure / total_value) * 100
            if exposure_pct > 25:
                concentrated_sectors.append({
                    "sector": sector,
                    "exposure": exposure,
                    "exposure_pct": exposure_pct,
                    "expected_loss": sector_loss[sector],
                    "holdings": sector_holdings[sector]
                })
        
        # Create recommendations for each concentrated sector
        for sector_data in concentrated_sectors:
            priority = self._calculate_priority(sector_data["exposure_pct"])
            
            affected_holding_ids = [h["holding_id"] for h in sector_data["holdings"][:10]]
            
            message = (
                f"Sector concentration in {sector_data['sector']} represents {sector_data['exposure_pct']:.1f}% "
                f"of portfolio value (${sector_data['exposure']:,.0f}). "
                f"Expected losses in this sector: ${sector_data['expected_loss']:,.0f}. "
                f"Consider diversifying across multiple sectors to reduce concentration risk."
            )
            
            rec = Recommendation(
                portfolio_id=portfolio_id,
                scenario_id=scenario_id,
                recommendation_type=RecommendationType.DIVERSIFY,
                priority=priority,
                message=message,
                affected_holdings=affected_holding_ids,
                potential_impact=Decimal(str(sector_data["expected_loss"]))
            )
            
            recommendations.append(rec)
        
        return recommendations
    
    def _flag_watchlist_issuers(
        self,
        portfolio_id: str,
        scenario_id: str,
        holdings_with_risk: List[Dict]
    ) -> List[Recommendation]:
        """
        Flag issuers with high aggregated losses for watchlist.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            holdings_with_risk: List of holdings with risk data
            
        Returns:
            List of watchlist recommendations
        """
        recommendations = []
        
        # Group by issuer
        issuer_data = {}
        
        for holding in holdings_with_risk:
            issuer = holding.get("issuer_name") or "Unknown"
            
            if issuer not in issuer_data:
                issuer_data[issuer] = {
                    "total_value": 0.0,
                    "total_loss": 0.0,
                    "holdings": []
                }
            
            issuer_data[issuer]["total_value"] += holding["market_value"]
            issuer_data[issuer]["total_loss"] += holding["expected_loss"]
            issuer_data[issuer]["holdings"].append(holding)
        
        # Find issuers with aggregated_loss > 5% of issuer market value
        watchlist_issuers = []
        for issuer, data in issuer_data.items():
            if data["total_value"] > 0:
                loss_pct = (data["total_loss"] / data["total_value"]) * 100
                if loss_pct > 5:
                    watchlist_issuers.append({
                        "issuer": issuer,
                        "total_value": data["total_value"],
                        "total_loss": data["total_loss"],
                        "loss_pct": loss_pct,
                        "holdings": data["holdings"]
                    })
        
        # Create recommendations for watchlist issuers
        for issuer_info in watchlist_issuers:
            # Priority based on absolute loss amount
            impact_pct = (issuer_info["total_loss"] / issuer_info["total_value"]) * 100
            priority = self._calculate_priority(impact_pct)
            
            affected_holding_ids = [h["holding_id"] for h in issuer_info["holdings"]]
            
            message = (
                f"Issuer {issuer_info['issuer']} has aggregated losses of ${issuer_info['total_loss']:,.0f} "
                f"({issuer_info['loss_pct']:.1f}% of issuer exposure). "
                f"Total exposure: ${issuer_info['total_value']:,.0f}. "
                f"Add to watchlist for enhanced monitoring."
            )
            
            rec = Recommendation(
                portfolio_id=portfolio_id,
                scenario_id=scenario_id,
                recommendation_type=RecommendationType.WATCHLIST,
                priority=priority,
                message=message,
                affected_holdings=affected_holding_ids,
                potential_impact=Decimal(str(issuer_info["total_loss"]))
            )
            
            recommendations.append(rec)
        
        return recommendations
    
    def _check_insurance_coverage(
        self,
        portfolio_id: str,
        scenario_id: str,
        holdings_with_risk: List[Dict]
    ) -> List[Recommendation]:
        """
        Recommend insurance review for holdings with high dependency and losses.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            holdings_with_risk: List of holdings with risk data
            
        Returns:
            List of insurance review recommendations
        """
        recommendations = []
        
        # Find holdings with high insurance dependency (>60) and significant expected loss
        insurance_review_holdings = []
        
        for holding in holdings_with_risk:
            insurance_score = holding.get("insurance_dependency_score", 0.0)
            expected_loss = holding.get("expected_loss", 0.0)
            
            # High insurance dependency and loss > $500k
            if insurance_score > 60 and expected_loss > 500000:
                insurance_review_holdings.append(holding)
        
        if insurance_review_holdings:
            # Sort by expected loss descending
            insurance_review_holdings.sort(key=lambda x: x["expected_loss"], reverse=True)
            
            total_loss = sum(h["expected_loss"] for h in insurance_review_holdings)
            total_value = sum(h["market_value"] for h in insurance_review_holdings)
            
            # Calculate priority
            impact_pct = (total_loss / total_value) * 100 if total_value > 0 else 0
            priority = self._calculate_priority(impact_pct)
            
            affected_holding_ids = [h["holding_id"] for h in insurance_review_holdings[:10]]
            
            message = (
                f"Review insurance coverage for {len(insurance_review_holdings)} holdings "
                f"with high insurance dependency and significant expected losses. "
                f"Total expected losses: ${total_loss:,.0f}. "
                f"Top holdings: {', '.join([h['asset_name'] for h in insurance_review_holdings[:3]])}. "
                f"Verify coverage adequacy and consider additional protection."
            )
            
            rec = Recommendation(
                portfolio_id=portfolio_id,
                scenario_id=scenario_id,
                recommendation_type=RecommendationType.INSURANCE_REVIEW,
                priority=priority,
                message=message,
                affected_holdings=affected_holding_ids,
                potential_impact=Decimal(str(total_loss))
            )
            
            recommendations.append(rec)
        
        return recommendations
    
    def _calculate_priority(self, impact_pct: float) -> str:
        """
        Calculate priority level based on portfolio impact percentage.
        
        Args:
            impact_pct: Impact as percentage of portfolio
            
        Returns:
            Priority level: critical, high, medium, or low
        """
        if impact_pct > 10:
            return "critical"
        elif impact_pct > 5:
            return "high"
        elif impact_pct > 2:
            return "medium"
        else:
            return "low"
    
    def _create_default_recommendation(
        self,
        portfolio_id: str,
        scenario_id: str,
        total_value: float
    ) -> Recommendation:
        """
        Create a default recommendation when no specific issues found.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            total_value: Total portfolio value
            
        Returns:
            Default recommendation
        """
        message = (
            f"Portfolio shows balanced risk profile under this scenario. "
            f"Continue monitoring climate risk metrics and consider periodic rebalancing "
            f"to maintain diversification. Total portfolio value: ${total_value:,.0f}."
        )
        
        return Recommendation(
            portfolio_id=portfolio_id,
            scenario_id=scenario_id,
            recommendation_type=RecommendationType.DIVERSIFY,
            priority="low",
            message=message,
            affected_holdings=None,
            potential_impact=Decimal("0.00")
        )
