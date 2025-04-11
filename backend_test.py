import requests
import pytest
from datetime import datetime

class TestLocalDealFinder:
    def __init__(self):
        self.base_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"
        self.test_coordinates = {
            "lat": 37.7749,
            "lng": -122.4194
        }
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
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
                return True, response.json()
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                return False, None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_api_health(self):
        """Test API health endpoint"""
        return self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )

    def test_generate_sample_deals(self):
        """Test sample deals generation"""
        return self.run_test(
            "Generate Sample Deals",
            "POST",
            "sample-deals",
            200
        )

    def test_get_all_deals(self):
        """Test getting all deals without filters"""
        return self.run_test(
            "Get All Deals",
            "GET",
            "deals",
            200
        )

    def test_get_deals_with_location(self):
        """Test getting deals with location filter"""
        params = {
            "lat": self.test_coordinates["lat"],
            "lng": self.test_coordinates["lng"],
            "radius": 5
        }
        return self.run_test(
            "Get Deals with Location",
            "GET",
            "deals",
            200,
            params=params
        )

    def test_get_deals_with_category(self):
        """Test getting deals filtered by category"""
        params = {"category": "retail"}
        return self.run_test(
            "Get Deals by Category",
            "GET",
            "deals",
            200,
            params=params
        )

    def test_get_deals_with_min_discount(self):
        """Test getting deals filtered by minimum discount"""
        params = {"min_discount": 30}
        return self.run_test(
            "Get Deals by Min Discount",
            "GET",
            "deals",
            200,
            params=params
        )

    def test_get_deals_with_all_filters(self):
        """Test getting deals with all filters combined"""
        params = {
            "lat": self.test_coordinates["lat"],
            "lng": self.test_coordinates["lng"],
            "radius": 5,
            "category": "retail",
            "min_discount": 30
        }
        return self.run_test(
            "Get Deals with All Filters",
            "GET",
            "deals",
            200,
            params=params
        )

    def validate_deal_structure(self, deal):
        """Validate the structure of a deal object"""
        required_fields = [
            "id", "title", "description", "discount_percentage",
            "business_name", "category", "location"
        ]
        
        for field in required_fields:
            if field not in deal:
                print(f"❌ Missing required field: {field}")
                return False
        
        if "location" in deal:
            location_fields = ["lat", "lng", "address"]
            for field in location_fields:
                if field not in deal["location"]:
                    print(f"❌ Missing required location field: {field}")
                    return False
        
        return True

    def run_all_tests(self):
        """Run all tests and validate responses"""
        print("\n🚀 Starting Local Deal Finder API Tests...")

        # Generate sample deals first
        success, _ = self.test_generate_sample_deals()
        if not success:
            print("❌ Failed to generate sample deals, stopping tests")
            return False

        # Test API health
        success, _ = self.test_api_health()
        if not success:
            print("❌ API health check failed, stopping tests")
            return False

        # Test getting all deals
        success, response = self.test_get_all_deals()
        if success and response:
            print(f"Found {len(response)} deals")
            # Validate first deal structure
            if len(response) > 0:
                if not self.validate_deal_structure(response[0]):
                    print("❌ Deal structure validation failed")
                    return False

        # Test location-based filtering
        self.test_get_deals_with_location()

        # Test category filtering
        self.test_get_deals_with_category()

        # Test discount filtering
        self.test_get_deals_with_min_discount()

        # Test all filters combined
        self.test_get_deals_with_all_filters()

        # Print test results
        print(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = TestLocalDealFinder()
    success = tester.run_all_tests()
    exit(0 if success else 1)
