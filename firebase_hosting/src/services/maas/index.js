// MaaS - Management as a Service
import { request, postJson, putJson } from '../http';
import { saveToken } from './session';
import { apiUrl } from '../../api';

export const getHealth = () => request('/api/v1/maas/health');
export const getBudgetStatus = () => request('/api/v1/maas/budget-status');
export const getTenants = () => request('/api/v1/maas/tenants');
export const getUsers = () => request('/api/v1/maas/users');

// Single sign-in: resolves to the signed-in user, whose role decides the portal
export const login = (email, password) =>
  postJson('/api/v1/maas/auth/login', { email, password }).then((res) => {
    saveToken(res.session.access_token);
    return res.user;
  });

// The signed-in person's language and assistant modes
export const getPreferences = () => request('/api/v1/maas/auth/preferences');
export const savePreferences = (preferences) => putJson('/api/v1/maas/auth/preferences', preferences);

// Mails with a link (password reset, staff invite). In the demo they land in an in-app mailbox, not a real inbox.
// These calls are made before anyone is signed in, so they carry no token and a failure keeps the server's reason.
async function openCall(path, options) {
  const res = await fetch(apiUrl(path), options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const error = new Error(typeof data.detail === 'string' ? data.detail : `The request failed (${res.status}).`);
    error.status = res.status;
    throw error;
  }
  return data;
}
const post = (path, body) => openCall(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export const requestPasswordReset = (email) => post('/api/v1/maas/auth/password/forgot', { email });
export const resetPassword = (token, newPassword) => post('/api/v1/maas/auth/password/reset', { token, new_password: newPassword });
export const readInvite = (token) => openCall(`/api/v1/maas/auth/invite?token=${encodeURIComponent(token)}`);
export const acceptInvite = (token, name, password) => post('/api/v1/maas/auth/invite/accept', { token, name, password });
export const readMailbox = (email) => openCall(`/api/v1/maas/auth/mailbox?email=${encodeURIComponent(email)}`);
