import unittest
import requests
import json
from datetime import datetime

class DealFinderAPITest(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"
        
    def test_root_endpoint(self):
        response = requests.get(f"{self.base_url}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the Real-Time Local Deal Finder API"})

    def test_get_deals_no_location(self):
        response = requests.get(f"{self.base_url}/deals")
        self.assertEqual(response.status_code, 200)
        deals = response.json()
        self.assertIsInstance(deals, list)

    def test_get_deals_bengaluru(self):
        params = {
            "lat": 12.9399,
            "lng": 77.5826,
            "category": "retail",
            "radius": 5.0,
            "min_discount": 15.0
        }
        response = requests.get(f"{self.base_url}/deals", params=params)
        self.assertEqual(response.status_code, 200)
        deals = response.json()
        self.assertIsInstance(deals, list)
        if deals:  # If deals are found
            self.assertIn("Bengaluru", deals[0]["location"]["address"])

    def test_get_deals_san_francisco(self):
        params = {
            "lat": 37.7749,
            "lng": -122.4194,
            "category": "retail",
            "radius": 5.0,
            "min_discount": 15.0
        }
        response = requests.get(f"{self.base_url}/deals", params=params)
        self.assertEqual(response.status_code, 200)
        deals = response.json()
        self.assertIsInstance(deals, list)
        if deals:  # If deals are found
            self.assertIn("San Francisco", deals[0]["location"]["address"])

    def test_generate_sample_deals(self):
        response = requests.post(f"{self.base_url}/sample-deals")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)
        self.assertIn("Generated", result["message"])

    def test_scrape_deals_bengaluru(self):
        params = {
            "location": "Jayanagar 2nd Block, Bengaluru",
            "lat": 12.9399,
            "lng": 77.5826,
            "category": "retail"
        }
        response = requests.post(f"{self.base_url}/scrape-deals", params=params)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)

if __name__ == '__main__':
    unittest.main()