import React, { useState, useEffect } from 'react';
import { loadSession, saveSession, clearSession } from './services/maas/session';
import LandingPage from './users/customer/LandingPage';
import SignInModal from './services/maas/SignInModal';
import Navbar from './Navbar';
import { CONTAINER } from './layout';
import OwnerView from './users/owner/OwnerView';
import ConsumerView from './users/consumer/ConsumerView';
import { clearConsumerCache } from './users/consumer/api';
import CustomerView from './users/customer/CustomerView';
import { userBase, setBase, navigate, usePath } from './router';
import BiddingModal from './services/paas/BiddingModal';
import AiAssistantDrawer from './services/paas/AiAssistantDrawer';

// The first page of each kind of user; a Consumer's is chosen by the Root (see ConsumerNav)
const DEFAULT_PAGE = { owner: 'maas/dashboard', consumer: '', customer: 'paas/catalog' };
let pendingPath = '';
let legacyHash = '';

export default function App() {
  const [currentUser, setCurrentUser] = useState(loadSession); // restored after a reload
  const isAuthenticated = currentUser !== null;
  const activeRole = currentUser ? currentUser.role : 'Customer'; // set by the account: Owner, Consumer or Customer
  const [isSignInModalOpen, setIsSignInModalOpen] = useState(false);
  const [selectedProductForBid, setSelectedProductForBid] = useState(null);
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);
  const path = usePath();
  setBase(currentUser ? userBase(currentUser) : '');

  // Keep the address in the form /<user>/<role>/<service>/<category>/...
  // Signed out: the home page lives at /, and a page address opened then is kept for after sign-in.
  // Signed in: an address for another user type or role is moved into this person's own area.
  useEffect(() => {
    const now = window.location.pathname; // the live address (an earlier run may already have moved it)
    const parts = now.split('/').filter(Boolean);
    const hash = window.location.hash.startsWith('#/') ? window.location.hash.slice(2) : '';
    if (!currentUser) {
      if (hash) legacyHash = hash;
      if (parts.length) pendingPath = now;
      if (parts.length || window.location.hash) { window.history.replaceState(null, '', '/'); window.dispatchEvent(new Event('routechange')); }
      return;
    }
    const own = userBase(currentUser);
    const [type] = own.split('/').filter(Boolean);
    const legacy = hash || legacyHash;
    legacyHash = '';
    if (legacy) { // an old #/... address: open the same page at its new address
      navigate(`${own}/${type === 'owner' ? 'maas/' : ''}${legacy}`, { replace: true });
      return;
    }
    if (now.startsWith(`${own}/`) || (now === own && !DEFAULT_PAGE[type])) return;
    const rest = parts[0] === type ? parts.slice(2) : [];
    const start = rest.length ? rest.join('/') : DEFAULT_PAGE[type] || '';
    navigate(start ? `${own}/${start}` : own, { replace: true });
  }, [path, currentUser]);


  const handleSignInSuccess = (userProfile) => {
    clearConsumerCache();
    saveSession(userProfile);
    setCurrentUser(userProfile);
    setIsSignInModalOpen(false);
    // open the page asked for before signing in, if it belongs to this kind of user
    const wanted = pendingPath;
    pendingPath = '';
    const [type] = userBase(userProfile).split('/').filter(Boolean);
    const rest = wanted.split('/').filter(Boolean);
    if (rest[0] === type && rest.length > 2) navigate(`${userBase(userProfile)}/${rest.slice(2).join('/')}`, { replace: true });
  };

  const handleSignOut = () => {
    clearConsumerCache();
    clearSession();
    setCurrentUser(null);
    navigate('/', { replace: true });
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
        currentUser={currentUser}
        onSignOut={handleSignOut}
      />

      {/* The body is the only part that scrolls */}
      <main id="app-scroll" className="relative flex-1 min-h-0 overflow-y-auto overflow-x-hidden">
        <div className={`${CONTAINER} py-5 sm:py-6`}>
          {activeRole === 'Owner' && <OwnerView />}
          {activeRole === 'Consumer' && <ConsumerView tenant={currentUser?.tenant} isRoot={currentUser?.department === 'Root'} user={currentUser} />}
          {activeRole === 'Customer' && (
            <CustomerView
              onOpenBidding={(prod) => setSelectedProductForBid(prod)}
              onOpenAiAssistant={() => setIsAiDrawerOpen(true)}
            />
          )}
        </div>
        <footer className={`${CONTAINER} flex flex-wrap items-center justify-between gap-2 border-t border-google-gray-200 py-4 text-xs text-google-gray-500`}>
          <span><span className="font-semibold text-google-teal">AuraCommerce 360</span> · Circular Commerce Platform</span>
          <span>© {new Date().getFullYear()} AIONOS</span>
        </footer>
      </main>

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
