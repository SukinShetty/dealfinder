import requests
import pytest
from datetime import datetime

class DealFinderAPITester:
    def __init__(self, base_url):
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
            elif method == 'POST':
                response = requests.post(url, params=params)

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

    def test_location_based_filtering(self):
        """Test location-based deal filtering"""
        print("\n📍 Testing Location-based Filtering...")

        # Test Brigade Road deals
        success, brigade_deals = self.run_test(
            "Brigade Road Deals",
            "GET",
            "deals",
            200,
            params={
                "lat": "12.9720",
                "lng": "77.6081",
                "radius": "5"
            }
        )
        if success:
            brigade_stores = [d["business_name"] for d in brigade_deals]
            print(f"Brigade Road stores found: {brigade_stores}")
            assert any("Brigade Road" in d["location"]["address"] for d in brigade_deals), "No Brigade Road deals found"

        # Test Jayanagar deals
        success, jayanagar_deals = self.run_test(
            "Jayanagar Deals",
            "GET",
            "deals",
            200,
            params={
                "lat": "12.9399",
                "lng": "77.5826",
                "radius": "5"
            }
        )
        if success:
            jayanagar_stores = [d["business_name"] for d in jayanagar_deals]
            print(f"Jayanagar stores found: {jayanagar_stores}")
            assert any("Jayanagar" in d["location"]["address"] for d in jayanagar_deals), "No Jayanagar deals found"

    def test_price_formatting(self):
        """Test price formatting in deals"""
        print("\n💰 Testing Price Formatting...")
        
        success, deals = self.run_test(
            "Get Deals with Prices",
            "GET",
            "deals",
            200
        )
        if success and deals:
            for deal in deals:
                if deal.get("original_price"):
                    assert isinstance(deal["original_price"], (int, float)), "Original price should be numeric"
                if deal.get("sale_price"):
                    assert isinstance(deal["sale_price"], (int, float)), "Sale price should be numeric"
                print(f"✅ Price format valid for deal: {deal['title']}")

def main():
    # Initialize tester with the public endpoint
    tester = DealFinderAPITester("https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com")

    # Generate sample deals first
    print("\n🔄 Generating sample deals...")
    tester.run_test("Generate Sample Deals", "POST", "sample-deals", 200)

    # Run tests
    tester.test_location_based_filtering()
    tester.test_price_formatting()

    # Print results
    print(f"\n📊 Tests Summary:")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    main()