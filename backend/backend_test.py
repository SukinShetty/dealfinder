import requests
import pytest
from datetime import datetime

class DealFinderAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, params=None, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return True, response.json()
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_generate_sample_data(self):
        """Generate sample deals data"""
        return self.run_test(
            "Generate Sample Data",
            "POST",
            "sample-deals",
            200
        )

    def test_get_deals_san_francisco(self):
        """Test getting deals in San Francisco"""
        return self.run_test(
            "Get San Francisco Deals",
            "GET",
            "deals",
            200,
            params={
                "lat": 37.7749,
                "lng": -122.4194,
                "radius": 5.0,
                "min_discount": 15.0
            }
        )

    def test_get_deals_bengaluru(self):
        """Test getting deals in Bengaluru (Jayanagar)"""
        return self.run_test(
            "Get Bengaluru Deals",
            "GET",
            "deals",
            200,
            params={
                "lat": 12.9259,
                "lng": 77.5944,
                "radius": 5.0,
                "min_discount": 15.0
            }
        )

    def test_get_deals_invalid_location(self):
        """Test getting deals with invalid location (middle of ocean)"""
        return self.run_test(
            "Get Deals Invalid Location",
            "GET",
            "deals",
            200,
            params={
                "lat": 0.0,
                "lng": 0.0,
                "radius": 5.0,
                "min_discount": 15.0
            }
        )

    def test_get_deals_with_category(self):
        """Test getting deals filtered by category"""
        return self.run_test(
            "Get Deals By Category",
            "GET",
            "deals",
            200,
            params={
                "lat": 37.7749,
                "lng": -122.4194,
                "category": "restaurant",
                "radius": 5.0,
                "min_discount": 15.0
            }
        )

def main():
    # Setup
    base_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com"
    tester = DealFinderAPITester(base_url)

    # First generate sample data
    success, response = tester.test_generate_sample_data()
    if not success:
        print("❌ Failed to generate sample data, stopping tests")
        return 1

    print("\n🔄 Testing different locations and filters...")
    
    # Test San Francisco deals
    success, sf_deals = tester.test_get_deals_san_francisco()
    if success:
        print(f"Found {len(sf_deals)} deals in San Francisco")
        
    # Test Bengaluru deals
    success, blr_deals = tester.test_get_deals_bengaluru()
    if success:
        print(f"Found {len(blr_deals)} deals in Bengaluru")

    # Test invalid location
    success, invalid_deals = tester.test_get_deals_invalid_location()
    if success:
        print(f"Found {len(invalid_deals)} deals for invalid location (should be 0)")

    # Test category filter
    success, category_deals = tester.test_get_deals_with_category()
    if success:
        print(f"Found {len(category_deals)} restaurant deals")

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    main()