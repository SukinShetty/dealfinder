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
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from pathlib import Path
import json
from math import radians, sin, cos, sqrt, atan2
from bson import ObjectId
from fastapi.encoders import jsonable_encoder

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
        # San Francisco Deals
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
            "url": "https://www.google.com/search?q=Fashion+Outlet+clothing+sales+San+Francisco"
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
            "url": "https://www.google.com/search?q=Pizza+Paradise+buy+one+get+one+San+Francisco"
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
            "url": "https://www.google.com/search?q=Tech+World+electronics+sales+San+Francisco"
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
            "url": "https://www.google.com/search?q=Gourmet+Grill+menu+discount+San+Francisco"
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
            "url": "https://www.google.com/search?q=Book+Haven+free+book+promotion"
        },
        
        # Bengaluru Deals (Jayanagar)
        {
            "title": "40% Off on All Clothing",
            "description": "Special sale on all clothing items. Limited time only!",
            "discount_percentage": 40.0,
            "business_name": "Fashion Hub",
            "category": "retail",
            "location": {
                "lat": 12.9399039,
                "lng": 77.5826382,
                "address": "11th Main Rd, 2nd Block, Jayanagar, Bengaluru"
            },
            "original_price": 2000.0,
            "sale_price": 1200.0,
            "expiration_date": datetime(2025, 5, 10),
            "image_url": "https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://www.google.com/search?q=Fashion+Hub+clothing+discount+Jayanagar+Bengaluru"
        },
        {
            "title": "25% Off on Dosa Combos",
            "description": "Enjoy 25% off on all dosa combos. Valid for dine-in and takeaway.",
            "discount_percentage": 25.0,
            "business_name": "South Indian Delight",
            "category": "restaurant",
            "location": {
                "lat": 12.9385,
                "lng": 77.5832,
                "address": "30th Cross, Jayanagar 2nd Block, Bengaluru"
            },
            "original_price": 250.0,
            "sale_price": 187.5,
            "expiration_date": datetime(2025, 4, 20),
            "image_url": "https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://www.google.com/search?q=South+Indian+Delight+dosa+discount+Jayanagar+Bengaluru"
        },
        {
            "title": "50% Off on Second Coffee",
            "description": "Buy one coffee, get 50% off on the second one. Perfect for catch-ups!",
            "discount_percentage": 50.0,
            "business_name": "Coffee Culture",
            "category": "restaurant",
            "location": {
                "lat": 12.9410,
                "lng": 77.5815,
                "address": "Cool Joint Rd, Jayanagar 2nd Block, Bengaluru"
            },
            "original_price": 180.0,
            "sale_price": 90.0,
            "expiration_date": datetime(2025, 5, 5),
            "image_url": "https://images.unsplash.com/photo-1497935586047-9242eb4fc795?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://example-restaurant.com/deals/bengaluru-coffee"
        },
        {
            "title": "20% Off on All Electronics",
            "description": "Special discount on all electronics including smartphones, laptops and accessories.",
            "discount_percentage": 20.0,
            "business_name": "Gadget Zone",
            "category": "retail",
            "location": {
                "lat": 12.9395,
                "lng": 77.5840,
                "address": "Brigade Rd, Jayanagar 2nd Block, Bengaluru"
            },
            "original_price": 50000.0,
            "sale_price": 40000.0,
            "expiration_date": datetime(2025, 4, 25),
            "image_url": "https://images.unsplash.com/photo-1550009158-9ebf69173e03?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://example-retail.com/deals/bengaluru-electronics"
        }
    ]
    
    # Clear ALL existing deals first
    await db.deals.delete_many({})
    
    # Insert sample deals
    for deal in sample_deals:
        deal_obj = Deal(**deal)
        await db.deals.insert_one(deal_obj.dict())
    
    return {"message": f"Generated {len(sample_deals)} sample deals"}

# API routes
@app.get("/api")
async def root():
    return {"message": "Welcome to the Real-Time Local Deal Finder API"}

# Helper function to convert MongoDB documents to JSON-serializable objects
def serialize_deal(deal: Dict[str, Any]) -> Dict[str, Any]:
    if deal.get("_id"):
        deal["id"] = str(deal["_id"])
        del deal["_id"]
    
    # Convert any nested ObjectIds
    for key, value in deal.items():
        if isinstance(value, ObjectId):
            deal[key] = str(value)
        elif isinstance(value, dict):
            deal[key] = serialize_deal(value)
        elif isinstance(value, list):
            deal[key] = [serialize_deal(item) if isinstance(item, dict) else item for item in value]
    
    return deal

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
        
        # Convert documents to JSON-serializable objects
        serialized_deals = [serialize_deal(deal) for deal in deals]
        
        # Filter by distance if location is provided
        if lat is not None and lng is not None:
            filtered_deals = []
            # Determine city name from user request (this is a simplification)
            is_bengaluru = any(loc in str(lat) + str(lng) for loc in ["12.9", "77.5"])
            is_san_francisco = any(loc in str(lat) + str(lng) for loc in ["37.7", "-122"])
            
            for deal in serialized_deals:
                # Only include deals from the correct city
                if is_bengaluru and "Bengaluru" not in deal["location"]["address"]:
                    continue
                if is_san_francisco and "San Francisco" not in deal["location"]["address"]:
                    continue
                    
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
        
        return serialized_deals
    
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
