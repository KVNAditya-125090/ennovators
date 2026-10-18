import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { ChevronDown, RefreshCw, Sparkles } from 'lucide-react';
import { Dropdown, ErrorNote, FIELD, label, money, useToast } from '../consumer/ui';
import { fieldsFor } from '../../services/features/FeatureCards';
import { getStorefront } from './api';
import ResultView from './Results';
import { shrinkPhoto } from '../../services/saas/photo';

// How a shopper uses the features that have no screen of their own. Nothing opens in a pop-up:
//  - a feature that only shows something (no input needed) is displayed right there, and refreshes in place;
//  - a feature that needs input is a row that unfolds into its form, and the answer appears under the form;
//  - where a form asks for a product, order, store or ticket, the shopper picks from their own list instead of
//    typing an id.
// Calls go through the gate exactly like every other Customer feature.

const read = (e) => e.method === 'GET';
const noInput = (e) => read(e) && e.parameters.length === 0;
const short = (text) => (text.length <= 30 ? text : '');

// The lists a shopper can pick from, by the id a form asks for: how to load them, and how each choice reads
const CHOICES = {
  product_id: { load: async () => (await getStorefront()).products ?? [], value: (r) => r.id, text: (r) => r.name },
  order_id: { path: '/paas/order/read/customer/v1', pick: 'orders', value: (r) => r.order_id, text: (r) => `${r.placed_at ?? 'Order'} · ${money(r.total_usd ?? 0)} · ${String(r.order_id).slice(0, 8)}` },
  store_id: { path: '/maas/location/store/list/v1', pick: 'stores', value: (r) => r.store_id, text: (r) => `${r.name}${r.city ? `, ${r.city}` : ''}` },
  ticket_id: { path: '/saas/ticket/read/customer/v1', pick: 'tickets', value: (r) => r.ticket_id || r.id, text: (r) => `${r.subject || r.type || 'Ticket'} · ${String(r.ticket_id || r.id).slice(0, 8)}` },
  reservation_id: { path: '/paas/reserve/item/read/v1', pick: 'reservations', value: (r) => r.reservation_id || r.id, text: (r) => `${r.name || r.product_name || 'Reservation'} · ${String(r.reservation_id || r.id).slice(0, 8)}` }
};

function useChoices(name, ctx) {
  const spec = CHOICES[name];
  const [rows, setRows] = useState(null);
  useEffect(() => {
    if (!spec) return undefined;
    let live = true;
    (async () => {
      try {
        if (spec.load) { if (live) setRows(await spec.load()); return; }
        if (!ctx.can(spec.path)) { if (live) setRows([]); return; }
        const data = await ctx.call(spec.path, {});
        if (live) setRows(data[spec.pick] ?? []);
      } catch { if (live) setRows([]); }
    })();
    return () => { live = false; };
  }, [name, spec, ctx, ctx.version]);
  return spec ? { rows, spec } : null;
}

