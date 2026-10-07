// Customer - utilizes the services via the consumer
import { request, postJson } from '../../services/http';

export const getStorefront = () => request('/api/v1/customer/storefront');
export const sendQuery = (query) => postJson('/api/v1/customer/queries', query);
