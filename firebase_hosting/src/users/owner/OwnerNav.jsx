import React, { useState, useEffect } from 'react';

// The Owner's navigation: one link for each section of the console
const ITEMS = [
  { key: 'dashboard', label: 'Dashboard', href: '#/dashboard' },
  { key: 'queries', label: 'Queries', href: '#/queries' },
  { key: 'consumers', label: 'Consumers', href: '#/consumers' },
  { key: 'monitor', label: 'Monitor', href: '#/monitor' },
  { key: 'telemetry', label: 'Telemetry', href: '#/telemetry' }
];

const useHash = () => {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onChange = () => setHash(window.location.hash);
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return hash;
};

export default function OwnerNav() {
  const hash = useHash();
  const [section = ''] = hash.replace(/^#\/?/, '').split('/');
  const current = section || 'dashboard';

  return (
    <nav className="flex w-full items-center gap-1" aria-label="Owner">
      {ITEMS.map((item) => {
        const active = current === item.key;
        return (
          <a
            key={item.key}
            href={item.href}
            aria-current={active ? 'page' : undefined}
            className={`flex-1 rounded-lg px-3 py-2 text-center text-sm font-semibold transition-colors ${active ? 'bg-google-blue-light text-google-blue-dark' : 'text-google-gray-700 hover:bg-google-gray-100'}`}
          >
            {item.label}
          </a>
        );
      })}
    </nav>
  );
}
