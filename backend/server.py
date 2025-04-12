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
import re
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
async def scrape_deals(location_name=None, lat=None, lng=None, category=None):
    """
    Use Firecrawl API to scrape deals from local store websites based on location
    """
    try:
        if not location_name and (not lat or not lng):
            raise HTTPException(status_code=400, detail="Location name or coordinates required")
        
        logger.info(f"Scraping deals for location: {location_name} or coordinates: {lat}, {lng}, category: {category}")
        
        # Clear previous deals for this location to avoid duplicates
        location_query = {}
        if location_name:
            location_query = {"location.address": {"$regex": location_name, "$options": "i"}}
        
        await db.deals.delete_many(location_query)
        
        # Determine which stores to target based on location and category
        target_stores = await find_local_stores(location_name, lat, lng, category)
        
        if not target_stores:
            logger.warning(f"No stores found for location: {location_name} or coordinates: {lat}, {lng}")
            return {"message": "No local stores found for the specified location"}
        
        all_deals = []
        
        for store in target_stores:
            # Set up Firecrawl API request
            headers = {
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Customized payload for each store website
            store_selectors = {
                # Zudio/Tata Cliq selectors
                "tatacliq.com": {
                    "selector": ".product-card, .product-grid-item, .product-tile",
                    "properties": {
                        "title": ".product-name, .product-title, h2",
                        "description": ".product-description, .product-info",
                        "discount": ".discount-label, .discount-tag, span:contains(\"%\")",
                        "original_price": ".strike-price, .original-price, .old-price",
                        "sale_price": ".discount-price, .selling-price, .sale-price",
                        "image": "img@src"
                    }
                },
                # Levi's selectors
                "levi.in": {
                    "selector": ".product-tile, .product-item, .product-card",
                    "properties": {
                        "title": ".product-name, .product-title",
                        "description": ".product-description, .product-details",
                        "discount": ".badge, .promo-badge, .discount-percentage",
                        "original_price": ".price-standard, .list-price, .original-price",
                        "sale_price": ".price-sales, .sale-price, .current-price",
                        "image": "img.product-image@src"
                    }
                },
                # H&M selectors
                "hm.com": {
                    "selector": ".product-item, .product-tile, li.product-detail",
                    "properties": {
                        "title": ".item-heading, .product-title, h3",
                        "description": ".product-description, .item-description",
                        "discount": ".item-price .sale, .discount-label, span:contains(\"%\")",
                        "original_price": ".price-regular, .original-price",
                        "sale_price": ".price-sale, .sale-price, .reduced-price",
                        "image": "img.item-image@src"
                    }
                },
                # Dominos selectors
                "dominos.co.in": {
                    "selector": ".offer-box, .coupon-box, .deal-item",
                    "properties": {
                        "title": ".offer-title, .coupon-title, h3",
                        "description": ".offer-description, .details",
                        "discount": ".discount-text, .deal-discount, span:contains(\"%\")",
                        "original_price": ".original-price, .strike-price",
                        "sale_price": ".offer-price, .deal-price",
                        "image": "img@src"
                    }
                },
                # Default selectors for any other store
                "default": {
                    "selector": "div.product, div.offer, div.promotion, div.deal, article.product, li.product",
                    "properties": {
                        "title": "h2, h3, .product-title, .offer-title, .title",
                        "description": ".description, .product-details, p, .offer-description",
                        "discount": ".discount, .sale-badge, .offer-percentage, span:contains(\"%\")",
                        "original_price": ".original-price, .regular-price, .old-price, del",
                        "sale_price": ".sale-price, .offer-price, .special-price, ins",
                        "image": "img@src"
                    }
                }
            }
            
            # Determine which selectors to use based on the store's website URL
            store_domain = None
            for domain in store_selectors.keys():
                if domain in store["website"]:
                    store_domain = domain
                    break
            
            # Use default selectors if the domain doesn't match any known ones
            if not store_domain or store_domain == "default":
                store_domain = "default"
            
            # Build the payload with the appropriate selectors
            payload = {
                "url": store["website"],
                "wait_for": "domcontentloaded",
                "extract_rules": {
                    "deals": {
                        "selector": store_selectors[store_domain]["selector"],
                        "type": "list",
                        "properties": store_selectors[store_domain]["properties"]
                    }
                }
            }
            
            logger.info(f"Sending request to Firecrawl API for store: {store['name']}, URL: {store['website']}")
            
            # Call the Firecrawl API
            try:
                response = requests.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    store_deals = data.get("deals", [])
                    if not store_deals and "extract_rules" in data:
                        # Try alternate format where extract_rules is returned
                        store_deals = data.get("extract_rules", {}).get("deals", [])
                    
                    if store_deals:
                        logger.info(f"Found {len(store_deals)} potential deals for {store['name']}")
                        
                        # Process and store each deal
                        for deal_data in store_deals:
                            try:
                                # Extract discount percentage
                                discount_text = deal_data.get("discount", "")
                                if not discount_text:
                                    # Try to calculate from original and sale prices
                                    original_price_text = deal_data.get("original_price", "").replace("$", "").replace("₹", "").replace("€", "").strip()
                                    sale_price_text = deal_data.get("sale_price", "").replace("$", "").replace("₹", "").replace("€", "").strip()
                                    
                                    if original_price_text and sale_price_text:
                                        try:
                                            original_price = float(original_price_text)
                                            sale_price = float(sale_price_text)
                                            if original_price > 0:
                                                discount_percentage = round(((original_price - sale_price) / original_price) * 100, 2)
                                            else:
                                                continue
                                        except (ValueError, TypeError):
                                            continue
                                    else:
                                        continue
                                else:
                                    # Extract percentage from text
                                    discount_match = re.search(r'(\d+)[%]', discount_text)
                                    if discount_match:
                                        discount_percentage = float(discount_match.group(1))
                                    else:
                                        try:
                                            discount_percentage = float(discount_text.strip("%"))
                                        except (ValueError, TypeError):
                                            continue
                                
                                # Skip deals with less than 15% discount
                                if discount_percentage < 15:
                                    continue
                                
                                # Format prices
                                original_price_text = deal_data.get("original_price", "").replace("$", "").replace("₹", "").replace("€", "").strip()
                                sale_price_text = deal_data.get("sale_price", "").replace("$", "").replace("₹", "").replace("€", "").strip()
                                
                                try:
                                    original_price = float(original_price_text) if original_price_text else None
                                    sale_price = float(sale_price_text) if sale_price_text else None
                                except (ValueError, TypeError):
                                    original_price = None
                                    sale_price = None
                                
                                # Create the deal object
                                deal = Deal(
                                    title=deal_data.get("title", "Unknown Deal").strip(),
                                    description=deal_data.get("description", "").strip(),
                                    discount_percentage=discount_percentage,
                                    business_name=store["name"],
                                    category=store["category"],
                                    location=Location(
                                        lat=store["lat"],
                                        lng=store["lng"],
                                        address=store["address"]
                                    ),
                                    original_price=original_price,
                                    sale_price=sale_price,
                                    image_url=deal_data.get("image", ""),
                                    url=store["website"],
                                    expiration_date=None  # Usually not available from scraped data
                                )
                                
                                # Store in database
                                await db.deals.insert_one(deal.dict())
                                all_deals.append(deal)
                                
                            except Exception as e:
                                logger.error(f"Error processing deal from {store['name']}: {e}")
                    else:
                        logger.warning(f"No deals found for {store['name']}")
                else:
                    logger.error(f"Error from Firecrawl API for {store['name']}: {response.status_code} - {response.text}")
            
            except Exception as e:
                logger.error(f"Error scraping {store['name']}: {e}")
        
        return {"message": f"Scraped and processed {len(all_deals)} deals from {len(target_stores)} stores"}
    
    except Exception as e:
        logger.error(f"Error in scrape_deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def find_local_stores(location_name=None, lat=None, lng=None, category=None):
    """
    Find local stores based on location and category
    This would typically use an external API like Google Places, but for demonstration
    we'll use a simplified approach with some predefined stores
    """
    stores = []
    
    # Determine if we're looking for Bengaluru or San Francisco area
    is_bengaluru = False
    is_san_francisco = False
    
    if location_name:
        is_bengaluru = "bengaluru" in location_name.lower() or "bangalore" in location_name.lower() or "jayanagar" in location_name.lower()
        is_san_francisco = "san francisco" in location_name.lower() or "sf" in location_name.lower()
    elif lat and lng:
        # More precise coordinate-based detection for Bengaluru (Jayanagar area)
        is_bengaluru = 12.92 <= float(lat) <= 12.95 and 77.57 <= float(lng) <= 77.59
        # More precise coordinate-based detection for San Francisco
        is_san_francisco = 37.7 <= float(lat) <= 37.8 and -122.5 <= float(lng) <= -122.3
    
    # Define some stores for Bengaluru (Jayanagar)
    if is_bengaluru:
        bengaluru_stores = [
            {
                "name": "Zudio Jayanagar",
                "category": "retail",
                "address": "11th Main Rd, 2nd Block, Jayanagar, Bengaluru",
                "lat": 12.9399039,
                "lng": 77.5826382,
                "website": "https://www.tatacliq.com/zudio/c-msh1451/offers"
            },
            {
                "name": "Levi's Store Jayanagar",
                "category": "retail",
                "address": "30th Cross, Jayanagar 2nd Block, Bengaluru",
                "lat": 12.9385,
                "lng": 77.5832,
                "website": "https://www.levi.in/discount/sale"
            },
            {
                "name": "H&M Jayanagar",
                "category": "retail",
                "address": "Cool Joint Rd, Jayanagar 2nd Block, Bengaluru",
                "lat": 12.9410,
                "lng": 77.5815,
                "website": "https://www2.hm.com/en_in/sale.html"
            },
            {
                "name": "Dominos Pizza Jayanagar",
                "category": "restaurant",
                "address": "Brigade Rd, Jayanagar 2nd Block, Bengaluru",
                "lat": 12.9395,
                "lng": 77.5840,
                "website": "https://www.dominos.co.in/offers"
            }
        ]
        stores.extend(bengaluru_stores)
    
    # Define some stores for San Francisco
    if is_san_francisco:
        sf_stores = [
            {
                "name": "Gap Union Square",
                "category": "retail",
                "address": "123 Market St, San Francisco, CA",
                "lat": 37.7749,
                "lng": -122.4194,
                "website": "https://www.gap.com/browse/category.do?cid=1065504"
            },
            {
                "name": "Little Italy Restaurant",
                "category": "restaurant",
                "address": "456 Mission St, San Francisco, CA",
                "lat": 37.7739,
                "lng": -122.4312,
                "website": "https://littleitaly-sf.com/specials/"
            },
            {
                "name": "Best Buy SF",
                "category": "retail",
                "address": "789 Powell St, San Francisco, CA",
                "lat": 37.7833,
                "lng": -122.4167,
                "website": "https://www.bestbuy.com/site/electronics/top-deals/pcmcat1563299784494.c"
            },
            {
                "name": "Cheesecake Factory",
                "category": "restaurant",
                "address": "101 California St, San Francisco, CA",
                "lat": 37.7694,
                "lng": -122.4862,
                "website": "https://www.thecheesecakefactory.com/specials-and-promotions/"
            }
        ]
        stores.extend(sf_stores)
    
    # Filter by category if provided
    if category and category != "all":
        stores = [store for store in stores if store["category"] == category]
    
    return stores

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
            "business_name": "Gap Union Square",
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
            "url": "https://www.gap.com/browse/category.do?cid=1065504"
        },
        {
            "title": "Buy One Get One Free Pizza",
            "description": "Order any large pizza and get a second one free. Valid for dine-in only.",
            "discount_percentage": 50.0,
            "business_name": "Little Italy Restaurant",
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
            "url": "https://littleitaly-sf.com/specials/"
        },
        {
            "title": "30% Off All Electronics",
            "description": "Save 30% on all electronics. Includes TVs, computers, and smartphones.",
            "discount_percentage": 30.0,
            "business_name": "Best Buy SF",
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
            "url": "https://www.bestbuy.com/site/electronics/top-deals/pcmcat1563299784494.c"
        },
        {
            "title": "20% Off Entire Menu",
            "description": "Enjoy 20% off your entire order. Valid Monday through Thursday.",
            "discount_percentage": 20.0,
            "business_name": "Cheesecake Factory",
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
            "url": "https://www.thecheesecakefactory.com/specials-and-promotions/"
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
            "url": "https://www.barnesandnoble.com/b/books/_/N-1fZ29Z8q8"
        },
        
        # Bengaluru Deals (Jayanagar)
        {
            "title": "40% Off on All Clothing",
            "description": "Special sale on all clothing items. Limited time only!",
            "discount_percentage": 40.0,
            "business_name": "Zudio Jayanagar",
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
            "url": "https://www.tatacliq.com/zudio/c-msh1451/offers"
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
            "url": "https://www.zomato.com/bangalore/south-indian-restaurants-in-jayanagar"
        },
        {
            "title": "50% Off on Second Pair of Jeans",
            "description": "Buy one pair of jeans, get 50% off on the second one. All styles!",
            "discount_percentage": 50.0,
            "business_name": "Levi's Store Jayanagar",
            "category": "retail",
            "location": {
                "lat": 12.9410,
                "lng": 77.5815,
                "address": "Cool Joint Rd, Jayanagar 2nd Block, Bengaluru"
            },
            "original_price": 3999.0,
            "sale_price": 1999.0,
            "expiration_date": datetime(2025, 5, 5),
            "image_url": "https://images.unsplash.com/photo-1497935586047-9242eb4fc795?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://www.levi.in/discount/sale"
        },
        {
            "title": "20% Off on All Summer Collection",
            "description": "Special discount on the entire summer collection - tops, tees, and accessories included.",
            "discount_percentage": 20.0,
            "business_name": "H&M Jayanagar",
            "category": "retail",
            "location": {
                "lat": 12.9395,
                "lng": 77.5840,
                "address": "Brigade Rd, Jayanagar 2nd Block, Bengaluru"
            },
            "original_price": 1499.0,
            "sale_price": 1199.0,
            "expiration_date": datetime(2025, 4, 25),
            "image_url": "https://images.unsplash.com/photo-1550009158-9ebf69173e03?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60",
            "url": "https://www2.hm.com/en_in/sale.html"
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
            is_bengaluru = 12.92 <= float(lat) <= 12.95 and 77.57 <= float(lng) <= 77.59
            is_san_francisco = 37.7 <= float(lat) <= 37.8 and -122.5 <= float(lng) <= -122.3
            
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
async def trigger_deal_scraping(
    location: str = Query(None, description="Name of the location"),
    lat: float = Query(None, description="Latitude coordinate"),
    lng: float = Query(None, description="Longitude coordinate"),
    category: str = Query(None, description="Category of stores to scrape (retail, restaurant)")
):
    """
    Trigger deal scraping from websites based on location
    """
    result = await scrape_deals(location_name=location, lat=lat, lng=lng, category=category)
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
