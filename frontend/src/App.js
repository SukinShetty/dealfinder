import { useState, useEffect } from "react";
import "./App.css";
import NotificationManager from "./NotificationManager";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [location, setLocation] = useState({ lat: "", lng: "" });
  const [filter, setFilter] = useState({ category: "all", radius: 5, minDiscount: 15 });
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);

  useEffect(() => {
    // Generate sample deals only if there's no data in our database yet
    const initializeApp = async () => {
      try {
        // First, just try to fetch existing deals
        const response = await fetch(`${BACKEND_URL}/api/deals`);
        const data = await response.json();
        
        if (Array.isArray(data) && data.length > 0) {
          // We already have deals, just display them
          setDeals(data);
          setLoading(false);
        } else {
          // No deals found, generate sample data
          await fetch(`${BACKEND_URL}/api/sample-deals`, {
            method: 'POST',
          });
          fetchDeals();
        }
      } catch (err) {
        console.error("Failed to initialize app:", err);
        setError("Failed to load deals. Please try again.");
        setLoading(false);
      }
    };

    initializeApp();
  }, []);

  const fetchDeals = async () => {
    try {
      setLoading(true);
      let url = `${BACKEND_URL}/api/deals?min_discount=${filter.minDiscount}`;
      
      if (filter.category !== "all") {
        url += `&category=${filter.category}`;
      }
      
      if (location.lat && location.lng) {
        url += `&lat=${location.lat}&lng=${location.lng}&radius=${filter.radius}`;
      }
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error("Failed to fetch deals");
      }
      
      const data = await response.json();
      
      // Ensure deals are unique by ID
      const uniqueDeals = {};
      data.forEach(deal => {
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

  const handleLocationSubmit = (e) => {
    e.preventDefault();
    fetchDeals();
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

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold">Real-Time Local Deal Finder</h1>
          <p className="text-lg mt-2">Find the best local deals near you</p>
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-8">
        <section className="filters-section mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Find Deals Near You</h2>
            
            <form onSubmit={handleLocationSubmit} className="location-form mb-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label htmlFor="latitude" className="block text-sm font-medium text-gray-700 mb-1">
                    Latitude
                  </label>
                  <input
                    type="text"
                    id="latitude"
                    className="input-field"
                    placeholder="e.g. 37.7749"
                    value={location.lat}
                    onChange={(e) => setLocation({ ...location, lat: e.target.value })}
                  />
                </div>
                <div>
                  <label htmlFor="longitude" className="block text-sm font-medium text-gray-700 mb-1">
                    Longitude
                  </label>
                  <input
                    type="text"
                    id="longitude"
                    className="input-field"
                    placeholder="e.g. -122.4194"
                    value={location.lng}
                    onChange={(e) => setLocation({ ...location, lng: e.target.value })}
                  />
                </div>
              </div>
              <button type="submit" className="search-button">
                Find Deals
              </button>
            </form>
            
            <div className="filters grid grid-cols-1 md:grid-cols-3 gap-4">
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
              <p>Loading deals...</p>
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
              <p>No deals found matching your criteria.</p>
              <p>Try adjusting your filters or location.</p>
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
                          <span className="original-price">${deal.original_price.toFixed(2)}</span>
                        )}
                        {deal.sale_price && (
                          <span className="sale-price">${deal.sale_price.toFixed(2)}</span>
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
                    <a href={deal.url} target="_blank" rel="noopener noreferrer" className="deal-cta">
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
