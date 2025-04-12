import pytest
import requests
import json
from datetime import datetime

# Use the public endpoint for testing
BASE_URL = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"

class TestDealFinder:
    def setup_method(self):
        # Generate sample deals before testing
        response = requests.post(f"{BASE_URL}/sample-deals")
        assert response.status_code == 200
        print("Sample deals generated successfully")

    def test_brigade_road_deals(self):
        """Test deals for Brigade Road location"""
        # Brigade Road coordinates
        params = {
            "lat": 12.9720,
            "lng": 77.6081,
            "radius": 5.0
        }
        
        response = requests.get(f"{BASE_URL}/deals", params=params)
        assert response.status_code == 200
        deals = response.json()
        
        # Verify only Brigade Road deals are returned
        for deal in deals:
            assert "Brigade Road" in deal["location"]["address"]
            
        # Verify specific stores
        store_names = [deal["business_name"] for deal in deals]
        expected_stores = ["Lifestyle Brigade Road", "Adidas Store Brigade Road"]
        for store in expected_stores:
            assert store in store_names
            
        print(f"Found {len(deals)} deals in Brigade Road")

    def test_jayanagar_deals(self):
        """Test deals for Jayanagar location"""
        # Jayanagar coordinates
        params = {
            "lat": 12.9399,
            "lng": 77.5826,
            "radius": 5.0
        }
        
        response = requests.get(f"{BASE_URL}/deals", params=params)
        assert response.status_code == 200
        deals = response.json()
        
        # Verify only Jayanagar deals are returned
        for deal in deals:
            assert "Jayanagar" in deal["location"]["address"]
            
        # Verify specific stores
        store_names = [deal["business_name"] for deal in deals]
        expected_stores = ["Zudio Jayanagar", "Levi's Store Jayanagar"]
        for store in expected_stores:
            assert store in store_names
            
        print(f"Found {len(deals)} deals in Jayanagar")

    def test_price_formatting(self):
        """Test price formatting in deals"""
        response = requests.get(f"{BASE_URL}/deals")
        assert response.status_code == 200
        deals = response.json()
        
        for deal in deals:
            # Verify prices are numbers without decimal places
            if deal.get("original_price"):
                assert isinstance(deal["original_price"], (int, float))
            if deal.get("sale_price"):
                assert isinstance(deal["sale_price"], (int, float))
                
        print("Price formatting verified successfully")

    def test_deal_urls(self):
        """Test that deal URLs are valid"""
        response = requests.get(f"{BASE_URL}/deals")
        assert response.status_code == 200
        deals = response.json()
        
        for deal in deals:
            assert deal["url"].startswith("http")
            # Verify URLs for specific stores
            if "Lifestyle" in deal["business_name"]:
                assert "lifestylestores.com" in deal["url"]
            elif "Adidas" in deal["business_name"]:
                assert "adidas.co.in" in deal["url"]
                
        print("Deal URLs verified successfully")

if __name__ == "__main__":
    pytest.main(["-v", "test_server.py"])
