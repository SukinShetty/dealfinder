import pytest
import requests
import json
from datetime import datetime

# Use the public endpoint for testing
BASE_URL = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com"

def test_root_endpoint():
    """Test the root endpoint"""
    response = requests.get(f"{BASE_URL}/api")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Real-Time Local Deal Finder API"}

def test_generate_sample_deals():
    """Test generating sample deals"""
    response = requests.post(f"{BASE_URL}/api/sample-deals")
    assert response.status_code == 200
    assert "Generated" in response.json()["message"]

def test_get_deals_bengaluru():
    """Test getting deals for Bengaluru location"""
    # Jayanagar 2nd Block coordinates
    params = {
        "lat": 12.9399,
        "lng": 77.5826,
        "category": "retail",
        "radius": 5.0,
        "min_discount": 15.0
    }
    response = requests.get(f"{BASE_URL}/api/deals", params=params)
    assert response.status_code == 200
    deals = response.json()
    
    # Verify deals structure and content
    assert isinstance(deals, list)
    if deals:  # If deals are found
        for deal in deals:
            assert "title" in deal
            assert "business_name" in deal
            assert "category" in deal
            assert "location" in deal
            assert "discount_percentage" in deal
            assert deal["discount_percentage"] >= 15.0
            assert "Bengaluru" in deal["location"]["address"]
            assert deal["category"] == "retail"

def test_get_deals_san_francisco():
    """Test getting deals for San Francisco location"""
    params = {
        "lat": 37.7749,
        "lng": -122.4194,
        "category": "restaurant",
        "radius": 5.0,
        "min_discount": 15.0
    }
    response = requests.get(f"{BASE_URL}/api/deals", params=params)
    assert response.status_code == 200
    deals = response.json()
    
    # Verify deals structure and content
    assert isinstance(deals, list)
    if deals:  # If deals are found
        for deal in deals:
            assert "title" in deal
            assert "business_name" in deal
            assert "category" in deal
            assert "location" in deal
            assert "discount_percentage" in deal
            assert deal["discount_percentage"] >= 15.0
            assert "San Francisco" in deal["location"]["address"]
            assert deal["category"] == "restaurant"

def test_scrape_deals_bengaluru():
    """Test scraping deals for Bengaluru"""
    params = {
        "location": "Jayanagar 2nd Block, Bengaluru",
        "lat": 12.9399,
        "lng": 77.5826,
        "category": "retail"
    }
    response = requests.post(f"{BASE_URL}/api/scrape-deals", params=params)
    assert response.status_code == 200
    assert "stores" in response.json()["message"]

def test_scrape_deals_san_francisco():
    """Test scraping deals for San Francisco"""
    params = {
        "location": "San Francisco, CA",
        "lat": 37.7749,
        "lng": -122.4194,
        "category": "restaurant"
    }
    response = requests.post(f"{BASE_URL}/api/scrape-deals", params=params)
    assert response.status_code == 200
    assert "stores" in response.json()["message"]

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
