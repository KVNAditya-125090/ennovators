import { useRest } from '../../router';
import { useViewState, activeView } from './consumerViews';
import { FEATURE_PAGE, PAGE_FEATURES } from './featureCatalog';

// The pages inside each service. A page shows when the workspace has opted into at least one of its endpoints.
// A page shows when the person may use at least one of its endpoints: the ones its own screen needs, plus the
// catalog features shown on it as feature cards (featureCatalog.js). Pages with `subtitle` are made only of feature cards.
const BASE = [
  { key: 'maas', label: 'Management as a Service', pages: [
    { key: 'overview', label: 'Overview', needs: ['/maas/analytics/dashboard/read/v1', '/maas/root-account/read/v1'] },
    { key: 'billing', label: 'Billing and Cost', needs: ['/maas/billing/invoice/read/v1', '/maas/billing/usage/read/v1'] },
    { key: 'team', label: 'Roles and Team', needs: ['/maas/role/read/v1'] },
    { key: 'customize', label: 'Customization', needs: ['/maas/interface/template/read/v1'] },
    { key: 'services', label: 'Services and endpoints', needs: [], subtitle: 'What your workspace has bought, what your customers can use, opt-in requests, API keys and service identities' },
    { key: 'partners', label: 'Partners', needs: [], subtitle: 'Links with partner consumers, and what your customers may use through them' },
    { key: 'owner', label: 'Owner tickets', needs: [], subtitle: 'Questions and partner-link requests you raise with the platform owner' },
    { key: 'locations', label: 'Stores and locations', needs: [], subtitle: 'Your stores, for pickups, drop-offs and local delivery' },
    { key: 'data', label: 'Data and audit', needs: [], subtitle: 'Customers, records, the audit log and fraud review' },
    { key: 'impact', label: 'Impact', needs: [], subtitle: 'Environmental impact of your workspace, with baselines, sources and confidence' },
    { key: 'account', label: 'Account and sign-in', needs: [], subtitle: 'Sign-in, sessions, passwords and invites for the root and staff accounts' },
    { key: 'settings', label: 'Settings', needs: ['/maas/root-account/settings/read/v1'] }
  ] },
  { key: 'paas', label: 'Product as a Service', pages: [
    { key: 'products', label: 'Products and stock', needs: ['/paas/catalog/product/read/v1'] },
    { key: 'orders', label: 'Orders', needs: ['/paas/order/read/staff/v1'] },
    { key: 'forecast', label: 'Demand forecast', needs: ['/paas/forecast/demand/read/v1'] },
    { key: 'bidding', label: 'Bidding', needs: [], subtitle: 'Rules and guardrails for customer bids, AI decisions and human offers' },
    { key: 'pricing', label: 'Pricing and promotions', needs: [], subtitle: 'Dynamic pricing, coupons, bundles, customer segments, green credits and personalization' },
    { key: 'insights', label: 'Insights', needs: [], subtitle: 'Sales, customer behaviour, seller trust, fraud review, impact and the shopping assistant' }
  ] },
  { key: 'taas', label: 'Transport as a Service', pages: [
    { key: 'shipments', label: 'Shipments', needs: ['/taas/shipment/read/staff/v1'] },
    { key: 'returns', label: 'Return routes', needs: ['/saas/return/request/read/v1'] },
    { key: 'delivery', label: 'Delivery rules', needs: ['/taas/analytics/delivery/read/v1', '/taas/delivery/rules/set/v1'] },
    { key: 'insights', label: 'Insights', needs: ['/taas/insights/delivery/read/v1', '/taas/analytics/delivery/read/v1'] }
  ] },
  { key: 'saas', label: 'Support as a Service', pages: [
    { key: 'tickets', label: 'Tickets', needs: ['/saas/ticket/read/staff/v1'] },
    { key: 'returns', label: 'Returns and refunds', needs: ['/saas/return/request/read/v1'] },
    { key: 'aftersales', label: 'Repairs and recycling', needs: [], subtitle: 'Repairs, refurbishers, trade-ins and recycling handovers' }
  ] }
];

