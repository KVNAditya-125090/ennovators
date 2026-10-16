import React, { useState, useMemo } from 'react';
import { Play, Eye, Sparkles, Check } from 'lucide-react';
import { Section, Btn, FormModal, Drawer, ErrorNote, Empty, label } from '../../users/consumer/ui';

// Every catalog feature (endpoint) that has no screen of its own yet, shown as a card that can be run from here.
// The form is built from the endpoint's parameters, so a feature works as soon as it is in the catalog.
// Until the backend is integrated these calls are answered by preview stand-ins (cloud_run/preview.py):
// a change is recorded and a read shows what was recorded. Used by the Consumer pages and the Owner's Operations page.

const FIELD_TYPES = { int: 'number', num: 'number', text: 'textarea', obj: 'textarea', list: 'lines', date: 'date', dt: 'datetime-local', email: 'email', secret: 'password' };
const HINTS = {
  list: 'One per line',
  obj: 'JSON, for example {"key": "value"}',
  file: 'File name or link',
  secret: 'Kept private'
};

// The form fields for an endpoint's parameters
export function fieldsFor(endpoint) {
  return endpoint.parameters.map((p) => ({
    name: p.name,
    label: label(p.name),
    required: p.required,
    type: p.type === 'enum' ? 'select' : p.type === 'bool' ? 'select' : FIELD_TYPES[p.type] || 'text',
    options: p.type === 'enum' ? p.values : p.type === 'bool' ? [{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }] : undefined,
    step: p.type === 'int' ? 1 : undefined,
    hint: HINTS[p.type]
  }));
}

// The values from the form, in the types the endpoint expects
function toParams(endpoint, values) {
  const out = { ...values };
  endpoint.parameters.forEach((p) => {
    const v = out[p.name];
    if (v === undefined) return;
    if (p.type === 'bool') out[p.name] = v === 'true';
    if (p.type === 'obj') {
      try { out[p.name] = JSON.parse(v); } catch { throw new Error(`${label(p.name)} must be JSON, for example {"key": "value"}`); }
    }
  });
  return out;
}

const isRead = (e) => e.method === 'GET';
const featureName = (e) => label(e.feature);

function Value({ value }) {
  if (value === null || value === undefined || value === '') return <span className="text-google-gray-400">—</span>;
  if (Array.isArray(value)) return <span>{value.map(String).join(', ')}</span>;
  if (typeof value === 'object') return <code className="text-sm break-all">{JSON.stringify(value)}</code>;
  return <span className="break-words">{String(value)}</span>;
}

// What came back: a list of records, one record, or anything else
function Result({ data }) {
  const items = Array.isArray(data?.items) ? data.items : null;
  const record = data?.record;
  return (
    <div className="space-y-4">
      {items && (items.length === 0 ? <Empty>Nothing here yet.</Empty> : (
        <ul className="space-y-2">
          {items.map((r, i) => (
            <li key={r.id || i} className="rounded-xl border border-google-gray-200 p-3">
              <div className="flex justify-between gap-3 text-sm text-google-gray-500"><span className="font-semibold text-google-gray-800">{label(r.action || r.id)}</span><span>{r.at}{r.by ? ` • ${r.by}` : ''}</span></div>
              {r.params && <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 text-sm">{Object.entries(r.params).map(([k, v]) => <React.Fragment key={k}><dt className="text-google-gray-500">{label(k)}</dt><dd><Value value={v} /></dd></React.Fragment>)}</dl>}
            </li>
          ))}
        </ul>
      ))}
      {record && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 rounded-lg bg-google-green-light px-3 py-2 text-sm font-medium text-google-green"><Check className="h-4 w-4" />Saved{record.by ? ` by ${record.by}` : ''}{record.at ? ` · ${record.at}` : ''}</div>
          {record.params && Object.keys(record.params).length > 0 && (
            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
              {Object.entries(record.params).map(([k, v]) => <React.Fragment key={k}><dt className="text-google-gray-500">{label(k)}</dt><dd><Value value={v} /></dd></React.Fragment>)}
            </dl>
          )}
        </div>
      )}
      {!items && !record && <pre className="whitespace-pre-wrap break-all rounded-lg bg-google-gray-50 p-3 text-sm">{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}

// features: endpoint objects. run(endpoint, params) returns a promise of the response body.
export default function FeatureCards({ features, run, title = 'More actions', subtitle }) {
  const [form, setForm] = useState(null);     // the endpoint whose form is open
  const [result, setResult] = useState(null); // { endpoint, data }
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState('');

  const groups = useMemo(() => {
    const by = {};
    features.forEach((e) => { (by[e.feature] = by[e.feature] || []).push(e); });
    return Object.entries(by);
  }, [features]);
  if (features.length === 0) return null;

  const go = async (endpoint, values = {}) => {
    setBusy(endpoint.path);
    setError('');
    try {
      const data = await run(endpoint, toParams(endpoint, values));
      setResult({ endpoint, data });
      return true;
    } catch (err) {
      setError(err.message || 'The request failed.');
      return false;
    } finally {
      setBusy(null);
    }
  };
  const open = (e) => {
    setError('');
    if (e.parameters.length === 0) go(e); else setForm(e);
  };

  return (
    <Section title={title} subtitle={subtitle || `${features.length} ${features.length === 1 ? 'action' : 'actions'}`} className="mt-4">
      {!form && <ErrorNote error={error} />}
      <div className="space-y-5">
        {groups.map(([feature, list]) => (
          <div key={feature}>
            <div className="mb-2 text-sm font-bold uppercase tracking-wider text-google-gray-500">{featureName(list[0])}</div>
            <ul className="divide-y divide-google-gray-100 rounded-xl border border-google-gray-200">
              {list.map((e) => (
                <li key={e.path} data-endpoint={e.path} className="scroll-mt-24 flex flex-wrap items-center justify-between gap-3 px-4 py-2.5">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 text-base text-google-gray-900">
                      {e.description}
                      {e.ai && <span className="inline-flex items-center gap-1 rounded-full bg-google-blue-light px-2 py-0.5 text-xs font-semibold text-google-blue-dark"><Sparkles className="h-3 w-3" />AI</span>}
                      {e.actor === 'System' && <span title="Runs on its own when the event happens; run it now by hand" className="inline-flex items-center rounded-full bg-google-gray-100 px-2 py-0.5 text-xs font-semibold text-google-gray-700">Automatic</span>}
                      {e.actor === 'Partner' && <span title="Done by a linked partner; record it on their behalf" className="inline-flex items-center rounded-full bg-google-yellow-light px-2 py-0.5 text-xs font-semibold text-[#B06000]">Partner</span>}
                    </div>
                  </div>
                  <Btn disabled={busy === e.path} onClick={() => open(e)} aria-label={`${isRead(e) ? 'View' : 'Open'}: ${e.description}`}>
                    {isRead(e) ? <Eye className="h-3.5 w-3.5 inline mr-1" /> : <Play className="h-3.5 w-3.5 inline mr-1" />}
                    {busy === e.path ? 'Working...' : isRead(e) ? 'View' : 'Open'}
                  </Btn>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {form && (
        <FormModal title={form.description} fields={fieldsFor(form)} submitLabel={isRead(form) ? 'View' : 'Save'} error={error} busy={busy === form.path}
          onClose={() => { setForm(null); setError(''); }}
          onSubmit={(values) => go(form, values)} />
      )}
      {result && (
        <Drawer title={result.endpoint.description} onClose={() => setResult(null)}>
          <Result data={result.data} />
        </Drawer>
      )}
    </Section>
  );
}
