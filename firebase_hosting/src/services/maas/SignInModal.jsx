import React, { useState } from 'react';
import { X, ShieldCheck, UserCheck, ShoppingBag, Sparkles, ArrowRight, Lock } from 'lucide-react';

export default function SignInModal({ isOpen, onClose, onSignInSuccess }) {
  const [selectedRole, setSelectedRole] = useState('Customer'); // Owner, Consumer, Customer

  if (!isOpen) return null;

  const handleSignIn = () => {
    const userProfiles = {
      Owner: { name: 'Aditya Kothapalli', email: 'admin@auracommerce.io', role: 'Owner' },
      Consumer: { name: 'Sarah Chen (GreenCycle)', email: 'seller@greencycle.com', role: 'Consumer' },
      Customer: { name: 'Marcus Vance', email: 'marcus.customer@gmail.com', role: 'Customer' }
    };

    onSignInSuccess(userProfiles[selectedRole]);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-google-gray-200 relative overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-start pb-4 border-b border-google-gray-200">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-google-teal to-google-blue flex items-center justify-center text-white shadow-sm">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-bold text-lg text-google-gray-900">Sign In to Platform</h3>
              <p className="text-xs text-google-gray-600">AuraCommerce 360 Authentication</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-google-gray-400 hover:text-google-gray-700 rounded-full hover:bg-google-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content & Role Selection */}
        <div className="py-6 space-y-4">
          <label className="block text-xs font-bold text-google-gray-700 uppercase tracking-wider">
            Select Your Role to Log In:
          </label>

          <div className="space-y-3">
            {/* Customer Role */}
            <div
              onClick={() => setSelectedRole('Customer')}
              className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-center justify-between ${
                selectedRole === 'Customer'
                  ? 'border-google-teal bg-google-teal-surface/50 shadow-xs'
                  : 'border-google-gray-200 hover:border-google-teal/40'
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className={`p-2.5 rounded-xl ${selectedRole === 'Customer' ? 'bg-google-teal text-white' : 'bg-google-gray-100 text-google-gray-700'}`}>
                  <ShoppingBag className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-google-gray-900">Customer / Shopper</h4>
                  <p className="text-xs text-google-gray-600">Multi-seller bidding, store catalog & AI chat</p>
                </div>
              </div>
              <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${selectedRole === 'Customer' ? 'border-google-teal bg-google-teal text-white' : 'border-google-gray-300'}`}>
                {selectedRole === 'Customer' && <div className="w-2 h-2 rounded-full bg-white"></div>}
              </div>
            </div>

            {/* Consumer Role */}
            <div
              onClick={() => setSelectedRole('Consumer')}
              className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-center justify-between ${
                selectedRole === 'Consumer'
                  ? 'border-google-teal bg-google-teal-surface/50 shadow-xs'
                  : 'border-google-gray-200 hover:border-google-teal/40'
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className={`p-2.5 rounded-xl ${selectedRole === 'Consumer' ? 'bg-google-teal text-white' : 'bg-google-gray-100 text-google-gray-700'}`}>
                  <UserCheck className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-google-gray-900">Consumer / Retail Seller</h4>
                  <p className="text-xs text-google-gray-600">Surplus auctions, TimesFM forecasting & TaaS</p>
                </div>
              </div>
              <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${selectedRole === 'Consumer' ? 'border-google-teal bg-google-teal text-white' : 'border-google-gray-300'}`}>
                {selectedRole === 'Consumer' && <div className="w-2 h-2 rounded-full bg-white"></div>}
              </div>
            </div>

            {/* Owner Role */}
            <div
              onClick={() => setSelectedRole('Owner')}
              className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-center justify-between ${
                selectedRole === 'Owner'
                  ? 'border-google-teal bg-google-teal-surface/50 shadow-xs'
                  : 'border-google-gray-200 hover:border-google-teal/40'
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className={`p-2.5 rounded-xl ${selectedRole === 'Owner' ? 'bg-google-teal text-white' : 'bg-google-gray-100 text-google-gray-700'}`}>
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-google-gray-900">Owner / SuperAdmin</h4>
                  <p className="text-xs text-google-gray-600">MaaS admin, tenant RBAC & $120 budget tracker</p>
                </div>
              </div>
              <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${selectedRole === 'Owner' ? 'border-google-teal bg-google-teal text-white' : 'border-google-gray-300'}`}>
                {selectedRole === 'Owner' && <div className="w-2 h-2 rounded-full bg-white"></div>}
              </div>
            </div>
          </div>

          <button
            onClick={handleSignIn}
            className="w-full google-btn-primary py-3 text-sm bg-gradient-to-r from-google-teal to-google-blue mt-4"
          >
            <Lock className="h-4 w-4" />
            <span>Authenticate & Access Platform</span>
          </button>
        </div>
      </div>
    </div>
  );
}

