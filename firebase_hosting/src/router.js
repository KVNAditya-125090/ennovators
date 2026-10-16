import { useState, useEffect } from 'react';

// Every page has a plain address, with no "#":
//   /<user>/<role>/<service>/<category>/<more...>
// for example /owner/manager/maas/monitor/paas, /consumer/root/saas/returns or /customer/individual/paas/catalog.
// <user> is owner, consumer or customer; <role> is the signed-in person's role (for a customer: individual or business).

const EVENT = 'routechange';
let base = ''; // /<user>/<role> of whoever is signed in

export const slug = (value) => String(value ?? '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

const DEFAULT_ROLE = { owner: 'manager', consumer: 'member', customer: 'individual' };

// /<user>/<role> for a signed-in person
export function userBase(user) {
  const type = slug(user?.role) || 'customer';
  return `/${type}/${slug(user?.department) || DEFAULT_ROLE[type] || 'member'}`;
}

export const setBase = (value) => { base = value; };
export const getBase = () => base;

// The address of a page inside the signed-in person's area, for example href('maas/monitor')
export const href = (rest = '') => {
  const tail = String(rest).replace(/^\/+|\/+$/g, '');
  return tail ? `${base}/${tail}` : base;
};

export function navigate(to, { replace = false } = {}) {
  const here = window.location.pathname + window.location.search;
  if (to === here) return;
  window.history[replace ? 'replaceState' : 'pushState'](null, '', to);
  window.dispatchEvent(new Event(EVENT));
}

// Go to a page inside the signed-in person's area
export const go = (rest, options) => navigate(href(rest), options);

// The parts of the address after /<user>/<role>, decoded
export const restSegments = (path = window.location.pathname) =>
  path.split('/').filter(Boolean).slice(2).map((s) => { try { return decodeURIComponent(s); } catch { return s; } });

// Re-renders whenever the address changes (links, Back and Forward)
export function usePath() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const onChange = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onChange);
    window.addEventListener(EVENT, onChange);
    return () => { window.removeEventListener('popstate', onChange); window.removeEventListener(EVENT, onChange); };
  }, []);
  return path;
}

export const useRest = () => restSegments(usePath());

// Plain <a href="/..."> links inside the app change the page without reloading it
export function installLinkHandler() {
  window.addEventListener('click', (e) => {
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target instanceof Element ? e.target.closest('a[href]') : null;
    if (!a || (a.target && a.target !== '_self') || a.hasAttribute('download')) return;
    const url = new URL(a.href, window.location.href);
    if (url.origin !== window.location.origin || url.pathname.startsWith('/api') || /\.[a-z0-9]+$/i.test(url.pathname)) return;
    e.preventDefault();
    navigate(url.pathname + url.search);
  }, true);
}