export const SERVICES = BASE.map((svc) => ({
  ...svc,
  pages: svc.pages.map((p) => ({ ...p, needs: [...p.needs, ...(PAGE_FEATURES[`${svc.key}/${p.key}`] ?? [])] }))
}));

// Which page each group of features lives on. The command palette uses this to jump from a feature to its screen.
const FEATURE_PAGES = [
  ['/maas/root-account/settings', 'maas', 'settings'], ['/maas/root-account', 'maas', 'overview'], ['/maas/analytics', 'maas', 'overview'],
  ['/maas/billing', 'maas', 'billing'], ['/maas/role', 'maas', 'team'], ['/maas/user', 'maas', 'team'], ['/maas/notification', 'maas', 'team'],
  ['/maas/interface', 'maas', 'customize'],
  ['/paas/catalog', 'paas', 'products'], ['/paas/inventory', 'paas', 'products'], ['/paas/order', 'paas', 'orders'], ['/paas/forecast', 'paas', 'forecast'],
  ['/taas/shipment', 'taas', 'shipments'], ['/taas/route/optimize', 'taas', 'shipments'], ['/taas/vehicle', 'taas', 'shipments'], ['/taas/delivery/eta', 'taas', 'shipments'], ['/taas/delivery/slot', 'taas', 'shipments'], ['/taas/explain', 'taas', 'shipments'], ['/taas/recommendation', 'taas', 'shipments'], ['/taas/reverse', 'taas', 'returns'], ['/taas/pickup', 'taas', 'returns'],
  ['/taas/delivery', 'taas', 'delivery'], ['/taas/locale', 'taas', 'delivery'],
  ['/taas/insights', 'taas', 'insights'], ['/taas/analytics', 'taas', 'insights'], ['/taas/impact', 'taas', 'insights'],
  ['/saas/ticket', 'saas', 'tickets'], ['/saas/return', 'saas', 'returns']
];

export function pageForPath(path) {
  if (FEATURE_PAGE[path]) { const [service, page] = FEATURE_PAGE[path].split('/'); return { service, page }; }
  const hit = FEATURE_PAGES.find(([prefix]) => path.startsWith(prefix));
  return hit ? { service: hit[1], page: hit[2] } : null;
}

export const pageId = (service, page) => `${service}/${page}`;

// The pages of one service this workspace may use. `can` says whether an endpoint is opted into.
// A role's view, when there is one, narrows it to the pages that role was given.
export const availablePages = (serviceKey, can, view = null) =>
  (SERVICES.find((s) => s.key === serviceKey)?.pages ?? [])
    .filter((p) => p.needs.some(can))
    .filter((p) => !view?.pages || view.pages.includes(pageId(serviceKey, p.key)));

// The same, for whoever is being previewed right now
export function useAllowedPages(serviceKey, can) {
  const view = activeView(useViewState());
  return availablePages(serviceKey, can, view);
}

// The address is /consumer/<role>/<service>/<page>[/<feature>], for example /consumer/root/saas/returns
// or /consumer/root/maas/roles/role/create (the feature is the endpoint's path without its service and version)
export function useRoute() {
  const [service = '', page = '', ...feature] = useRest();
  return { service: SERVICES.some((s) => s.key === service) ? service : SERVICES[0].key, page, feature: feature.join('/') };
}

// The address of one feature: its page, then the endpoint path without the service and version
export const featureRest = (service, page, endpointPath) =>
  [service, page, ...endpointPath.split('/').filter(Boolean).slice(1).filter((p, i, all) => !(i === all.length - 1 && /^v\d+$/.test(p)))].join('/');

// Which page of the service to show: the one in the address if it is available, otherwise the first
export function useCurrentPage(serviceKey, pages) {
  const route = useRoute();
  const wanted = route.service === serviceKey ? route.page : '';
  return (pages.find((p) => p.key === wanted) ?? pages[0])?.key;
}
