import React, { useState, useEffect } from 'react';
import { ShoppingBag, Gavel, Sparkles, Leaf, RefreshCw, Star, ShieldCheck } from 'lucide-react';

export default function CustomerView({ onOpenBidding, onOpenAiAssistant }) {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetch('/api/v1/paas/products')
      .then(r => r.json())
      .then(data => setProducts(data))
      .catch(err => console.warn('PaaS fetch error:', err));
  }, []);

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-gradient-to-r from-google-teal via-google-blue to-google-teal-dark rounded-2xl p-6 text-white shadow-sm">
        <div className="flex justify-between items-start">
          <div>
            <span className="inline-block px-3 py-1 bg-white/20 text-white rounded-full text-xs font-semibold mb-2 backdrop-blur-xs">
              Customer Experience Storefront
            </span>
            <h1 className="text-2xl font-bold">Circular Shopping & Multi-Seller Bidding</h1>
            <p className="text-sm text-white/90 mt-1 max-w-2xl">
              Utilizes services via consumer sellers. Enjoy real-time competitive seller bidding, carbon impact ratings, and hassle-free AI return & trade-in triage.
            </p>
          </div>
          <div className="bg-white/10 p-3 rounded-xl backdrop-blur-xs hidden md:block">
            <ShoppingBag className="h-10 w-10 text-white" />
          </div>
        </div>
      </div>

      {/* Unique Feature Callout Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-google-gray-200 flex items-center space-x-3">
          <div className="p-2.5 bg-google-teal-surface text-google-teal rounded-lg">
            <Gavel className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-semibold text-sm text-google-gray-900">Multi-Seller Bidding Protocol</h4>
            <p className="text-xs text-google-gray-600">Sellers compete in real-time to offer you the lowest price</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-google-gray-200 flex items-center space-x-3">
          <div className="p-2.5 bg-google-green-light text-google-green rounded-lg">
            <Leaf className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-semibold text-sm text-google-gray-900">Carbon Impact Score</h4>
            <p className="text-xs text-google-gray-600">Know exact CO2 savings for new vs refurbished items</p>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-google-gray-200 flex items-center space-x-3">
          <div className="p-2.5 bg-google-blue-light text-google-blue rounded-lg">
            <RefreshCw className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-semibold text-sm text-google-gray-900">Future Value Buy-Back</h4>
            <p className="text-xs text-google-gray-600">Guaranteed buy-back value for trade-in anytime</p>
          </div>
        </div>
      </div>

      {/* Product Catalog Grid */}
      <div>
        <h2 className="text-xl font-bold text-google-gray-900 mb-4 flex items-center gap-2">
          <ShoppingBag className="h-5 w-5 text-google-teal" />
          <span>Available Products & Live Auctions</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {products.map((product) => (
            <div key={product.id} className="google-card overflow-hidden flex flex-col justify-between group">
              <div>
                <div className="relative">
                  <img src={product.image_url} alt={product.name} className="w-full h-48 object-cover group-hover:scale-105 transition-all duration-300" />
                  <span className="absolute top-3 right-3 google-pill bg-white/90 backdrop-blur-xs text-google-teal font-semibold shadow-xs">
                    {product.condition}
                  </span>
                </div>

                <div className="p-5">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-google-gray-900 text-base">{product.name}</h3>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-google-gray-600 mb-3">
                    <span className="flex items-center gap-1 text-google-yellow font-bold">
                      <Star className="h-3.5 w-3.5 fill-google-yellow" /> 4.9
                    </span>
                    <span>•</span>
                    <span className="text-google-green font-medium">{product.carbon_footprint_kg} kg CO2e saved</span>
                  </div>

                  <div className="flex items-baseline justify-between my-4 pt-3 border-t border-google-gray-100">
                    <div>
                      <span className="text-xs text-google-gray-500 block">List Price</span>
                      <span className="text-sm line-through text-google-gray-400">${product.retail_price}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-google-teal font-semibold block">Bidding Starts At</span>
                      <span className="text-xl font-extrabold text-google-teal">${product.current_bidding_floor}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-5 pt-0 space-y-2">
                <button
                  onClick={() => onOpenBidding(product)}
                  className="w-full google-btn-primary bg-gradient-to-r from-google-teal to-google-blue"
                >
                  <Gavel className="h-4 w-4" />
                  <span>Start Live Multi-Seller Bid</span>
                </button>

                <button
                  onClick={onOpenAiAssistant}
                  className="w-full google-btn-secondary text-xs py-2"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>AI Condition Triage / Trade-in</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

