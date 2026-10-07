// Customer - utilizes the services via the consumer
import { request } from '../../services/http';

export const getStorefront = () => request('/api/v1/customer/storefront');
