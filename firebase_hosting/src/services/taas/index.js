// TaaS - Transport as a Service
import { request } from '../http';

export const getShipments = () => request('/api/v1/taas/shipments');
