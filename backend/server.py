from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import os
import logging
import requests
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from pathlib import Path
import json
from math import radians, sin, cos, sqrt, atan2

# /backend 
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Firecrawl API key
FIRECRAWL_API_KEY = os.environ.get('FIRECRAWL_API_KEY')

# Data models
class Location(BaseModel):
    lat: float
    lng: float
    address: str

class Deal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    discount_percentage: float
    original_price: Optional[float] = None
    sale_price: Optional[float] = None
    business_name: str
    category: str
    location: Location
    expiration_date: Optional[datetime] = None
    image_url: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

# Calculate distance between two coordinates in miles
def calculate_distance(lat1, lng1, lat2, lng2):
    # Convert latitude and longitude from degrees to radians
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    radius = 3956  # Radius of Earth in miles
    distance = radius * c
    
    return distance

# Firecrawl API integration
async def scrape_deals():
    """
    Use Firecrawl API to scrape deals from websites
    """
    try:
        # Example target websites for retail and restaurants
        # This would be expanded or made configurable in a production app
        target_sites = [
            "https://www.example-retail.com",
            "https://www.example-restaurant.com"
        ]
        
        all_deals = []
        
        for site in target_sites:
            # Set up Firecrawl API request
            headers = {
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # This payload would be customized based on the actual structure of the target sites
            payload = {
                "url": site,
                "selectors": [
                    {
                        "name": "deals",
                        "selector": ".deal-item",  # CSS selector for deal elements
                        "type": "list",
                        "properties": {
                            "title": ".deal-title",
                            "description": ".deal-description",
                            "discount": ".discount-percentage",
                            "original_price": ".original-price",
                            "sale_price": ".sale-price",
                            "business_name": ".business-name",
                            "location": ".location-data",  # This would contain address data
                            "expiration": ".expiration-date"
                        }
                    }
                ]
            }
            
            # Example usage of Firecrawl API (URL would be adjusted based on actual API)
            response = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if "deals" in data and data["deals"]:
                    all_deals.extend(data["deals"])
            else:
                logger.error(f"Error from Firecrawl API: {response.status_code} - {response.text}")
        
        # Process and store deals
        for deal_data in all_deals:
            # Extract and format deal data
            # This would be customized based on the actual structure of scraped data
            try:
                discount_text = deal_data.get("discount", "0%").strip("%")
                discount_percentage = float(discount_text)
                
                if discount_percentage < 15:
                    continue  # Skip deals with less than 15% discount
                
                # Format location data
                location_data = deal_data.get("location", "")
                # In a real app, we'd use geocoding to get lat/lng from address
                # For now, use placeholder values
                location = Location(
                    lat=37.7749,  # Example latitude
                    lng=-122.4194,  # Example longitude
                    address=location_data
                )
                
                # Create deal object
                deal = Deal(
                    title=deal_data.get("title", ""),
                    description=deal_data.get("description", ""),
                    discount_percentage=discount_percentage,
                    business_name=deal_data.get("business_name", ""),
                    category="retail" if "retail" in site else "restaurant",
                    location=location,
                    original_price=float(deal_data.get("original_price", "0").strip("$") or 0),
                    sale_price=float(deal_data.get("sale_price", "0").strip("$") or 0),
                    url=site
                )
                
                # Store in database
                await db.deals.insert_one(deal.dict())
                
            except Exception as e:
                logger.error(f"Error processing deal: {e}")
                
        return {"message": f"Scraped and processed {len(all_deals)} deals"}
    
    except Exception as e:
        logger.error(f"Error in scrape_deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mock function to generate sample deals for testing
async def generate_sample_deals():
    """
    Generate sample deals for testing purposes
    """
    sample_deals = [
        {
            "title": "50% Off All Clothing",
            "description": "Get 50% off all clothing items in store. Limited time offer!",
            "discount_percentage": 50.0,
            "business_name": "Fashion Outlet",
            "category": "retail",
            "location": {
                "lat": 37.7749,
                "lng": -122.4194,
                "address": "123 Market St, San Francisco, CA"
            },
            "original_price": 100.0,
            "sale_price": 50.0,
            "expiration_date": datetime(2025, 5, 1),
            "image_url": "https://images.unsplash.com/photo-1567401893414-76b7b1e5a7a5?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://example-retail.com/deals/clothing-sale"
        },
        {
            "title": "Buy One Get One Free Pizza",
            "description": "Order any large pizza and get a second one free. Valid for dine-in only.",
            "discount_percentage": 50.0,
            "business_name": "Pizza Paradise",
            "category": "restaurant",
            "location": {
                "lat": 37.7739,
                "lng": -122.4312,
                "address": "456 Mission St, San Francisco, CA"
            },
            "original_price": 25.0,
            "sale_price": 12.5,
            "expiration_date": datetime(2025, 4, 15),
            "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://example-restaurant.com/deals/bogo-pizza"
        },
        {
            "title": "30% Off All Electronics",
            "description": "Save 30% on all electronics. Includes TVs, computers, and smartphones.",
            "discount_percentage": 30.0,
            "business_name": "Tech World",
            "category": "retail",
            "location": {
                "lat": 37.7833,
                "lng": -122.4167,
                "address": "789 Powell St, San Francisco, CA"
            },
            "original_price": 1000.0,
            "sale_price": 700.0,
            "expiration_date": datetime(2025, 4, 30),
            "image_url": "https://images.unsplash.com/photo-1498049794561-7780e7231661?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://example-retail.com/deals/electronics-sale"
        },
        {
            "title": "20% Off Entire Menu",
            "description": "Enjoy 20% off your entire order. Valid Monday through Thursday.",
            "discount_percentage": 20.0,
            "business_name": "Gourmet Grill",
            "category": "restaurant",
            "location": {
                "lat": 37.7694,
                "lng": -122.4862,
                "address": "101 California St, San Francisco, CA"
            },
            "original_price": 50.0,
            "sale_price": 40.0,
            "expiration_date": datetime(2025, 5, 15),
            "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://example-restaurant.com/deals/menu-discount"
        },
        {
            "title": "Buy 2 Get 1 Free Books",
            "description": "Purchase any two books and get a third book of equal or lesser value for free.",
            "discount_percentage": 33.3,
            "business_name": "Book Haven",
            "category": "retail",
            "location": {
                "lat": 37.7699,
                "lng": -122.4660,
                "address": "222 Valencia St, San Francisco, CA"
            },
            "original_price": 60.0,
            "sale_price": 40.0,
            "expiration_date": datetime(2025, 6, 1),
            "image_url": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://example-retail.com/deals/book-promotion"
        }
    ]
    
    # Clear existing sample deals
    await db.deals.delete_many({"business_name": {"$in": ["Fashion Outlet", "Pizza Paradise", "Tech World", "Gourmet Grill", "Book Haven"]}})
    
    # Insert sample deals
    for deal in sample_deals:
        deal_obj = Deal(**deal)
        await db.deals.insert_one(deal_obj.dict())
    
    return {"message": f"Generated {len(sample_deals)} sample deals"}

# API routes
@app.get("/api")
async def root():
    return {"message": "Welcome to the Real-Time Local Deal Finder API"}

@app.get("/api/deals")
async def get_deals(
    lat: float = Query(None, description="User's latitude"),
    lng: float = Query(None, description="User's longitude"),
    category: Optional[str] = Query(None, description="Filter by category (retail, restaurant)"),
    radius: float = Query(5.0, description="Search radius in miles, default 5 miles"),
    min_discount: float = Query(15.0, description="Minimum discount percentage")
):
    """
    Get deals filtered by location, category, and discount percentage
    """
    try:
        # Build query
        query = {"discount_percentage": {"$gte": min_discount}}
        
        if category:
            query["category"] = category
        
        # Get deals from database
        cursor = db.deals.find(query)
        deals = await cursor.to_list(length=100)
        
        # Filter by distance if location is provided
        if lat is not None and lng is not None:
            filtered_deals = []
            for deal in deals:
                deal_lat = deal["location"]["lat"]
                deal_lng = deal["location"]["lng"]
                distance = calculate_distance(lat, lng, deal_lat, deal_lng)
                
                if distance <= radius:
                    # Add distance to deal
                    deal["distance"] = round(distance, 2)
                    filtered_deals.append(deal)
            
            # Sort by distance
            filtered_deals.sort(key=lambda x: x["distance"])
            return filtered_deals
        
        return deals
    
    except Exception as e:
        logger.error(f"Error getting deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape-deals")
async def trigger_deal_scraping():
    """
    Trigger deal scraping from websites
    """
    result = await scrape_deals()
    return result

@app.post("/api/sample-deals")
async def create_sample_deals():
    """
    Generate sample deals for testing
    """
    result = await generate_sample_deals()
    return result

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
