"""Tests for portfolio API endpoints"""

import pytest
from io import BytesIO


class TestPortfolioEndpoints:
    """Test portfolio CRUD endpoints"""
    
    def test_create_portfolio(self, client):
        """Test POST /api/portfolios"""
        response = client.post(
            "/api/portfolios",
            json={"name": "Test Portfolio", "base_currency": "USD"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Portfolio"
        assert data["base_currency"] == "USD"
        assert "id" in data
    
    def test_get_portfolio(self, client):
        """Test GET /api/portfolios/{id}"""
        # Create portfolio first
        create_response = client.post(
            "/api/portfolios",
            json={"name": "Test Portfolio"}
        )
        portfolio_id = create_response.json()["id"]
        
        # Get portfolio
        response = client.get(f"/api/portfolios/{portfolio_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["portfolio_id"] == portfolio_id
        assert data["name"] == "Test Portfolio"
    
    def test_get_nonexistent_portfolio(self, client):
        """Test GET /api/portfolios/{id} with invalid ID"""
        response = client.get("/api/portfolios/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    def test_list_portfolios(self, client):
        """Test GET /api/portfolios"""
        # Create multiple portfolios
        client.post("/api/portfolios", json={"name": "Portfolio 1"})
        client.post("/api/portfolios", json={"name": "Portfolio 2"})
        
        # List portfolios
        response = client.get("/api/portfolios")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    def test_update_portfolio(self, client):
        """Test PUT /api/portfolios/{id}"""
        # Create portfolio
        create_response = client.post(
            "/api/portfolios",
            json={"name": "Original Name"}
        )
        portfolio_id = create_response.json()["id"]
        
        # Update portfolio
        response = client.put(
            f"/api/portfolios/{portfolio_id}",
            json={"name": "Updated Name", "base_currency": "EUR"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["base_currency"] == "EUR"
    
    def test_delete_portfolio(self, client):
        """Test DELETE /api/portfolios/{id}"""
        # Create portfolio
        create_response = client.post(
            "/api/portfolios",
            json={"name": "To Delete"}
        )
        portfolio_id = create_response.json()["id"]
        
        # Delete portfolio
        response = client.delete(f"/api/portfolios/{portfolio_id}")
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/portfolios/{portfolio_id}")
        assert get_response.status_code == 404


class TestHoldingsEndpoints:
    """Test holdings endpoints"""
    
    def test_upload_holdings_csv(self, client):
        """Test POST /api/portfolios/{id}/upload-holdings"""
        # Create portfolio
        create_response = client.post(
            "/api/portfolios",
            json={"name": "Test Portfolio"}
        )
        portfolio_id = create_response.json()["id"]
        
        # Create CSV content
        csv_content = """asset_id,asset_name,asset_type,issuer_name,sector,country,state_region,latitude,longitude,market_value
ASSET001,Test Building,Real Estate,Test Corp,Utilities,USA,Texas,29.7604,-95.3698,1000000.00
ASSET002,Test Facility,Industrial,Test Inc,Energy,USA,Louisiana,30.0,-90.0,2000000.00"""
        
        # Upload CSV
        files = {"file": ("holdings.csv", BytesIO(csv_content.encode()), "text/csv")}
        response = client.post(
            f"/api/portfolios/{portfolio_id}/upload-holdings",
            files=files
        )
        assert response.status_code == 200
        data = response.json()
        assert data["holdings_count"] == 2
        assert data["portfolio_id"] == portfolio_id
    
    def test_upload_invalid_csv(self, client):
        """Test uploading CSV with invalid data"""
        # Create portfolio
        create_response = client.post(
            "/api/portfolios",
            json={"name": "Test Portfolio"}
        )
        portfolio_id = create_response.json()["id"]
        
        # Create invalid CSV (missing required fields)
        csv_content = """asset_id,asset_name
ASSET001,Test Asset"""
        
        files = {"file": ("holdings.csv", BytesIO(csv_content.encode()), "text/csv")}
        response = client.post(
            f"/api/portfolios/{portfolio_id}/upload-holdings",
            files=files
        )
        assert response.status_code == 400
    
    def test_get_holdings(self, client):
        """Test GET /api/portfolios/{id}/holdings"""
        # Create portfolio
        create_response = client.post(
            "/api/portfolios",
            json={"name": "Test Portfolio"}
        )
        portfolio_id = create_response.json()["id"]
        
        # Upload holdings
        csv_content = """asset_id,asset_name,asset_type,issuer_name,sector,country,latitude,longitude,market_value
ASSET001,Test Asset,Real Estate,Test Corp,Utilities,USA,29.7604,-95.3698,1000000.00"""
        
        files = {"file": ("holdings.csv", BytesIO(csv_content.encode()), "text/csv")}
        client.post(f"/api/portfolios/{portfolio_id}/upload-holdings", files=files)
        
        # Get holdings
        response = client.get(f"/api/portfolios/{portfolio_id}/holdings")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["holdings"]) == 1
        assert data["holdings"][0]["asset_id"] == "ASSET001"


class TestSampleData:
    """Test sample data endpoints"""
    
    def test_get_sample_portfolio_data(self, client):
        """Test GET /api/portfolios/sample/data"""
        response = client.get("/api/portfolios/sample/data")
        assert response.status_code == 200
        data = response.json()
        assert "portfolio" in data
        assert "holdings" in data
        assert data["holdings_count"] > 0
        assert len(data["holdings"]) == data["holdings_count"]
    
    def test_create_sample_portfolio(self, client):
        """Test POST /api/portfolios/sample/create"""
        response = client.post("/api/portfolios/sample/create")
        assert response.status_code == 201
        data = response.json()
        assert "portfolio_id" in data
        assert data["holdings_count"] > 0
        assert "message" in data


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test GET /"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self, client):
        """Test GET /health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
