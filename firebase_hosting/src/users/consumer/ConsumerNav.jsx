import React, { useState, useEffect, useRef } from 'react';
import { loadWorkspace } from './api';
import { SERVICES, availablePages, useRoute } from './consumerPages';
import { SERVICE_LOOK } from './ui';
import { CONTAINER } from '../../layout';
import { go as goTo, restSegments } from '../../router';
import { useViewState, activeView, setView } from './consumerViews';
import CommandPalette from './CommandPalette';

// The Consumer's navigation: a row of services, then a row with the pages of the current service.
// What shows is what this person's role allows (permissions) narrowed to the pages the Root chose for that role (Customization).
// Search: Ctrl+K.
// Each service takes a quarter of the row, as if all four were bought, and the row is centred:
// a workspace (or role) with fewer services keeps the same tab size instead of one stretched tab
const SLOT = 'min-w-0 grow-0 shrink-0 basis-[calc((100%-0.75rem)/4)]';
// The tab label shortens with the screen: MaaS on a phone, Management on a tablet, the full name on a desktop
const SHORT = { maas: ['MaaS', 'Management'], paas: ['PaaS', 'Product'], taas: ['TaaS', 'Transport'], saas: ['SaaS', 'Support'] };
const TabLabel = ({ service }) => (
  <>
    <span className="truncate sm:hidden">{SHORT[service.key][0]}</span>
    <span className="hidden truncate sm:inline lg:hidden">{SHORT[service.key][1]}</span>
    <span className="hidden truncate lg:inline">{service.label}</span>
  </>
);

export default function ConsumerNav({ tenant, user, isRoot = true }) {
  const route = useRoute();
  const view = activeView(useViewState());
  const [opted, setOpted] = useState(null); // {path: endpoint}
  const [searching, setSearching] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    let live = true;
    setView(null);
    loadWorkspace(tenant, user?.email).then(({ endpoints, view: roleView }) => {
      if (!live) return;
      setView(isRoot ? null : roleView);
      setOpted(endpoints);
    }).catch(() => { if (live) setOpted({}); });
    return () => { live = false; };
  }, [tenant, user?.email, isRoot]);

  useEffect(() => {
    const onKey = (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setSearching((s) => !s); } };
    const onOpen = () => setSearching(true);
    window.addEventListener('keydown', onKey);
    window.addEventListener('open-palette', onOpen);
    return () => { window.removeEventListener('keydown', onKey); window.removeEventListener('open-palette', onOpen); };
  }, []);

  const can = (path) => Boolean(opted && opted[path]);
  const go = (service, page, replace = false) => goTo(page ? `${service}/${page}` : service, { replace });

  // Right after sign-in, open the first page the Root chose for this role. After that, anyone on a service they
  // have nothing on (or that their role hides) is sent to the first page they do have.
  const landed = useRef(false);
  useEffect(() => {
    if (!opted) return;
    if (!landed.current) {
      landed.current = true;
      const [svc, page] = (view?.landing || '').split('/');
      if (restSegments().length === 0 && svc && availablePages(svc, can, view).some((p) => p.key === page)) { go(svc, page, true); return; }
    }
    const here = availablePages(route.service, can, view);
    if (here.length > 0) {
      // a page this person may not see, in a service they do have: show the address of the page they get
      if (!route.page || !here.some((p) => p.key === route.page)) go(route.service, here[0].key, true);
      return;
    }
    const open = SERVICES.find((s) => availablePages(s.key, can, view).length > 0);
    if (open) go(open.key, availablePages(open.key, can, view)[0].key, true);
  }, [opted, view, route.service, route.page]); // eslint-disable-line react-hooks/exhaustive-deps

  const shown = SERVICES.filter((service) => !opted || availablePages(service.key, can, view).length > 0);
  const pages = opted ? availablePages(route.service, can, view) : [];
  const currentPage = (pages.find((p) => p.key === route.page) ?? pages[0])?.key;
  const look = SERVICE_LOOK[route.service];

  return (
    <nav ref={ref} aria-label="Consumer">
      {/* Services: each a quarter of the row, centred */}
      <div className={CONTAINER}>
        <div className="flex items-stretch justify-center gap-1">
          {shown.map((service) => {
            const active = route.service === service.key;
            const Icon = SERVICE_LOOK[service.key].icon;
            const first = opted ? availablePages(service.key, can, view)[0]?.key ?? '' : '';
            return (
              <button key={service.key} onClick={() => go(service.key, first)} aria-current={active ? 'page' : undefined} aria-label={service.label} title={service.label}
                className={`${SLOT} relative flex h-11 items-center justify-center gap-2 px-2 text-sm font-medium transition-colors ${active ? 'text-google-teal-dark' : 'text-google-gray-600 hover:text-google-gray-900'}`}>
                <Icon className={`h-4 w-4 shrink-0 ${active ? SERVICE_LOOK[service.key].text : ''}`} />
                <TabLabel service={service} />
                {active && <span className={`absolute inset-x-2 bottom-0 h-[3px] rounded-t ${SERVICE_LOOK[service.key].solid}`} aria-hidden="true" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* The pages of the current service */}
      {pages.length > 1 && (
        <div className="border-t border-google-gray-100 bg-google-gray-50/60">
          <div className={CONTAINER}>
            <div className="flex justify-start gap-1 overflow-x-auto py-1.5 md:justify-center" role="list">
              {pages.map((p) => (
                <button key={p.key} role="listitem" onClick={() => go(route.service, p.key)} aria-current={currentPage === p.key ? 'page' : undefined}
                  className={`shrink-0 whitespace-nowrap rounded-md px-3 py-1.5 text-sm transition-colors ${currentPage === p.key ? `${look.tint} font-medium !text-google-teal-dark` : 'text-google-gray-600 hover:bg-white hover:text-google-gray-900'}`}>
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {searching && opted && <CommandPalette opted={opted} view={view} onClose={() => setSearching(false)} />}
    </nav>
  );
}
