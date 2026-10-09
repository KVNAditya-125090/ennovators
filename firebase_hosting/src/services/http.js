import { loadSession } from './maas/session';

// Shared fetch helper. Paths are relative: Firebase Hosting rewrites /api/** to Cloud Run.
// Every call says who is signed in, so the API can check the caller (preview: no token yet).
export async function request(path, options = {}) {
  const email = loadSession()?.email;
  const headers = { ...(options.headers || {}), ...(email ? { 'X-User-Email': encodeURIComponent(email) } : {}) };
  const res = await fetch(path, { ...options, headers });
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
