"""Tests for recommendation engine"""

import pytest
from decimal import Decimal
from app.engines.recommendation import RecommendationEngine
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.scenario import Scenario
from app.models.risk_result import RiskResult
from app.schemas.enums import RecommendationType


def test_generate_recommendations_rebalancing(db_session, sample_portfolio, sample_scenario):
    """Test generation of rebalancing recommendations for high-risk holdings"""
    # Create holdings with high risk scores
    holdings = []
    for i in range(5):
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            asset_id=f"ASSET{i}",
            asset_name=f"High Risk Asset {i}",
            asset_type="equity",
            issuer_name=f"Issuer {i}",
            sector="Energy",
            country="USA",
            state_region="Texas",
            latitude=Decimal("29.7604"),
            longitude=Decimal("-95.3698"),
            market_value=Decimal("1000000.00"),
            insurance_dependency_score=Decimal("50.0")
        )
        db_session.add(holding)
        holdings.append(holding)
    
    db_session.commit()
    
    # Create risk results with high combined scores
    for holding in holdings:
        risk_result = RiskResult(
            portfolio_id=sample_portfolio.id,
            holding_id=holding.id,
            scenario_id=sample_scenario.id,
            physical_score=Decimal("80.0"),
            transition_score=Decimal("75.0"),
            combined_score=Decimal("78.0"),  # Above 75 threshold
            expected_loss=Decimal("100000.00"),
            stressed_return_delta=Decimal("-10.0"),
            confidence="high"
        )
        db_session.add(risk_result)
    
    db_session.commit()
    
    # Generate recommendations
    engine = RecommendationEngine(db_session)
    recommendations = engine.generate_recommendations(
        str(sample_portfolio.id),
        str(sample_scenario.id)
    )
    
    # Verify rebalancing recommendation exists
    rebalance_recs = [r for r in recommendations if r.recommendation_type == RecommendationType.REBALANCE]
    assert len(rebalance_recs) > 0
    
    rec = rebalance_recs[0]
    assert rec.priority in ["critical", "high", "medium", "low"]
    assert "rebalancing" in rec.message.lower() or "rebalance" in rec.message.lower()
    assert rec.potential_impact > 0
    assert rec.affected_holdings is not None
    assert len(rec.affected_holdings) > 0


def test_generate_recommendations_geographic_hotspot(db_session, sample_portfolio, sample_scenario):
    """Test identification of geographic hotspots"""
    # Create holdings concentrated in one region (>15% of portfolio)
    total_value = Decimal("10000000.00")
    texas_value = Decimal("2000000.00")  # 20% concentration
    
    # Texas holdings
    texas_holdings = []
    for i in range(3):
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            asset_id=f"TX{i}",
            asset_name=f"Texas Asset {i}",
            asset_type="real_estate",
            issuer_name=f"Texas Issuer {i}",
            sector="Real Estate",
            country="USA",
            state_region="Texas",
            latitude=Decimal("29.7604"),
            longitude=Decimal("-95.3698"),
            market_value=texas_value / 3,
            insurance_dependency_score=Decimal("60.0")
        )
        db_session.add(holding)
        texas_holdings.append(holding)
    
    # Other holdings to make up the rest
    other_value = total_value - texas_value
    other_holdings = []
    for i in range(5):
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            asset_id=f"OTHER{i}",
            asset_name=f"Other Asset {i}",
            asset_type="equity",
            issuer_name=f"Other Issuer {i}",
            sector="Technology",
            country="USA",
            state_region="California",
            latitude=Decimal("37.7749"),
            longitude=Decimal("-122.4194"),
            market_value=other_value / 5,
            insurance_dependency_score=Decimal("30.0")
        )
        db_session.add(holding)
        other_holdings.append(holding)
    
    # Flush to get holding IDs
    db_session.flush()
    
    # Create risk results for Texas holdings
    for holding in texas_holdings:
        risk_result = RiskResult(
            portfolio_id=sample_portfolio.id,
            holding_id=holding.id,
            scenario_id=sample_scenario.id,
            physical_score=Decimal("70.0"),
            transition_score=Decimal("50.0"),
            combined_score=Decimal("62.0"),
            expected_loss=Decimal("50000.00"),
            stressed_return_delta=Decimal("-8.0"),
            confidence="high"
        )
        db_session.add(risk_result)
    
    # Create risk results for other holdings
    for holding in other_holdings:
        risk_result = RiskResult(
            portfolio_id=sample_portfolio.id,
            holding_id=holding.id,
            scenario_id=sample_scenario.id,
            physical_score=Decimal("40.0"),
            transition_score=Decimal("30.0"),
            combined_score=Decimal("36.0"),
            expected_loss=Decimal("10000.00"),
            stressed_return_delta=Decimal("-3.0"),
            confidence="medium"
        )
        db_session.add(risk_result)
    
    db_session.commit()
    
    # Generate recommendations
    engine = RecommendationEngine(db_session)
    recommendations = engine.generate_recommendations(
        str(sample_portfolio.id),
        str(sample_scenario.id)
    )
    
    # Verify geographic hotspot recommendation exists
    diversify_recs = [r for r in recommendations if r.recommendation_type == RecommendationType.DIVERSIFY]
    assert len(diversify_recs) > 0
    
    # Check if Texas is mentioned in any diversification recommendation
    texas_mentioned = any("Texas" in rec.message for rec in diversify_recs)
    assert texas_mentioned


