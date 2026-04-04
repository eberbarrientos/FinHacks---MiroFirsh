"""Risk Calculation Service for orchestrating climate risk analysis"""

from typing import List, Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
import redis
import json
import logging

from app.engines.exposure import ClimateExposureEngine
from app.engines.financial_impact import FinancialImpactEngine, ConcentrationMetrics
from app.models.risk_result import RiskResult as RiskResultModel
from app.models.holding import Holding as HoldingModel
from app.models.scenario import Scenario as ScenarioModel
from app.schemas.holding import Holding
from app.schemas.scenario import Scenario
from app.schemas.risk_result import RiskResult
from app.config import settings

logger = logging.getLogger(__name__)


class RiskCalculationService:
    """
    Service for orchestrating risk calculations across portfolios.
    
    Responsibilities:
    - Orchestrate calls to ClimateExposureEngine and FinancialImpactEngine
    - Store risk results in database
    - Cache calculated results in Redis
    - Provide portfolio-level summary metrics
    """
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the risk calculation service.
        
        Args:
            db: Database session
            redis_client: Optional Redis client for caching
        """
        self.db = db
        self.redis_client = redis_client
        self.exposure_engine = ClimateExposureEngine()
        self.financial_engine = FinancialImpactEngine()
    
    def calculate_portfolio_risk(
        self,
        portfolio_id: str,
        scenario_id: str
    ) -> Dict[str, any]:
        """
        Calculate risk for all holdings in a portfolio under a given scenario.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            
        Returns:
            Dictionary containing:
            - holdings_count: Number of holdings processed
            - portfolio_metrics: Portfolio-level risk metrics
            - calculation_time: Time taken for calculation
        """
        logger.info(f"Starting risk calculation for portfolio {portfolio_id}, scenario {scenario_id}")
        
        # Check cache first
        cache_key = f"risk_calc:{portfolio_id}:{scenario_id}"
        if self.redis_client:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Returning cached result for {cache_key}")
                return cached_result
        
        # Fetch holdings and scenario from database
        holdings = self.db.query(HoldingModel).filter(
            HoldingModel.portfolio_id == portfolio_id
        ).all()
        
        if not holdings:
            raise ValueError(f"No holdings found for portfolio {portfolio_id}")
        
        scenario = self.db.query(ScenarioModel).filter(
            ScenarioModel.id == scenario_id
        ).first()
        
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Convert to Pydantic schemas
        holding_schemas = [Holding.model_validate(h) for h in holdings]
        scenario_schema = Scenario.model_validate(scenario)
        
        # Calculate risk for each holding
        risk_scores = {}
        risk_results = []
        
        for holding in holding_schemas:
            # Calculate exposure scores
            physical_score = self.exposure_engine.compute_physical_score(
                holding, scenario_schema
            )
            transition_score = self.exposure_engine.compute_transition_score(
                holding, scenario_schema
            )
            combined_score = self.exposure_engine.compute_combined_score(
                physical_score, transition_score
            )
            confidence = self.exposure_engine.assign_confidence(holding)
            
            # Calculate financial impact
            expected_loss = self.financial_engine.calculate_expected_loss(
                holding, combined_score, scenario_schema
            )
            
            # Store risk score for portfolio-level calculations
            risk_scores[holding.id] = combined_score
            
            # Create risk result
            risk_result = {
                "holding_id": holding.id,
                "physical_score": physical_score,
                "transition_score": transition_score,
                "combined_score": combined_score,
                "expected_loss": expected_loss,
                "confidence": confidence.value,
            }
            risk_results.append(risk_result)
            
            # Store in database
            self._store_risk_result(
                portfolio_id=portfolio_id,
                holding_id=holding.id,
                scenario_id=scenario_id,
                physical_score=physical_score,
                transition_score=transition_score,
                combined_score=combined_score,
                expected_loss=expected_loss,
                confidence=confidence.value,
            )
        
        # Calculate portfolio-level metrics
        total_portfolio_value = sum(float(h.market_value) for h in holding_schemas)
        portfolio_climate_var = self.financial_engine.compute_portfolio_var(
            holding_schemas, risk_scores, scenario_schema
        )
        stressed_drawdown = self.financial_engine.calculate_stressed_drawdown(
            portfolio_climate_var, total_portfolio_value
        )
        
        # Calculate issuer aggregation
        issuer_aggregated = self.financial_engine.aggregate_by_issuer(
            holding_schemas, risk_scores, scenario_schema
        )
        
        # Calculate concentration risks
        concentration_metrics = self.financial_engine.compute_concentration_risk(
            holding_schemas, total_portfolio_value
        )
        
        # Identify top risks
        top_hotspot = self._identify_top_hotspot(holding_schemas, risk_scores)
        top_sector_risk = self._identify_top_sector_risk(
            holding_schemas, risk_scores, concentration_metrics
        )
        
        # Prepare result
        result = {
            "holdings_count": len(holdings),
            "portfolio_metrics": {
                "portfolio_value": round(total_portfolio_value, 2),
                "climate_var": round(portfolio_climate_var, 2),
                "stressed_drawdown": round(stressed_drawdown, 2),
                "top_hotspot": top_hotspot,
                "top_sector_risk": top_sector_risk,
                "issuer_aggregated": issuer_aggregated,
                "concentration_metrics": {
                    "sector_concentration": concentration_metrics.sector_concentration,
                    "geography_concentration": concentration_metrics.geography_concentration,
                    "issuer_concentration": concentration_metrics.issuer_concentration,
                    "sector_penalty": float(concentration_metrics.sector_penalty),
                    "geography_penalty": float(concentration_metrics.geography_penalty),
                    "issuer_penalty": float(concentration_metrics.issuer_penalty),
                    "total_penalty": float(concentration_metrics.total_penalty),
                }
            },
            "risk_results": risk_results,
        }
        
        # Cache the result
        if self.redis_client:
            self._store_in_cache(cache_key, result)
        
        logger.info(f"Risk calculation completed for portfolio {portfolio_id}")
        return result
    
    def get_risk_results(
        self,
        portfolio_id: str,
        scenario_id: str
    ) -> List[Dict[str, any]]:
        """
        Retrieve stored risk results for a portfolio and scenario.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            
        Returns:
            List of risk results with holding details
        """
        # Check cache first
        cache_key = f"risk_results:{portfolio_id}:{scenario_id}"
        if self.redis_client:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
        
        # Query from database
        results = self.db.query(RiskResultModel).filter(
            RiskResultModel.portfolio_id == portfolio_id,
            RiskResultModel.scenario_id == scenario_id
        ).all()
        
        # Convert to dict with holding details
        risk_results = []
        for result in results:
            holding = self.db.query(HoldingModel).filter(
                HoldingModel.id == result.holding_id
            ).first()
            
            if holding:
                risk_results.append({
                    "holding_id": str(result.holding_id),
                    "asset_name": holding.asset_name,
                    "issuer_name": holding.issuer_name,
                    "sector": holding.sector,
                    "market_value": float(holding.market_value),
                    "physical_score": float(result.physical_score),
                    "transition_score": float(result.transition_score),
                    "combined_score": float(result.combined_score),
                    "expected_loss": float(result.expected_loss),
                    "confidence": result.confidence,
                    "calculated_at": result.calculated_at.isoformat(),
                })
        
        # Cache the results
        if self.redis_client:
            self._store_in_cache(cache_key, risk_results)
        
        return risk_results
    
    def get_portfolio_summary(
        self,
        portfolio_id: str,
        scenario_id: str
    ) -> Dict[str, any]:
        """
        Get portfolio-level summary metrics for a scenario.
        
        Args:
            portfolio_id: UUID of the portfolio
            scenario_id: UUID of the scenario
            
        Returns:
            Dictionary with portfolio summary metrics
        """
        # Check cache first
        cache_key = f"risk_summary:{portfolio_id}:{scenario_id}"
        if self.redis_client:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
        
        # Get risk results
        results = self.db.query(RiskResultModel).filter(
            RiskResultModel.portfolio_id == portfolio_id,
            RiskResultModel.scenario_id == scenario_id
        ).all()
        
        if not results:
            raise ValueError(f"No risk results found for portfolio {portfolio_id} and scenario {scenario_id}")
        
        # Get holdings
        holdings = self.db.query(HoldingModel).filter(
            HoldingModel.portfolio_id == portfolio_id
        ).all()
        
        # Calculate summary metrics
        total_portfolio_value = sum(float(h.market_value) for h in holdings)
        total_expected_loss = sum(float(r.expected_loss) for r in results)
        stressed_drawdown = (total_expected_loss / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # Get top risks
        top_risks = sorted(
            results,
            key=lambda r: float(r.combined_score),
            reverse=True
        )[:10]
        
        top_risk_holdings = []
        for risk in top_risks:
            holding = next((h for h in holdings if h.id == risk.holding_id), None)
            if holding:
                top_risk_holdings.append({
                    "asset_name": holding.asset_name,
                    "issuer_name": holding.issuer_name,
                    "combined_score": float(risk.combined_score),
                    "expected_loss": float(risk.expected_loss),
                })
        
        summary = {
            "portfolio_value": round(total_portfolio_value, 2),
            "climate_var": round(total_expected_loss, 2),
            "stressed_drawdown": round(stressed_drawdown, 2),
            "holdings_count": len(holdings),
            "top_risks": top_risk_holdings,
        }
        
        # Cache the summary
        if self.redis_client:
            self._store_in_cache(cache_key, summary)
        
        return summary
    
    def _store_risk_result(
        self,
        portfolio_id: str,
        holding_id: str,
        scenario_id: str,
        physical_score: float,
        transition_score: float,
        combined_score: float,
        expected_loss: float,
        confidence: str,
    ) -> None:
        """Store risk result in database, updating if exists."""
        # Check if result already exists
        existing = self.db.query(RiskResultModel).filter(
            RiskResultModel.holding_id == holding_id,
            RiskResultModel.scenario_id == scenario_id
        ).first()
        
        if existing:
            # Update existing result
            existing.physical_score = Decimal(str(physical_score))
            existing.transition_score = Decimal(str(transition_score))
            existing.combined_score = Decimal(str(combined_score))
            existing.expected_loss = Decimal(str(expected_loss))
            existing.confidence = confidence
        else:
            # Create new result
            risk_result = RiskResultModel(
                portfolio_id=portfolio_id,
                holding_id=holding_id,
                scenario_id=scenario_id,
                physical_score=Decimal(str(physical_score)),
                transition_score=Decimal(str(transition_score)),
                combined_score=Decimal(str(combined_score)),
                expected_loss=Decimal(str(expected_loss)),
                stressed_return_delta=Decimal("0.0"),  # Placeholder
                confidence=confidence,
            )
            self.db.add(risk_result)
        
        self.db.commit()
    
    def _identify_top_hotspot(
        self,
        holdings: List[Holding],
        risk_scores: Dict[str, float]
    ) -> str:
        """Identify geographic region with highest risk concentration."""
        region_risks: Dict[str, List[float]] = {}
        
        for holding in holdings:
            region = holding.state_region or holding.country or "Unknown"
            score = risk_scores.get(holding.id, 0.0)
            
            if region not in region_risks:
                region_risks[region] = []
            region_risks[region].append(score)
        
        # Calculate average risk per region
        region_avg_risks = {
            region: sum(scores) / len(scores)
            for region, scores in region_risks.items()
        }
        
        # Return region with highest average risk
        if region_avg_risks:
            top_region = max(region_avg_risks.items(), key=lambda x: x[1])
            return top_region[0]
        
        return "Unknown"
    
    def _identify_top_sector_risk(
        self,
        holdings: List[Holding],
        risk_scores: Dict[str, float],
        concentration_metrics: ConcentrationMetrics
    ) -> str:
        """Identify sector with highest combined risk and concentration."""
        sector_risks: Dict[str, List[float]] = {}
        
        for holding in holdings:
            sector = holding.sector or "Unknown"
            score = risk_scores.get(holding.id, 0.0)
            
            if sector not in sector_risks:
                sector_risks[sector] = []
            sector_risks[sector].append(score)
        
        # Calculate average risk per sector
        sector_avg_risks = {
            sector: sum(scores) / len(scores)
            for sector, scores in sector_risks.items()
        }
        
        # Weight by concentration
        sector_weighted_risks = {}
        for sector, avg_risk in sector_avg_risks.items():
            concentration = concentration_metrics.sector_concentration.get(sector, 0.0)
            sector_weighted_risks[sector] = avg_risk * (1 + concentration / 100.0)
        
        # Return sector with highest weighted risk
        if sector_weighted_risks:
            top_sector = max(sector_weighted_risks.items(), key=lambda x: x[1])
            return top_sector[0]
        
        return "Unknown"
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Retrieve data from Redis cache."""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                logger.debug(f"Cache hit for {key}")
                return json.loads(cached_data)
            logger.debug(f"Cache miss for {key}")
        except Exception as e:
            logger.warning(f"Cache retrieval failed for {key}: {e}")
        return None
    
    def _store_in_cache(self, key: str, data: Dict, ttl: Optional[int] = None) -> None:
        """
        Store data in Redis cache with TTL.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (defaults to settings.redis_ttl)
        """
        try:
            cache_ttl = ttl or settings.redis_ttl
            self.redis_client.setex(
                key,
                cache_ttl,
                json.dumps(data, default=str)
            )
            logger.debug(f"Cached data for {key} with TTL {cache_ttl}s")
        except Exception as e:
            logger.warning(f"Cache storage failed for {key}: {e}")
    
    def invalidate_cache(self, portfolio_id: str, scenario_id: Optional[str] = None) -> None:
        """
        Invalidate cached results for a portfolio and optionally a specific scenario.
        
        Args:
            portfolio_id: Portfolio UUID
            scenario_id: Optional scenario UUID. If None, invalidates all scenarios for the portfolio.
        """
        if not self.redis_client:
            return
        
        try:
            if scenario_id:
                # Invalidate specific scenario
                keys_to_delete = [
                    f"risk_calc:{portfolio_id}:{scenario_id}",
                    f"risk_results:{portfolio_id}:{scenario_id}",
                    f"risk_summary:{portfolio_id}:{scenario_id}"
                ]
                deleted = self.redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {deleted} cache keys for portfolio {portfolio_id}, scenario {scenario_id}")
            else:
                # Invalidate all scenarios for portfolio
                pattern = f"*:{portfolio_id}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {deleted} cache keys for portfolio {portfolio_id}")
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
