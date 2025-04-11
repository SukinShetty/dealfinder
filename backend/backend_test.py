import pytest
import requests
import json
from datetime import datetime

# Use the public endpoint for testing
BASE_URL = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"

def test_api_root():
    response = requests.get(f"{BASE_URL}")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to the Real-Time Local Deal Finder API"

def test_generate_sample_deals():
    response = requests.post(f"{BASE_URL}/sample-deals")
    assert response.status_code == 200
    assert "Generated" in response.json()["message"]

def test_bengaluru_deals():
    # Test Jayanagar 2nd Block, Bengaluru coordinates
    params = {
        "lat": 12.9399039,
        "lng": 77.5826382,
        "radius": 5,
        "min_discount": 15
    }
    response = requests.get(f"{BASE_URL}/deals", params=params)
    assert response.status_code == 200
    deals = response.json()
    assert len(deals) > 0
    
    # Verify deals are in Bengaluru
    bengaluru_deals = [deal for deal in deals if "Bengaluru" in deal["location"]["address"]]
    assert len(bengaluru_deals) > 0
    print(f"Found {len(bengaluru_deals)} deals in Bengaluru")

def test_san_francisco_deals():
    # Test San Francisco coordinates
    params = {
        "lat": 37.7749,
        "lng": -122.4194,
        "radius": 5,
        "min_discount": 15
    }
    response = requests.get(f"{BASE_URL}/deals", params=params)
    assert response.status_code == 200
    deals = response.json()
    assert len(deals) > 0
    
    # Verify deals are in San Francisco
    sf_deals = [deal for deal in deals if "San Francisco" in deal["location"]["address"]]
    assert len(sf_deals) > 0
    print(f"Found {len(sf_deals)} deals in San Francisco")

def test_category_filter():
    # Test retail category in Bengaluru
    params = {
        "lat": 12.9399039,
        "lng": 77.5826382,
        "radius": 5,
        "min_discount": 15,
        "category": "retail"
    }
    response = requests.get(f"{BASE_URL}/deals", params=params)
    assert response.status_code == 200
    deals = response.json()
    assert len(deals) > 0
    assert all(deal["category"] == "retail" for deal in deals)

if __name__ == "__main__":
    print("Running backend API tests...")
    test_api_root()
    print("✅ API root test passed")
    
    test_generate_sample_deals()
    print("✅ Sample deals generation test passed")
    
    test_bengaluru_deals()
    print("✅ Bengaluru deals test passed")
    
    test_san_francisco_deals()
    print("✅ San Francisco deals test passed")
    
    test_category_filter()
    print("✅ Category filter test passed")
    
    print("\n✨ All backend tests completed successfully!")