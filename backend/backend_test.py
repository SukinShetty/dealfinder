import pytest
import requests
import json
from datetime import datetime

class TestLocalDealFinderAPI:
    def __init__(self):
        self.base_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status=200, params=None):
        """Run a single API test"""
        self.tests_run += 1
        url = f"{self.base_url}/{endpoint}"
        
        print(f"\n🔍 Testing {name}...")
        try:
            if method == 'GET':
                response = requests.get(url, params=params)
            elif method == 'POST':
                response = requests.post(url, json=params)

            if response.status_code == expected_status:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return True, response.json()
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                return False, None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test(
            "Root Endpoint",
            "GET",
            ""
        )

    def test_get_deals_brigade_road(self):
        """Test getting deals for Brigade Road"""
        params = {
            "lat": 12.9720,
            "lng": 77.6081,
            "radius": 1,
            "min_discount": 15
        }
        return self.run_test(
            "Get Brigade Road Deals",
            "GET",
            "deals",
            params=params
        )

    def test_get_deals_jayanagar(self):
        """Test getting deals for Jayanagar"""
        params = {
            "lat": 12.9399,
            "lng": 77.5826,
            "radius": 1,
            "min_discount": 15
        }
        return self.run_test(
            "Get Jayanagar Deals",
            "GET",
            "deals",
            params=params
        )

    def test_generate_sample_deals(self):
        """Test generating sample deals"""
        return self.run_test(
            "Generate Sample Deals",
            "POST",
            "sample-deals"
        )

def main():
    tester = TestLocalDealFinderAPI()
    
    # Test root endpoint
    tester.test_root_endpoint()
    
    # Generate sample deals
    tester.test_generate_sample_deals()
    
    # Test getting deals for different locations
    success, brigade_deals = tester.test_get_deals_brigade_road()
    if success:
        print("\nBrigade Road Deals Analysis:")
        for deal in brigade_deals:
            if "Brigade" in deal["location"]["address"]:
                print(f"✓ Found Brigade Road deal: {deal['business_name']}")
            else:
                print(f"✗ Non-Brigade Road deal found: {deal['business_name']}")

    success, jayanagar_deals = tester.test_get_deals_jayanagar()
    if success:
        print("\nJayanagar Deals Analysis:")
        for deal in jayanagar_deals:
            if "Jayanagar" in deal["location"]["address"]:
                print(f"✓ Found Jayanagar deal: {deal['business_name']}")
            else:
                print(f"✗ Non-Jayanagar deal found: {deal['business_name']}")

    # Print final results
    print(f"\n📊 Tests Summary:")
    print(f"Total Tests: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")

if __name__ == "__main__":
    main()