def test_generate_recommendations_sector_concentration(db_session, sample_portfolio, sample_scenario):
    """Test detection of sector concentration"""
    # Create holdings with >25% in one sector
    total_value = Decimal("10000000.00")
    energy_value = Decimal("3000000.00")  # 30% concentration
    
    # Energy sector holdings
    energy_holdings = []
    for i in range(4):
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            asset_id=f"ENERGY{i}",
            asset_name=f"Energy Asset {i}",
            asset_type="equity",
            issuer_name=f"Energy Corp {i}",
            sector="Energy",
            country="USA",
            state_region="Texas",
            latitude=Decimal("29.7604"),
            longitude=Decimal("-95.3698"),
            market_value=energy_value / 4,
            insurance_dependency_score=Decimal("40.0")
        )
        db_session.add(holding)
        energy_holdings.append(holding)
    
    # Other sector holdings
    other_value = total_value - energy_value
    other_holdings = []
    for i in range(6):
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            asset_id=f"TECH{i}",
            asset_name=f"Tech Asset {i}",
            asset_type="equity",
            issuer_name=f"Tech Inc {i}",
            sector="Technology",
            country="USA",
            state_region="California",
            latitude=Decimal("37.7749"),
            longitude=Decimal("-122.4194"),
            market_value=other_value / 6,
            insurance_dependency_score=Decimal("20.0")
        )
        db_session.add(holding)
        other_holdings.append(holding)
    
    # Flush to get holding IDs
    db_session.flush()
    
    # Create risk results for energy holdings
    for holding in energy_holdings:
        risk_result = RiskResult(
            portfolio_id=sample_portfolio.id,
            holding_id=holding.id,
            scenario_id=sample_scenario.id,
            physical_score=Decimal("65.0"),
            transition_score=Decimal("70.0"),
            combined_score=Decimal("67.0"),
            expected_loss=Decimal("80000.00"),
            stressed_return_delta=Decimal("-9.0"),
            confidence="high"
        )
        db_session.add(risk_result)
    
    # Create risk results for other holdings
    for holding in other_holdings:
        risk_result = RiskResult(
            portfolio_id=sample_portfolio.id,
            holding_id=holding.id,
            scenario_id=sample_scenario.id,
            physical_score=Decimal("30.0"),
            transition_score=Decimal("25.0"),
            combined_score=Decimal("28.0"),
            expected_loss=Decimal("5000.00"),
            stressed_return_delta=Decimal("-2.0"),
            confidence="medium"
        )
        db_session.add(risk_result)
    
    db_session.commit()
    
    # Generate recommendations
    engine = RecommendationEngine(db_session)
    recommendations = engine.generate_recommendations(
        str(sample_portfolio.id),
        str(sample_scenario.id)
    )
    
    # Verify sector concentration recommendation exists
    diversify_recs = [r for r in recommendations if r.recommendation_type == RecommendationType.DIVERSIFY]
    assert len(diversify_recs) > 0
    
    # Check if Energy sector is mentioned
    energy_mentioned = any("Energy" in rec.message for rec in diversify_recs)
    assert energy_mentioned


def test_generate_recommendations_watchlist_issuer(db_session, sample_portfolio, sample_scenario):
    """Test flagging of issuers for watchlist"""
    # Create holdings from same issuer with >5% aggregated loss
    issuer_value = Decimal("2000000.00")
    issuer_loss = Decimal("150000.00")  # 7.5% loss
    
    watchlist_holdings = []
    for i in range(3):
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            asset_id=f"WATCH{i}",
            asset_name=f"Watchlist Asset {i}",
            asset_type="bond",
            issuer_name="High Risk Issuer",
            sector="Utilities",
            country="USA",
            state_region="Florida",
            latitude=Decimal("25.7617"),
            longitude=Decimal("-80.1918"),
            market_value=issuer_value / 3,
            insurance_dependency_score=Decimal("55.0")
        )
        db_session.add(holding)
        watchlist_holdings.append(holding)
    
    # Flush to get holding IDs
    db_session.flush()
    
    # Create risk results
    for holding in watchlist_holdings:
        risk_result = RiskResult(
            portfolio_id=sample_portfolio.id,
            holding_id=holding.id,
            scenario_id=sample_scenario.id,
            physical_score=Decimal("75.0"),
            transition_score=Decimal("60.0"),
            combined_score=Decimal("69.0"),
            expected_loss=issuer_loss / 3,
            stressed_return_delta=Decimal("-7.5"),
            confidence="high"
        )
        db_session.add(risk_result)
    
    db_session.commit()
    
    # Generate recommendations
    engine = RecommendationEngine(db_session)
    recommendations = engine.generate_recommendations(
        str(sample_portfolio.id),
        str(sample_scenario.id)
    )
    
    # Verify watchlist recommendation exists
    watchlist_recs = [r for r in recommendations if r.recommendation_type == RecommendationType.WATCHLIST]
    assert len(watchlist_recs) > 0
    
    rec = watchlist_recs[0]
    assert "High Risk Issuer" in rec.message
    assert "watchlist" in rec.message.lower()


