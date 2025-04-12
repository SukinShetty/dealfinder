import pytest
import requests
import json
from datetime import datetime

class TestLocalDealFinder:
    def __init__(self):
        self.base_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status=200, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params)
            elif method == 'POST':
                response = requests.post(url, json=params)

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

    def test_brigade_road_deals(self):
        """Test deals for Brigade Road location"""
        success, response = self.run_test(
            "Brigade Road Deals",
            "GET",
            "deals",
            params={
                "lat": 12.9720,
                "lng": 77.6081,
                "radius": 1.0
            }
        )
        if success:
            deals = response
            print(f"Found {len(deals)} deals for Brigade Road")
            # Verify deals are actually from Brigade Road
            brigade_deals = [d for d in deals if "Brigade" in d["location"]["address"]]
            print(f"Brigade Road specific deals: {len(brigade_deals)}/{len(deals)}")
            return len(brigade_deals) > 0
        return False

    def test_jayanagar_deals(self):
        """Test deals for Jayanagar location"""
        success, response = self.run_test(
            "Jayanagar Deals",
            "GET",
            "deals",
            params={
                "lat": 12.9399,
                "lng": 77.5826,
                "radius": 1.0
            }
        )
        if success:
            deals = response
            print(f"Found {len(deals)} deals for Jayanagar")
            # Verify deals are actually from Jayanagar
            jayanagar_deals = [d for d in deals if "Jayanagar" in d["location"]["address"]]
            print(f"Jayanagar specific deals: {len(jayanagar_deals)}/{len(deals)}")
            return len(jayanagar_deals) > 0
        return False

    def test_price_format(self):
        """Test price formatting in deals"""
        success, response = self.run_test(
            "Price Format",
            "GET",
            "deals",
            params={
                "lat": 12.9720,
                "lng": 77.6081,
                "radius": 5.0
            }
        )
        if success and response:
            deals = response
            for deal in deals[:3]:  # Check first 3 deals
                print(f"\nChecking price format for deal: {deal['title']}")
                if deal.get('original_price'):
                    print(f"Original price: {deal['original_price']}")
                    assert isinstance(deal['original_price'], (int, float))
                if deal.get('sale_price'):
                    print(f"Sale price: {deal['sale_price']}")
                    assert isinstance(deal['sale_price'], (int, float))
            return True
        return False

    def test_view_deal_links(self):
        """Test view deal links"""
        success, response = self.run_test(
            "View Deal Links",
            "GET",
            "deals",
            params={
                "lat": 12.9720,
                "lng": 77.6081,
                "radius": 5.0
            }
        )
        if success and response:
            deals = response
            for deal in deals[:3]:  # Check first 3 deals
                print(f"\nChecking deal URL: {deal['title']}")
                assert deal['url'].startswith('http'), f"Invalid URL format: {deal['url']}"
            return True
        return False

def main():
    tester = TestLocalDealFinder()
    
    # First ensure we have sample data
    print("\n🔄 Generating sample data...")
    requests.post(f"{tester.base_url}/sample-deals")
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if tester.test_brigade_road_deals():
        tests_passed += 1
    
    if tester.test_jayanagar_deals():
        tests_passed += 1
    
    if tester.test_price_format():
        tests_passed += 1
    
    if tester.test_view_deal_links():
        tests_passed += 1

    # Print results
    print(f"\n📊 Tests passed: {tests_passed}/{total_tests}")
    return 0 if tests_passed == total_tests else 1

if __name__ == "__main__":
    main()