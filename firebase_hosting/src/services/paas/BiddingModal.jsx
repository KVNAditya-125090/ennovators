import React, { useState, useEffect } from 'react';
import { openBiddingRoom } from './index';
import { X, Gavel, CheckCircle, Clock, ShieldAlert, Sparkles, Trophy } from 'lucide-react';

export default function BiddingModal({ product, onClose }) {
  const [budget, setBudget] = useState(product?.current_bidding_floor || 180.00);
  const [auctionState, setAuctionState] = useState('IDLE'); // IDLE, RUNNING, COMPLETED
  const [biddingResult, setBiddingResult] = useState(null);

  const startBidding = async () => {
    setAuctionState('RUNNING');
    try {
      const res = await openBiddingRoom(product.id, budget);
      
      // Simulate 2.5 second live auction window
      setTimeout(() => {
        setBiddingResult(res);
        setAuctionState('COMPLETED');
      }, 2200);
    } catch (err) {
      console.warn('Bid error:', err);
      setAuctionState('IDLE');
    }
  };

  if (!product) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-google-gray-200 relative overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-start pb-4 border-b border-google-gray-200">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-google-teal-surface text-google-teal rounded-xl">
              <Gavel className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-bold text-lg text-google-gray-900">Customer-to-Multi-Seller Bidding</h3>
              <p className="text-xs text-google-gray-600">Protocol 7.2.1 • Bounded Real-time Auction</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-google-gray-400 hover:text-google-gray-700 rounded-full hover:bg-google-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="py-5 space-y-4">
          <div className="flex items-center space-x-4 bg-google-gray-50 p-3 rounded-xl border border-google-gray-200">
            <img src={product.image_url} alt={product.name} className="w-16 h-16 rounded-lg object-cover" />
            <div>
              <h4 className="font-bold text-google-gray-900 text-sm">{product.name}</h4>
              <p className="text-xs text-google-gray-600">List Price: ${product.retail_price} • Floor: ${product.current_bidding_floor}</p>
            </div>
          </div>

          {auctionState === 'IDLE' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-google-gray-700 mb-1">
                  Enter Your Maximum Budget Cap ($):
                </label>
                <input
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(parseFloat(e.target.value))}
                  className="w-full px-4 py-2.5 rounded-xl border border-google-gray-300 focus:ring-2 focus:ring-google-teal focus:border-google-teal outline-none font-semibold text-lg text-google-teal"
                />
              </div>

              <div className="p-3 bg-google-teal-surface/50 rounded-xl text-xs text-google-teal-dark border border-google-teal-light/40 flex items-start space-x-2">
                <Sparkles className="h-4 w-4 text-google-teal shrink-0 mt-0.5" />
                <span>
                  The Bidding Engine will open a live bidding room and invite eligible sellers (Retailer, Refurbishers & Outlets) to submit counter-offers.
                </span>
              </div>

              <button
                onClick={startBidding}
                className="w-full google-btn-primary py-3 text-sm bg-google-teal"
              >
                <Gavel className="h-4 w-4" />
                <span>Open Bidding Room Now</span>
              </button>
            </div>
          )}

          {auctionState === 'RUNNING' && (
            <div className="py-8 text-center space-y-4">
              <div className="inline-block p-4 bg-google-teal-surface rounded-full">
                <Gavel className="h-8 w-8 text-google-teal" />
              </div>
              <h4 className="font-bold text-google-gray-900">Broadcasting Auction Window...</h4>
              <p className="text-xs text-google-gray-600">Collecting live bids from 3 matched sellers within floor & ceiling guardrails...</p>
              <div className="w-48 mx-auto bg-google-gray-200 h-2 rounded-full overflow-hidden">
                <div className="bg-google-teal h-full animate-pulse rounded-full w-3/4"></div>
              </div>
            </div>
          )}

          {auctionState === 'COMPLETED' && biddingResult && (
            <div className="space-y-4 animate-fade-in">
              <div className="p-4 bg-google-green-light/60 border border-google-green rounded-xl">
                <div className="flex items-center space-x-2 text-google-green font-bold text-sm mb-2">
                  <Trophy className="h-5 w-5" />
                  <span>Winning Best-Fit Offer Awarded!</span>
                </div>
                <div className="flex justify-between items-baseline">
                  <div>
                    <div className="font-bold text-google-gray-900 text-lg">{biddingResult.winning_best_fit.seller_name}</div>
                    <div className="text-xs text-google-gray-600">{biddingResult.winning_best_fit.condition} • {biddingResult.winning_best_fit.delivery_days}-Day Delivery</div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-extrabold text-google-teal">${biddingResult.winning_best_fit.offer_price}</div>
                    <div className="text-xs text-google-green font-semibold">Saved ${(budget - biddingResult.winning_best_fit.offer_price).toFixed(2)}</div>
                  </div>
                </div>
              </div>

              <div className="text-xs font-semibold text-google-gray-700">All Competing Seller Offers:</div>
              <div className="space-y-2">
                {biddingResult.offers.map((offer, idx) => (
                  <div key={idx} className="p-3 border border-google-gray-200 rounded-lg flex justify-between items-center text-xs">
                    <div>
                      <span className="font-semibold text-google-gray-900">{offer.seller_name}</span>
                      <span className="text-google-gray-500 ml-2">({offer.condition})</span>
                    </div>
                    <div className="font-bold text-google-gray-800">${offer.offer_price}</div>
                  </div>
                ))}
              </div>

              <button
                onClick={onClose}
                className="w-full google-btn-primary py-2.5 text-sm bg-google-teal"
              >
                <CheckCircle className="h-4 w-4" />
                <span>Accept Winning Offer & Checkout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

