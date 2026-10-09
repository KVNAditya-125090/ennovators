import { useSyncExternalStore } from 'react';

// The pages the signed-in person's role shows, as chosen by the Root on the Customization page.
// A view is { landing: 'service/page', pages: ['service/page', ...] }; null means no narrowing (the Root, or a role with no view).
// Permissions decide what a role can do; the view only narrows which of those pages appear.
let state = { view: null };
const listeners = new Set();
const emit = () => listeners.forEach((l) => l());

export const subscribe = (l) => { listeners.add(l); return () => listeners.delete(l); };
export const getViewState = () => state;
export const useViewState = () => useSyncExternalStore(subscribe, getViewState);

export const setView = (view) => { state = { view: view || null }; emit(); };
export const activeView = (s = state) => s.view;
