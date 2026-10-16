// Keeps the signed-in user for the life of the browser tab, so a reload does not sign you out.
// It is cleared on sign-out and when the tab is closed. Preview only: the API issues no tokens yet,
// so this stores the profile, not a credential.
const KEY = 'auracommerce.session';
const ROLES = ['Owner', 'Consumer', 'Customer'];

export function loadSession() {
  try {
    const user = JSON.parse(window.sessionStorage.getItem(KEY));
    return user && typeof user.name === 'string' && ROLES.includes(user.role) ? user : null;
  } catch {
    return null;
  }
}

export function saveSession(user) {
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify(user));
  } catch {
    // storage can be blocked (private mode); the session then lasts until reload
  }
}

export function clearSession() {
  try {
    window.sessionStorage.removeItem(KEY);
  } catch {
    // nothing to clear
  }
}
