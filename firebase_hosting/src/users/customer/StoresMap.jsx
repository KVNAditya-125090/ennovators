import React, { useEffect, useMemo, useState } from 'react';
import { MapPin, LocateFixed } from 'lucide-react';
import { DispatchMap, mapsConfigured } from '../../maps';
import { ErrorNote, Btn } from '../consumer/ui';

const LIST = '/maas/location/store/list/v1';
const NEARBY = '/maas/location/store/nearby/find/v1';

// The seller's stores on a map. "Use my location" asks the browser for where the shopper is (they are asked first) and lists
// the stores by road distance, nearest first. Without a Maps key the list still works; only the map is replaced by a note.
export default function StoresMap({ call, can }) {
  const [stores, setStores] = useState(null);
  const [near, setNear] = useState(null); // the stores ranked by distance from the shopper
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!can(LIST)) return;
    call(LIST, {}).then((d) => setStores(d.stores || [])).catch((err) => setError(err.message));
  }, [call, can]);

  const markers = useMemo(() => (stores || []).filter((s) => s.latitude != null && s.longitude != null)
    .map((s) => ({ lat: s.latitude, lng: s.longitude, label: s.name })), [stores]);

  const locate = () => {
    if (!navigator.geolocation) { setError('Your browser cannot share its location.'); return; }
    setBusy(true); setError('');
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try { setNear(await call(NEARBY, { latitude: pos.coords.latitude, longitude: pos.coords.longitude })); }
        catch (err) { setError(err.message); }
        finally { setBusy(false); }
      },
      () => { setBusy(false); setError('Location was not shared. You can still pick a store from the list.'); },
      { timeout: 10000 }
    );
  };

  if (!can(LIST) || !stores || stores.length === 0) return null;
  const ranked = near?.stores || stores;
  return (
    <section className="mb-6 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-google-teal-dark">Our stores{mapsConfigured() ? ' on the map' : ''}</h3>
        {can(NEARBY) && <Btn kind="primary" disabled={busy} onClick={locate}><LocateFixed className="mr-1 inline h-3.5 w-3.5" />{busy ? 'Finding you...' : 'Use my location'}</Btn>}
      </div>
      <ErrorNote error={error} />
      {mapsConfigured() && markers.length > 0 && <DispatchMap markers={markers} height={320} />}
      <ul className="grid gap-2 md:grid-cols-2">
        {ranked.map((s, i) => (
          <li key={s.store_id} className={`rounded-xl border p-3 text-sm ${near && i === 0 ? 'border-google-green bg-google-green-light/40' : 'border-google-gray-200 bg-white'}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-1.5 font-semibold text-google-gray-900"><MapPin className="h-4 w-4 text-google-teal" />{s.name}{near && i === 0 && <span className="rounded-full bg-google-green-light px-2 py-0.5 text-xs text-google-green">Nearest</span>}</div>
              {s.distance_km != null && <div className="whitespace-nowrap text-xs text-google-gray-600">{s.distance_km} km{s.duration_minutes ? ` · ${s.duration_minutes} min` : ''}</div>}
            </div>
            <div className="mt-0.5 text-google-gray-600">{[s.address, s.city].filter(Boolean).join(', ')}</div>
            {s.opening_hours && <div className="text-xs text-google-gray-500">{s.opening_hours}</div>}
            {s.distance_source === 'estimate' && <div className="text-xs text-google-gray-400">Straight-line estimate</div>}
          </li>
        ))}
      </ul>
    </section>
  );
}
