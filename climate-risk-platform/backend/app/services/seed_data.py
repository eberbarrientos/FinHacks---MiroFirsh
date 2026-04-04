"""Seed data service for creating sample portfolios"""

from typing import List, Dict
from decimal import Decimal
from .company_data import CompanyDataService


class SeedDataService:
    """Service for generating sample portfolio data"""
    
    @staticmethod
    def get_sample_portfolio() -> Dict:
        """
        Get comprehensive sample portfolio with 50+ holdings
        Uses realistic company data from CompanyDataService
        
        Returns:
            Dictionary with portfolio metadata and holdings list
        """
        # Use the new company data service for realistic data
        return CompanyDataService.generate_portfolio(num_holdings=50, seed=42)
