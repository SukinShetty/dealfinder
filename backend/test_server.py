import pytest
import httpx
import os
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_root():
    response = client.get("/api")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Real-Time Local Deal Finder API"}

def test_generate_sample_deals():
    response = client.post("/api/sample-deals")
    assert response.status_code == 200
    assert "Generated" in response.json()["message"]

def test_get_deals_brigade_road():
    # Test Brigade Road deals
    response = client.get("/api/deals", params={
        "lat": 12.9720,
        "lng": 77.6081,
        "location": "Brigade Road, Bengaluru"
    })
    assert response.status_code == 200
    deals = response.json()
    
    # Verify only Brigade Road deals are returned
    for deal in deals:
        assert "Brigade" in deal["location"]["address"]
        assert deal["business_name"] in ["Lifestyle Brigade Road", "Adidas Store Brigade Road", "Westside Brigade Road"]

def test_get_deals_jayanagar():
    # Test Jayanagar deals
    response = client.get("/api/deals", params={
        "lat": 12.9399,
        "lng": 77.5826,
        "location": "Jayanagar, Bengaluru"
    })
    assert response.status_code == 200
    deals = response.json()
    
    # Verify only Jayanagar deals are returned
    for deal in deals:
        assert "Jayanagar" in deal["location"]["address"]
        assert deal["business_name"] in ["Zudio Jayanagar", "Levi's Store Jayanagar", "H&M Jayanagar"]

def test_get_deals_with_category():
    # Test filtering by category
    response = client.get("/api/deals", params={
        "lat": 12.9720,
        "lng": 77.6081,
        "category": "retail"
    })
    assert response.status_code == 200
    deals = response.json()
    
    # Verify all deals are retail
    for deal in deals:
        assert deal["category"] == "retail"

def test_get_deals_with_min_discount():
    # Test minimum discount filter
    min_discount = 30
    response = client.get("/api/deals", params={
        "lat": 12.9720,
        "lng": 77.6081,
        "min_discount": min_discount
    })
    assert response.status_code == 200
    deals = response.json()
    
    # Verify all deals have at least the minimum discount
    for deal in deals:
        assert deal["discount_percentage"] >= min_discount

if __name__ == "__main__":
    pytest.main(["-v", "test_server.py"])
