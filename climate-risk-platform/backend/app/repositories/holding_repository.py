"""Holding repository for database operations"""

from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.holding import Holding
from app.schemas.holding import HoldingCreate


class HoldingRepository:
    """Repository for holding CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, portfolio_id: UUID, holding: HoldingCreate) -> Holding:
        """Create a new holding"""
        db_holding = Holding(
            portfolio_id=portfolio_id,
            asset_id=holding.asset_id,
            asset_name=holding.asset_name,
            asset_type=holding.asset_type,
            issuer_name=holding.issuer_name,
            sector=holding.sector,
            country=holding.country,
            state_region=holding.state_region,
            latitude=holding.latitude,
            longitude=holding.longitude,
            market_value=holding.market_value,
            revenue_exposure_pct=holding.revenue_exposure_pct,
            carbon_intensity_proxy=holding.carbon_intensity_proxy,
            insurance_dependency_score=holding.insurance_dependency_score,
            supply_chain_dependency_score=holding.supply_chain_dependency_score
        )
        self.db.add(db_holding)
        self.db.commit()
        self.db.refresh(db_holding)
        return db_holding
    
    def create_bulk(self, portfolio_id: UUID, holdings: List[HoldingCreate]) -> List[Holding]:
        """Create multiple holdings in bulk"""
        db_holdings = []
        for holding in holdings:
            db_holding = Holding(
                portfolio_id=portfolio_id,
                asset_id=holding.asset_id,
                asset_name=holding.asset_name,
                asset_type=holding.asset_type,
                issuer_name=holding.issuer_name,
                sector=holding.sector,
                country=holding.country,
                state_region=holding.state_region,
                latitude=holding.latitude,
                longitude=holding.longitude,
                market_value=holding.market_value,
                revenue_exposure_pct=holding.revenue_exposure_pct,
                carbon_intensity_proxy=holding.carbon_intensity_proxy,
                insurance_dependency_score=holding.insurance_dependency_score,
                supply_chain_dependency_score=holding.supply_chain_dependency_score
            )
            db_holdings.append(db_holding)
        
        self.db.bulk_save_objects(db_holdings, return_defaults=True)
        self.db.commit()
        return db_holdings
    
    def get_by_id(self, holding_id: UUID) -> Optional[Holding]:
        """Get holding by ID"""
        return self.db.query(Holding).filter(Holding.id == holding_id).first()
    
    def get_by_portfolio(self, portfolio_id: UUID, skip: int = 0, limit: int = 100) -> List[Holding]:
        """Get all holdings for a portfolio with pagination"""
        return (
            self.db.query(Holding)
            .filter(Holding.portfolio_id == portfolio_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_count_by_portfolio(self, portfolio_id: UUID) -> int:
        """Get count of holdings for a portfolio"""
        return self.db.query(Holding).filter(Holding.portfolio_id == portfolio_id).count()
    
    def update(self, holding_id: UUID, holding_update: HoldingCreate) -> Optional[Holding]:
        """Update an existing holding"""
        db_holding = self.get_by_id(holding_id)
        if not db_holding:
            return None
        
        for field, value in holding_update.model_dump().items():
            setattr(db_holding, field, value)
        
        self.db.commit()
        self.db.refresh(db_holding)
        return db_holding
    
    def delete(self, holding_id: UUID) -> bool:
        """Delete a holding"""
        db_holding = self.get_by_id(holding_id)
        if not db_holding:
            return False
        
        self.db.delete(db_holding)
        self.db.commit()
        return True
    
    def delete_by_portfolio(self, portfolio_id: UUID) -> int:
        """Delete all holdings for a portfolio"""
        count = self.db.query(Holding).filter(Holding.portfolio_id == portfolio_id).delete()
        self.db.commit()
        return count