def test_generate_recommendations_insurance_review(db_session, sample_portfolio, sample_scenario):
    """Test insurance review recommendations"""
    # Create holdings with high insurance dependency and significant loss
    insurance_holdings = []
    for i in range(3):
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            asset_id=f"INS{i}",
            asset_name=f"Insurance Dependent Asset {i}",
            asset_type="real_estate",
            issuer_name=f"Property Owner {i}",
            sector="Real Estate",
            country="USA",
            state_region="Florida",
            latitude=Decimal("25.7617"),
            longitude=Decimal("-80.1918"),
            market_value=Decimal("3000000.00"),
            insurance_dependency_score=Decimal("75.0")  # High dependency
        )
        db_session.add(holding)
        insurance_holdings.append(holding)
    
    # Flush to get holding IDs
    db_session.flush()
    
    # Create risk results
    for holding in insurance_holdings:
        risk_result = RiskResult(
            portfolio_id=sample_portfolio.id,
            holding_id=holding.id,
            scenario_id=sample_scenario.id,
            physical_score=Decimal("80.0"),
            transition_score=Decimal("40.0"),
            combined_score=Decimal("66.0"),
            expected_loss=Decimal("600000.00"),  # Significant loss
            stressed_return_delta=Decimal("-20.0"),
            confidence="high"
        )
        db_session.add(risk_result)
    
    db_session.commit()
    
    # Generate recommendations
    engine = RecommendationEngine(db_session)
    recommendations = engine.generate_recommendations(
        str(sample_portfolio.id),
        str(sample_scenario.id)
    )
    
    # Verify insurance review recommendation exists
    insurance_recs = [r for r in recommendations if r.recommendation_type == RecommendationType.INSURANCE_REVIEW]
    assert len(insurance_recs) > 0
    
    rec = insurance_recs[0]
    assert "insurance" in rec.message.lower()
    assert rec.potential_impact > 0


def test_calculate_priority(db_session):
    """Test priority calculation logic"""
    engine = RecommendationEngine(db_session)
    
    assert engine._calculate_priority(15.0) == "critical"  # >10%
    assert engine._calculate_priority(7.5) == "high"       # 5-10%
    assert engine._calculate_priority(3.0) == "medium"     # 2-5%
    assert engine._calculate_priority(1.0) == "low"        # <2%


def test_default_recommendation(db_session, sample_portfolio, sample_scenario):
    """Test that default recommendation is created when no issues found"""
    # Create well-diversified holdings with low risk (avoid concentration triggers)
    # Need at least 7 holdings to keep each sector/region below 15% threshold
    sectors = ["Government", "Technology", "Healthcare", "Finance", "Consumer", "Industrial", "Utilities"]
    regions = ["DC", "California", "New York", "Texas", "Illinois", "Florida", "Massachusetts"]
    
    low_risk_holdings = []
    for i in range(7):
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            asset_id=f"LOW{i}",
            asset_name=f"Low Risk Asset {i}",
            asset_type="bond",
            issuer_name=f"Safe Issuer {i}",
            sector=sectors[i],
            country="USA",
            state_region=regions[i],
            latitude=Decimal("38.9072") + i,
            longitude=Decimal("-77.0369") - i,
            market_value=Decimal("1000000.00"),
            insurance_dependency_score=Decimal("20.0")
        )
        db_session.add(holding)
        low_risk_holdings.append(holding)
    
    # Flush to get holding IDs
    db_session.flush()
    
    # Create risk results with low scores
    for holding in low_risk_holdings:
        risk_result = RiskResult(
            portfolio_id=sample_portfolio.id,
            holding_id=holding.id,
            scenario_id=sample_scenario.id,
            physical_score=Decimal("20.0"),
            transition_score=Decimal("15.0"),
            combined_score=Decimal("18.0"),  # Low score (well below 75 threshold)
            expected_loss=Decimal("5000.00"),  # Low loss
            stressed_return_delta=Decimal("-0.5"),
            confidence="high"
        )
        db_session.add(risk_result)
    
    db_session.commit()
    
    # Generate recommendations
    engine = RecommendationEngine(db_session)
    recommendations = engine.generate_recommendations(
        str(sample_portfolio.id),
        str(sample_scenario.id)
    )
    
    # Should have at least one recommendation
    assert len(recommendations) >= 1
    
    # With well-diversified low-risk portfolio, should get default "balanced" recommendation
    messages = [r.message for r in recommendations]
    balanced_mentioned = any("balanced" in msg.lower() for msg in messages)
    
    assert balanced_mentioned, f"Expected balanced message for diversified low-risk portfolio, got: {messages}"
