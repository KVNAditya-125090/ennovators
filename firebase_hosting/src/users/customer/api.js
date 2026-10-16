// Customer - a shopper who uses a consumer's enabled services, within that consumer's brand.
import { request, postJson } from '../../services/http';
import { subscribe, useRevision } from '../../services/sync';
import { useState, useEffect } from 'react';

// The home-page storefront and query form (public, kept from the original portal)
export const getStorefront = () => request('/api/v1/customer/storefront');
export const sendQuery = (query) => postJson('/api/v1/customer/queries', query);

// The Customer-side endpoints this consumer has switched on for its customers, grouped by service, with the
// consumer's tenant id and brand. The shopper shops only within this consumer.
export const getEndpoints = (consumer = '') =>
  request(`/api/v1/customer/endpoints?tenant=${encodeURIComponent(consumer)}`);

// Calls one catalog endpoint through the gate. Reads send values in the query string, changes send JSON.
// A refusal throws an Error whose message is the reason, ready to show.
export async function callEndpoint(tenantId, endpoint, params = {}, user = {}) {
  const query = endpoint.method === 'GET' || endpoint.method === 'DELETE';
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ''));
  const qs = query && Object.keys(clean).length ? `?${new URLSearchParams(clean)}` : '';
  const res = await fetch(`/api${endpoint.path}${qs}`, {
    method: endpoint.method,
    headers: {
      'X-Tenant-Id': tenantId || '',
      ...(user.name ? { 'X-User-Name': encodeURIComponent(user.name) } : {}),
      ...(user.email ? { 'X-User-Email': encodeURIComponent(user.email) } : {}),
      ...(query ? {} : { 'Content-Type': 'application/json' })
    },
    body: query ? undefined : JSON.stringify(clean)
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body?.detail;
    throw new Error(detail?.message || (typeof detail === 'string' ? detail : `The request failed (${res.status}).`));
  }
  return body;
}

// The shopper's storefront, fetched once: the consumer's id and brand, and the endpoints they may use as {path: endpoint}.
let store = null;
export function loadStore() {
  if (!store) {
    store = getEndpoints()
      .then((data) => ({
        tenantId: data.tenant_id,
        consumer: data.consumer,
        services: data.services,
        endpoints: Object.fromEntries(Object.values(data.services).flat().map((e) => [e.path, e])),
        template: data.template ?? { published: false }
      }))
      .catch((err) => { store = null; throw err; });
  }
  return store;
}

// Forget what was fetched, so the next shopper gets fresh access
export function clearCustomerCache() { store = null; }

subscribe(clearCustomerCache); // the Owner switched something, or the consumer changed its storefront

// The store as a hook: loads it, and loads it again when access or the storefront changed. The result only changes
// when what the shopper may see actually changed, so screens do not flash on every check.
export function useStore(user) {
  const rev = useRevision();
  const [state, setState] = useState({ store: null, failed: false });
  useEffect(() => {
    let live = true;
    loadStore()
      .then((next) => { if (live) setState((cur) => (cur.store && same(cur.store, next) ? cur : { store: next, failed: false })); })
      .catch(() => { if (live) setState((cur) => (cur.store ? cur : { store: null, failed: true })); });
    return () => { live = false; };
  }, [user?.email, rev]);
  return state;
}

const same = (a, b) => JSON.stringify([a.tenantId, a.consumer, Object.keys(a.endpoints).sort(), a.template]) ===
  JSON.stringify([b.tenantId, b.consumer, Object.keys(b.endpoints).sort(), b.template]);
