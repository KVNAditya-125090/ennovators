import React, { useState, useEffect } from 'react';
import { getHealth } from './services/maas';
import LandingPage from './users/customer/LandingPage';
import SignInModal from './services/maas/SignInModal';
import Navbar from './Navbar';
import OwnerView from './users/owner/OwnerView';
import ConsumerView from './users/consumer/ConsumerView';
import CustomerView from './users/customer/CustomerView';
import BiddingModal from './services/paas/BiddingModal';
import AiAssistantDrawer from './services/saas/AiAssistantDrawer';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [activeRole, setActiveRole] = useState('Customer'); // Owner, Consumer, Customer
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
    setCurrentUser(userProfile);
    setActiveRole(userProfile.role);
    setIsAuthenticated(true);
    setIsSignInModalOpen(false);
  };

  const handleSignOut = () => {
    setIsAuthenticated(false);
    setCurrentUser(null);
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
    <div className="min-h-screen bg-google-gray-50 flex flex-col justify-between">
      <div>
        <Navbar
          activeRole={activeRole}
          setActiveRole={setActiveRole}
          apiConnected={apiConnected}
          currentUser={currentUser}
          onSignOut={handleSignOut}
          onOpenAiAssistant={() => setIsAiDrawerOpen(true)}
        />

        <main className="w-full px-4 sm:px-8 lg:px-12 2xl:px-20 py-6">
          {activeRole === 'Owner' && <OwnerView />}
          {activeRole === 'Consumer' && <ConsumerView />}
          {activeRole === 'Customer' && (
            <CustomerView
              onOpenBidding={(prod) => setSelectedProductForBid(prod)}
              onOpenAiAssistant={() => setIsAiDrawerOpen(true)}
            />
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-google-gray-200 py-6 mt-12">
        <div className="w-full px-4 sm:px-8 lg:px-12 2xl:px-20 flex flex-col sm:flex-row justify-between items-center text-xs text-google-gray-600 gap-4">
          <div>
            <span className="font-bold text-google-teal">AuraCommerce 360</span> • GCP Serverless Platform
          </div>
          <div className="flex space-x-4">
            <span>Firebase Hosting</span>
            <span>•</span>
            <span>Cloud Run</span>
            <span>•</span>
            <span>Vertex AI Gemini Flash</span>
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
