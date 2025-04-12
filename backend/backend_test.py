import unittest
import requests
import json

class DealFinderAPITest(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"
        
    def test_root_endpoint(self):
        response = requests.get(f"{self.base_url}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Welcome to the Real-Time Local Deal Finder API")

    def test_get_deals_no_location(self):
        response = requests.get(f"{self.base_url}/deals")
        self.assertEqual(response.status_code, 200)
        deals = response.json()
        self.assertIsInstance(deals, list)

    def test_get_deals_with_location(self):
        params = {
            "lat": 12.9399039,
            "lng": 77.5826382,
            "category": "retail",
            "radius": 5,
            "min_discount": 15
        }
        response = requests.get(f"{self.base_url}/deals", params=params)
        self.assertEqual(response.status_code, 200)
        deals = response.json()
        self.assertIsInstance(deals, list)
        
        if deals:  # If deals are found
            first_deal = deals[0]
            required_fields = ["id", "title", "description", "discount_percentage", 
                             "business_name", "category", "location"]
            for field in required_fields:
                self.assertIn(field, first_deal)

    def test_scrape_deals(self):
        params = {
            "location": "Jayanagar 2nd Block, Bengaluru",
            "lat": 12.9399039,
            "lng": 77.5826382,
            "category": "retail"
        }
        response = requests.post(f"{self.base_url}/scrape-deals", params=params)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)

    def test_sample_deals(self):
        response = requests.post(f"{self.base_url}/sample-deals")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)

if __name__ == "__main__":
    unittest.main()