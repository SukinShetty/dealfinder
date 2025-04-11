import requests
import sys
from datetime import datetime

class DealFinderAPITester:
    def __init__(self, base_url="https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

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

    def test_get_all_deals(self):
        """Test getting all deals"""
        return self.run_test(
            "Get All Deals",
            "GET",
            "deals",
            200
        )

    def test_get_deals_with_location(self, lat, lon):
        """Test getting deals with location filtering"""
        params = {
            "latitude": lat,
            "longitude": lon
        }
        return self.run_test(
            "Get Deals with Location",
            "GET",
            "deals",
            200,
            params=params
        )

    def test_get_deals_by_category(self, category):
        """Test getting deals filtered by category"""
        params = {
            "category": category
        }
        return self.run_test(
            "Get Deals by Category",
            "GET",
            "deals",
            200,
            params=params
        )

    def test_get_deals_with_location_and_category(self, lat, lon, category):
        """Test getting deals filtered by both location and category"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "category": category
        }
        return self.run_test(
            "Get Deals with Location and Category",
            "GET",
            "deals",
            200,
            params=params
        )

def main():
    # Setup
    tester = DealFinderAPITester()
    
    # Test 1: Get all deals
    print("\n📋 Testing basic deals retrieval...")
    success, all_deals = tester.test_get_all_deals()
    if success:
        # Check for duplicates
        deal_ids = [deal["id"] for deal in all_deals["deals"]]
        unique_ids = set(deal_ids)
        if len(deal_ids) != len(unique_ids):
            print("❌ Found duplicate deals!")
        else:
            print("✅ No duplicate deals found")

    # Test 2: Test with San Francisco coordinates
    print("\n📍 Testing location-based filtering...")
    success, location_deals = tester.test_get_deals_with_location(37.7749, -122.4194)
    
    # Test 3: Test retail category
    print("\n🏪 Testing retail category filtering...")
    success, retail_deals = tester.test_get_deals_by_category("retail")
    
    # Test 4: Test restaurant category
    print("\n🍽️ Testing restaurant category filtering...")
    success, restaurant_deals = tester.test_get_deals_by_category("restaurant")
    
    # Test 5: Test combined location and category
    print("\n🎯 Testing combined location and category filtering...")
    success, combined_deals = tester.test_get_deals_with_location_and_category(37.7749, -122.4194, "retail")

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
