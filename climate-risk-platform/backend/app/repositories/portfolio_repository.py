"""Portfolio repository for database operations"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate


class PortfolioRepository:
    """Repository for portfolio CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, portfolio: PortfolioCreate) -> Portfolio:
        """Create a new portfolio"""
        db_portfolio = Portfolio(
            name=portfolio.name,
            base_currency=portfolio.base_currency
        )
        self.db.add(db_portfolio)
        self.db.commit()
        self.db.refresh(db_portfolio)
        return db_portfolio
    
    def get_by_id(self, portfolio_id: UUID) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Portfolio]:
        """Get all portfolios with pagination"""
        return self.db.query(Portfolio).offset(skip).limit(limit).all()
    
    def update(self, portfolio_id: UUID, portfolio_update: PortfolioCreate) -> Optional[Portfolio]:
        """Update an existing portfolio"""
        db_portfolio = self.get_by_id(portfolio_id)
        if not db_portfolio:
            return None
        
        db_portfolio.name = portfolio_update.name
        db_portfolio.base_currency = portfolio_update.base_currency
        db_portfolio.updated_at = func.now()
        
        self.db.commit()
        self.db.refresh(db_portfolio)
        return db_portfolio
    
    def delete(self, portfolio_id: UUID) -> bool:
        """Delete a portfolio"""
        db_portfolio = self.get_by_id(portfolio_id)
        if not db_portfolio:
            return False
        
        self.db.delete(db_portfolio)
        self.db.commit()
        return True
    
    def get_portfolio_summary(self, portfolio_id: UUID) -> Optional[dict]:
        """Get portfolio summary with holdings count and total value using optimized query"""
        from app.models.holding import Holding
        
        portfolio = self.get_by_id(portfolio_id)
        if not portfolio:
            return None
        
        # Use database aggregation instead of loading all holdings into memory
        summary_query = (
            self.db.query(
                func.count(Holding.id).label('holdings_count'),
                func.sum(Holding.market_value).label('total_value')
            )
            .filter(Holding.portfolio_id == portfolio_id)
            .first()
        )
        
        holdings_count = summary_query.holdings_count or 0
        total_value = float(summary_query.total_value or 0)
        
        return {
            "id": str(portfolio.id),
            "name": portfolio.name,
            "base_currency": portfolio.base_currency,
            "holdings_count": holdings_count,
            "total_value": total_value,
            "created_at": portfolio.created_at,
            "updated_at": portfolio.updated_at
        }
