// Shared fetch helper. Paths are relative: Firebase Hosting rewrites /api/** to Cloud Run.
export async function request(path, options) {
  const res = await fetch(path, options);
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
