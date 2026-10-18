import { authHeader } from './maas/session';
import { apiUrl } from '../api';

// Shared fetch helper. Paths start with /api; apiUrl() puts the Cloud Run address in front of them (see ../api.js).
// Every call carries the sign-in token, so the API knows who is calling and can check them.
export async function request(path, options = {}) {
  const headers = { ...(options.headers || {}), ...authHeader() };
  const res = await fetch(apiUrl(path), { ...options, headers });
  if (!res.ok) {
    const error = new Error(`${path} failed with ${res.status}`);
    error.status = res.status;
    throw error;
  }
  return res.json();
}

const sendJson = (method, path, body) =>
  request(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

export const postJson = (path, body) => sendJson('POST', path, body);
export const putJson = (path, body) => sendJson('PUT', path, body);
export const patchJson = (path, body) => sendJson('PATCH', path, body);
