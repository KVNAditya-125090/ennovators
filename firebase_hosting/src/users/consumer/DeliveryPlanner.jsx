import React, { useState } from 'react';
import { X, Sparkles, Navigation, Truck, CalendarClock, Clock, Check, PencilLine, Info } from 'lucide-react';
import { useConsumer, useToast, ErrorNote, Btn, Pill, Chips, FIELD, label } from './ui';

// AI delivery planning for one shipment: route, vehicle, delivery time and delivery slots.
// Each recommendation comes with its reasons. Staff accept it, or override it with a reason (kept with the shipment).
// Only the parts this workspace opted into, and this person's role allows, are shown.
const P = {
  route: '/taas/route/optimize/recommend/v1',
  vehicle: '/taas/vehicle/recommend/v1',
  eta: '/taas/delivery/eta/predict/v1',
  slot: '/taas/delivery/slot/recommend/v1',
  accept: '/taas/recommendation/accept/v1',
  override: '/taas/recommendation/override/v1'
};
export const PLANNER_PATHS = [P.route, P.vehicle, P.eta, P.slot];

const PARTS = [
  { key: 'route', title: 'Route', icon: Navigation, path: P.route, blurb: 'Shortest, fastest, cheapest or greenest path, with extra stops' },
  { key: 'vehicle', title: 'Vehicle', icon: Truck, path: P.vehicle, blurb: 'The vehicle type that fits the load and distance best' },
  { key: 'eta', title: 'Delivery date and time', icon: Clock, path: P.eta, blurb: 'When it will arrive, with a window and confidence' },
  { key: 'slot', title: 'Delivery slots', icon: CalendarClock, path: P.slot, blurb: 'Slots to offer, ranked by how likely they are to be met' }
];

const COLUMNS = {
  route: [['via', 'Via'], ['distance_km', 'Km'], ['hours', 'Hours'], ['cost_usd', 'Cost $'], ['co2_kg', 'CO2 kg']],
  vehicle: [['distance_km', 'Km'], ['hours', 'Hours'], ['cost_usd', 'Cost $'], ['co2_kg', 'CO2 kg'], ['why_not', 'Fits']],
  eta: [['eta', 'Expected'], ['earliest', 'Earliest'], ['latest', 'Latest']],
  slot: [['on_time_chance', 'On time'], ['note', 'Note']]
};
const cell = (key, o) => {
  if (key === 'why_not') return o.fits ? 'Yes' : <span className="text-google-red">{o.why_not}</span>;
  if (key === 'on_time_chance') return `${Math.round(o.on_time_chance * 100)}%`;
  return o[key] ?? '';
};

function Why({ explanation }) {
  return (
    <div className="rounded-xl bg-google-blue-light/50 p-3 text-sm text-google-gray-800">
      <div className="flex items-center gap-1.5 font-semibold text-google-teal"><Info className="h-4 w-4" />Why this is recommended</div>
      <p className="mt-1 text-base text-google-gray-900">{explanation.summary}</p>
      <ul className="mt-2 list-disc space-y-0.5 pl-5">{explanation.factors.map((f, i) => <li key={i}>{f}</li>)}</ul>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-google-gray-600">
        <span>Confidence {Math.round(explanation.confidence * 100)}%</span>
        <span>Based on: {explanation.data_sources.join('; ')}</span>
      </div>
    </div>
  );
}

