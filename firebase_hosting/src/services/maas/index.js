// MaaS - Management as a Service
import { request, postJson } from '../http';

export const getHealth = () => request('/api/v1/maas/health');
export const getBudgetStatus = () => request('/api/v1/maas/budget-status');
export const getTenants = () => request('/api/v1/maas/tenants');
export const getUsers = () => request('/api/v1/maas/users');

// Single sign-in: resolves to the signed-in user, whose role decides the portal
export const login = (email, password) =>
  postJson('/api/v1/maas/auth/login', { email, password }).then((res) => res.user);
