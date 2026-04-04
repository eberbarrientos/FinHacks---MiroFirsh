"""Pytest configuration and fixtures"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models.base import Base
from app.main import app
from app.database import get_db


# Use in-memory SQLite for testing
# Note: Model tests require PostgreSQL due to UUID type incompatibility with SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Enable foreign key support in SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_portfolio(db_session):
    """Create a sample portfolio for testing"""
    from app.models.portfolio import Portfolio
    from app.models.holding import Holding
    from uuid import uuid4
    
    portfolio = Portfolio(
        id=uuid4(),
        name="Test Portfolio",
        base_currency="USD"
    )
    db_session.add(portfolio)
    db_session.commit()
    
    # Add some holdings
    holdings = [
        Holding(
            id=uuid4(),
            portfolio_id=portfolio.id,
            asset_id="ASSET001",
            asset_name="Test Asset 1",
            asset_type="Equity",
            issuer_name="Test Issuer 1",
            sector="Energy",
            country="USA",
            state_region="Texas",
            latitude=29.7604,
            longitude=-95.3698,
            market_value=1000000.0
        ),
        Holding(
            id=uuid4(),
            portfolio_id=portfolio.id,
            asset_id="ASSET002",
            asset_name="Test Asset 2",
            asset_type="Equity",
            issuer_name="Test Issuer 2",
            sector="Technology",
            country="USA",
            state_region="California",
            latitude=37.7749,
            longitude=-122.4194,
            market_value=2000000.0
        )
    ]
    
    for holding in holdings:
        db_session.add(holding)
    db_session.commit()
    
    return portfolio


@pytest.fixture
def sample_scenario(db_session):
    """Create a sample scenario for testing"""
    from app.models.scenario import Scenario
    from uuid import uuid4
    
    scenario = Scenario(
        id=uuid4(),
        name="Test Hurricane Scenario",
        scenario_type="hurricane",
        severity="high",
        time_horizon="12m"
    )
    db_session.add(scenario)
    db_session.commit()
    
    return scenario


@pytest.fixture
def sample_portfolio_with_risk_results(db_session):
    """Create a sample portfolio with risk calculation results"""
    from app.models.portfolio import Portfolio
    from app.models.holding import Holding
    from app.models.scenario import Scenario
    from app.models.risk_result import RiskResult
    from uuid import uuid4
    
    # Create portfolio
    portfolio = Portfolio(
        id=uuid4(),
        name="Test Portfolio with Risk",
        base_currency="USD"
    )
    db_session.add(portfolio)
    
    # Create scenario
    scenario = Scenario(
        id=uuid4(),
        name="Test Scenario",
        scenario_type="hurricane",
        severity="high",
        time_horizon="12m"
    )
    db_session.add(scenario)
    db_session.commit()
    
    # Add holdings with geographic diversity
    holdings_data = [
        # High risk cluster in Texas
        {"asset_name": "Houston Energy", "issuer": "Energy Corp", "sector": "Energy",
         "lat": 29.7, "lon": -95.3, "region": "Texas", "score": 85.0, "loss": 5000000},
        {"asset_name": "Dallas Power", "issuer": "Power Inc", "sector": "Utilities",
         "lat": 29.8, "lon": -95.4, "region": "Texas", "score": 80.0, "loss": 4000000},
        {"asset_name": "Austin Grid", "issuer": "Grid Co", "sector": "Utilities",
         "lat": 29.9, "lon": -95.2, "region": "Texas", "score": 75.0, "loss": 3000000},
        
        # Low risk in California
        {"asset_name": "SF Tech", "issuer": "Tech Corp", "sector": "Technology",
         "lat": 37.7, "lon": -122.4, "region": "California", "score": 30.0, "loss": 1000000},
        {"asset_name": "LA Services", "issuer": "Services Inc", "sector": "Services",
         "lat": 34.0, "lon": -118.2, "region": "California", "score": 35.0, "loss": 1500000},
    ]
    
    for i, h_data in enumerate(holdings_data):
        holding = Holding(
            id=uuid4(),
            portfolio_id=portfolio.id,
            asset_id=f"ASSET{i:03d}",
            asset_name=h_data["asset_name"],
            asset_type="Equity",
            issuer_name=h_data["issuer"],
            sector=h_data["sector"],
            country="USA",
            state_region=h_data["region"],
            latitude=h_data["lat"],
            longitude=h_data["lon"],
            market_value=h_data["loss"] * 2  # Market value is 2x expected loss
        )
        db_session.add(holding)
        db_session.flush()
        
        # Add risk result
        risk_result = RiskResult(
            id=uuid4(),
            portfolio_id=portfolio.id,
            holding_id=holding.id,
            scenario_id=scenario.id,
            physical_score=h_data["score"] * 0.7,
            transition_score=h_data["score"] * 0.3,
            combined_score=h_data["score"],
            expected_loss=h_data["loss"],
            stressed_return_delta=-5.0,
            confidence="high"
        )
        db_session.add(risk_result)
    
    db_session.commit()
    
    return {
        "portfolio_id": portfolio.id,
        "scenario_id": scenario.id,
        "portfolio": portfolio,
        "scenario": scenario
    }
