import requests
import unittest
from datetime import datetime

class DealFinderAPITest(unittest.TestCase):
    def setUp(self):
        self.base_url = "https://484ff713-fe7c-4092-8908-e6296d7ea8df.preview.emergentagent.com/api"
        self.test_deal = {
            "title": f"Test Deal {datetime.now().strftime('%H%M%S')}",
            "description": "50% off on all items",
            "category": "retail",
            "location": {
                "type": "Point",
                "coordinates": [-122.4194, 37.7749]  # San Francisco coordinates
            },
            "expiration": "2025-03-01T00:00:00Z",
            "discount": "50%"
        }

    def test_1_create_deal(self):
        """Test creating a new deal"""
        response = requests.post(f"{self.base_url}/deals", json=self.test_deal)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.test_deal["id"] = data["id"]
        print("✅ Create deal test passed")

    def test_2_get_deals(self):
        """Test getting all deals"""
        response = requests.get(f"{self.base_url}/deals")
        self.assertEqual(response.status_code, 200)
        deals = response.json()
        self.assertIsInstance(deals, list)
        print("✅ Get all deals test passed")

    def test_3_get_deals_by_location(self):
        """Test getting deals by location"""
        params = {
            "lat": 37.7749,
            "lon": -122.4194,
            "radius": 10000  # 10km radius
        }
        response = requests.get(f"{self.base_url}/deals", params=params)
        self.assertEqual(response.status_code, 200)
        deals = response.json()
        self.assertIsInstance(deals, list)
        print("✅ Get deals by location test passed")

    def test_4_get_deals_by_category(self):
        """Test getting deals by category"""
        categories = ["retail", "restaurant"]
        for category in categories:
            response = requests.get(f"{self.base_url}/deals", params={"category": category})
            self.assertEqual(response.status_code, 200)
            deals = response.json()
            self.assertIsInstance(deals, list)
            if deals:
                self.assertTrue(all(deal["category"] == category for deal in deals))
        print("✅ Get deals by category test passed")

    def test_5_check_duplicate_deals(self):
        """Test that duplicate deals are not allowed"""
        # Try to create the same deal again
        response = requests.post(f"{self.base_url}/deals", json=self.test_deal)
        self.assertNotEqual(response.status_code, 200)
        print("✅ Duplicate deal prevention test passed")

    def test_6_check_distance_calculation(self):
        """Test distance calculation in deal responses"""
        params = {
            "lat": 37.7749,
            "lon": -122.4194
        }
        response = requests.get(f"{self.base_url}/deals", params=params)
        self.assertEqual(response.status_code, 200)
        deals = response.json()
        if deals:
            self.assertTrue(all("distance" in deal for deal in deals))
        print("✅ Distance calculation test passed")

if __name__ == "__main__":
    unittest.main(verbosity=2)
