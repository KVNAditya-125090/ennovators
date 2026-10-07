import React from 'react';
import { ShieldCheck, UserCheck, ShoppingBag, Server, Sparkles, LogOut, User } from 'lucide-react';

export default function Navbar({ activeRole, setActiveRole, apiConnected, currentUser, onSignOut, onOpenAiAssistant }) {
  return (
    <header className="bg-white border-b border-google-gray-200 sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-google-teal to-google-blue flex items-center justify-center text-white shadow-sm">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-google-gray-900 tracking-tight">AuraCommerce 360</span>
                <span className="google-pill bg-google-teal-surface text-google-teal border border-google-teal-light/30">
                  GCP Serverless
                </span>
              </div>
              <p className="text-xs text-google-gray-600 hidden sm:block">Intelligent End-to-End Circular Retail Platform</p>
            </div>
          </div>

          {/* Role Switcher */}
          <div className="flex items-center bg-google-gray-100 p-1 rounded-full border border-google-gray-200">
            <button
              onClick={() => setActiveRole('Owner')}
              className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                activeRole === 'Owner'
                  ? 'bg-google-teal text-white shadow-xs'
                  : 'text-google-gray-700 hover:text-google-gray-900'
              }`}
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Owner Portal</span>
            </button>

            <button
              onClick={() => setActiveRole('Consumer')}
              className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                activeRole === 'Consumer'
                  ? 'bg-google-teal text-white shadow-xs'
                  : 'text-google-gray-700 hover:text-google-gray-900'
              }`}
            >
              <UserCheck className="h-3.5 w-3.5" />
              <span>Consumer Portal</span>
            </button>

            <button
              onClick={() => setActiveRole('Customer')}
              className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                activeRole === 'Customer'
                  ? 'bg-google-teal text-white shadow-xs'
                  : 'text-google-gray-700 hover:text-google-gray-900'
              }`}
            >
              <ShoppingBag className="h-3.5 w-3.5" />
              <span>Customer Storefront</span>
            </button>
          </div>

          {/* Backend Status & Authenticated Profile / Sign Out */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenAiAssistant}
              className="google-btn-primary text-xs py-2 px-3 bg-gradient-to-r from-google-teal to-google-blue hover:opacity-95"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span className="hidden md:inline">Gemini Flash AI</span>
            </button>

            {currentUser && (
              <div className="flex items-center space-x-2 border-l border-google-gray-200 pl-3">
                <div className="flex items-center space-x-2 text-xs bg-google-gray-100 px-3 py-1.5 rounded-full border border-google-gray-200">
                  <User className="h-3.5 w-3.5 text-google-teal" />
                  <span className="font-semibold text-google-gray-900">{currentUser.name}</span>
                </div>

                <button
                  onClick={onSignOut}
                  title="Sign Out to Product Page"
                  className="p-2 text-google-gray-500 hover:text-google-red hover:bg-google-red-light/50 rounded-full transition-all"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
