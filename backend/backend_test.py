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

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )

    def test_get_deals_bengaluru(self):
        """Test getting deals for Bengaluru location"""
        params = {
            'lat': 12.9399039,
            'lng': 77.5826382,
            'category': 'retail',
            'radius': 5.0,
            'min_discount': 15.0
        }
        return self.run_test(
            "Get Bengaluru Deals",
            "GET",
            "deals",
            200,
            params
        )

    def test_get_deals_san_francisco(self):
        """Test getting deals for San Francisco location"""
        params = {
            'lat': 37.7749,
            'lng': -122.4194,
            'category': 'restaurant',
            'radius': 5.0,
            'min_discount': 15.0
        }
        return self.run_test(
            "Get San Francisco Deals",
            "GET",
            "deals",
            200,
            params
        )

    def test_scrape_deals(self):
        """Test the deal scraping endpoint"""
        params = {
            'location': 'Jayanagar 2nd Block, Bengaluru',
            'lat': 12.9399039,
            'lng': 77.5826382,
            'category': 'retail'
        }
        return self.run_test(
            "Scrape Deals",
            "POST",
            "scrape-deals",
            200,
            params
        )

    def test_sample_deals(self):
        """Test generating sample deals"""
        return self.run_test(
            "Generate Sample Deals",
            "POST",
            "sample-deals",
            200
        )

def main():
    # Initialize tester with the backend URL
    tester = DealFinderAPITester("https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com")
    
    # Run all tests
    tester.test_root_endpoint()
    tester.test_sample_deals()  # Generate sample data first
    tester.test_get_deals_bengaluru()
    tester.test_get_deals_san_francisco()
    tester.test_scrape_deals()

    # Print results
    print(f"\n📊 Tests Summary:")
    print(f"Total tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    main()