import { useState, useEffect } from 'react';

// Keeps the three portals in step. The platform counts every change that can alter access or the interface
// (the Owner opting a consumer in or out, roles and permissions, the consumer's storefront template). Each portal
// asks for that count every few seconds, and again when the tab is shown, and reloads what it displays when it moved.
// Listeners registered with subscribe() run first, in order, so caches are cleared before screens read again.
const EVERY_MS = 4000;
let revision = null;
let timer = null;
const listeners = new Set();

async function poll() {
  try {
    const res = await fetch('/api/v1/sync/revision', { cache: 'no-store' });
    if (!res.ok) return;
    const { revision: next } = await res.json();
    const moved = revision !== null && next !== revision;
    revision = next;
    if (moved) listeners.forEach((fn) => fn(next));
  } catch { /* offline or restarting: try again on the next tick */ }
}

const onShow = () => { if (document.visibilityState === 'visible') poll(); };

function start() {
  if (timer) return;
  poll();
  timer = window.setInterval(() => { if (document.visibilityState === 'visible') poll(); }, EVERY_MS);
  document.addEventListener('visibilitychange', onShow);
  window.addEventListener('focus', onShow);
}

function stop() {
  if (!timer || listeners.size > 0) return;
  window.clearInterval(timer);
  timer = null;
  document.removeEventListener('visibilitychange', onShow);
  window.removeEventListener('focus', onShow);
}

// Runs fn whenever the platform's access or interface changed. Returns a function that stops listening.
export function subscribe(fn) {
  listeners.add(fn);
  start();
  return () => { listeners.delete(fn); stop(); };
}

// A number that goes up each time something changed: put it in an effect's dependencies to reload on change.
export function useRevision() {
  const [rev, setRev] = useState(0);
  useEffect(() => subscribe(() => setRev((n) => n + 1)), []);
  return rev;
}
