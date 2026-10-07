import React from 'react';
import OwnerNav from './users/owner/OwnerNav';
import { ShieldCheck, UserCheck, ShoppingBag, Server, Sparkles, LogOut, User } from 'lucide-react';

const PORTALS = {
  Owner: { label: 'Owner Portal', icon: ShieldCheck },
  Consumer: { label: 'Consumer Portal', icon: UserCheck },
  Customer: { label: 'Customer Storefront', icon: ShoppingBag }
};

export default function Navbar({ activeRole, apiConnected, currentUser, onSignOut, onOpenAiAssistant }) {
  return (
    <header className="relative shrink-0 bg-white border-b border-google-gray-200 z-40">
      <div className="w-full px-4 sm:px-8 lg:px-12 2xl:px-20">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl google-gradient-diag flex items-center justify-center text-white shadow-sm">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-google-gray-900 tracking-tight">AuraCommerce 360</span>
              </div>
              <p className="text-xs text-google-gray-600 hidden sm:block">Intelligent End-to-End Circular Retail Platform</p>
            </div>
          </div>

          {/* Portal for the signed-in account */}
          {activeRole !== 'Owner' && <div className="hidden md:flex items-center space-x-2 bg-google-teal-surface text-google-teal-dark border border-google-teal/20 px-4 py-1.5 rounded-full text-sm font-semibold">
            {(() => {
              const Icon = PORTALS[activeRole]?.icon || User;
              return <Icon className="h-4 w-4" />;
            })()}
            <span>{PORTALS[activeRole]?.label || 'Portal'}</span>
          </div>}

          {/* Backend Status & Authenticated Profile / Sign Out */}
          <div className="flex items-center space-x-3">
            {/* The Owner manages the platform and has no use for the shopping assistant */}
            {activeRole !== 'Owner' && (
              <button
                onClick={onOpenAiAssistant}
                className="google-btn-primary text-xs py-2 px-3 bg-google-teal hover:bg-google-teal-dark"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span className="hidden md:inline">AI Assistant</span>
              </button>
            )}

            {currentUser && (
              <div className={`flex items-center space-x-2 ${activeRole === 'Owner' ? '' : 'border-l border-google-gray-200 pl-3'}`}>
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

      {/* The Owner navigates the console from a row below the header */}
      {activeRole === 'Owner' && (
        <div className="border-t border-google-gray-200 bg-white">
          <div className="w-full px-4 sm:px-8 lg:px-12 2xl:px-20 py-1.5">
            <OwnerNav />
          </div>
        </div>
      )}
    </header>
  );
}
