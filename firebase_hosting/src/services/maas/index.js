// MaaS - Management as a Service
import { request } from '../http';

export const getHealth = () => request('/api/v1/maas/health');
export const getBudgetStatus = () => request('/api/v1/maas/budget-status');
export const getTenants = () => request('/api/v1/maas/tenants');
export const getUsers = () => request('/api/v1/maas/users');
