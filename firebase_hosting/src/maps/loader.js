// Google Maps - loads the Maps JavaScript API once, when a map or address box first needs it.
// The browser key comes from VITE_GOOGLE_MAPS_KEY (set in firebase_hosting/.env.local, never in git). The key is
// restricted in Google Cloud to this site's addresses and to the Maps JavaScript and Places APIs.

const KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY;
let loading = null;

export const mapsConfigured = () => Boolean(KEY);

export function loadMaps() {
  if (!KEY) return Promise.reject(new Error('Maps is not configured: VITE_GOOGLE_MAPS_KEY is not set.'));
  if (window.google?.maps?.importLibrary) return Promise.resolve(window.google.maps);
  if (!loading) {
    loading = new Promise((resolve, reject) => {
      // Google calls this once the library is really ready; the script's own load event can come before importLibrary exists
      window.__lakshmiMapsReady = () => {
        if (typeof window.google?.maps?.importLibrary === 'function') resolve(window.google.maps);
        else { loading = null; reject(new Error('The map library did not start.')); }
      };
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(KEY)}&v=weekly&loading=async&callback=__lakshmiMapsReady`;
      script.async = true;
      script.onerror = () => { loading = null; reject(new Error('The map could not be loaded.')); };
      document.head.appendChild(script);
    });
  }
  return loading;
}
