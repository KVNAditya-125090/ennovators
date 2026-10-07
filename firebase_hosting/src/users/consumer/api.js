// Consumer - consumes the services
import { request } from '../../services/http';

export const getDashboard = (sku, tenant) =>
  request(`/api/v1/consumer/dashboard?sku=${encodeURIComponent(sku)}&tenant=${encodeURIComponent(tenant || '')}`);