function Part({ part, shipment, onApplied }) {
  const { can, call } = useConsumer();
  const toast = useToast();
  const [objective, setObjective] = useState('greenest');
  const [stops, setStops] = useState('');
  const [kg, setKg] = useState(shipment.weight_kg ?? '');
  const [litres, setLitres] = useState(shipment.volume_l ?? '');
  const [decision, setDecision] = useState(null);
  const [choice, setChoice] = useState('');
  const [reason, setReason] = useState('');
  const [overriding, setOverriding] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  if (!can(part.path)) return null;

  const run = async (path, params, after) => {
    setBusy(true);
    setError('');
    try { const r = await call(path, params); after(r); } catch (err) { setError(err.message); } finally { setBusy(false); }
  };
  const recommend = () => {
    const params = { shipment_id: shipment.shipment_id };
    if (part.key === 'route') { params.objective = objective; const list = stops.split(',').map((s) => s.trim()).filter(Boolean); if (list.length) params.stops = list; }
    if (part.key === 'vehicle') { if (kg !== '') params.weight_kg = Number(kg); if (litres !== '') params.volume_l = Number(litres); }
    run(part.path, params, (d) => { setDecision(d); setChoice(d.recommended); setOverriding(false); setReason(''); });
  };
  const finish = (r) => { setDecision(r.decision); onApplied(); toast(r.decision.status === 'overridden' ? `${part.title}: your choice applied` : `${part.title}: recommendation applied`); };
  const accept = () => run(P.accept, { decision_id: decision.decision_id }, finish);
  const override = () => run(P.override, { decision_id: decision.decision_id, choice, reason }, finish);
  const Icon = part.icon;
  const decided = decision && decision.status !== 'proposed';

  return (
    <section className="rounded-2xl border border-google-gray-200 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-google-yellow-light text-[#B06000]"><Icon className="h-4 w-4" /></span>
          <div><div className="text-base font-semibold text-google-gray-900">{part.title}</div><div className="text-sm text-google-gray-500">{part.blurb}</div></div>
        </div>
        <Btn kind="primary" disabled={busy} onClick={recommend}><Sparkles className="h-3.5 w-3.5 inline mr-1" />{decision ? 'Recommend again' : 'Recommend'}</Btn>
      </div>

      {part.key === 'route' && (
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Chips value={objective} onChange={setObjective} options={['greenest', 'shortest', 'fastest', 'cheapest'].map((o) => ({ value: o, label: label(o) }))} />
          <input className={`${FIELD} w-64`} value={stops} onChange={(e) => setStops(e.target.value)} placeholder="Extra stops, comma separated" aria-label="Extra stops, comma separated" />
        </div>
      )}
      {part.key === 'vehicle' && (
        <div className="mt-3 flex flex-wrap gap-3">
          <input className={`${FIELD} w-40`} type="number" min="0" step="any" value={kg} onChange={(e) => setKg(e.target.value)} placeholder="Weight kg (5)" aria-label="Weight in kg" />
          <input className={`${FIELD} w-40`} type="number" min="0" step="any" value={litres} onChange={(e) => setLitres(e.target.value)} placeholder="Volume litres (20)" aria-label="Volume in litres" />
        </div>
      )}
      <div className="mt-3"><ErrorNote error={error} /></div>

      {decision && (
        <div className="mt-1 space-y-3">
          <div className="overflow-x-auto rounded-xl border border-google-gray-200">
            <table className="w-full text-sm">
              <thead><tr className="bg-google-gray-50 text-left text-xs uppercase tracking-wider text-google-gray-500"><th className="px-3 py-2">Option</th>{COLUMNS[part.key].map(([, h]) => <th key={h} className="px-3 py-2">{h}</th>)}</tr></thead>
              <tbody className="divide-y divide-google-gray-100">
                {decision.options.map((o) => (
                  <tr key={o.name} className={o.name === decision.recommended ? 'bg-google-green-light/40' : ''}>
                    <td className="px-3 py-2 font-semibold text-google-gray-900 whitespace-nowrap">{o.name}{o.name === decision.recommended && <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-google-green-light px-2 py-0.5 text-xs text-google-green"><Sparkles className="h-3 w-3" />AI pick</span>}{decision.chosen === o.name && decision.status === 'overridden' && <span className="ml-2 rounded-full bg-google-blue-light px-2 py-0.5 text-xs text-google-blue-dark">Your choice</span>}</td>
                    {COLUMNS[part.key].map(([k]) => <td key={k} className="px-3 py-2 text-google-gray-700">{cell(k, o)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Why explanation={decision.explanation} />
          {decided ? (
            <div className="flex flex-wrap items-center gap-2 text-sm text-google-gray-700">
              <Pill value={decision.status === 'accepted' ? 'resolved' : 'approved'} label={label(decision.status)} />
              <span>{decision.chosen} applied{decision.decided_by ? ` by ${decision.decided_by}` : ''} at {decision.decided_at}{decision.reason ? `. Reason: ${decision.reason}` : ''}</span>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex flex-wrap gap-2">
                {can(P.accept) && <Btn kind="primary" disabled={busy} onClick={accept}><Check className="h-3.5 w-3.5 inline mr-1" />Accept {decision.recommended}</Btn>}
                {can(P.override) && decision.options.length > 1 && <Btn disabled={busy} onClick={() => setOverriding((v) => !v)}><PencilLine className="h-3.5 w-3.5 inline mr-1" />Choose another</Btn>}
              </div>
              {overriding && (
                <div className="flex flex-wrap items-center gap-2">
                  <select className={`${FIELD} w-auto`} value={choice} onChange={(e) => setChoice(e.target.value)} aria-label="Your choice">
                    {decision.options.map((o) => <option key={o.name} value={o.name} disabled={o.fits === false}>{o.name}{o.fits === false ? ' (does not fit)' : ''}</option>)}
                  </select>
                  <input className={`${FIELD} flex-1 min-w-[14rem]`} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Why you are overriding (kept for the audit)" aria-label="Reason for the override" />
                  <Btn kind="primary" disabled={busy || !reason.trim() || choice === decision.recommended} onClick={override}>Apply my choice</Btn>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default function DeliveryPlanner({ shipment, onClose, onApplied }) {
  const { can } = useConsumer();
  const plan = [['Route', shipment.route], ['Vehicle', shipment.vehicle], ['Arrives', shipment.eta], ['Slot', shipment.delivery_slot]];
  return (
    <div className="fixed inset-0 z-50 bg-black/30" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <aside role="dialog" aria-modal="true" aria-label={`Plan delivery for ${shipment.shipment_id}`} className="absolute right-0 top-0 h-full w-full max-w-3xl overflow-y-auto bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-xl font-semibold text-google-teal-dark">Plan delivery: {shipment.shipment_id}</h3>
            <p className="text-sm text-google-gray-600">{shipment.origin} to {shipment.destination}</p>
          </div>
          <button onClick={onClose} aria-label="Close" className="text-google-gray-500 hover:text-google-gray-900"><X className="h-5 w-5" /></button>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {plan.map(([k, v]) => <div key={k} className="rounded-xl bg-google-gray-50 px-3 py-2"><div className="text-xs uppercase tracking-wider text-google-gray-500">{k}</div><div className="text-sm font-semibold text-google-gray-900">{v || 'Not set'}</div></div>)}
        </div>
        <div className="mt-4 space-y-4">
          {PARTS.map((part) => <Part key={part.key} part={part} shipment={shipment} onApplied={onApplied} />)}
          {!PLANNER_PATHS.some(can) && <p className="text-base text-google-gray-600">Your workspace or role has no AI delivery planning features.</p>}
        </div>
      </aside>
    </div>
  );
}
