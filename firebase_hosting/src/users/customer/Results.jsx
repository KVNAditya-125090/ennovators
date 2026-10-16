import React from 'react';
import { Check } from 'lucide-react';
import { label, money, Pill } from '../consumer/ui';

// Shows whatever an endpoint sent back as readable content instead of raw data: a message, details as
// label/value rows, and lists of records as cards. Nothing here is specific to one endpoint, so a new
// feature reads well as soon as it exists. Used by the Customer pages (inline, never in a pop-up).

const SKIP = new Set(['preview', 'source', 'message', 'record']);
const TITLE_KEYS = ['name', 'title', 'subject', 'order_id', 'ticket_id', 'reservation_id', 'product_id', 'id'];
const isObj = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

function format(key, v) {
  if (v === null || v === undefined || v === '') return <span className="text-google-gray-400">—</span>;
  if (typeof v === 'boolean') return v ? 'Yes' : 'No';
  if (typeof v === 'number') {
    if (/_usd$|^price$|^amount$|^total$/.test(key)) return money(v);
    if (/_pct$/.test(key)) return `${v}%`;
    if (/_kg$/.test(key)) return `${v} kg`;
    if (/_km$/.test(key)) return `${v} km`;
    return v.toLocaleString();
  }
  if (typeof v === 'string') {
    if (/(^|_)status$|^state$/.test(key)) return <Pill value={v} />;
    if (/^https?:\/\//.test(v)) return <a href={v} target="_blank" rel="noreferrer" className="text-google-blue underline break-all">{v}</a>;
    return <span className="break-words">{v}</span>;
  }
  if (Array.isArray(v)) return v.every((x) => !isObj(x) && !Array.isArray(x)) ? <span>{v.map(String).join(', ')}</span> : <Rows data={v} nested />;
  return <Rows data={v} nested />;
}

// One object as label / value rows
function Fields({ data, skip = [] }) {
  const entries = Object.entries(data).filter(([k]) => !SKIP.has(k) && !skip.includes(k));
  if (entries.length === 0) return null;
  return (
    <dl className="grid grid-cols-[minmax(7rem,auto)_1fr] gap-x-4 gap-y-1.5 text-sm">
      {entries.map(([k, v]) => (
        <React.Fragment key={k}>
          <dt className="text-google-gray-500">{label(k)}</dt>
          <dd className="min-w-0 text-google-gray-900">{format(k, v)}</dd>
        </React.Fragment>
      ))}
    </dl>
  );
}

// A list of records as cards, or a list of plain values
function Rows({ data, nested = false }) {
  if (isObj(data)) return <div className={nested ? 'rounded-lg bg-google-gray-50 p-3' : ''}><Fields data={data} /></div>;
  if (!Array.isArray(data)) return format('', data);
  if (data.length === 0) return <span className="text-google-gray-500">Nothing here yet.</span>;
  return (
    <ul className="space-y-2">
      {data.map((r, i) => {
        if (!isObj(r)) return <li key={i} className="text-sm">{String(r)}</li>;
        const titleKey = TITLE_KEYS.find((k) => typeof r[k] === 'string' && r[k]) || null;
        const title = titleKey ? (/id$/.test(titleKey) ? `${label(titleKey.replace(/_id$/, ''))} ${String(r[titleKey]).slice(0, 8)}` : r[titleKey]) : `Item ${i + 1}`;
        return (
          <li key={r.id || r.order_id || r.product_id || i} className="rounded-xl border border-google-gray-200 bg-white p-3">
            <div className="mb-1.5 flex items-start justify-between gap-3">
              <span className="font-semibold text-google-gray-900 break-words">{title}</span>
              {typeof r.status === 'string' && <Pill value={r.status} />}
            </div>
            <Fields data={r} skip={[titleKey, 'status'].filter(Boolean)} />
          </li>
        );
      })}
    </ul>
  );
}

// What came back, laid out. A single list (cart lines, stores...) shows as cards; several values as rows.
export default function ResultView({ data, wrote = false }) {
  if (data === null || data === undefined) return null;
  if (!isObj(data)) return <Rows data={data} />;
  const message = data.message;
  const record = data.record;
  const rest = Object.fromEntries(Object.entries(data).filter(([k]) => !SKIP.has(k)));
  const scalars = Object.entries(rest).filter(([, v]) => !Array.isArray(v) && !isObj(v));
  const blocks = Object.entries(rest).filter(([, v]) => Array.isArray(v) || isObj(v));
  return (
    <div className="space-y-3">
      {(wrote || record) && (
        <div role="status" className="flex items-center gap-2 rounded-lg bg-google-green-light px-3 py-2 text-sm font-medium text-google-green">
          <Check className="h-4 w-4 shrink-0" />{message || 'Done.'}
        </div>
      )}
      {!(wrote || record) && message && <p className="text-sm text-google-gray-700">{message}</p>}
      {record?.params && Object.keys(record.params).length > 0 && <Fields data={record.params} />}
      {scalars.length > 0 && <Fields data={Object.fromEntries(scalars)} />}
      {blocks.map(([k, v]) => (
        <div key={k}>
          {(blocks.length > 1 || scalars.length > 0 || !/^(items|results|data)$/.test(k)) && <div className="mb-1.5 text-xs font-bold uppercase tracking-wider text-google-gray-500">{label(k)}</div>}
          <Rows data={v} />
        </div>
      ))}
    </div>
  );
}
