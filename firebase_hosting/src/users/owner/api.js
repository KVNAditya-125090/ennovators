// Owner - the developer of the product: consumers, their APIs and what they cost
import { request, putJson, patchJson } from '../../services/http';

export const getOverview = () => request('/api/v1/owner/overview');
export const getConsumer = (tenantId) => request(`/api/v1/owner/consumers/${encodeURIComponent(tenantId)}`);
export const getAnalytics = (period) => request(`/api/v1/owner/analytics?period=${encodeURIComponent(period)}`);
export const getApis = () => request('/api/v1/owner/apis');
export const getTelemetry = (level) => request(`/api/v1/owner/telemetry?level=${encodeURIComponent(level)}`);
export const getQueries = () => request('/api/v1/owner/queries');
export const updateQuery = (queryId, status) => patchJson(`/api/v1/owner/queries/${encodeURIComponent(queryId)}`, { status });
export const getConsumerEndpoints = (tenantId, service) =>
  request(`/api/v1/owner/consumers/${encodeURIComponent(tenantId)}/services/${encodeURIComponent(service)}/endpoints`);
export const setEndpointEnabled = (tenantId, path, enabled) =>
  putJson(`/api/v1/owner/consumers/${encodeURIComponent(tenantId)}/endpoints`, { path, enabled });
export const setServiceEnabled = (tenantId, service, enabled) =>
  putJson(`/api/v1/owner/consumers/${encodeURIComponent(tenantId)}/services/${encodeURIComponent(service)}`, { enabled });
export const updateEndpointSettings = (tenantId, path, changes) =>
  patchJson(`/api/v1/owner/consumers/${encodeURIComponent(tenantId)}/endpoints/settings`, { path, ...changes });

// The Owner's own catalog features (owner-side endpoints). They run in preview until the backend is integrated.
export const getOwnerFeatures = () => request('/api/v1/owner/features');
export async function runOwnerFeature(endpoint, params = {}) {
  const read = endpoint.method === 'GET' || endpoint.method === 'DELETE';
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ''));
  const qs = read && Object.keys(clean).length ? `?${new URLSearchParams(clean)}` : '';
  try {
    return await request(`/api/v1/owner/features/run${endpoint.path}${qs}`, {
      method: endpoint.method,
      headers: read ? {} : { 'Content-Type': 'application/json' },
      body: read ? undefined : JSON.stringify(clean)
    });
  } catch (err) {
    throw new Error(err.status === 422 ? 'Some required details are missing or not valid.' : 'The request failed. Please try again.');
  }
}
