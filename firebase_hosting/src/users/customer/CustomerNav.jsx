import React, { useEffect, useRef } from 'react';
import { useStore } from './api';
import { SERVICES, availablePages, useRoute } from './customerPages';
import { SERVICE_LOOK } from '../consumer/ui';
import { CONTAINER } from '../../layout';
import { go as goTo, restSegments } from '../../router';

// The Customer's navigation: a row of services (Shop, Delivery, Support, Account), then the pages of the current
// service. What shows is what the consumer has switched on for its customers. There are no roles.
const SLOT = 'min-w-0 grow-0 shrink-0 basis-[calc((100%-0.75rem)/4)]';

export default function CustomerNav({ user }) {
  const route = useRoute();
  const { store, failed } = useStore(user);
  const endpoints = store?.endpoints ?? (failed ? {} : null); // {path: endpoint}

  const go = (service, page, replace = false) => goTo(page ? `${service}/${page}` : service, { replace });

  // Land on the first available page; move anyone on a page or service they have nothing on to one they do.
  const landed = useRef(false);
  useEffect(() => {
    if (!endpoints) return;
    if (!landed.current) {
      landed.current = true;
      if (restSegments().length < 2) {
        const svc = SERVICES.find((s) => availablePages(s.key, endpoints).length > 0);
        if (svc) { go(svc.key, availablePages(svc.key, endpoints)[0].key, true); return; }
      }
    }
    const here = availablePages(route.service, endpoints);
    if (here.length > 0) {
      if (!route.page || !here.some((p) => p.key === route.page)) go(route.service, here[0].key, true);
      return;
    }
    const open = SERVICES.find((s) => availablePages(s.key, endpoints).length > 0);
    if (open) go(open.key, availablePages(open.key, endpoints)[0].key, true);
  }, [endpoints, route.service, route.page]); // eslint-disable-line react-hooks/exhaustive-deps

  const shown = SERVICES.filter((service) => !endpoints || availablePages(service.key, endpoints).length > 0);
  const pages = endpoints ? availablePages(route.service, endpoints) : [];
  const currentPage = (pages.find((p) => p.key === route.page) ?? pages[0])?.key;
  const look = SERVICE_LOOK[route.service];

  return (
    <nav aria-label="Customer">
      <div className={CONTAINER}>
        <div className="flex items-stretch justify-center gap-1">
          {shown.map((service) => {
            const active = route.service === service.key;
            const Icon = SERVICE_LOOK[service.key].icon;
            const first = endpoints ? availablePages(service.key, endpoints)[0]?.key ?? '' : '';
            return (
              <button key={service.key} onClick={() => go(service.key, first)} aria-current={active ? 'page' : undefined} aria-label={service.label} title={service.label}
                className={`${SLOT} relative flex h-11 items-center justify-center gap-2 px-2 text-sm font-medium transition-all ${active ? 'bg-gradient-to-t from-google-blue-light/70 to-transparent text-google-teal-dark' : 'text-google-gray-600 hover:bg-google-gray-50 hover:text-google-gray-900'}`}>
                <Icon className={`h-4 w-4 shrink-0 ${active ? SERVICE_LOOK[service.key].text : ''}`} />
                <span className="truncate">{service.label}</span>
                {active && <span className={`absolute inset-x-2 bottom-0 h-[3px] rounded-t ${SERVICE_LOOK[service.key].solid} animate-fade`} aria-hidden="true" />}
              </button>
            );
          })}
        </div>
      </div>

      {pages.length > 1 && (
        <div className="border-t border-google-gray-100 bg-gradient-to-r from-google-blue-light/50 via-white/40 to-google-green-light/50">
          <div className={CONTAINER}>
            <div className="flex justify-start gap-1 overflow-x-auto py-1.5 md:justify-center" role="list">
              {pages.map((p) => (
                <button key={p.key} role="listitem" onClick={() => go(route.service, p.key)} aria-current={currentPage === p.key ? 'page' : undefined}
                  className={`shrink-0 whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm transition-all ${currentPage === p.key ? 'bg-white font-semibold !text-google-teal-dark shadow-sm ring-1 ring-google-blue/25' : 'text-google-gray-600 hover:bg-white/80 hover:text-google-gray-900'}`}>
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
