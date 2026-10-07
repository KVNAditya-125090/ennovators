import React, { useState, useEffect } from 'react';
import { getHealth } from './services/maas';
import { loadSession, saveSession, clearSession } from './services/maas/session';
import LandingPage from './users/customer/LandingPage';
import SignInModal from './services/maas/SignInModal';
import Navbar from './Navbar';
import OwnerView from './users/owner/OwnerView';
import ConsumerView from './users/consumer/ConsumerView';
import CustomerView from './users/customer/CustomerView';
import BiddingModal from './services/paas/BiddingModal';
import AiAssistantDrawer from './services/saas/AiAssistantDrawer';

export default function App() {
  const [currentUser, setCurrentUser] = useState(loadSession); // restored after a reload
  const isAuthenticated = currentUser !== null;
  const activeRole = currentUser ? currentUser.role : 'Customer'; // set by the account: Owner, Consumer or Customer
  const [isSignInModalOpen, setIsSignInModalOpen] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);
  const [selectedProductForBid, setSelectedProductForBid] = useState(null);
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);

  useEffect(() => {
    getHealth()
      .then(data => {
        if (data.status === 'Healthy') setApiConnected(true);
      })
      .catch(() => setApiConnected(false));
  }, []);

  const handleSignInSuccess = (userProfile) => {
    saveSession(userProfile);
    setCurrentUser(userProfile);
    setIsSignInModalOpen(false);
  };

  const handleSignOut = () => {
    clearSession();
    setCurrentUser(null);
    window.history.replaceState(null, '', window.location.pathname);
  };

  // If not authenticated, show public Product Landing Page
  if (!isAuthenticated) {
    return (
      <>
        <LandingPage onOpenSignIn={() => setIsSignInModalOpen(true)} />
        <SignInModal
          isOpen={isSignInModalOpen}
          onClose={() => setIsSignInModalOpen(false)}
          onSignInSuccess={handleSignInSuccess}
        />
      </>
    );
  }

  // Once signed in, render the interactive platform dashboard
  return (
    <div className="app-shell bg-google-gray-50 flex flex-col">
      <Navbar
        activeRole={activeRole}
        apiConnected={apiConnected}
        currentUser={currentUser}
        onSignOut={handleSignOut}
        onOpenAiAssistant={() => setIsAiDrawerOpen(true)}
      />

      {/* The body is the only part that scrolls */}
      <main id="app-scroll" className="relative flex-1 min-h-0 overflow-y-auto">
        <div className="w-full px-4 sm:px-8 lg:px-12 2xl:px-20 py-6">
          {activeRole === 'Owner' && <OwnerView />}
          {activeRole === 'Consumer' && <ConsumerView tenant={currentUser?.tenant} />}
          {activeRole === 'Customer' && (
            <CustomerView
              onOpenBidding={(prod) => setSelectedProductForBid(prod)}
              onOpenAiAssistant={() => setIsAiDrawerOpen(true)}
            />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="shrink-0 bg-white border-t border-google-gray-200 py-6">
        <div className="w-full px-4 sm:px-8 lg:px-12 2xl:px-20 flex flex-col sm:flex-row justify-between items-center text-xs text-google-gray-600 gap-4">
          <div>
            <span className="font-bold text-google-teal">AuraCommerce 360</span> • Circular Commerce Platform
          </div>
        </div>
      </footer>

      {/* Interactive Modals */}
      {selectedProductForBid && (
        <BiddingModal
          product={selectedProductForBid}
          onClose={() => setSelectedProductForBid(null)}
        />
      )}

      <AiAssistantDrawer
        isOpen={isAiDrawerOpen}
        onClose={() => setIsAiDrawerOpen(false)}
      />
    </div>
  );
}
