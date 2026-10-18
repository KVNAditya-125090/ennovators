import React, { useEffect, useRef, useState } from 'react';
import { loadMaps, mapsConfigured } from './loader';

// The street, city, postcode and country of a picked place, for forms that have a field for each
function addressParts(place) {
  const get = (...types) => (place.addressComponents || []).find((c) => types.some((t) => c.types.includes(t)))?.longText || '';
  const street = [get('street_number'), get('route'), get('sublocality_level_1', 'sublocality')].filter(Boolean).join(' ');
  return { line1: street || (place.formattedAddress || '').split(',')[0], city: get('locality', 'administrative_area_level_2'),
           postcode: get('postal_code'), country: get('country') };
}

// An address box that suggests places as the person types (Places API, new).
//   onSelect({ address, lat, lng, placeId, parts })   called when a suggestion is picked; parts = { line1, city, postcode, country }
//   region: a two-letter country code such as "in", to keep suggestions local
// One session token covers a whole typing session, so Google bills it once. With no key it is a plain text box.
export default function AddressAutocomplete({ onSelect, region = 'in', placeholder = 'Start typing an address', className = '' }) {
  const [text, setText] = useState('');
  const [options, setOptions] = useState([]);
  const places = useRef(null);
  const session = useRef(null);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  const ask = (value) => {
    clearTimeout(timer.current);
    if (!mapsConfigured() || value.trim().length < 3) { setOptions([]); return; }
    // wait for a pause in typing, so each word is one call and not each letter
    timer.current = setTimeout(async () => {
      try {
        const maps = await loadMaps();
        places.current = places.current || (await maps.importLibrary('places'));
        session.current = session.current || new places.current.AutocompleteSessionToken();
        const { suggestions } = await places.current.AutocompleteSuggestion.fetchAutocompleteSuggestions({
          input: value, sessionToken: session.current, includedRegionCodes: [region]
        });
        setOptions(suggestions.map((s) => s.placePrediction).filter(Boolean));
      } catch {
        setOptions([]);
      }
    }, 350);
  };

  const pick = async (prediction) => {
    setOptions([]);
    setText(prediction.text.text);
    try {
      const place = prediction.toPlace();
      await place.fetchFields({ fields: ['formattedAddress', 'location', 'addressComponents'] });
      session.current = null; // the session ends when a place is picked
      onSelect?.({ address: place.formattedAddress, lat: place.location.lat(), lng: place.location.lng(), placeId: prediction.placeId, parts: addressParts(place) });
    } catch {
      onSelect?.({ address: prediction.text.text, lat: null, lng: null, placeId: prediction.placeId, parts: { line1: prediction.text.text.split(',')[0], city: '', postcode: '', country: '' } });
    }
  };

  return (
    <div className={`relative ${className}`}>
      <input
        type="text"
        value={text}
        onChange={(e) => { setText(e.target.value); ask(e.target.value); }}
        placeholder={placeholder}
        autoComplete="off"
        aria-label="Address"
        className="w-full rounded-lg border border-google-gray-300 px-3 py-2 text-sm focus:border-google-blue focus:outline-none focus:ring-4 focus:ring-google-blue/15"
      />
      {options.length > 0 && (
        <ul role="listbox" className="absolute z-20 mt-1 w-full overflow-hidden rounded-lg border border-google-gray-200 bg-white shadow-lg">
          {options.map((o) => (
            <li key={o.placeId}>
              <button type="button" onClick={() => pick(o)} className="block w-full px-3 py-2 text-left text-sm hover:bg-google-gray-100">{o.text.text}</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
