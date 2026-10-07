import React, { useState, useEffect } from 'react';
import { Package, TrendingUp, Truck, Gavel, RefreshCw, CheckCircle, ArrowRight, BarChart2 } from 'lucide-react';
import { getDashboard } from './api';

export default function ConsumerView() {
  const [products, setProducts] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [forecastSku, setForecastSku] = useState('SKU-WATCH-G3');
  const [forecastData, setForecastData] = useState(null);
  const [auctionMessage, setAuctionMessage] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const dashboard = await getDashboard(forecastSku);
      setProducts(dashboard.products);
      setShipments(dashboard.shipments);
      setForecastData(dashboard.forecast);
    } catch (err) {
      console.warn('API fetch error:', err);
    }
  };

  const triggerSurplusAuction = (productName) => {
    setAuctionMessage(`Surplus Auction Opened for ${productName}! Inviting certified buyers & refurbishers...`);
    setTimeout(() => setAuctionMessage(''), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="google-hero rounded-2xl p-6 text-white shadow-sm">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex gap-2 mb-2">
              <span className="px-3 py-1 bg-white/20 text-white rounded-full text-xs font-semibold backdrop-blur-xs">
                PaaS — Product as a Service
              </span>
              <span className="px-3 py-1 bg-white/20 text-white rounded-full text-xs font-semibold backdrop-blur-xs">
                TaaS — Transport as a Service
              </span>
            </div>
            <h1 className="text-2xl font-bold">Consumer Operations & Inventory Console</h1>
            <p className="text-sm text-white/90 mt-1 max-w-2xl">
              Consumes services to list, sell, buy products, monitor TimesFM zero-shot demand forecasts, open surplus auctions, and manage cradle-to-cradle transport logistics.
            </p>
          </div>
          <div className="bg-white/10 p-3 rounded-xl backdrop-blur-xs hidden md:block">
            <Package className="h-10 w-10 text-white" />
          </div>
        </div>
      </div>

      {auctionMessage && (
        <div className="p-4 bg-google-green-light border border-google-green text-google-gray-900 rounded-xl font-medium text-sm flex items-center justify-between animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-google-green" />
            <span>{auctionMessage}</span>
          </div>
          <span className="text-xs text-google-gray-600">Firestore Real-time Active</span>
        </div>
      )}

      {/* Grid: Inventory & Forecasting */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Product Catalog & Surplus Actions */}
        <div className="lg:col-span-2 google-card p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="font-bold text-lg text-google-gray-900 flex items-center gap-2">
                <Package className="h-5 w-5 text-google-teal" />
                <span>Product Listings & Surplus Auctions</span>
              </h3>
              <p className="text-xs text-google-gray-600">Managed SKUs across retail stores and refurbishers</p>
            </div>
            <span className="google-pill bg-google-teal-surface text-google-teal">Live Catalog</span>
          </div>

          <div className="space-y-3">
            {products.map((item) => (
              <div key={item.id} className="p-4 border border-google-gray-200 rounded-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:border-google-teal transition-all">
                <div className="flex items-center space-x-4">
                  <img src={item.image_url} alt={item.name} className="w-14 h-14 rounded-lg object-cover border border-google-gray-200" />
                  <div>
                    <h4 className="font-semibold text-google-gray-900 text-sm">{item.name}</h4>
                    <div className="flex items-center gap-2 text-xs text-google-gray-600 mt-0.5">
                      <span>{item.sku}</span>
                      <span>•</span>
                      <span className="text-google-teal font-medium">{item.condition}</span>
                    </div>
                    <div className="text-xs text-google-gray-500 mt-1">Stock: <span className="font-bold text-google-gray-900">{item.stock} units</span></div>
                  </div>
                </div>

                <div className="flex sm:flex-col items-end justify-between w-full sm:w-auto gap-2">
                  <div className="text-right">
                    <div className="text-xs text-google-gray-500">Retail: ${item.retail_price}</div>
                    <div className="text-sm font-bold text-google-teal">Floor: ${item.current_bidding_floor}</div>
                  </div>
                  <button
                    onClick={() => triggerSurplusAuction(item.name)}
                    className="google-btn-secondary py-1.5 px-3 text-xs bg-google-teal-surface hover:bg-google-teal hover:text-white"
                  >
                    <Gavel className="h-3.5 w-3.5" />
                    <span>Open Surplus Bid</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* TimesFM Forecasting Widget */}
        <div className="google-card p-6 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-lg text-google-gray-900 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-google-teal" />
                <span>TimesFM Forecast</span>
              </h3>
              <span className="google-pill bg-google-teal-surface text-google-teal">Quantized CPU</span>
            </div>
            <p className="text-xs text-google-gray-600 mb-4">
              Zero-shot time series AI model predicting regional demand surge to prevent stock-outs & overstock.
            </p>

            {forecastData && (
              <div className="bg-google-gray-50 p-4 rounded-xl border border-google-gray-200 space-y-3">
                <div className="flex justify-between text-xs text-google-gray-700">
                  <span>Target SKU:</span>
                  <span className="font-bold text-google-teal">{forecastData.sku}</span>
                </div>
                <div className="flex justify-between text-xs text-google-gray-700">
                  <span>Reorder Point:</span>
                  <span className="font-bold text-google-gray-900">{forecastData.recommended_reorder_point} units</span>
                </div>

                <div className="mt-3">
                  <div className="text-xs font-semibold text-google-gray-600 mb-2">14-Day Demand Trend</div>
                  <div className="h-24 flex items-end justify-between gap-1 pt-2 px-1 bg-white rounded-lg border border-google-gray-200">
                    {forecastData.daily_forecast?.slice(0, 10).map((day, idx) => (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
                        <div
                          className="w-full bg-google-teal rounded-t transition-all hover:bg-google-blue"
                          style={{ height: `${(day.predicted_demand / 60) * 100}%` }}
                        ></div>
                        <span className="text-[9px] text-google-gray-500">{day.date.slice(-2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-google-gray-200 text-xs text-google-gray-600 flex justify-between items-center">
            <span>Model: TimesFM 1.0</span>
            <span className="text-google-green font-semibold">Zero-shot Ready</span>
          </div>
        </div>
      </div>

      {/* TaaS Section: Reverse Logistics & Goods Movement */}
      <div className="google-card p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="font-bold text-lg text-google-gray-900 flex items-center gap-2">
              <Truck className="h-5 w-5 text-google-blue" />
              <span>Transport as a Service (TaaS) — Forward & Reverse Logistics</span>
            </h3>
            <p className="text-xs text-google-gray-600">Track movement of goods A to B, peer-to-peer forwarding, and refurbisher routes</p>
          </div>
          <span className="google-pill bg-google-blue-light text-google-blue-dark">Real-time Carrier Network</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {shipments.map((shp) => (
            <div key={shp.shipment_id} className="p-4 rounded-xl border border-google-gray-200 bg-google-gray-50 hover:bg-white transition-all">
              <div className="flex justify-between items-start mb-2">
                <span className="google-pill bg-white border border-google-gray-300 text-google-gray-800">
                  {shp.type}
                </span>
                <span className="text-xs font-semibold text-google-green">{shp.status}</span>
              </div>
              <div className="text-xs font-bold text-google-gray-900 mt-2">{shp.origin}</div>
              <div className="flex justify-center my-1">
                <ArrowRight className="h-4 w-4 text-google-gray-400" />
              </div>
              <div className="text-xs font-bold text-google-gray-900">{shp.destination}</div>
              <div className="mt-3 pt-3 border-t border-google-gray-200 text-xs flex justify-between text-google-gray-600">
                <span>CO2 Saved: <strong className="text-google-teal">{shp.co2_saved_kg} kg</strong></span>
                <span>ETA: {shp.eta}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

