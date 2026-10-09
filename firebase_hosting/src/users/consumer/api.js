// Consumer - consumes the services
import { request } from '../../services/http';

export const getDashboard = (sku, tenant) =>
  request(`/api/v1/consumer/dashboard?sku=${encodeURIComponent(sku)}&tenant=${encodeURIComponent(tenant || '')}`);

// The endpoints this workspace has opted into, by service
export const getEndpoints = (tenant, email = '') =>
  request(`/api/v1/consumer/endpoints?tenant=${encodeURIComponent(tenant || '')}&email=${encodeURIComponent(email)}`);

// Calls one catalog endpoint through the gate. Reads send the values in the query string, changes send them as JSON.
// A refusal throws an Error whose message is the reason, ready to show.
export async function callEndpoint(tenantId, endpoint, params = {}, user = {}) {
  const query = endpoint.method === 'GET' || endpoint.method === 'DELETE';
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ''));
  const qs = query && Object.keys(clean).length ? `?${new URLSearchParams(clean)}` : '';
  const res = await fetch(`/api${endpoint.path}${qs}`, {
    method: endpoint.method,
    headers: { 'X-Tenant-Id': tenantId || '', ...(user.name ? { 'X-User-Name': encodeURIComponent(user.name) } : {}), ...(user.email ? { 'X-User-Email': encodeURIComponent(user.email) } : {}), ...(query ? {} : { 'Content-Type': 'application/json' }) },
    body: query ? undefined : JSON.stringify(clean)
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body?.detail;
    throw new Error(detail?.message || (typeof detail === 'string' ? detail : `The request failed (${res.status}).`));
  }
  return body;
}

// What this person may use: the opted-into endpoints their role allows, as {path: endpoint}, and the pages their role shows.
// Fetched once per person and shared by the menu and the pages; cleared on sign-in and sign-out (clearConsumerCache).
let access = {};
function loadAccess(tenant, email = '') {
  const key = `${tenant || ''}|${email}`;
  if (!access[key]) {
    access[key] = getEndpoints(tenant, email)
      .then((data) => ({ endpoints: Object.fromEntries(Object.values(data.services).flat().map((e) => [e.path, e])), view: data.view ?? null }))
      .catch((err) => { delete access[key]; throw err; });
  }
  return access[key];
}

export const loadOpted = (tenant, email = '') => loadAccess(tenant, email).then((a) => a.endpoints);

// The workspace id, the endpoints and the role's view, fetched once. The menu and the command palette need them before any page loads.
let workspaces = {};
export function loadWorkspace(tenant, email = '') {
  const key = `${tenant || ''}|${email}`;
  if (!workspaces[key]) {
    workspaces[key] = Promise.all([getDashboard('SKU-WATCH-G3', tenant), loadAccess(tenant, email)])
      .then(([dashboard, a]) => ({ tenantId: dashboard.workspace?.tenant?.tenant_id, endpoints: a.endpoints, view: a.view }))
      .catch((err) => { delete workspaces[key]; throw err; });
  }
  return workspaces[key];
}

// Forget what was fetched, so the next person (or the same person after a change) gets fresh access
export function clearConsumerCache() {
  access = {};
  workspaces = {};
}
