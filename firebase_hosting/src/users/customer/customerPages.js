import { useRest } from '../../router';

// The Customer portal mirrors the Consumer console: a row of services, then the pages of the current service.
// A page shows when the consumer has switched on at least one of its endpoints for customers.
// Each page owns a set of path prefixes; every available endpoint is shown on the first page that matches,
// so a feature appears in the interface as soon as it is in the catalog (no per-endpoint list to maintain).
export const SERVICES = [
  { key: 'paas', label: 'Shop', pages: [
    { key: 'shop', label: 'Shop', subtitle: 'Browse, search and discover products, passports and greener choices',
      storefront: true, prefixes: ['/paas/catalog', '/paas/passport', '/paas/store-stock', '/paas/environment',
        '/paas/recommendation', '/paas/explain', '/paas/pricing', '/paas/return-risk', '/paas/basket', '/paas/parts'] },
    { key: 'cart', label: 'Cart & orders', subtitle: 'Your cart, checkout, orders, invoices, reservations and wishlist', screen: 'cart',
      prefixes: ['/paas/order', '/paas/payment', '/paas/promotion', '/paas/wishlist', '/paas/reserve', '/paas/pickup'] },
    { key: 'bidding', label: 'Bidding', subtitle: 'Negotiate price with AI or the seller, compare multi-seller offers and surplus auctions',
      prefixes: ['/paas/bid', '/paas/auction'] },
    { key: 'rewards', label: 'Rewards & reviews', subtitle: 'Green credits, buy-back value, reviews and your personalization',
      prefixes: ['/paas/green-credits', '/paas/future-value', '/paas/feedback', '/paas/personalization'] },
    { key: 'stores', label: 'Stores', subtitle: 'Store locations, and the nearest store to you for pickup and drop-off', from: 'maas', screen: 'stores', prefixes: ['/maas/location'] },
    { key: 'assistant', label: 'Shopping assistant', subtitle: 'Ask about products, prices and bids', screen: 'assistant', prefixes: ['/paas/assistant'] }
  ] },
  { key: 'taas', label: 'Delivery', pages: [
    { key: 'delivery', label: 'Delivery & tracking', subtitle: 'Choose how it ships, track it, and see the carbon of each option',
      prefixes: ['/taas/delivery', '/taas/tracking', '/taas/carbon', '/taas/environment'] },
    { key: 'returns', label: 'Returns transport', subtitle: 'Request a pickup, or forward a return straight to the next buyer',
      prefixes: ['/taas/reverse', '/taas/peer-forward'] },
    { key: 'assistant', label: 'Delivery assistant', subtitle: 'Ask about delivery', screen: 'assistant', prefixes: ['/taas/assistant'] }
  ] },
  { key: 'saas', label: 'Support', pages: [
    { key: 'support', label: 'Tickets & disputes', subtitle: 'Raise and track queries, returns, repairs and trade-ins, and open a dispute',
      prefixes: ['/saas/ticket', '/saas/dispute'] },
    { key: 'returns', label: 'Returns & grading', subtitle: 'Start a guided return, submit photos and see the grade and value',
      prefixes: ['/saas/return', '/saas/grading', '/saas/dropoff'] },
    { key: 'aftersales', label: 'Repair, recycle & trade-in', subtitle: 'Request a repair, recycling or trade-in, and get reuse or recycling advice',
      prefixes: ['/saas/repair', '/saas/recycling', '/saas/trade-in', '/saas/recommendation'] },
    { key: 'scorecard', label: 'My impact', subtitle: 'Value recovered, waste diverted and carbon saved, and why a grade or route was chosen',
      prefixes: ['/saas/scorecard', '/saas/explain'] },
    { key: 'assistant', label: 'Support assistant', subtitle: 'Ask support a question', screen: 'assistant', prefixes: ['/saas/assistant'] }
  ] },
  { key: 'maas', label: 'Account', pages: [
    { key: 'account', label: 'My account', subtitle: 'Your profile, password, language and data', screen: 'account',
      prefixes: ['/maas/customer-account', '/maas/locale'] },
    { key: 'help', label: 'Account help', subtitle: 'Ask about your account and signing in', screen: 'assistant', prefixes: ['/maas/assistant'] }
  ] }
];

// Features that belong to signing in or to the platform, not to a signed-in shopper's pages. Registration, sign-in,
// sign-out, mail verification, session refresh and password reset happen on the sign-in screen and the Navbar; the
// payment gateway is called by checkout itself. They stay in the catalog and stay enforced by the gate, but are not shown here.
const HIDDEN = ['/maas/customer-account/register', '/maas/customer-account/login', '/maas/customer-account/logout',
  '/maas/customer-account/mail/verify', '/maas/customer-account/session', '/maas/customer-account/password/reset',
  '/paas/payment/gateway'];
export const isHidden = (path) => HIDDEN.some((p) => path.startsWith(p));
// Voice variants need a microphone; the chat screen uses the text endpoint, so these are not listed as forms.
export const isVoice = (path) => /\/assistant\//.test(path) && /speech/.test(path);

// Endpoints a page's own screen already covers, so they are not listed again as forms below it
const HANDLED = {
  'paas/shop': ['/paas/order/cart/add/v1', '/paas/wishlist/item/add/v1'],
  'paas/cart': ['/paas/order/cart/add/v1', '/paas/order/cart/remove/v1', '/paas/order/cart/read/v1', '/paas/order/checkout/place/v1',
    '/paas/order/read/customer/v1', '/paas/order/cancel/customer/v1', '/paas/promotion/coupon/apply/v1',
    '/paas/wishlist/item/add/v1', '/paas/wishlist/item/remove/v1', '/paas/wishlist/read/v1']
};
export const isHandled = (service, page, path) => {
  const info = SERVICES.find((s) => s.key === service)?.pages.find((p) => p.key === page);
  if (info?.screen === 'account') return true;
  if (info?.screen === 'assistant') return true;
  return (HANDLED[`${service}/${page}`] || []).includes(path);
};

// The endpoints of one page: every available endpoint whose path starts with one of the page's prefixes,
// and that no earlier page in the same service already claimed.
export function pageEndpoints(serviceKey, pageKey, endpoints) {
  const service = SERVICES.find((s) => s.key === serviceKey);
  if (!service) return [];
  const pool = (page) => Object.values(endpoints || {}).filter((e) => e.service.toLowerCase() === (page.from || serviceKey) && !isHidden(e.path));
  const taken = new Set();
  let mine = [];
  for (const page of service.pages) {
    const here = pool(page).filter((e) => page.prefixes.some((p) => e.path.startsWith(p)) && !taken.has(e.path));
    here.forEach((e) => taken.add(e.path));
    if (page.key === pageKey) mine = here;
  }
  return mine;
}

// The pages of a service that have at least one available endpoint
export function availablePages(serviceKey, endpoints) {
  return (SERVICES.find((s) => s.key === serviceKey)?.pages ?? [])
    .filter((p) => pageEndpoints(serviceKey, p.key, endpoints).some((e) => !isVoice(e.path)));
}

// The address is /customer/<type>/<service>/<page>, for example /customer/individual/paas/shop
export function useRoute() {
  const [service = '', page = ''] = useRest();
  const known = SERVICES.some((s) => s.key === service);
  return { service: known ? service : SERVICES[0].key, page };
}
