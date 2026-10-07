// Consumer - consumes the services
import { request } from '../../services/http';

export const getDashboard = (sku) => request(`/api/v1/consumer/dashboard?sku=${sku}`);
