from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

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
    category: str  # retail, restaurant, etc.
    location: Location
    expiration_date: Optional[datetime] = None
    image_url: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
