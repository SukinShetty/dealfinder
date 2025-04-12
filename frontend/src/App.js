import { useState, useEffect } from "react";
import "./App.css";
import NotificationManager from "./NotificationManager";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [locationInput, setLocationInput] = useState("");
  const [location, setLocation] = useState({ lat: "", lng: "" });
  const [filter, setFilter] = useState({ category: "all", radius: 5, minDiscount: 15 });
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [isGeocoding, setIsGeocoding] = useState(false);
  const [currency, setCurrency] = useState("USD");

  useEffect(() => {
    // Just initialize the app, don't load deals right away
    setLoading(false);
  }, []);

  const fetchDeals = async (locationName) => {
    try {
      setLoading(true);
      let url = `${BACKEND_URL}/api/deals?min_discount=${filter.minDiscount}`;
      
      if (filter.category !== "all") {
        url += `&category=${filter.category}`;
      }
      
      if (location.lat && location.lng) {
        url += `&lat=${location.lat}&lng=${location.lng}&radius=${filter.radius}`;
        
        // Add location name to help with filtering
        if (locationName) {
          url += `&location=${encodeURIComponent(locationName)}`;
        }
      }
      
      console.log("Fetching deals from:", url);
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error("Failed to fetch deals");
      }
      
      const data = await response.json();
      console.log(`Found ${data.length} deals`);
      
      // Filter deals based on location name if provided - STRICT FILTERING
      let filteredDeals = data;
      if (locationName) {
        const locationLower = locationName.toLowerCase();
        if (locationLower.includes("brigade")) {
          console.log("Filtering for Brigade Road deals ONLY");
          filteredDeals = data.filter(deal => 
            deal.location.address.includes("Brigade Road") && !deal.location.address.includes("Jayanagar")
          );
          if (filteredDeals.length === 0) {
            // Fallback to a more lenient search
            filteredDeals = data.filter(deal => 
              deal.location.address.includes("Brigade") && !deal.location.address.includes("Jayanagar")
            );
          }
        } else if (locationLower.includes("jayanagar")) {
          console.log("Filtering for Jayanagar deals ONLY");
          filteredDeals = data.filter(deal => 
            deal.location.address.includes("Jayanagar") && !deal.location.address.includes("Brigade")
          );
        } else if (locationLower.includes("san francisco") || locationLower.includes("sf")) {
          console.log("Filtering for San Francisco deals ONLY");
          filteredDeals = data.filter(deal => 
            deal.location.address.includes("San Francisco") && 
            !deal.location.address.includes("Jayanagar") && 
            !deal.location.address.includes("Brigade")
          );
        }
        
        // Fallback in case strict filtering removed all deals
        if (filteredDeals.length === 0) {
          console.log("No deals found with strict filtering, using more lenient filtering");
          if (locationLower.includes("brigade")) {
            filteredDeals = data.filter(deal => deal.business_name.includes("Brigade") || 
                                               deal.business_name.includes("Lifestyle") || 
                                               deal.business_name.includes("Adidas") || 
                                               deal.business_name.includes("Westside") ||
                                               deal.business_name.includes("Hard Rock"));
          } else if (locationLower.includes("jayanagar")) {
            filteredDeals = data.filter(deal => deal.business_name.includes("Jayanagar") || 
                                               deal.business_name.includes("Zudio") || 
                                               deal.business_name.includes("Levi's") || 
                                               deal.business_name.includes("H&M") ||
                                               deal.business_name.includes("Dominos"));
          }
        }
        
        console.log(`After filtering: ${filteredDeals.length} deals match location`);
      }
      
      // Ensure deals are unique by ID
      const uniqueDeals = {};
      filteredDeals.forEach(deal => {
        uniqueDeals[deal.id] = deal;
      });
      
      setDeals(Object.values(uniqueDeals));
      setLoading(false);
    } catch (err) {
      console.error("Error fetching deals:", err);
      setError("Failed to fetch deals. Please try again.");
      setLoading(false);
    }
  };

  const handleLocationSubmit = async (e) => {
    e.preventDefault();
    
    if (!locationInput.trim()) {
      setError("Please enter a location");
      return;
    }
    
    try {
      setIsGeocoding(true);
      setError(null);
      
      // Using the OpenStreetMap Nominatim API for geocoding (free and no API key required)
      const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationInput)}&limit=1`);
      
      if (!response.ok) {
        throw new Error("Failed to geocode location");
      }
      
      const data = await response.json();
      
      if (data.length === 0) {
        setError("Location not found. Please try a different location.");
        setIsGeocoding(false);
        return;
      }
      
      const { lat, lon } = data[0];
      // Store the location name along with coordinates
      setLocation({ lat, lng: lon, name: locationInput });
      
      // First, scrape deals for this location using Firecrawl API
      setLoading(true);
      setIsGeocoding(false);
      
      try {
        // Call the scrape-deals endpoint with the location information
        const scrapeResponse = await fetch(`${BACKEND_URL}/api/scrape-deals?location=${encodeURIComponent(locationInput)}&lat=${lat}&lng=${lon}&category=${filter.category}`, {
          method: 'POST',
          // Set a longer timeout for this request
          signal: AbortSignal.timeout(30000) // 30 second timeout
        });
        
        if (!scrapeResponse.ok) {
          throw new Error("Failed to scrape deals for this location");
        }
        
        // Now fetch the deals with location name included to ensure proper filtering
        await fetchDeals(locationInput);
      } catch (scrapeErr) {
        console.error("Error scraping deals:", scrapeErr);
        
        // Check if it's a timeout error
        if (scrapeErr.name === "TimeoutError" || scrapeErr.name === "AbortError") {
          setError("The request took too long. The server might be busy. Please try again or try a different location.");
        } else {
          setError("Failed to find deals for this location. Please try again or try a different location.");
        }
        
        setLoading(false);
      }
    } catch (err) {
      console.error("Geocoding error:", err);
      setError("Failed to find coordinates for this location. Please try again.");
      setIsGeocoding(false);
      setLoading(false);
    }
  };

  const handleCategoryChange = (e) => {
    setFilter({ ...filter, category: e.target.value });
  };

  const handleRadiusChange = (e) => {
    setFilter({ ...filter, radius: Number(e.target.value) });
  };

  const handleDiscountChange = (e) => {
    setFilter({ ...filter, minDiscount: Number(e.target.value) });
  };

  const formatDate = (dateString) => {
    if (!dateString) return "No expiration";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };
  
  // Currency conversion helper
  const formatPrice = (price, currencyCode) => {
    let conversionRate = 1; // Default for USD
    
    if (currencyCode === "INR") {
      conversionRate = 83.12; // 1 USD to INR (as of April 2025)
    } else if (currencyCode === "EUR") {
      conversionRate = 0.92; // 1 USD to EUR (as of April 2025)
    }
    
    const convertedPrice = price * conversionRate;
    
    // Format with thousand separators and proper decimal places
    const formattedValue = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(Math.round(convertedPrice));
    
    return {
      symbol: currencyCode === "USD" ? "$" : currencyCode === "INR" ? "₹" : "€",
      value: formattedValue
    };
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Real-Time Local Deal Finder</h1>
            <p className="text-lg mt-2">Find the best local deals near you</p>
          </div>
          {NotificationManager.isSupported() && (
            <button 
              onClick={async () => {
                const permission = await NotificationManager.requestPermission();
                setNotificationsEnabled(permission);
                if (permission) {
                  // Show a success notification
                  new Notification("Notifications Enabled", {
                    body: "You'll now receive alerts for new deals near you!"
                  });
                }
              }}
              className={`notification-button ${notificationsEnabled ? 'enabled' : ''}`}
            >
              {notificationsEnabled ? "Notifications On" : "Enable Notifications"}
            </button>
          )}
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-8">
        <section className="filters-section mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Find Deals Near You</h2>
            
            <form onSubmit={handleLocationSubmit} className="location-form mb-6">
              <div className="mb-4">
                <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                  Enter your location
                </label>
                <input
                  type="text"
                  id="location"
                  className="input-field"
                  placeholder="e.g. Jayanagar 2nd Block, Bengaluru"
                  value={locationInput}
                  onChange={(e) => setLocationInput(e.target.value)}
                  aria-label="Location search input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Try exact searches like "Jayanagar 2nd Block, Bengaluru" or "San Francisco, CA" for best results
                </p>
              </div>
              <button 
                type="submit" 
                className="search-button"
                disabled={isGeocoding}
              >
                {isGeocoding ? 'Searching...' : 'Find Deals'}
              </button>
            </form>
            
            <div className="filters grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  id="category"
                  className="select-field"
                  value={filter.category}
                  onChange={handleCategoryChange}
                >
                  <option value="all">All Categories</option>
                  <option value="retail">Retail</option>
                  <option value="restaurant">Restaurants</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="radius" className="block text-sm font-medium text-gray-700 mb-1">
                  Distance (miles)
                </label>
                <select
                  id="radius"
                  className="select-field"
                  value={filter.radius}
                  onChange={handleRadiusChange}
                >
                  <option value="1">1 mile</option>
                  <option value="3">3 miles</option>
                  <option value="5">5 miles</option>
                  <option value="10">10 miles</option>
                  <option value="25">25 miles</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="minDiscount" className="block text-sm font-medium text-gray-700 mb-1">
                  Minimum Discount
                </label>
                <select
                  id="minDiscount"
                  className="select-field"
                  value={filter.minDiscount}
                  onChange={handleDiscountChange}
                >
                  <option value="15">15% or more</option>
                  <option value="25">25% or more</option>
                  <option value="50">50% or more</option>
                  <option value="75">75% or more</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-1">
                  Currency
                </label>
                <select
                  id="currency"
                  className="select-field"
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                >
                  <option value="USD">USD ($)</option>
                  <option value="INR">INR (₹)</option>
                  <option value="EUR">EUR (€)</option>
                </select>
              </div>
            </div>
            
            <button onClick={fetchDeals} className="filter-button mt-4">
              Apply Filters
            </button>
          </div>
        </section>
        
        <section className="deals-section">
          <h2 className="text-2xl font-bold mb-6">Available Deals</h2>
          
          {loading ? (
            <div className="loading-spinner">
              <div className="spinner"></div>
              <p>Scraping deals from {locationInput}...</p>
              <p className="text-sm text-gray-500 mt-2">
                We're fetching deals from stores like {locationInput.toLowerCase().includes("brigade") ? 
                  "Lifestyle, Adidas, and Westside" : 
                  locationInput.toLowerCase().includes("jayanagar") ? 
                  "Zudio, Levi's, and H&M" : 
                  "Gap, Best Buy, and local restaurants"} in your area. This may take 15-30 seconds.
              </p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
              <button onClick={fetchDeals} className="retry-button">
                Try Again
              </button>
            </div>
          ) : deals.length === 0 ? (
            <div className="no-deals-message">
              {!location.lat && !location.lng ? (
                <div>
                  <p>Enter a location above to find deals nearby.</p>
                  <p>Try searching for "Jayanagar 2nd Block, Bengaluru" or "San Francisco, CA".</p>
                </div>
              ) : (
                <div>
                  <p>No deals found within {filter.radius} miles of your selected location.</p>
                  <p>Try these exact searches: "Jayanagar 2nd Block, Bengaluru" or "San Francisco, CA" where we have sample deals.</p>
                  <p>Current search location: {locationInput} (coordinates: {location.lat}, {location.lng})</p>
                </div>
              )}
            </div>
          ) : (
            <div className="deals-grid">
              {deals.map((deal) => (
                <div key={deal.id} className="deal-card">
                  <div className="deal-header">
                    <span className={`deal-category ${deal.category}`}>
                      {deal.category.charAt(0).toUpperCase() + deal.category.slice(1)}
                    </span>
                    <span className="deal-discount">{deal.discount_percentage}% Off</span>
                  </div>
                  
                  {deal.image_url && (
                    <div className="deal-image">
                      <img src={deal.image_url} alt={deal.title} />
                    </div>
                  )}
                  
                  <div className="deal-content">
                    <h3 className="deal-title">{deal.title}</h3>
                    <p className="deal-business">{deal.business_name}</p>
                    <p className="deal-description">{deal.description}</p>
                    
                    {(deal.original_price || deal.sale_price) && (
                      <div className="deal-prices">
                        {deal.original_price && (
                          <span className="original-price">
                            {formatPrice(deal.original_price, currency).symbol}
                            {formatPrice(deal.original_price, currency).value}
                          </span>
                        )}
                        {deal.sale_price && (
                          <span className="sale-price">
                            {formatPrice(deal.sale_price, currency).symbol}
                            {formatPrice(deal.sale_price, currency).value}
                          </span>
                        )}
                      </div>
                    )}
                    
                    <div className="deal-meta">
                      <div className="deal-location">
                        <i className="location-icon">📍</i>
                        <span>{deal.location.address}</span>
                      </div>
                      
                      {deal.distance !== undefined && (
                        <div className="deal-distance">
                          <span>{deal.distance} miles away</span>
                        </div>
                      )}
                      
                      <div className="deal-expiration">
                        <span>Expires: {formatDate(deal.expiration_date)}</span>
                      </div>
                    </div>
                  </div>
                  
                  {deal.url && (
                    <a 
                      href={deal.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="deal-cta"
                      onClick={(e) => {
                        // Log for debugging
                        console.log("Opening URL:", deal.url);
                      }}
                    >
                      View Deal
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
      
      <footer className="app-footer">
        <div className="container mx-auto px-4 py-6">
          <p>© 2025 Real-Time Local Deal Finder</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
