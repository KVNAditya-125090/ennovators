import React, { useMemo, useCallback } from 'react';
import { useStore, callEndpoint } from './api';
import { SERVICES, useRoute, pageEndpoints, isHandled, isVoice } from './customerPages';
import { SERVICE_LOOK, ToastProvider } from '../consumer/ui';
import FeaturePanels from './FeaturePanels';
import AccountPage from './AccountPage';
import CartPage from './CartPage';
import AssistantChat from './AssistantChat';
import Storefront from './Storefront';
import StoresMap from './StoresMap';

// What the Customer portal shows for the signed-in shopper: the consumer's brand, then the page in the address.
// Every feature the consumer switched on for customers is reachable here; features without a dedicated screen are
// shown inline (FeaturePanels): what only shows something is displayed in place, and what needs input unfolds into its form.
// Nothing is hidden behind an Open/View button or a pop-up. Calls go through the gate.
export default function CustomerView({ onOpenBidding, onOpenAiAssistant, user }) {
  const { service, page } = useRoute();
  const { store, failed } = useStore(user);

  const endpoints = store?.endpoints;
  const can = useCallback((path) => Boolean(endpoints && endpoints[path]), [endpoints]);
  const call = useCallback((path, params) => {
    if (!endpoints?.[path]) return Promise.reject(new Error('This feature is not available from this seller.'));
    return callEndpoint(store.tenantId, endpoints[path], params, user || {});
  }, [endpoints, store, user]);

  const pageInfo = useMemo(() => SERVICES.find((s) => s.key === service)?.pages.find((p) => p.key === page)
    ?? SERVICES.find((s) => s.key === service)?.pages[0], [service, page]);

  if (failed) return <div className="text-base text-google-red">Could not reach the store. Check that the platform is running and try again.</div>;
  if (!store || !pageInfo) return <div className="text-base text-google-gray-600">Loading the store...</div>;

  const look = SERVICE_LOOK[service];
  const Icon = look.icon;
  const serviceLabel = SERVICES.find((s) => s.key === service)?.label;
  const features = pageEndpoints(service, pageInfo.key, endpoints);
  const panels = features.filter((e) => !isHandled(service, pageInfo.key, e.path) && !isVoice(e.path));

  // The consumer's published storefront: its own name, colour, logo and banner. Customers never see the platform's.
  const tpl = store.template?.published ? store.template : null;
  const brand = tpl?.branding ?? {};
  const colour = brand.colour || '';
  const brandName = brand.brand_name || store.consumer;

  return (
    <ToastProvider>
      <div>
        {tpl && (
          <div className="google-card mb-5 overflow-hidden" data-storefront-version={tpl.version}>
            <div className="flex items-center gap-3 px-5 py-3">
              {brand.logo
                ? <img src={brand.logo} alt="" className="h-8 w-8 rounded-lg object-cover" />
                : <span className="flex h-8 w-8 items-center justify-center rounded-lg font-bold text-white" style={colour ? { background: colour } : undefined}>{brandName.charAt(0).toUpperCase()}</span>}
              <span className="text-lg font-bold text-google-gray-900">{brandName}</span>
            </div>
            {tpl.layout?.hero && (
              <div className="px-5 py-8 text-white" style={{ background: colour ? `linear-gradient(135deg, ${colour}, ${colour}CC)` : undefined }}>
                <div className="text-2xl font-extrabold">{brandName}</div>
                {brand.tagline && <div className="mt-1 text-base opacity-90">{brand.tagline}</div>}
              </div>
            )}
          </div>
        )}
        <div className="hero-strip mb-5 flex items-center gap-4 rounded-2xl px-5 py-4">
          <span className={`hidden h-12 w-12 shrink-0 items-center justify-center rounded-xl shadow-sm sm:flex ${look.tint}`}><Icon className="h-6 w-6" /></span>
          <div className="min-w-0">
            <div className="mb-0.5 flex items-center gap-1.5 text-xs font-medium text-google-gray-500">
              {serviceLabel}<span aria-hidden="true">›</span><span className="text-google-gray-700">{pageInfo.label}</span>
            </div>
            <h2 className="text-2xl font-semibold leading-tight tracking-tight text-google-teal-dark">{pageInfo.label}</h2>
            {pageInfo.subtitle && <p className="mt-0.5 text-sm text-google-gray-600">{pageInfo.subtitle}</p>}
          </div>
          <span className="ml-auto hidden shrink-0 rounded-full bg-white/80 px-3 py-1 text-xs text-google-gray-500 shadow-sm md:inline">Shopping with <span className="font-semibold text-google-teal" style={colour ? { color: colour } : undefined}>{brandName}</span></span>
        </div>

        {pageInfo.storefront && (
          <Storefront call={call} can={can} layout={tpl?.layout?.style || 'grid'} colour={colour} onOpenBidding={onOpenBidding} onOpenAiAssistant={onOpenAiAssistant} />
        )}

        {pageInfo.screen === 'account' && <AccountPage call={call} can={can} />}
        {pageInfo.screen === 'cart' && <CartPage call={call} can={can} />}
        {pageInfo.screen === 'stores' && <StoresMap call={call} can={can} />}
        {pageInfo.screen === 'assistant' && <AssistantChat service={service} call={call} can={can} />}

        <FeaturePanels
          key={`${service}/${pageInfo.key}`}
          features={panels}
          title={pageInfo.storefront || pageInfo.screen ? 'More you can do here' : undefined}
          call={call}
          can={can}
        />

        {features.length === 0 && !pageInfo.storefront && (
          <div className="text-base text-google-gray-600 py-6 text-center">This seller has not switched on any features here yet.</div>
        )}
      </div>
    </ToastProvider>
  );
}