// Photos for grading: the shopper picks up to 3 pictures, shrunk in the browser, and the first one is graded
function PhotoPicker({ field, value, onChange }) {
  const photos = Array.isArray(value) ? value : [];
  const [problem, setProblem] = useState('');
  const add = async (files) => {
    setProblem('');
    try {
      const next = await Promise.all([...files].slice(0, 3 - photos.length).map((f) => shrinkPhoto(f)));
      onChange([...photos, ...next]);
    } catch (err) { setProblem(err.message); }
  };
  return (
    <div>
      <input type="file" accept="image/jpeg,image/png,image/webp" multiple aria-label={field.label} disabled={photos.length >= 3} onChange={(e) => { add(e.target.files); e.target.value = ''; }}
        className="block w-full text-sm text-google-gray-700 file:mr-3 file:rounded-lg file:border-0 file:bg-google-gray-100 file:px-3 file:py-2 file:text-sm file:font-semibold" />
      {problem && <span className="mt-1 block text-xs text-google-red">{problem}</span>}
      {photos.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2">
          {photos.map((src, i) => (
            <div key={i} className="relative">
              <img src={src} alt={`Photo ${i + 1}`} className="h-16 w-16 rounded-lg border border-google-gray-200 object-cover" />
              <button type="button" aria-label={`Remove photo ${i + 1}`} onClick={() => onChange(photos.filter((_, j) => j !== i))}
                className="absolute -right-1.5 -top-1.5 h-5 w-5 rounded-full bg-google-gray-700 text-xs leading-5 text-white">×</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Field({ field, value, onChange, ctx }) {
  const choices = useChoices(field.name, ctx);
  const options = choices?.rows?.length ? choices.rows.map((r) => ({ value: choices.spec.value(r), label: choices.spec.text(r) })) : null;
  let control;
  if (field.name === 'photos') {
    control = <PhotoPicker field={field} value={value} onChange={onChange} />;
  } else if (options) {
    control = <Dropdown ariaLabel={field.label} value={value} onChange={onChange} options={options} placeholder="Choose one" />;
  } else if (field.type === 'select') {
    control = <Dropdown ariaLabel={field.label} value={value} onChange={onChange} options={field.options.map((o) => (typeof o === 'string' ? { value: o, label: label(o) } : o))} />;
  } else if (field.type === 'textarea' || field.type === 'lines') {
    control = <textarea className={FIELD} rows={3} aria-label={field.label} value={value} onChange={(e) => onChange(e.target.value)} />;
  } else {
    control = <input className={FIELD} aria-label={field.label} type={field.type || 'text'} step={field.type === 'number' ? 'any' : undefined} value={value} onChange={(e) => onChange(e.target.value)} />;
  }
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-semibold text-google-gray-800">{field.label}{field.required ? '' : <span className="font-normal text-google-gray-500"> (optional)</span>}</span>
      {control}
      {choices && choices.rows && choices.rows.length === 0 && CHOICES[field.name] && field.name !== 'product_id' && (
        <span className="mt-1 block text-xs text-google-gray-500">You have none yet, so paste an id if you have one.</span>
      )}
      {!options && field.hint && <span className="mt-1 block text-xs text-google-gray-500">{field.hint}</span>}
    </label>
  );
}

const typed = (endpoint, fields, values) => {
  const out = {};
  fields.forEach((f) => {
    const raw = values[f.name];
    if (raw === '' || raw === undefined) return;
    const p = endpoint.parameters.find((x) => x.name === f.name);
    if (Array.isArray(raw)) out[f.name] = raw;
    else if (p.type === 'bool') out[f.name] = raw === 'true';
    else if (p.type === 'obj') {
      const text = String(raw).trim();
      if (text.startsWith('{') || text.startsWith('[')) { try { out[f.name] = JSON.parse(text); } catch { throw new Error(`${f.label} looks like JSON but is not valid. Check the brackets and quotes, or type plain text.`); } }
      else out[f.name] = text;
    }
    else if (f.type === 'number') out[f.name] = Number(raw);
    else if (f.type === 'lines') out[f.name] = String(raw).split('\n').map((x) => x.trim()).filter(Boolean);
    else out[f.name] = raw;
  });
  return out;
};

function Badges({ e }) {
  return (
    <>
      {e.ai && <span className="inline-flex items-center gap-1 rounded-full bg-google-blue-light px-2 py-0.5 text-xs font-semibold text-google-blue-dark"><Sparkles className="h-3 w-3" />AI</span>}
      {e.actor === 'System' && <span title="Runs on its own when the event happens" className="rounded-full bg-google-gray-100 px-2 py-0.5 text-xs font-semibold text-google-gray-700">Automatic</span>}
      {e.actor === 'Partner' && <span title="Done by a linked partner" className="rounded-full bg-google-yellow-light px-2 py-0.5 text-xs font-semibold text-[#B06000]">Partner</span>}
    </>
  );
}

// A feature that only shows something: it loads when it appears
function ShowPanel({ e, ctx }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    setBusy(true);
    try { setData(await ctx.call(e.path, {})); setError(''); } catch (err) { setError(err.message); } finally { setBusy(false); }
  }, [e.path, ctx]);
  useEffect(() => { load(); }, [load, ctx.version]);
  return (
    <div data-endpoint={e.path} className="scroll-mt-24 rounded-xl border border-google-gray-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h4 className="flex flex-wrap items-center gap-2 text-base font-semibold text-google-gray-900">{e.description}<Badges e={e} /></h4>
        <button type="button" onClick={load} disabled={busy} aria-label={`Refresh: ${e.description}`} className="rounded-lg p-1.5 text-google-gray-500 hover:bg-google-gray-100 disabled:opacity-60">
          <RefreshCw className={`h-4 w-4 ${busy ? 'animate-spin' : ''}`} />
        </button>
      </div>
      <ErrorNote error={error} />
      {data ? <ResultView data={data} /> : !error && <p className="text-sm text-google-gray-500">Loading...</p>}
    </div>
  );
}

// A feature that needs input: a row that unfolds into its form, with the answer right under it
function ActionPanel({ e, ctx }) {
  const fields = useMemo(() => fieldsFor(e), [e]);
  const blank = () => Object.fromEntries(fields.map((f) => [f.name, '']));
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState(blank);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const toast = useToast();
  const wrote = !read(e);
  const submit = async (ev) => {
    ev.preventDefault();
    const missing = fields.find((f) => f.required && (values[f.name] === '' || values[f.name] === undefined || (Array.isArray(values[f.name]) && values[f.name].length === 0)));
    if (missing) { setError(`Fill in ${missing.label.toLowerCase()}.`); return; }
    setBusy(true);
    setError('');
    try {
      setData(await ctx.call(e.path, typed(e, fields, values)));
      if (wrote) { setValues(blank()); ctx.changed(); toast('Done'); }
    } catch (err) {
      setError(err.message || 'The request failed.');
      setData(null);
    } finally {
      setBusy(false);
    }
  };
  const verb = wrote ? short(e.description) || 'Submit' : 'Show';
  return (
    <div data-endpoint={e.path} className="scroll-mt-24 rounded-xl border border-google-gray-200 bg-white">
      <button type="button" aria-expanded={open} onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left">
        <span className="flex flex-wrap items-center gap-2 text-base text-google-gray-900">{e.description}<Badges e={e} /></span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-google-gray-500 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="border-t border-google-gray-100 px-4 py-4">
          <form onSubmit={submit} className="space-y-3">
            <ErrorNote error={error} />
            <div className="grid gap-3 md:grid-cols-2">
              {fields.map((f) => (
                <div key={f.name} className={f.type === 'textarea' || f.type === 'lines' ? 'md:col-span-2' : ''}>
                  <Field field={f} ctx={ctx} value={values[f.name]} onChange={(v) => setValues((cur) => ({ ...cur, [f.name]: v }))} />
                </div>
              ))}
            </div>
            <button type="submit" disabled={busy} className="inline-flex items-center justify-center rounded-lg google-btn-gradient px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-60">
              {busy ? 'Working...' : verb}
            </button>
          </form>
          {data && <div className="mt-4 border-t border-google-gray-100 pt-4"><ResultView data={data} wrote={wrote} /></div>}
        </div>
      )}
    </div>
  );
}

// features: endpoint objects. call(path, params) returns the response body; can(path) says whether it is switched on.
export default function FeaturePanels({ features, call, can, title }) {
  const [version, setVersion] = useState(0); // goes up after a change, so lists to pick from and shown results refresh
  const ctx = useMemo(() => ({ call, can, version, changed: () => setVersion((v) => v + 1) }), [call, can, version]);
  const groups = useMemo(() => {
    const by = {};
    features.forEach((e) => { (by[e.feature] = by[e.feature] || []).push(e); });
    return Object.entries(by);
  }, [features]);
  if (features.length === 0) return null;
  return (
    <div className="mt-6 space-y-6">
      {title && <h3 className="text-lg font-semibold text-google-teal-dark">{title}</h3>}
      {groups.map(([feature, list]) => (
        <section key={feature}>
          <div className="mb-2 text-sm font-bold uppercase tracking-wider text-google-gray-500">{label(feature)}</div>
          <div className="space-y-2">
            {[...list.filter(noInput), ...list.filter((e) => !noInput(e))].map((e) => (noInput(e) ? <ShowPanel key={e.path} e={e} ctx={ctx} /> : <ActionPanel key={e.path} e={e} ctx={ctx} />))}
          </div>
        </section>
      ))}
    </div>
  );
}
