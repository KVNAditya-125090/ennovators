import React, { useState, useEffect } from 'react';
import { Sparkles, ShoppingBag, ShieldCheck, UserCheck, ArrowRight, Gavel, Leaf, RefreshCw, Star, Lock } from 'lucide-react';
import { getProducts } from '../../services/paas';

export default function LandingPage({ onOpenSignIn }) {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    getProducts()
      .then(data => setProducts(data))
      .catch(err => console.warn('PaaS fetch error:', err));
  }, []);

  return (
    <div className="min-h-screen bg-google-gray-50 flex flex-col justify-between font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-google-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-google-teal to-google-blue flex items-center justify-center text-white shadow-sm">
                <Sparkles className="h-6 w-6" />
              </div>
              <div>
                <span className="font-bold text-xl text-google-gray-900 tracking-tight">AuraCommerce 360</span>
                <span className="ml-2 google-pill bg-google-teal-surface text-google-teal border border-google-teal-light/30">
                  Circular Retail Platform
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => onOpenSignIn()}
                className="google-btn-primary bg-gradient-to-r from-google-teal to-google-blue px-6 py-2 text-sm shadow-sm hover:opacity-95"
              >
                <Lock className="h-4 w-4" />
                <span>Sign In to Platform</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
        <div className="bg-gradient-to-r from-google-teal-dark via-google-teal to-google-blue rounded-3xl p-8 sm:p-12 text-white shadow-md relative overflow-hidden">
          <div className="max-w-3xl relative z-10 space-y-4">
            <span className="inline-block px-3.5 py-1 bg-white/20 rounded-full text-xs font-semibold backdrop-blur-xs">
              Google Cloud Serverless Architecture Reference Implementation
            </span>
            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
              Intelligent 360° Circular Commerce & Bidding Platform
            </h1>
            <p className="text-base sm:text-lg text-white/90 leading-relaxed">
              Unifying sourcing, inventory forecasting, multi-seller bidding, and AI-driven reverse logistics under one connected Google Cloud environment.
            </p>
            <div className="pt-4 flex flex-wrap gap-4">
              <button
                onClick={() => onOpenSignIn()}
                className="bg-white text-google-teal hover:bg-google-teal-surface font-bold px-7 py-3 rounded-full shadow-md transition-all flex items-center space-x-2 text-sm"
              >
                <span>Launch Demo & Sign In</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="google-card p-6 border-t-4 border-t-google-teal">
            <div className="p-3 bg-google-teal-surface text-google-teal rounded-xl w-fit mb-4">
              <Gavel className="h-6 w-6" />
            </div>
            <h3 className="font-bold text-lg text-google-gray-900 mb-2">Customer-to-Multi-Seller Bidding</h3>
            <p className="text-xs text-google-gray-600 leading-relaxed">
              Real-time Firestore auction protocol where eligible sellers submit competitive offers against customer requests in bounded time windows.
            </p>
          </div>

          <div className="google-card p-6 border-t-4 border-t-google-blue">
            <div className="p-3 bg-google-blue-light text-google-blue rounded-xl w-fit mb-4">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="font-bold text-lg text-google-gray-900 mb-2">Gemini Flash AI Assistant</h3>
            <p className="text-xs text-google-gray-600 leading-relaxed">
              Multi-modal conversational shopping, image-based return photo grading, and automated cradle-to-cradle reverse logistics routing.
            </p>
          </div>

          <div className="google-card p-6 border-t-4 border-t-google-green">
            <div className="p-3 bg-google-green-light text-google-green rounded-xl w-fit mb-4">
              <Leaf className="h-6 w-6" />
            </div>
            <h3 className="font-bold text-lg text-google-gray-900 mb-2">TimesFM & TabFM Intelligence</h3>
            <p className="text-xs text-google-gray-600 leading-relaxed">
              Zero-shot time series forecasting for inventory reorder points and tabular condition-grade value estimation running on quantized CPU containers.
            </p>
          </div>
        </div>

        {/* Product Showcase Section */}
        <div>
          <div className="flex justify-between items-end mb-6">
            <div>
              <span className="text-xs font-bold text-google-teal uppercase tracking-wider block mb-1">Featured Products</span>
              <h2 className="text-2xl font-bold text-google-gray-900">Explore Circular Products</h2>
            </div>
            <button
              onClick={() => onOpenSignIn()}
              className="text-xs font-semibold text-google-teal hover:underline flex items-center gap-1"
            >
              <span>Sign in to participate in live bids</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {products.map((product) => (
              <div key={product.id} className="google-card overflow-hidden flex flex-col justify-between group">
                <div>
                  <div className="relative">
                    <img src={product.image_url} alt={product.name} className="w-full h-48 object-cover group-hover:scale-105 transition-all duration-300" />
                    <span className="absolute top-3 right-3 google-pill bg-white/90 backdrop-blur-xs text-google-teal font-semibold">
                      {product.condition}
                    </span>
                  </div>

                  <div className="p-5">
                    <h3 className="font-bold text-google-gray-900 text-base mb-1">{product.name}</h3>
                    <div className="flex items-center gap-2 text-xs text-google-gray-600 mb-3">
                      <span className="flex items-center gap-1 text-google-yellow font-bold">
                        <Star className="h-3.5 w-3.5 fill-google-yellow" /> 4.9
                      </span>
                      <span>•</span>
                      <span className="text-google-green font-medium">{product.carbon_footprint_kg} kg CO2e saved</span>
                    </div>

                    <div className="flex items-baseline justify-between pt-3 border-t border-google-gray-100">
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

                <div className="p-5 pt-0">
                  <button
                    onClick={() => onOpenSignIn()}
                    className="w-full google-btn-primary text-xs py-2.5 bg-gradient-to-r from-google-teal to-google-blue"
                  >
                    <Lock className="h-3.5 w-3.5" />
                    <span>Sign In to Bid or Buy</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-google-gray-200 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center text-xs text-google-gray-600 gap-4">
          <div>
            <span className="font-bold text-google-teal">AuraCommerce 360</span> • GCP Circular Commerce Platform
          </div>
          <button
            onClick={() => onOpenSignIn()}
            className="text-xs font-semibold text-google-teal hover:underline"
          >
            Access Platform Dashboard →
          </button>
        </div>
      </footer>
    </div>
  );
}

