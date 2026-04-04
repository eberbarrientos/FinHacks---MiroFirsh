"""
Company data service for generating realistic portfolio holdings

This service provides realistic company data for climate risk simulations.
Companies are based on real sectors and regions with realistic financial profiles.
"""

from typing import List, Dict, Any
from decimal import Decimal
import random


class CompanyDataService:
    """Service for generating realistic company portfolio data"""
    
    # Real company templates by sector with realistic profiles
    COMPANY_TEMPLATES = {
        "Energy": [
            {"name": "ExxonMobil", "type": "Oil & Gas", "carbon": 480, "insurance": 70, "supply_chain": 85},
            {"name": "Chevron", "type": "Oil & Gas", "carbon": 450, "insurance": 72, "supply_chain": 82},
            {"name": "ConocoPhillips", "type": "Oil & Gas", "carbon": 420, "insurance": 68, "supply_chain": 80},
            {"name": "Phillips 66", "type": "Refining", "carbon": 380, "insurance": 65, "supply_chain": 88},
            {"name": "Valero Energy", "type": "Refining", "carbon": 400, "insurance": 67, "supply_chain": 85},
            {"name": "Marathon Petroleum", "type": "Refining", "carbon": 390, "insurance": 66, "supply_chain": 84},
            {"name": "Occidental Petroleum", "type": "Oil & Gas", "carbon": 410, "insurance": 69, "supply_chain": 78},
            {"name": "Devon Energy", "type": "Oil & Gas", "carbon": 350, "insurance": 64, "supply_chain": 75},
            {"name": "Pioneer Natural Resources", "type": "Oil & Gas", "carbon": 340, "insurance": 62, "supply_chain": 72},
            {"name": "EOG Resources", "type": "Oil & Gas", "carbon": 330, "insurance": 60, "supply_chain": 70},
        ],
        "Utilities": [
            {"name": "NextEra Energy", "type": "Electric Utility", "carbon": 120, "insurance": 55, "supply_chain": 65},
            {"name": "Duke Energy", "type": "Electric Utility", "carbon": 280, "insurance": 60, "supply_chain": 70},
            {"name": "Southern Company", "type": "Electric Utility", "carbon": 300, "insurance": 62, "supply_chain": 72},
            {"name": "Dominion Energy", "type": "Electric Utility", "carbon": 250, "insurance": 58, "supply_chain": 68},
            {"name": "American Electric Power", "type": "Electric Utility", "carbon": 320, "insurance": 63, "supply_chain": 74},
            {"name": "Xcel Energy", "type": "Electric Utility", "carbon": 200, "insurance": 52, "supply_chain": 62},
            {"name": "Entergy", "type": "Electric Utility", "carbon": 270, "insurance": 65, "supply_chain": 75},
            {"name": "FirstEnergy", "type": "Electric Utility", "carbon": 290, "insurance": 58, "supply_chain": 68},
        ],
        "Real Estate": [
            {"name": "Prologis", "type": "Industrial REIT", "carbon": 45, "insurance": 70, "supply_chain": 40},
            {"name": "American Tower", "type": "Infrastructure REIT", "carbon": 35, "insurance": 55, "supply_chain": 45},
            {"name": "Equinix", "type": "Data Center REIT", "carbon": 180, "insurance": 50, "supply_chain": 60},
            {"name": "Simon Property Group", "type": "Retail REIT", "carbon": 55, "insurance": 75, "supply_chain": 50},
            {"name": "Realty Income", "type": "Retail REIT", "carbon": 40, "insurance": 65, "supply_chain": 45},
            {"name": "AvalonBay Communities", "type": "Residential REIT", "carbon": 38, "insurance": 80, "supply_chain": 35},
            {"name": "Welltower", "type": "Healthcare REIT", "carbon": 60, "insurance": 72, "supply_chain": 55},
            {"name": "Digital Realty", "type": "Data Center REIT", "carbon": 175, "insurance": 48, "supply_chain": 58},
        ],
        "Materials": [
            {"name": "Linde", "type": "Industrial Gases", "carbon": 280, "insurance": 55, "supply_chain": 75},
            {"name": "Air Products", "type": "Industrial Gases", "carbon": 260, "insurance": 52, "supply_chain": 72},
            {"name": "Sherwin-Williams", "type": "Chemicals", "carbon": 180, "insurance": 48, "supply_chain": 80},
            {"name": "Freeport-McMoRan", "type": "Mining", "carbon": 350, "insurance": 60, "supply_chain": 70},
            {"name": "Nucor", "type": "Steel", "carbon": 520, "insurance": 58, "supply_chain": 82},
            {"name": "Newmont", "type": "Mining", "carbon": 220, "insurance": 55, "supply_chain": 65},
            {"name": "Dow Inc", "type": "Chemicals", "carbon": 380, "insurance": 62, "supply_chain": 85},
            {"name": "International Paper", "type": "Paper & Packaging", "carbon": 240, "insurance": 50, "supply_chain": 78},
        ],
        "Transportation": [
            {"name": "Union Pacific", "type": "Railroad", "carbon": 180, "insurance": 55, "supply_chain": 90},
            {"name": "CSX Corporation", "type": "Railroad", "carbon": 175, "insurance": 52, "supply_chain": 88},
            {"name": "Norfolk Southern", "type": "Railroad", "carbon": 170, "insurance": 54, "supply_chain": 87},
            {"name": "FedEx", "type": "Logistics", "carbon": 220, "insurance": 60, "supply_chain": 95},
            {"name": "UPS", "type": "Logistics", "carbon": 210, "insurance": 58, "supply_chain": 94},
            {"name": "Delta Air Lines", "type": "Airlines", "carbon": 280, "insurance": 70, "supply_chain": 85},
            {"name": "Southwest Airlines", "type": "Airlines", "carbon": 260, "insurance": 68, "supply_chain": 82},
            {"name": "J.B. Hunt Transport", "type": "Trucking", "carbon": 190, "insurance": 62, "supply_chain": 92},
        ],
        "Technology": [
            {"name": "Apple", "type": "Consumer Electronics", "carbon": 25, "insurance": 35, "supply_chain": 90},
            {"name": "Microsoft", "type": "Software", "carbon": 30, "insurance": 30, "supply_chain": 55},
            {"name": "Alphabet", "type": "Internet Services", "carbon": 45, "insurance": 32, "supply_chain": 50},
            {"name": "Amazon", "type": "E-commerce", "carbon": 120, "insurance": 45, "supply_chain": 95},
            {"name": "NVIDIA", "type": "Semiconductors", "carbon": 35, "insurance": 38, "supply_chain": 88},
            {"name": "Meta Platforms", "type": "Social Media", "carbon": 40, "insurance": 28, "supply_chain": 45},
            {"name": "Tesla", "type": "Electric Vehicles", "carbon": 55, "insurance": 50, "supply_chain": 85},
            {"name": "Salesforce", "type": "Software", "carbon": 22, "insurance": 25, "supply_chain": 40},
        ],
        "Financials": [
            {"name": "JPMorgan Chase", "type": "Banking", "carbon": 15, "insurance": 40, "supply_chain": 35},
            {"name": "Bank of America", "type": "Banking", "carbon": 14, "insurance": 38, "supply_chain": 32},
            {"name": "Wells Fargo", "type": "Banking", "carbon": 13, "insurance": 42, "supply_chain": 30},
            {"name": "Goldman Sachs", "type": "Investment Banking", "carbon": 12, "insurance": 35, "supply_chain": 28},
            {"name": "Morgan Stanley", "type": "Investment Banking", "carbon": 11, "insurance": 33, "supply_chain": 26},
            {"name": "BlackRock", "type": "Asset Management", "carbon": 8, "insurance": 25, "supply_chain": 20},
            {"name": "Berkshire Hathaway", "type": "Conglomerate", "carbon": 85, "insurance": 30, "supply_chain": 55},
            {"name": "Chubb", "type": "Insurance", "carbon": 10, "insurance": 20, "supply_chain": 25},
        ],
        "Healthcare": [
            {"name": "UnitedHealth Group", "type": "Health Insurance", "carbon": 18, "insurance": 45, "supply_chain": 60},
            {"name": "Johnson & Johnson", "type": "Pharmaceuticals", "carbon": 65, "insurance": 55, "supply_chain": 80},
            {"name": "Pfizer", "type": "Pharmaceuticals", "carbon": 55, "insurance": 52, "supply_chain": 78},
            {"name": "Eli Lilly", "type": "Pharmaceuticals", "carbon": 48, "insurance": 50, "supply_chain": 75},
            {"name": "Merck", "type": "Pharmaceuticals", "carbon": 52, "insurance": 48, "supply_chain": 76},
            {"name": "AbbVie", "type": "Pharmaceuticals", "carbon": 45, "insurance": 46, "supply_chain": 74},
            {"name": "CVS Health", "type": "Healthcare Services", "carbon": 35, "insurance": 58, "supply_chain": 85},
            {"name": "HCA Healthcare", "type": "Hospitals", "carbon": 80, "insurance": 70, "supply_chain": 82},
        ],
        "Consumer Discretionary": [
            {"name": "Home Depot", "type": "Home Improvement", "carbon": 45, "insurance": 55, "supply_chain": 88},
            {"name": "McDonald's", "type": "Restaurants", "carbon": 55, "insurance": 50, "supply_chain": 75},
            {"name": "Nike", "type": "Apparel", "carbon": 38, "insurance": 42, "supply_chain": 92},
            {"name": "Starbucks", "type": "Restaurants", "carbon": 42, "insurance": 48, "supply_chain": 80},
            {"name": "Lowe's", "type": "Home Improvement", "carbon": 43, "insurance": 53, "supply_chain": 86},
            {"name": "Target", "type": "Retail", "carbon": 48, "insurance": 58, "supply_chain": 90},
            {"name": "TJX Companies", "type": "Retail", "carbon": 35, "insurance": 52, "supply_chain": 85},
            {"name": "Marriott International", "type": "Hotels", "carbon": 65, "insurance": 72, "supply_chain": 70},
        ],
        "Consumer Staples": [
            {"name": "Procter & Gamble", "type": "Consumer Products", "carbon": 55, "insurance": 45, "supply_chain": 85},
            {"name": "Coca-Cola", "type": "Beverages", "carbon": 48, "insurance": 42, "supply_chain": 80},
            {"name": "PepsiCo", "type": "Beverages", "carbon": 52, "insurance": 44, "supply_chain": 82},
            {"name": "Costco", "type": "Retail", "carbon": 40, "insurance": 50, "supply_chain": 88},
            {"name": "Walmart", "type": "Retail", "carbon": 65, "insurance": 55, "supply_chain": 95},
            {"name": "Philip Morris", "type": "Tobacco", "carbon": 35, "insurance": 38, "supply_chain": 75},
            {"name": "Mondelez", "type": "Food", "carbon": 58, "insurance": 46, "supply_chain": 84},
            {"name": "Colgate-Palmolive", "type": "Consumer Products", "carbon": 42, "insurance": 40, "supply_chain": 78},
        ],
        "Agriculture": [
            {"name": "Archer-Daniels-Midland", "type": "Agricultural Processing", "carbon": 180, "insurance": 65, "supply_chain": 90},
            {"name": "Bunge", "type": "Agricultural Processing", "carbon": 170, "insurance": 62, "supply_chain": 88},
            {"name": "Corteva", "type": "Agricultural Chemicals", "carbon": 120, "insurance": 55, "supply_chain": 82},
            {"name": "Deere & Company", "type": "Agricultural Equipment", "carbon": 95, "insurance": 50, "supply_chain": 85},
            {"name": "Tyson Foods", "type": "Food Processing", "carbon": 220, "insurance": 68, "supply_chain": 92},
            {"name": "Cargill", "type": "Agricultural Trading", "carbon": 200, "insurance": 60, "supply_chain": 95},
        ],
    }
    
    # Regional headquarters by state
    STATE_HEADQUARTERS = {
        "Texas": ["Houston", "Dallas", "Austin", "San Antonio"],
        "California": ["San Francisco", "Los Angeles", "San Diego", "San Jose"],
        "New York": ["New York City", "Buffalo", "Albany"],
        "Florida": ["Miami", "Tampa", "Orlando", "Jacksonville"],
        "Illinois": ["Chicago", "Springfield"],
        "Pennsylvania": ["Philadelphia", "Pittsburgh"],
        "Georgia": ["Atlanta", "Savannah"],
        "Washington": ["Seattle", "Tacoma"],
        "Massachusetts": ["Boston", "Cambridge"],
        "Colorado": ["Denver", "Boulder"],
        "Arizona": ["Phoenix", "Tucson"],
        "North Carolina": ["Charlotte", "Raleigh"],
        "Michigan": ["Detroit", "Grand Rapids"],
        "Ohio": ["Columbus", "Cleveland", "Cincinnati"],
        "New Jersey": ["Newark", "Jersey City"],
        "Virginia": ["Richmond", "Virginia Beach"],
        "Louisiana": ["New Orleans", "Baton Rouge"],
        "Tennessee": ["Nashville", "Memphis"],
        "Minnesota": ["Minneapolis", "St. Paul"],
        "Missouri": ["St. Louis", "Kansas City"],
        "Indiana": ["Indianapolis"],
        "Wisconsin": ["Milwaukee", "Madison"],
        "Oregon": ["Portland", "Eugene"],
        "Nevada": ["Las Vegas", "Reno"],
        "Utah": ["Salt Lake City"],
        "Oklahoma": ["Oklahoma City", "Tulsa"],
        "Iowa": ["Des Moines", "Cedar Rapids"],
        "Nebraska": ["Omaha", "Lincoln"],
        "Kansas": ["Wichita", "Kansas City"],
        "New Mexico": ["Albuquerque", "Santa Fe"],
        "Wyoming": ["Cheyenne", "Casper"],
        "North Dakota": ["Fargo", "Bismarck"],
        "South Dakota": ["Sioux Falls"],
        "Montana": ["Billings", "Missoula"],
        "Idaho": ["Boise"],
        "South Carolina": ["Charleston", "Columbia"],
        "Alabama": ["Birmingham", "Montgomery"],
        "Mississippi": ["Jackson"],
        "Arkansas": ["Little Rock"],
        "Kentucky": ["Louisville", "Lexington"],
        "West Virginia": ["Charleston"],
        "Maryland": ["Baltimore"],
        "Connecticut": ["Hartford", "New Haven"],
        "Delaware": ["Wilmington"],
        "Rhode Island": ["Providence"],
        "New Hampshire": ["Manchester"],
        "Vermont": ["Burlington"],
        "Maine": ["Portland"],
        "Hawaii": ["Honolulu"],
        "Alaska": ["Anchorage"],
    }
    
    # State coordinates (approximate centers)
    STATE_COORDS = {
        "Texas": (31.0, -100.0),
        "California": (36.7, -119.4),
        "New York": (42.9, -75.5),
        "Florida": (27.8, -81.8),
        "Illinois": (40.0, -89.0),
        "Pennsylvania": (40.9, -77.8),
        "Georgia": (32.7, -83.5),
        "Washington": (47.4, -120.5),
        "Massachusetts": (42.2, -71.5),
        "Colorado": (39.0, -105.5),
        "Arizona": (34.2, -111.6),
        "North Carolina": (35.5, -79.8),
        "Michigan": (44.3, -85.4),
        "Ohio": (40.4, -82.8),
        "New Jersey": (40.1, -74.7),
        "Virginia": (37.5, -78.8),
        "Louisiana": (30.5, -91.9),
        "Tennessee": (35.8, -86.3),
        "Minnesota": (46.0, -94.6),
        "Missouri": (38.5, -92.4),
        "Indiana": (39.8, -86.3),
        "Wisconsin": (44.5, -89.8),
        "Oregon": (44.0, -120.5),
        "Nevada": (39.5, -116.9),
        "Utah": (39.3, -111.7),
        "Oklahoma": (35.5, -97.5),
        "Iowa": (42.0, -93.5),
        "Nebraska": (41.5, -99.8),
        "Kansas": (38.5, -98.4),
        "New Mexico": (34.5, -106.0),
        "Wyoming": (43.0, -107.5),
        "North Dakota": (47.5, -100.5),
        "South Dakota": (44.4, -100.2),
        "Montana": (47.0, -110.0),
        "Idaho": (44.4, -114.7),
        "South Carolina": (33.8, -81.0),
        "Alabama": (32.8, -86.8),
        "Mississippi": (32.7, -89.7),
        "Arkansas": (34.8, -92.2),
        "Kentucky": (37.8, -85.7),
        "West Virginia": (38.9, -80.5),
        "Maryland": (39.0, -76.8),
        "Connecticut": (41.6, -72.7),
        "Delaware": (39.0, -75.5),
        "Rhode Island": (41.7, -71.5),
        "New Hampshire": (43.2, -71.6),
        "Vermont": (44.0, -72.7),
        "Maine": (45.3, -69.0),
        "Hawaii": (20.8, -156.3),
        "Alaska": (64.0, -153.0),
    }
    
    @classmethod
    def generate_portfolio(cls, num_holdings: int = 50, seed: int = None) -> Dict[str, Any]:
        """
        Generate a realistic portfolio with diverse holdings
        
        Args:
            num_holdings: Number of holdings to generate
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary with portfolio metadata and holdings list
        """
        if seed is not None:
            random.seed(seed)
        
        holdings = []
        used_companies = set()
        states = list(cls.STATE_COORDS.keys())
        
        # Ensure sector diversity
        sectors = list(cls.COMPANY_TEMPLATES.keys())
        holdings_per_sector = max(1, num_holdings // len(sectors))
        
        asset_id = 1
        for sector in sectors:
            templates = cls.COMPANY_TEMPLATES[sector]
            num_from_sector = min(len(templates), holdings_per_sector + random.randint(-1, 2))
            
            selected = random.sample(templates, min(num_from_sector, len(templates)))
            
            for template in selected:
                if template["name"] in used_companies:
                    continue
                used_companies.add(template["name"])
                
                # Select a state appropriate for the sector
                if sector == "Energy":
                    state = random.choice(["Texas", "Oklahoma", "Louisiana", "North Dakota", "Wyoming", "Colorado"])
                elif sector == "Technology":
                    state = random.choice(["California", "Washington", "Texas", "Massachusetts", "New York"])
                elif sector == "Financials":
                    state = random.choice(["New York", "North Carolina", "California", "Illinois", "Massachusetts"])
                elif sector == "Agriculture":
                    state = random.choice(["Iowa", "Nebraska", "Kansas", "Illinois", "Minnesota", "California"])
                else:
                    state = random.choice(states)
                
                lat, lon = cls.STATE_COORDS[state]
                # Add some randomness to coordinates
                lat += random.uniform(-1.5, 1.5)
                lon += random.uniform(-1.5, 1.5)
                
                # Generate realistic market value based on company type
                base_value = random.uniform(5_000_000, 100_000_000)
                if template["name"] in ["Apple", "Microsoft", "Alphabet", "Amazon", "NVIDIA"]:
                    base_value *= 5  # Tech giants
                elif template["name"] in ["JPMorgan Chase", "Bank of America", "Berkshire Hathaway"]:
                    base_value *= 4  # Financial giants
                elif template["name"] in ["ExxonMobil", "Chevron"]:
                    base_value *= 3  # Energy majors
                
                holdings.append({
                    "asset_id": f"ASSET{asset_id:04d}",
                    "asset_name": f"{template['name']} - {template['type']}",
                    "asset_type": template["type"],
                    "issuer_name": template["name"],
                    "sector": sector,
                    "country": "USA",
                    "state_region": state,
                    "latitude": round(lat, 4),
                    "longitude": round(lon, 4),
                    "market_value": Decimal(str(round(base_value, 2))),
                    "revenue_exposure_pct": Decimal(str(round(random.uniform(10, 60), 1))),
                    "carbon_intensity_proxy": Decimal(str(template["carbon"] + random.randint(-20, 20))),
                    "insurance_dependency_score": Decimal(str(template["insurance"] + random.randint(-5, 5))),
                    "supply_chain_dependency_score": Decimal(str(template["supply_chain"] + random.randint(-5, 5))),
                })
                asset_id += 1
                
                if len(holdings) >= num_holdings:
                    break
            
            if len(holdings) >= num_holdings:
                break
        
        return {
            "name": "Climate Risk Portfolio - Real Companies",
            "base_currency": "USD",
            "holdings": holdings
        }
