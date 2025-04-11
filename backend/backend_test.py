import requests
import pytest
from datetime import datetime

class TestLocalDealFinder:
    def __init__(self):
        self.base_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"
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
            "API Health",
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

    def test_get_deals_no_location(self):
        """Test getting deals without location"""
        return self.run_test(
            "Get Deals (No Location)",
            "GET",
            "deals",
            200
        )

    def test_get_deals_with_location(self):
        """Test getting deals with location"""
        params = {
            'lat': 12.9259,  # Jayanagar, Bengaluru coordinates
            'lng': 77.5944,
            'radius': 5,
            'min_discount': 15
        }
        return self.run_test(
            "Get Deals (With Location)",
            "GET",
            "deals",
            200,
            params=params
        )

    def test_get_deals_with_filters(self):
        """Test getting deals with filters"""
        params = {
            'category': 'retail',
            'min_discount': 25,
            'radius': 10,
            'lat': 37.7749,  # San Francisco coordinates
            'lng': -122.4194
        }
        return self.run_test(
            "Get Deals (With Filters)",
            "GET",
            "deals",
            200,
            params=params
        )

def main():
    tester = TestLocalDealFinder()
    
    # Run tests
    print("🚀 Starting API Tests...")
    
    # Test 1: API Health
    success, _ = tester.test_api_health()
    if not success:
        print("❌ API health check failed, stopping tests")
        return 1

    # Test 2: Generate Sample Deals
    success, _ = tester.test_generate_sample_deals()
    if not success:
        print("❌ Sample deals generation failed")
        return 1

    # Test 3: Get Deals (No Location)
    success, deals = tester.test_get_deals_no_location()
    if not success:
        print("❌ Getting deals without location failed")
        return 1
    print(f"📊 Found {len(deals)} deals without location filter")

    # Test 4: Get Deals (Jayanagar, Bengaluru)
    success, deals = tester.test_get_deals_with_location()
    if not success:
        print("❌ Getting deals with location failed")
        return 1
    print(f"📊 Found {len(deals)} deals near Jayanagar, Bengaluru")

    # Test 5: Get Deals (San Francisco with filters)
    success, deals = tester.test_get_deals_with_filters()
    if not success:
        print("❌ Getting deals with filters failed")
        return 1
    print(f"📊 Found {len(deals)} deals in San Francisco with filters")

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    main()