// Shared fetch helper. Paths are relative: Firebase Hosting rewrites /api/** to Cloud Run.
export async function request(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(`${path} failed with ${res.status}`);
  return res.json();
}

export const postJson = (path, body) =>
  request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
