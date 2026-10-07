// Owner - operates the services
import { request } from '../../services/http';

export const getOverview = () => request('/api/v1/owner/overview');
