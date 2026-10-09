import React from 'react';
import { href, useRest } from '../../router';

// The Owner's navigation: one link for each section of the console, at /owner/<role>/maas/<section>
const ITEMS = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'queries', label: 'Queries' },
  { key: 'consumers', label: 'Consumers' },
  { key: 'operations', label: 'Operations' },
  { key: 'monitor', label: 'Monitor' },
  { key: 'telemetry', label: 'Telemetry' }
];

export default function OwnerNav() {
  const [, section = ''] = useRest();
  const current = section || 'dashboard';

  return (
    <nav className="grid w-full grid-cols-3 sm:flex sm:items-stretch sm:justify-center" aria-label="Owner">
      {ITEMS.map((item) => {
        const active = current === item.key;
        return (
          <a
            key={item.key}
            href={href(`maas/${item.key}`)}
            aria-current={active ? 'page' : undefined}
            className={`relative flex h-11 min-w-0 items-center justify-center truncate px-3 text-sm font-medium transition-colors sm:flex-1 sm:max-w-[12rem] ${active ? 'text-google-teal-dark' : 'text-google-gray-600 hover:text-google-gray-900'}`}
          >
            {item.label}
            {active && <span className="absolute inset-x-3 bottom-0 h-[3px] rounded-t bg-google-blue" aria-hidden="true" />}
          </a>
        );
      })}
    </nav>
  );
}
