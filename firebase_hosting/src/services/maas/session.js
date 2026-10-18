// Keeps the signed-in user and their sign-in token for the life of the browser tab, so a reload does not sign you out.
// Both are cleared on sign-out and when the tab is closed. The token is what proves who you are to the API.
const KEY = 'lakshmi.session';
const TOKEN_KEY = 'lakshmi.token';
const ROLES = ['Owner', 'Consumer', 'Customer'];

export function loadSession() {
  try {
    const user = JSON.parse(window.sessionStorage.getItem(KEY));
    return user && typeof user.name === 'string' && ROLES.includes(user.role) ? user : null;
  } catch {
    return null;
  }
}

// The Root of a consumer: its department ends in Root (for example "Root")
export const isRootUser = (user) => Boolean(user?.department?.endsWith('Root'));

export function saveSession(user) {
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify(user));
  } catch {
    // storage can be blocked (private mode); the session then lasts until reload
  }
}

export function saveToken(token) {
  try {
    window.sessionStorage.setItem(TOKEN_KEY, token);
  } catch {
    // storage can be blocked (private mode); the token then lasts until reload
  }
}

// The header that proves who is calling, or nothing when nobody is signed in
export function authHeader() {
  try {
    const token = window.sessionStorage.getItem(TOKEN_KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

export function clearSession() {
  try {
    window.sessionStorage.removeItem(KEY);
    window.sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // nothing to clear
  }
}
