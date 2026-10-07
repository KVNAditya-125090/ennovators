// Owner - the developer of the product: consumers, their APIs and what they cost
import { request, putJson, patchJson } from '../../services/http';

export const getOverview = () => request('/api/v1/owner/overview');
export const getConsumer = (tenantId) => request(`/api/v1/owner/consumers/${encodeURIComponent(tenantId)}`);
export const setApiEnabled = (tenantId, apiId, enabled) =>
  putJson(`/api/v1/owner/consumers/${encodeURIComponent(tenantId)}/apis/${encodeURIComponent(apiId)}`, { enabled });
export const getAnalytics = (period) => request(`/api/v1/owner/analytics?period=${encodeURIComponent(period)}`);
export const updateApiSettings = (tenantId, apiId, changes) =>
  patchJson(`/api/v1/owner/consumers/${encodeURIComponent(tenantId)}/apis/${encodeURIComponent(apiId)}/settings`, changes);
export const getApis = () => request('/api/v1/owner/apis');
export const getTelemetry = (level) => request(`/api/v1/owner/telemetry?level=${encodeURIComponent(level)}`);
export const getQueries = () => request('/api/v1/owner/queries');
export const updateQuery = (queryId, status) => patchJson(`/api/v1/owner/queries/${encodeURIComponent(queryId)}`, { status });
