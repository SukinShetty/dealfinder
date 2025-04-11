import requests
import pytest
from datetime import datetime

class DealFinderAPITester:
    def __init__(self, base_url="https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"Response: {response.json()}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")

            return success, response.json() if success else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_get_deals(self):
        """Test getting all deals"""
        return self.run_test(
            "Get All Deals",
            "GET",
            "deals",
            200
        )

    def test_filtered_deals(self, category=None, min_discount=None, lat=37.7749, lon=-122.4194):
        """Test getting filtered deals"""
        params = {}
        if category:
            params['category'] = category
        if min_discount:
            params['min_discount'] = min_discount
        if lat and lon:
            params['lat'] = lat
            params['lon'] = lon
        
        return self.run_test(
            f"Get Filtered Deals (category={category}, min_discount={min_discount}, location=({lat},{lon}))",
            "GET",
            "deals",
            200,
            params=params
        )

def main():
    tester = DealFinderAPITester()
    
    # Test 1: Get all deals
    print("\n📌 Testing basic deals endpoint...")
    success, deals = tester.test_get_deals()
    
    # Test 2: Filter by category
    print("\n📌 Testing category filter - Retail...")
    tester.test_filtered_deals(category="retail")
    
    print("\n📌 Testing category filter - Restaurant...")
    tester.test_filtered_deals(category="restaurant")
    
    # Test 3: Filter by minimum discount
    print("\n📌 Testing minimum discount filter...")
    tester.test_filtered_deals(min_discount=20)
    
    # Test 4: Filter by location
    print("\n📌 Testing location-based filtering...")
    tester.test_filtered_deals(lat=37.7749, lon=-122.4194)
    
    # Test 5: Combined filters
    print("\n📌 Testing combined filters...")
    tester.test_filtered_deals(
        category="retail",
        min_discount=30,
        lat=37.7749,
        lon=-122.4194
    )
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    main()
