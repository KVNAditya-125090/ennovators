import React, { useEffect, useRef, useState } from 'react';
import { loadMaps, mapsConfigured } from './loader';

// A map with markers and, optionally, a route line (the encoded line the Routes API returns).
//   markers: [{ lat, lng, label }]      polyline: an encoded route line, or null
// Shows a short note instead when Maps is not configured, so a screen that uses it still works.
export default function DispatchMap({ markers = [], polyline = null, height = 360 }) {
  const box = useRef(null);
  const [problem, setProblem] = useState('');
  const markerKey = JSON.stringify(markers); // a new array with the same points must not rebuild the map: every build is a billed map load

  useEffect(() => {
    if (!mapsConfigured()) return undefined;
    let cancelled = false;
    (async () => {
      try {
        const maps = await loadMaps();
        const { Map, Polyline } = await maps.importLibrary('maps');
        const { AdvancedMarkerElement } = await maps.importLibrary('marker');
        const { encoding } = await maps.importLibrary('geometry');
        if (cancelled || !box.current) return;
        const bounds = new maps.LatLngBounds();
        const map = new Map(box.current, { center: { lat: 20.59, lng: 78.96 }, zoom: 4, mapId: 'DEMO_MAP_ID', streetViewControl: false });
        const points = JSON.parse(markerKey);
        points.forEach((m) => {
          bounds.extend(m);
          new AdvancedMarkerElement({ map, position: m, title: m.label || '' });
        });
        if (polyline) {
          const path = encoding.decodePath(polyline);
          new Polyline({ map, path, strokeColor: '#1A73E8', strokeWeight: 5 });
          path.forEach((p) => bounds.extend(p));
          if (points.length === 0 && path.length > 1) { // no markers given: mark where the route starts and ends
            new AdvancedMarkerElement({ map, position: path[0], title: 'Start' });
            new AdvancedMarkerElement({ map, position: path[path.length - 1], title: 'End' });
          }
        }
        if (!bounds.isEmpty()) map.fitBounds(bounds, 48);
      } catch (err) {
        if (!cancelled) setProblem(err.message);
      }
    })();
    return () => { cancelled = true; };
  }, [markerKey, polyline]);

  if (!mapsConfigured()) {
    return <div className="rounded-xl border border-dashed border-google-gray-200 p-6 text-sm text-google-gray-600">The map is not connected yet.</div>;
  }
  if (problem) {
    return <div className="rounded-xl border border-google-red p-6 text-sm text-google-red">{problem}</div>;
  }
  return <div ref={box} style={{ height }} className="w-full rounded-xl border border-google-gray-200" role="img" aria-label="Map" />;
}
