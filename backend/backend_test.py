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
        """Test generating sample deals"""
        return self.run_test(
            "Generate Sample Deals",
            "POST",
            "api/sample-deals",
            200
        )

    def test_get_deals_bengaluru(self):
        """Test getting deals near Bengaluru"""
        params = {
            "lat": 12.9259,  # Jayanagar, Bengaluru
            "lng": 77.5944,
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
        """Test getting deals near San Francisco"""
        params = {
            "lat": 37.7749,  # San Francisco
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

    def test_get_deals_with_category(self):
        """Test getting deals with category filter"""
        params = {
            "lat": 37.7749,
            "lng": -122.4194,
            "category": "restaurant",
            "radius": 5.0,
            "min_discount": 15.0
        }
        return self.run_test(
            "Get Restaurant Deals",
            "GET",
            "api/deals",
            200,
            params=params
        )

def main():
    # Get backend URL from environment variable
    backend_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com"
    
    # Setup tester
    tester = DealFinderAPITester(backend_url)
    
    # Run tests
    success, _ = tester.test_root_endpoint()
    if not success:
        print("❌ Root endpoint test failed, stopping tests")
        return 1

    # Generate sample deals
    success, _ = tester.test_generate_sample_deals()
    if not success:
        print("❌ Sample deals generation failed, stopping tests")
        return 1

    # Test Bengaluru deals
    success, bengaluru_deals = tester.test_get_deals_bengaluru()
    if success:
        print(f"Found {len(bengaluru_deals)} deals in Bengaluru")
        for deal in bengaluru_deals[:2]:  # Show first 2 deals
            print(f"- {deal['title']} at {deal['business_name']}")

    # Test San Francisco deals
    success, sf_deals = tester.test_get_deals_san_francisco()
    if success:
        print(f"Found {len(sf_deals)} deals in San Francisco")
        for deal in sf_deals[:2]:  # Show first 2 deals
            print(f"- {deal['title']} at {deal['business_name']}")

    # Test category filtering
    success, restaurant_deals = tester.test_get_deals_with_category()
    if success:
        print(f"Found {len(restaurant_deals)} restaurant deals")
        for deal in restaurant_deals[:2]:  # Show first 2 deals
            print(f"- {deal['title']} at {deal['business_name']}")

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    main()