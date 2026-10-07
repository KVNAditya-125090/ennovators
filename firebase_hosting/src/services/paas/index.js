// PaaS - Product as a Service
import { request } from '../http';

export const getProducts = () => request('/api/v1/paas/products');
export const getDemandForecast = (sku) => request(`/api/v1/paas/forecast/demand/${sku}`);
export const openBiddingRoom = (productId, maxBudget) =>
  request(`/api/v1/paas/bids/open?product_id=${productId}&max_budget=${maxBudget}`, { method: 'POST' });
