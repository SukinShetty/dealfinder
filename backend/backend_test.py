import requests
import pytest
from datetime import datetime

class TestLocalDealFinder:
    def __init__(self):
        self.base_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params)
            elif method == 'POST':
                response = requests.post(url)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return True, response.json()
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_bengaluru_deals(self):
        """Test deals in Bengaluru location"""
        success, response = self.run_test(
            "Bengaluru Deals",
            "GET",
            "deals",
            200,
            params={
                "lat": 12.9399039,
                "lng": 77.5826382,
                "radius": 5.0
            }
        )
        
        if success:
            # Verify all deals are from Bengaluru
            bengaluru_deals = [deal for deal in response if "Bengaluru" in deal["location"]["address"]]
            print(f"Found {len(bengaluru_deals)} Bengaluru deals out of {len(response)} total deals")
            return len(bengaluru_deals) > 0
        return False

    def test_san_francisco_deals(self):
        """Test deals in San Francisco location"""
        success, response = self.run_test(
            "San Francisco Deals",
            "GET",
            "deals",
            200,
            params={
                "lat": 37.7749,
                "lng": -122.4194,
                "radius": 5.0
            }
        )
        
        if success:
            # Verify all deals are from San Francisco
            sf_deals = [deal for deal in response if "San Francisco" in deal["location"]["address"]]
            print(f"Found {len(sf_deals)} San Francisco deals out of {len(response)} total deals")
            return len(sf_deals) > 0
        return False

    def test_category_filter(self):
        """Test category filtering"""
        success, response = self.run_test(
            "Category Filter - Restaurants",
            "GET",
            "deals",
            200,
            params={
                "category": "restaurant",
                "lat": 37.7749,
                "lng": -122.4194
            }
        )
        
        if success:
            # Verify all deals are restaurants
            restaurant_deals = [deal for deal in response if deal["category"] == "restaurant"]
            print(f"Found {len(restaurant_deals)} restaurant deals out of {len(response)} total deals")
            return len(restaurant_deals) == len(response)
        return False

    def test_minimum_discount(self):
        """Test minimum discount filter"""
        min_discount = 30.0
        success, response = self.run_test(
            f"Minimum Discount Filter ({min_discount}%)",
            "GET",
            "deals",
            200,
            params={
                "min_discount": min_discount,
                "lat": 37.7749,
                "lng": -122.4194
            }
        )
        
        if success:
            # Verify all deals meet minimum discount
            valid_deals = [deal for deal in response if deal["discount_percentage"] >= min_discount]
            print(f"Found {len(valid_deals)} deals with {min_discount}%+ discount out of {len(response)} total deals")
            return len(valid_deals) == len(response)
        return False

    def test_distance_filter(self):
        """Test distance-based filtering"""
        radius = 2.0
        success, response = self.run_test(
            f"Distance Filter ({radius} miles)",
            "GET",
            "deals",
            200,
            params={
                "lat": 37.7749,
                "lng": -122.4194,
                "radius": radius
            }
        )
        
        if success:
            # Verify all deals are within radius
            nearby_deals = [deal for deal in response if deal.get("distance", float('inf')) <= radius]
            print(f"Found {len(nearby_deals)} deals within {radius} miles out of {len(response)} total deals")
            return len(nearby_deals) == len(response)
        return False

def main():
    # Initialize test suite
    tester = TestLocalDealFinder()
    
    # Generate sample deals first
    print("\n🔄 Generating sample deals...")
    requests.post(f"{tester.base_url}/sample-deals")
    
    # Run tests
    tests = [
        ("Location - Bengaluru", tester.test_bengaluru_deals),
        ("Location - San Francisco", tester.test_san_francisco_deals),
        ("Category Filter", tester.test_category_filter),
        ("Minimum Discount", tester.test_minimum_discount),
        ("Distance Filter", tester.test_distance_filter)
    ]
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        result = test_func()
        print(f"{'✅ Passed' if result else '❌ Failed'}: {test_name}")
    
    # Print summary
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    main()
