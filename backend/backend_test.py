import pytest
import requests
import json
from datetime import datetime

class DealFinderAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, params=None, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
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
                return False, None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_root_endpoint(self):
        """Test root endpoint"""
        return self.run_test(
            "Root Endpoint",
            "GET",
            "api",
            200
        )

    def test_generate_sample_deals(self):
        """Generate sample deals"""
        return self.run_test(
            "Generate Sample Deals",
            "POST",
            "api/sample-deals",
            200
        )

    def test_get_deals_bengaluru(self):
        """Test getting deals in Bengaluru"""
        params = {
            "lat": 12.9399039,
            "lng": 77.5826382,
            "radius": 5.0,
            "min_discount": 15.0
        }
        return self.run_test(
            "Get Bengaluru Deals",
            "GET",
            "api/deals",
            200,
            params=params
        )

    def test_get_deals_san_francisco(self):
        """Test getting deals in San Francisco"""
        params = {
            "lat": 37.7749,
            "lng": -122.4194,
            "radius": 5.0,
            "min_discount": 15.0
        }
        return self.run_test(
            "Get San Francisco Deals",
            "GET",
            "api/deals",
            200,
            params=params
        )

    def test_category_filter(self):
        """Test category filtering"""
        params = {
            "lat": 37.7749,
            "lng": -122.4194,
            "category": "retail",
            "radius": 5.0,
            "min_discount": 15.0
        }
        return self.run_test(
            "Category Filter (Retail)",
            "GET",
            "api/deals",
            200,
            params=params
        )

    def test_discount_filter(self):
        """Test minimum discount filtering"""
        params = {
            "lat": 37.7749,
            "lng": -122.4194,
            "min_discount": 40.0
        }
        return self.run_test(
            "High Discount Filter (>40%)",
            "GET",
            "api/deals",
            200,
            params=params
        )

def main():
    # Get the backend URL from environment variable
    backend_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df-backend.preview.emergentagent.com"
    
    # Initialize tester
    tester = DealFinderAPITester(backend_url)
    
    # Run tests
    print("\n🚀 Starting API Tests...")
    
    # Test root endpoint
    root_success, _ = tester.test_root_endpoint()
    if not root_success:
        print("❌ Root endpoint test failed, stopping tests")
        return 1

    # Generate sample deals
    sample_success, _ = tester.test_generate_sample_deals()
    if not sample_success:
        print("❌ Sample deals generation failed, stopping tests")
        return 1

    # Test location-based filtering
    bengaluru_success, bengaluru_deals = tester.test_get_deals_bengaluru()
    if bengaluru_success:
        print(f"Found {len(bengaluru_deals)} deals in Bengaluru")
        # Verify deals are actually in Bengaluru
        bengaluru_deals_count = sum(1 for deal in bengaluru_deals if "Bengaluru" in deal["location"]["address"])
        print(f"Verified Bengaluru deals: {bengaluru_deals_count}")

    sf_success, sf_deals = tester.test_get_deals_san_francisco()
    if sf_success:
        print(f"Found {len(sf_deals)} deals in San Francisco")
        # Verify deals are actually in San Francisco
        sf_deals_count = sum(1 for deal in sf_deals if "San Francisco" in deal["location"]["address"])
        print(f"Verified San Francisco deals: {sf_deals_count}")

    # Test category filtering
    category_success, retail_deals = tester.test_category_filter()
    if category_success:
        print(f"Found {len(retail_deals)} retail deals")
        # Verify all deals are retail
        retail_count = sum(1 for deal in retail_deals if deal["category"] == "retail")
        print(f"Verified retail deals: {retail_count}")

    # Test discount filtering
    discount_success, high_discount_deals = tester.test_discount_filter()
    if discount_success:
        print(f"Found {len(high_discount_deals)} high-discount deals")
        # Verify all deals have high discount
        high_discount_count = sum(1 for deal in high_discount_deals if deal["discount_percentage"] >= 40.0)
        print(f"Verified high discount deals: {high_discount_count}")

    # Print final results
    print(f"\n📊 Tests Summary:")
    print(f"Total tests: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")

    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    exit(main())