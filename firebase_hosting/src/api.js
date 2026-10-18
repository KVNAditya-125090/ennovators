// Where the API lives. In production it is the Cloud Run service, set at build time in VITE_API_BASE_URL
// (firebase_hosting/.env.production). When it is not set (local development), paths stay relative, so the
// Vite dev server proxies /api to the backend on port 8000.
const BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export const apiUrl = (path) => `${BASE}${path}`;
