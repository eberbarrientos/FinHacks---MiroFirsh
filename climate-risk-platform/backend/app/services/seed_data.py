"""Seed data service for creating sample portfolios"""

from typing import List, Dict
from decimal import Decimal


class SeedDataService:
    """Service for generating sample portfolio data"""
    
    @staticmethod
    def get_sample_portfolio() -> Dict:
        """
        Get comprehensive sample portfolio with 50+ holdings
        Includes diverse asset types, sectors, and geographic locations
        with varying risk profiles (coastal, inland, high-carbon sectors)
        
        Returns:
            Dictionary with portfolio metadata and holdings list
        """
        holdings = [
            # High-risk coastal properties (Florida, Texas Gulf)
            {
                "asset_id": "ASSET001",
                "asset_name": "Miami Beach Resort Complex",
                "asset_type": "Real Estate",
                "issuer_name": "Coastal Properties Inc",
                "sector": "Real Estate",
                "country": "USA",
                "state_region": "Florida",
                "latitude": 25.7907,
                "longitude": -80.1300,
                "market_value": Decimal("12500000.00"),
                "revenue_exposure_pct": Decimal("25.0"),
                "carbon_intensity_proxy": Decimal("95.0"),
                "insurance_dependency_score": Decimal("90.0"),
                "supply_chain_dependency_score": Decimal("60.0")
            },
            {
                "asset_id": "ASSET002",
                "asset_name": "Houston Petrochemical Facility",
                "asset_type": "Industrial",
                "issuer_name": "Texas Energy Corp",
                "sector": "Energy",
                "country": "USA",
                "state_region": "Texas",
                "latitude": 29.7604,
                "longitude": -95.3698,
                "market_value": Decimal("25000000.00"),
                "revenue_exposure_pct": Decimal("40.0"),
                "carbon_intensity_proxy": Decimal("450.0"),
                "insurance_dependency_score": Decimal("75.0"),
                "supply_chain_dependency_score": Decimal("85.0")
            },
            {
                "asset_id": "ASSET003",
                "asset_name": "Tampa Bay Distribution Center",
                "asset_type": "Logistics",
                "issuer_name": "Gulf Logistics LLC",
                "sector": "Transportation",
                "country": "USA",
                "state_region": "Florida",
                "latitude": 27.9506,
                "longitude": -82.4572,
                "market_value": Decimal("8500000.00"),
                "revenue_exposure_pct": Decimal("18.0"),
                "carbon_intensity_proxy": Decimal("120.0"),
                "insurance_dependency_score": Decimal("80.0"),
                "supply_chain_dependency_score": Decimal("90.0")
            },
            
            # Wildfire-prone California assets
            {
                "asset_id": "ASSET004",
                "asset_name": "Northern California Winery",
                "asset_type": "Agriculture",
                "issuer_name": "Napa Valley Estates",
                "sector": "Agriculture",
                "country": "USA",
                "state_region": "California",
                "latitude": 38.2975,
                "longitude": -122.2869,
                "market_value": Decimal("6500000.00"),
                "revenue_exposure_pct": Decimal("12.0"),
                "carbon_intensity_proxy": Decimal("45.0"),
                "insurance_dependency_score": Decimal("85.0"),
                "supply_chain_dependency_score": Decimal("55.0")
            },
            {
                "asset_id": "ASSET005",
                "asset_name": "Los Angeles Office Tower",
                "asset_type": "Real Estate",
                "issuer_name": "Pacific REIT Holdings",
                "sector": "Real Estate",
                "country": "USA",
                "state_region": "California",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "market_value": Decimal("45000000.00"),
                "revenue_exposure_pct": Decimal("35.0"),
                "carbon_intensity_proxy": Decimal("110.0"),
                "insurance_dependency_score": Decimal("65.0"),
                "supply_chain_dependency_score": Decimal("50.0")
            },
            
            # Renewable energy assets (lower carbon)
            {
                "asset_id": "ASSET006",
                "asset_name": "Mojave Solar Farm",
                "asset_type": "Renewable Energy",
                "issuer_name": "Green Energy Corp",
                "sector": "Utilities",
                "country": "USA",
                "state_region": "California",
                "latitude": 35.0456,
                "longitude": -117.6897,
                "market_value": Decimal("18000000.00"),
                "revenue_exposure_pct": Decimal("28.0"),
                "carbon_intensity_proxy": Decimal("5.0"),
                "insurance_dependency_score": Decimal("40.0"),
                "supply_chain_dependency_score": Decimal("70.0")
            },
            {
                "asset_id": "ASSET007",
                "asset_name": "Iowa Wind Farm",
                "asset_type": "Renewable Energy",
                "issuer_name": "Midwest Wind Power",
                "sector": "Utilities",
                "country": "USA",
                "state_region": "Iowa",
                "latitude": 42.0308,
                "longitude": -93.6319,
                "market_value": Decimal("22000000.00"),
                "revenue_exposure_pct": Decimal("32.0"),
                "carbon_intensity_proxy": Decimal("3.0"),
                "insurance_dependency_score": Decimal("35.0"),
                "supply_chain_dependency_score": Decimal("65.0")
            },
            
            # High-carbon industrial assets
            {
                "asset_id": "ASSET008",
                "asset_name": "Pittsburgh Steel Mill",
                "asset_type": "Industrial",
                "issuer_name": "American Steel Industries",
                "sector": "Materials",
                "country": "USA",
                "state_region": "Pennsylvania",
                "latitude": 40.4406,
                "longitude": -79.9959,
                "market_value": Decimal("35000000.00"),
                "revenue_exposure_pct": Decimal("45.0"),
                "carbon_intensity_proxy": Decimal("520.0"),
                "insurance_dependency_score": Decimal("60.0"),
                "supply_chain_dependency_score": Decimal("80.0")
            },
            {
                "asset_id": "ASSET009",
                "asset_name": "Detroit Auto Manufacturing Plant",
                "asset_type": "Industrial",
                "issuer_name": "Motor City Manufacturing",
                "sector": "Consumer Discretionary",
                "country": "USA",
                "state_region": "Michigan",
                "latitude": 42.3314,
                "longitude": -83.0458,
                "market_value": Decimal("42000000.00"),
                "revenue_exposure_pct": Decimal("50.0"),
                "carbon_intensity_proxy": Decimal("380.0"),
                "insurance_dependency_score": Decimal("55.0"),
                "supply_chain_dependency_score": Decimal("95.0")
            },
            
            # Technology sector (lower carbon)
            {
                "asset_id": "ASSET010",
                "asset_name": "Seattle Tech Campus",
                "asset_type": "Real Estate",
                "issuer_name": "Pacific Northwest Tech REIT",
                "sector": "Technology",
                "country": "USA",
                "state_region": "Washington",
                "latitude": 47.6062,
                "longitude": -122.3321,
                "market_value": Decimal("55000000.00"),
                "revenue_exposure_pct": Decimal("42.0"),
                "carbon_intensity_proxy": Decimal("35.0"),
                "insurance_dependency_score": Decimal("45.0"),
                "supply_chain_dependency_score": Decimal("60.0")
            },
            {
                "asset_id": "ASSET011",
                "asset_name": "Austin Data Center",
                "asset_type": "Technology Infrastructure",
                "issuer_name": "Cloud Infrastructure Inc",
                "sector": "Technology",
                "country": "USA",
                "state_region": "Texas",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "market_value": Decimal("38000000.00"),
                "revenue_exposure_pct": Decimal("38.0"),
                "carbon_intensity_proxy": Decimal("180.0"),
                "insurance_dependency_score": Decimal("50.0"),
                "supply_chain_dependency_score": Decimal("75.0")
            },
            
            # Financial services
            {
                "asset_id": "ASSET012",
                "asset_name": "New York Financial Center",
                "asset_type": "Real Estate",
                "issuer_name": "Manhattan Properties LLC",
                "sector": "Financials",
                "country": "USA",
                "state_region": "New York",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "market_value": Decimal("75000000.00"),
                "revenue_exposure_pct": Decimal("55.0"),
                "carbon_intensity_proxy": Decimal("85.0"),
                "insurance_dependency_score": Decimal("60.0"),
                "supply_chain_dependency_score": Decimal("45.0")
            },
            {
                "asset_id": "ASSET013",
                "asset_name": "Chicago Trading Floor",
                "asset_type": "Real Estate",
                "issuer_name": "Midwest Financial Properties",
                "sector": "Financials",
                "country": "USA",
                "state_region": "Illinois",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "market_value": Decimal("48000000.00"),
                "revenue_exposure_pct": Decimal("40.0"),
                "carbon_intensity_proxy": Decimal("90.0"),
                "insurance_dependency_score": Decimal("55.0"),
                "supply_chain_dependency_score": Decimal("40.0")
            },
            
            # Healthcare facilities
            {
                "asset_id": "ASSET014",
                "asset_name": "Phoenix Medical Center",
                "asset_type": "Healthcare",
                "issuer_name": "Desert Health Systems",
                "sector": "Healthcare",
                "country": "USA",
                "state_region": "Arizona",
                "latitude": 33.4484,
                "longitude": -112.0740,
                "market_value": Decimal("32000000.00"),
                "revenue_exposure_pct": Decimal("30.0"),
                "carbon_intensity_proxy": Decimal("125.0"),
                "insurance_dependency_score": Decimal("70.0"),
                "supply_chain_dependency_score": Decimal("85.0")
            },
            {
                "asset_id": "ASSET015",
                "asset_name": "Boston Research Hospital",
                "asset_type": "Healthcare",
                "issuer_name": "New England Health Trust",
                "sector": "Healthcare",
                "country": "USA",
                "state_region": "Massachusetts",
                "latitude": 42.3601,
                "longitude": -71.0589,
                "market_value": Decimal("62000000.00"),
                "revenue_exposure_pct": Decimal("48.0"),
                "carbon_intensity_proxy": Decimal("140.0"),
                "insurance_dependency_score": Decimal("75.0"),
                "supply_chain_dependency_score": Decimal("80.0")
            },
            
            # Retail and consumer
            {
                "asset_id": "ASSET016",
                "asset_name": "Atlanta Shopping Mall",
                "asset_type": "Retail",
                "issuer_name": "Southern Retail Properties",
                "sector": "Consumer Discretionary",
                "country": "USA",
                "state_region": "Georgia",
                "latitude": 33.7490,
                "longitude": -84.3880,
                "market_value": Decimal("28000000.00"),
                "revenue_exposure_pct": Decimal("22.0"),
                "carbon_intensity_proxy": Decimal("105.0"),
                "insurance_dependency_score": Decimal("65.0"),
                "supply_chain_dependency_score": Decimal("70.0")
            },
            {
                "asset_id": "ASSET017",
                "asset_name": "Denver Distribution Hub",
                "asset_type": "Logistics",
                "issuer_name": "Mountain Logistics Corp",
                "sector": "Transportation",
                "country": "USA",
                "state_region": "Colorado",
                "latitude": 39.7392,
                "longitude": -104.9903,
                "market_value": Decimal("19000000.00"),
                "revenue_exposure_pct": Decimal("25.0"),
                "carbon_intensity_proxy": Decimal("135.0"),
                "insurance_dependency_score": Decimal("60.0"),
                "supply_chain_dependency_score": Decimal("90.0")
            },
            
            # Additional diverse holdings to reach 50+
            {
                "asset_id": "ASSET018",
                "asset_name": "Portland Green Building",
                "asset_type": "Real Estate",
                "issuer_name": "Pacific Northwest REIT",
                "sector": "Real Estate",
                "country": "USA",
                "state_region": "Oregon",
                "latitude": 45.5152,
                "longitude": -122.6784,
                "market_value": Decimal("24000000.00"),
                "revenue_exposure_pct": Decimal("20.0"),
                "carbon_intensity_proxy": Decimal("40.0"),
                "insurance_dependency_score": Decimal("50.0"),
                "supply_chain_dependency_score": Decimal("45.0")
            },
            {
                "asset_id": "ASSET019",
                "asset_name": "New Orleans Port Facility",
                "asset_type": "Transportation",
                "issuer_name": "Gulf Coast Shipping",
                "sector": "Transportation",
                "country": "USA",
                "state_region": "Louisiana",
                "latitude": 29.9511,
                "longitude": -90.0715,
                "market_value": Decimal("16000000.00"),
                "revenue_exposure_pct": Decimal("28.0"),
                "carbon_intensity_proxy": Decimal("200.0"),
                "insurance_dependency_score": Decimal("95.0"),
                "supply_chain_dependency_score": Decimal("85.0")
            },
            {
                "asset_id": "ASSET020",
                "asset_name": "Minneapolis Cold Storage",
                "asset_type": "Logistics",
                "issuer_name": "Northern Storage Solutions",
                "sector": "Consumer Staples",
                "country": "USA",
                "state_region": "Minnesota",
                "latitude": 44.9778,
                "longitude": -93.2650,
                "market_value": Decimal("14000000.00"),
                "revenue_exposure_pct": Decimal("18.0"),
                "carbon_intensity_proxy": Decimal("160.0"),
                "insurance_dependency_score": Decimal("55.0"),
                "supply_chain_dependency_score": Decimal("75.0")
            },
        ]
        
        # Add more holdings to reach 50+
        additional_holdings = [
            # More coastal properties
            ("ASSET021", "Charleston Historic District", "Real Estate", "Southern Heritage REIT", "Real Estate", "South Carolina", 32.7765, -79.9311, 15000000),
            ("ASSET022", "San Diego Marina Complex", "Real Estate", "Pacific Coast Properties", "Real Estate", "California", 32.7157, -117.1611, 21000000),
            ("ASSET023", "Virginia Beach Resort", "Real Estate", "Atlantic Properties Inc", "Real Estate", "Virginia", 36.8529, -75.9780, 18000000),
            
            # More energy sector
            ("ASSET024", "Oklahoma Natural Gas Plant", "Energy", "Plains Energy Corp", "Energy", "Oklahoma", 35.4676, -97.5164, 28000000),
            ("ASSET025", "Wyoming Coal Mine", "Energy", "Mountain Resources Inc", "Energy", "Wyoming", 43.0760, -107.2903, 32000000),
            ("ASSET026", "North Dakota Oil Field", "Energy", "Northern Energy Holdings", "Energy", "North Dakota", 47.5515, -101.0020, 40000000),
            
            # More tech and services
            ("ASSET027", "San Francisco Tech Hub", "Technology", "Bay Area Innovation", "Technology", "California", 37.7749, -122.4194, 52000000),
            ("ASSET028", "Raleigh Research Park", "Technology", "Research Triangle Properties", "Technology", "North Carolina", 35.7796, -78.6382, 26000000),
            ("ASSET029", "Salt Lake City Call Center", "Services", "Mountain Services Corp", "Communication Services", "Utah", 40.7608, -111.8910, 12000000),
            ("ASSET030", "Nashville Entertainment Complex", "Entertainment", "Music City Holdings", "Communication Services", "Tennessee", 36.1627, -86.7816, 19000000),
            
            # More manufacturing
            ("ASSET031", "Milwaukee Brewery", "Manufacturing", "Great Lakes Beverages", "Consumer Staples", "Wisconsin", 43.0389, -87.9065, 22000000),
            ("ASSET032", "Kansas City Food Processing", "Manufacturing", "Heartland Foods Inc", "Consumer Staples", "Missouri", 39.0997, -94.5786, 17000000),
            ("ASSET033", "Indianapolis Pharmaceutical Plant", "Manufacturing", "Midwest Pharma Corp", "Healthcare", "Indiana", 39.7684, -86.1581, 35000000),
            
            # More retail and commercial
            ("ASSET034", "Las Vegas Casino Resort", "Hospitality", "Desert Entertainment LLC", "Consumer Discretionary", "Nevada", 36.1699, -115.1398, 65000000),
            ("ASSET035", "Orlando Theme Park", "Entertainment", "Florida Entertainment Corp", "Consumer Discretionary", "Florida", 28.5383, -81.3792, 85000000),
            ("ASSET036", "Philadelphia Shopping Center", "Retail", "Northeast Retail Properties", "Consumer Discretionary", "Pennsylvania", 39.9526, -75.1652, 24000000),
            
            # More utilities
            ("ASSET037", "Tennessee Hydroelectric Dam", "Utilities", "Southern Power Co", "Utilities", "Tennessee", 35.5175, -84.5120, 45000000),
            ("ASSET038", "Arizona Solar Array", "Renewable Energy", "Desert Solar Inc", "Utilities", "Arizona", 33.4484, -112.0740, 16000000),
            ("ASSET039", "Texas Wind Farm", "Renewable Energy", "Lone Star Wind Power", "Utilities", "Texas", 31.9686, -99.9018, 28000000),
            
            # More agriculture
            ("ASSET040", "Nebraska Grain Elevator", "Agriculture", "Plains Agriculture Co", "Agriculture", "Nebraska", 41.4925, -99.9018, 8500000),
            ("ASSET041", "California Almond Orchard", "Agriculture", "Central Valley Farms", "Agriculture", "California", 36.7783, -119.4179, 12000000),
            ("ASSET042", "Florida Citrus Grove", "Agriculture", "Sunshine Agriculture Inc", "Agriculture", "Florida", 27.9947, -81.7603, 9500000),
            
            # More transportation
            ("ASSET043", "Memphis Logistics Center", "Logistics", "Central Distribution Corp", "Transportation", "Tennessee", 35.1495, -90.0490, 21000000),
            ("ASSET044", "Seattle Port Terminal", "Transportation", "Pacific Shipping Co", "Transportation", "Washington", 47.6062, -122.3321, 32000000),
            ("ASSET045", "Dallas Airport Warehouse", "Logistics", "Southwest Logistics LLC", "Transportation", "Texas", 32.7767, -96.7970, 18000000),
            
            # More financial
            ("ASSET046", "San Francisco Bank Tower", "Real Estate", "Bay Financial Properties", "Financials", "California", 37.7749, -122.4194, 68000000),
            ("ASSET047", "Charlotte Banking Center", "Real Estate", "Carolina Financial REIT", "Financials", "North Carolina", 35.2271, -80.8431, 42000000),
            
            # More healthcare
            ("ASSET048", "Miami Medical Complex", "Healthcare", "South Florida Health", "Healthcare", "Florida", 25.7617, -80.1918, 38000000),
            ("ASSET049", "Cleveland Clinic Facility", "Healthcare", "Great Lakes Health Trust", "Healthcare", "Ohio", 41.4993, -81.6944, 44000000),
            ("ASSET050", "San Antonio Hospital", "Healthcare", "Texas Health Systems", "Healthcare", "Texas", 29.4241, -98.4936, 36000000),
        ]
        
        for asset_id, name, asset_type, issuer, sector, state, lat, lon, value in additional_holdings:
            holdings.append({
                "asset_id": asset_id,
                "asset_name": name,
                "asset_type": asset_type,
                "issuer_name": issuer,
                "sector": sector,
                "country": "USA",
                "state_region": state,
                "latitude": lat,
                "longitude": lon,
                "market_value": Decimal(str(value)),
                "revenue_exposure_pct": Decimal(str(15.0 + (hash(asset_id) % 40))),
                "carbon_intensity_proxy": Decimal(str(50.0 + (hash(asset_id) % 400))),
                "insurance_dependency_score": Decimal(str(40.0 + (hash(asset_id) % 50))),
                "supply_chain_dependency_score": Decimal(str(45.0 + (hash(asset_id) % 50)))
            })
        
        return {
            "name": "Diversified Climate Risk Portfolio",
            "base_currency": "USD",
            "holdings": holdings
        }
