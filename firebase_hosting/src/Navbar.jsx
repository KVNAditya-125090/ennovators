import React, { useState, useEffect, useRef } from 'react';
import OwnerNav from './users/owner/OwnerNav';
import ConsumerNav from './users/consumer/ConsumerNav';
import CustomerNav from './users/customer/CustomerNav';
import { Sparkles, LogOut, Search, ChevronDown, Settings } from 'lucide-react';
import { useSettings } from './settings/SettingsProvider';
import { CONTAINER } from './layout';
import { isRootUser } from './services/maas/session';

// The app header: the Google colour band, the product and workspace, search, and the account menu.
// Below it, the Owner and Consumer navigation.

export default function Navbar({ activeRole, currentUser, onSignOut }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);
  const { t, openSettings } = useSettings();

  // close the account menu on outside click or Escape
  useEffect(() => {
    if (!menuOpen) return undefined;
    const onDown = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false); };
    const onKey = (e) => { if (e.key === 'Escape') setMenuOpen(false); };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDown); document.removeEventListener('keydown', onKey); };
  }, [menuOpen]);

  const workspace = activeRole === 'Owner' ? 'Owner console' : activeRole === 'Consumer' ? currentUser?.tenant : 'Storefront';
  const roleLine = `${activeRole}${currentUser?.department ? ` · ${currentUser.department}` : ''}`;
  const initial = (currentUser?.name || '?').trim().charAt(0).toUpperCase();

  return (
    <header className="relative shrink-0 bg-white/85 backdrop-blur-md border-b border-google-gray-200/80 z-40 shadow-[0_1px_12px_rgba(66,133,244,.08)]">
      <div className="h-1 google-gradient gradient-pan" aria-hidden="true" />
      <div className={CONTAINER}>
        <div className="flex h-14 items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="h-8 w-8 shrink-0 rounded-xl google-gradient-diag flex items-center justify-center text-white shadow-sm transition-transform hover:rotate-6">
              <Sparkles className="h-4 w-4" />
            </div>
            <span className="whitespace-nowrap text-base font-semibold tracking-tight text-google-gray-900">Lakshmi</span>
            {workspace && (
              <>
                <span className="hidden h-5 w-px bg-google-gray-300 sm:block" aria-hidden="true" />
                <span className="hidden truncate text-sm font-medium text-google-teal-dark sm:block">{workspace}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            {activeRole === 'Consumer' && (
              <button onClick={() => window.dispatchEvent(new Event('open-palette'))} aria-label="Search pages and features"
                className="flex h-9 items-center gap-2 rounded-lg border border-google-gray-200 bg-google-gray-50 px-3 text-sm text-google-gray-500 hover:border-google-gray-300 hover:bg-white">
                <Search className="h-4 w-4" />
                <span className="hidden md:inline">{t('nav.search')}</span>
                <kbd className="hidden rounded border border-google-gray-200 bg-white px-1.5 text-[11px] text-google-gray-500 md:inline">Ctrl K</kbd>
              </button>
            )}
            {currentUser && (
              <div className="relative" ref={menuRef}>
                <button onClick={() => setMenuOpen((open) => !open)} aria-haspopup="menu" aria-expanded={menuOpen} aria-label="Account menu"
                  className="flex items-center gap-2 rounded-lg py-1 pl-1 pr-2 hover:bg-google-gray-100">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full google-btn-gradient text-sm font-semibold text-white shadow-sm">{initial}</span>
                  <span className="hidden text-left leading-tight lg:block">
                    <span className="block text-sm font-medium text-google-gray-900">{currentUser.name}</span>
                    <span className="block text-xs text-google-gray-500">{roleLine}</span>
                  </span>
                  <ChevronDown className="hidden h-4 w-4 text-google-gray-500 lg:block" />
                </button>
                {menuOpen && (
                  <div role="menu" className="animate-pop absolute right-0 mt-2 w-64 max-w-[calc(100vw-2rem)] z-50 rounded-xl border border-google-gray-200 bg-white py-1 shadow-lg">
                    <div className="border-b border-google-gray-100 px-4 py-3 leading-tight">
                      <div className="truncate text-sm font-semibold text-google-gray-900">{currentUser.name}</div>
                      <div className="truncate text-xs text-google-gray-500">{currentUser.email}</div>
                      <div className="mt-1 truncate text-xs font-medium text-google-teal">{roleLine}</div>
                    </div>
                    <button role="menuitem" onClick={() => { setMenuOpen(false); openSettings(); }}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm text-google-gray-800 hover:bg-google-gray-100">
                      <Settings className="h-4 w-4" /> {t('menu.settings')}
                    </button>
                    <button role="menuitem" onClick={() => { setMenuOpen(false); onSignOut(); }}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm text-google-gray-800 hover:bg-google-gray-100">
                      <LogOut className="h-4 w-4" /> {t('menu.sign_out')}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {(activeRole === 'Owner' || activeRole === 'Consumer' || activeRole === 'Customer') && (
        <div className="border-t border-google-gray-200/70">
          {activeRole === 'Owner' && <div className={CONTAINER}><OwnerNav /></div>}
          {activeRole === 'Consumer' && <ConsumerNav tenant={currentUser?.tenant} user={currentUser} isRoot={isRootUser(currentUser)} />}
          {activeRole === 'Customer' && <CustomerNav user={currentUser} />}
        </div>
      )}
    </header>
  );
}
