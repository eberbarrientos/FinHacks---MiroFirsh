"""Portfolio ingestion service for CSV upload and validation"""

import csv
import io
from typing import List, Dict, Tuple
from fastapi import UploadFile
from decimal import Decimal, InvalidOperation

from app.schemas.holding import HoldingCreate


class ValidationError:
    """Represents a validation error with row number and details"""
    def __init__(self, row_number: int, field: str, message: str):
        self.row_number = row_number
        self.field = field
        self.message = message
    
    def to_dict(self) -> dict:
        return {
            "row": self.row_number,
            "field": self.field,
            "message": self.message
        }


class PortfolioIngestionService:
    """Service for portfolio CSV upload and validation"""
    
    REQUIRED_FIELDS = [
        "asset_id", "asset_name", "asset_type", "issuer_name", 
        "sector", "country", "latitude", "longitude", "market_value"
    ]
    
    OPTIONAL_FIELDS = [
        "state_region", "revenue_exposure_pct", "carbon_intensity_proxy",
        "insurance_dependency_score", "supply_chain_dependency_score"
    ]
    
    def validate_csv(self, file: UploadFile) -> Tuple[bool, List[str]]:
        """
        Validate CSV file format and required fields
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check file type
        if not file.filename.endswith('.csv'):
            errors.append("File must be a CSV file")
            return False, errors
        
        # Read file content
        try:
            content = file.file.read()
            file.file.seek(0)  # Reset file pointer
            
            # Try to decode as UTF-8
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                errors.append("File must be UTF-8 encoded")
                return False, errors
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(content_str))
            
            # Check for required fields in header
            if not csv_reader.fieldnames:
                errors.append("CSV file is empty or has no header row")
                return False, errors
            
            missing_fields = set(self.REQUIRED_FIELDS) - set(csv_reader.fieldnames)
            if missing_fields:
                errors.append(f"Missing required fields: {', '.join(missing_fields)}")
                return False, errors
            
            # Check if file has at least one data row
            rows = list(csv_reader)
            if len(rows) == 0:
                errors.append("CSV file has no data rows")
                return False, errors
            
            return True, []
            
        except Exception as e:
            errors.append(f"Error reading CSV file: {str(e)}")
            return False, errors
    
    def parse_holdings(self, file: UploadFile) -> Tuple[List[HoldingCreate], List[ValidationError]]:
        """
        Parse CSV file into HoldingCreate objects with validation
        
        Returns:
            Tuple of (holdings_list, validation_errors)
        """
        holdings = []
        errors = []
        
        # Read and parse CSV
        content = file.file.read()
        file.file.seek(0)
        content_str = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content_str))
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Validate and parse required fields
                holding_data = {}
                
                # String fields
                for field in ["asset_id", "asset_name", "asset_type", "issuer_name", "sector", "country"]:
                    value = row.get(field, "").strip()
                    if not value:
                        errors.append(ValidationError(row_num, field, f"{field} is required"))
                        continue
                    holding_data[field] = value
                
                # Optional string field
                state_region = row.get("state_region", "").strip()
                holding_data["state_region"] = state_region if state_region else None
                
                # Latitude validation
                try:
                    latitude = float(row.get("latitude", ""))
                    if latitude < -90 or latitude > 90:
                        errors.append(ValidationError(row_num, "latitude", "Latitude must be between -90 and 90"))
                        continue
                    holding_data["latitude"] = latitude
                except (ValueError, TypeError):
                    errors.append(ValidationError(row_num, "latitude", "Latitude must be a valid number"))
                    continue
                
                # Longitude validation
                try:
                    longitude = float(row.get("longitude", ""))
                    if longitude < -180 or longitude > 180:
                        errors.append(ValidationError(row_num, "longitude", "Longitude must be between -180 and 180"))
                        continue
                    holding_data["longitude"] = longitude
                except (ValueError, TypeError):
                    errors.append(ValidationError(row_num, "longitude", "Longitude must be a valid number"))
                    continue
                
                # Market value validation
                try:
                    market_value = Decimal(row.get("market_value", "0"))
                    if market_value <= 0:
                        errors.append(ValidationError(row_num, "market_value", "Market value must be greater than 0"))
                        continue
                    holding_data["market_value"] = market_value
                except (InvalidOperation, ValueError):
                    errors.append(ValidationError(row_num, "market_value", "Market value must be a valid number"))
                    continue
                
                # Optional numeric fields
                optional_numeric_fields = {
                    "revenue_exposure_pct": (0, 100),
                    "carbon_intensity_proxy": (None, None),
                    "insurance_dependency_score": (0, 100),
                    "supply_chain_dependency_score": (0, 100)
                }
                
                for field, (min_val, max_val) in optional_numeric_fields.items():
                    value_str = row.get(field, "").strip()
                    if value_str:
                        try:
                            value = Decimal(value_str)
                            if min_val is not None and value < min_val:
                                errors.append(ValidationError(row_num, field, f"{field} must be >= {min_val}"))
                                continue
                            if max_val is not None and value > max_val:
                                errors.append(ValidationError(row_num, field, f"{field} must be <= {max_val}"))
                                continue
                            holding_data[field] = value
                        except (InvalidOperation, ValueError):
                            errors.append(ValidationError(row_num, field, f"{field} must be a valid number"))
                            continue
                    else:
                        holding_data[field] = None
                
                # Create HoldingCreate object if no errors for this row
                row_errors = [e for e in errors if e.row_number == row_num]
                if not row_errors:
                    holding = HoldingCreate(**holding_data)
                    holdings.append(holding)
                    
            except Exception as e:
                errors.append(ValidationError(row_num, "general", f"Error parsing row: {str(e)}"))
        
        return holdings, errors
    
    def get_sample_portfolio(self) -> Dict:
        """
        Get sample portfolio data for demonstration
        
        Returns:
            Dictionary with portfolio metadata and holdings
        """
        sample_holdings = [
            {
                "asset_id": "ASSET001",
                "asset_name": "Houston Office Complex",
                "asset_type": "Real Estate",
                "issuer_name": "Texas REIT Holdings",
                "sector": "Real Estate",
                "country": "USA",
                "state_region": "Texas",
                "latitude": 29.7604,
                "longitude": -95.3698,
                "market_value": 5000000.00,
                "revenue_exposure_pct": 15.5,
                "carbon_intensity_proxy": 120.5,
                "insurance_dependency_score": 75.0,
                "supply_chain_dependency_score": 60.0
            },
            {
                "asset_id": "ASSET002",
                "asset_name": "Miami Coastal Property",
                "asset_type": "Real Estate",
                "issuer_name": "Coastal Properties Inc",
                "sector": "Real Estate",
                "country": "USA",
                "state_region": "Florida",
                "latitude": 25.7617,
                "longitude": -80.1918,
                "market_value": 8500000.00,
                "revenue_exposure_pct": 22.0,
                "carbon_intensity_proxy": 95.0,
                "insurance_dependency_score": 85.0,
                "supply_chain_dependency_score": 55.0
            },
            {
                "asset_id": "ASSET003",
                "asset_name": "California Solar Farm",
                "asset_type": "Renewable Energy",
                "issuer_name": "Green Energy Corp",
                "sector": "Utilities",
                "country": "USA",
                "state_region": "California",
                "latitude": 35.3733,
                "longitude": -119.0187,
                "market_value": 12000000.00,
                "revenue_exposure_pct": 30.0,
                "carbon_intensity_proxy": 10.0,
                "insurance_dependency_score": 45.0,
                "supply_chain_dependency_score": 70.0
            }
        ]
        
        return {
            "name": "Sample Climate Risk Portfolio",
            "base_currency": "USD",
            "holdings": sample_holdings
        }
