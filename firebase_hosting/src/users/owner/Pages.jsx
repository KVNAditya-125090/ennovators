import React, { useState, useEffect } from 'react';
import { Loader2, Search } from 'lucide-react';
import { getApis, getTelemetry, getQueries, updateQuery } from './api';
import { EndpointStatus, ENDPOINT_STATUS, QUERY_PILLS, formatDay } from './shared';

const SERVICE_CODES = ['MaaS', 'PaaS', 'TaaS', 'SaaS'];
const TH = 'px-5 py-3 font-semibold';
const HEAD_ROW = 'text-left text-xs uppercase tracking-wider text-google-gray-600 border-b border-google-gray-200';

// load one thing from the API and say when it is loading or has failed
function useLoad(load, deps) {
  const [state, setState] = useState({ data: null, error: '' });
  useEffect(() => {
    let cancelled = false;
    setState({ data: null, error: '' });
    load()
      .then((data) => { if (!cancelled) setState({ data, error: '' }); })
      .catch(() => { if (!cancelled) setState({ data: null, error: 'Could not load this page. Please try again.' }); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}

function SearchBox({ value, onChange, placeholder, label }) {
  return (
    <div className="relative w-full sm:w-96">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-google-gray-400" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={label}
        className="w-full rounded-lg border border-google-gray-300 bg-white py-2 pl-9 pr-3 text-sm focus:border-google-blue focus:outline-none focus:ring-2 focus:ring-google-blue/20"
      />
    </div>
  );
}

function PageShell({ title, subtitle, search, filters, state, children }) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        {search || (
          <div>
            <h1 className="text-2xl font-bold text-google-gray-900">{title}</h1>
            {subtitle && <p className="text-sm text-google-gray-600 mt-1">{subtitle}</p>}
          </div>
        )}
        {filters}
      </div>
      {state.error && <div className="rounded-lg bg-google-red-light text-google-red px-4 py-3 text-sm">{state.error}</div>}
      {!state.data && !state.error && <div className="flex items-center gap-2 text-sm text-google-gray-600"><Loader2 className="h-4 w-4 animate-spin" /> Loading...</div>}
      {state.data && children}
    </div>
  );
}

// the row of links that filters a page
function FilterLinks({ items, current }) {
  return (
    <div className="inline-flex gap-1 rounded-xl border border-google-gray-200 bg-white p-1 shadow-sm" aria-label="Filter">
      {items.map(([label, href, key]) => (
        <a
          key={key}
          href={href}
          aria-current={current === key ? 'page' : undefined}
          className={`rounded-lg px-3 py-1 text-sm font-semibold ${current === key ? 'bg-google-blue-light text-google-blue-dark' : 'text-google-gray-600 hover:bg-google-gray-100'}`}
        >
          {label}
        </a>
      ))}
    </div>
  );
}

function Empty({ children }) {
  return <div className="google-card p-8 text-center text-sm text-google-gray-600">{children}</div>;
}

// Every API on the platform and how its endpoint is doing
export function ApisPage({ service }) {
  const state = useLoad(getApis, []);
  const [query, setQuery] = useState('');
  const needle = query.trim().toLowerCase();
  const rows = state.data
    ? state.data.apis.filter((a) => (!service || a.service === service)
      && (!needle || [a.name, a.description, a.service, a.method, a.endpoint, (ENDPOINT_STATUS[a.endpoint_status] || {}).label || ''].some((v) => v.toLowerCase().includes(needle))))
    : [];
  return (
    <PageShell
      search={<SearchBox value={query} onChange={setQuery} placeholder="Search by API, service, endpoint or status" label="Search the APIs" />}
      state={state}
      filters={<FilterLinks current={service || 'all'} items={[['All', '#/monitor', 'all'], ...SERVICE_CODES.map((c) => [c, `#/monitor/${c}`, c])]} />}
    >
      {rows.length === 0 ? <Empty>No APIs match.</Empty> : (
        <div className="google-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className={HEAD_ROW}>
                <th className={TH}>API</th><th className={TH}>Service</th><th className={TH}>Endpoint</th><th className={TH}>Status</th>
                <th className={`${TH} text-right`}>Response</th><th className={`${TH} text-right`}>Consumers</th><th className={`${TH} text-right`}>Requests this month</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-google-gray-100">
              {rows.map((a) => (
                <tr key={a.api_id}>
                  <td className="px-5 py-3"><div className="font-semibold text-google-gray-900">{a.name}</div><div className="text-xs text-google-gray-500">{a.description}</div></td>
                  <td className="px-5 py-3 text-google-gray-700">{a.service}</td>
                  <td className="px-5 py-3 whitespace-nowrap"><span className="rounded bg-google-gray-100 px-1.5 py-0.5 text-xs font-bold text-google-gray-700 mr-2">{a.method}</span><code className="font-mono text-xs text-google-gray-700">{a.endpoint}</code></td>
                  <td className="px-5 py-3 whitespace-nowrap"><EndpointStatus status={a.endpoint_status} showLabel /></td>
                  <td className="px-5 py-3 text-right text-google-gray-600 whitespace-nowrap">{a.latency_ms.toLocaleString()} ms</td>
                  <td className="px-5 py-3 text-right text-google-gray-900">{a.consumers_opted} of {a.total_consumers}</td>
                  <td className="px-5 py-3 text-right font-semibold text-google-gray-900">{a.requests_this_month.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PageShell>
  );
}

const LEVELS = { errors: 'error', warnings: 'warning' };
const LEVEL_STYLES = { error: 'bg-google-red-light text-google-red', warning: 'bg-google-yellow-light text-google-gray-900', info: 'bg-google-green-light text-google-green' };
const stamp = (iso) => new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });

const LOG_STATUS_STYLES = { Success: LEVEL_STYLES.info, Warning: LEVEL_STYLES.warning, Failed: LEVEL_STYLES.error };

// The logs of the Google Cloud services behind the platform, all together
export function TelemetryPage({ level }) {
  const kind = LEVELS[level] || 'all';
  const state = useLoad(() => getTelemetry(kind), [kind]);
  const [query, setQuery] = useState('');
  const d = state.data;
  const needle = query.trim().toLowerCase();
  const rows = d ? d.logs.filter((l) => !needle || [l.service, l.method, l.endpoint, l.description, l.message, l.status].some((v) => v.toLowerCase().includes(needle))) : [];
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SearchBox value={query} onChange={setQuery} placeholder="Search by service, endpoint, message or status" label="Search the logs" />
        <FilterLinks current={LEVELS[level] ? level : 'all'} items={[['All', '#/telemetry', 'all'], ['Errors', '#/telemetry/errors', 'errors'], ['Warnings', '#/telemetry/warnings', 'warnings']]} />
      </div>
      {state.error && <div className="rounded-lg bg-google-red-light text-google-red px-4 py-3 text-sm">{state.error}</div>}
      {!d && !state.error && <div className="flex items-center gap-2 text-sm text-google-gray-600"><Loader2 className="h-4 w-4 animate-spin" /> Loading...</div>}
      {d && (rows.length === 0 ? <Empty>No log lines match.</Empty> : (
        <div className="google-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className={HEAD_ROW}>
                <th className={TH}>Time</th><th className={TH}>Service</th><th className={TH}>Endpoint</th><th className={TH}>Description</th><th className={TH}>Message</th><th className={TH}>Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-google-gray-100">
              {rows.map((l, i) => (
                <tr key={`${l.timestamp}-${l.service_id}-${i}`}>
                  <td className="px-5 py-2.5 text-google-gray-600 whitespace-nowrap">{stamp(l.timestamp)}</td>
                  <td className="px-5 py-2.5 whitespace-nowrap text-google-gray-900">{l.service}</td>
                  <td className="px-5 py-2.5 min-w-[18rem] max-w-md"><span className="rounded bg-google-gray-100 px-1.5 py-0.5 text-xs font-bold text-google-gray-700 mr-2">{l.method}</span><code className="font-mono text-xs text-google-gray-700 break-all">{l.endpoint}</code></td>
                  <td className="px-5 py-2.5 text-google-gray-600">{l.description}</td>
                  <td className="px-5 py-2.5 text-google-gray-900">{l.message}</td>
                  <td className="px-5 py-2.5"><span className={`google-pill ${LOG_STATUS_STYLES[l.status]}`}>{l.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

const STATUS_SLUGS = { new: 'New', 'in-conversation': 'In conversation', closed: 'Closed' };
const QUERY_STATUSES = ['New', 'In conversation', 'Closed'];

// The queries visitors send from the home page. The team replies by email or phone and moves each one along.
export function QueriesPage({ filter }) {
  const state = useLoad(getQueries, []);
  const [items, setItems] = useState(null);
  const [query, setQuery] = useState('');
  const [saving, setSaving] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { if (state.data) setItems(state.data.queries); }, [state.data]);

  const move = async (id, status) => {
    setSaving(id);
    setError('');
    try {
      const updated = await updateQuery(id, status);
      setItems((list) => list.map((q) => (q.query_id === id ? updated : q)));
    } catch (err) {
      setError('Could not change this query. Please try again.');
    } finally {
      setSaving(null);
    }
  };

  const wanted = STATUS_SLUGS[filter];
  const needle = query.trim().toLowerCase();
  const rows = (items || []).filter((q) => (!wanted || q.status === wanted)
    && (!needle || [q.query_id, q.name, q.email, q.mobile, q.message, q.status].some((v) => v.toLowerCase().includes(needle))));
  return (
    <PageShell
      search={<SearchBox value={query} onChange={setQuery} placeholder="Search by name, email, mobile or query" label="Search the queries" />}
      state={items ? { ...state, data: items } : state}
      filters={<FilterLinks current={filter || 'all'} items={[['All', '#/queries', 'all'], ['New', '#/queries/new', 'new'], ['In conversation', '#/queries/in-conversation', 'in-conversation'], ['Closed', '#/queries/closed', 'closed']]} />}
    >
      {error && <div className="rounded-lg bg-google-red-light text-google-red px-4 py-3 text-sm">{error}</div>}
      {rows.length === 0 ? <Empty>No queries match.</Empty> : (
        <div className="google-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className={HEAD_ROW}>
                <th className={TH}>Query</th><th className={TH}>Name</th><th className={TH}>Email</th><th className={TH}>Mobile</th><th className={TH}>Question</th><th className={TH}>Received</th><th className={TH}>Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-google-gray-100">
              {rows.map((q) => (
                <tr key={q.query_id} className="align-top">
                  <td className="px-5 py-3 font-semibold text-google-gray-900 whitespace-nowrap">{q.query_id}</td>
                  <td className="px-5 py-3 text-google-gray-900 whitespace-nowrap">{q.name}</td>
                  <td className="px-5 py-3"><a href={`mailto:${q.email}?subject=${encodeURIComponent('Your query to AuraCommerce 360')}`} className="text-google-blue-dark hover:underline [overflow-wrap:anywhere]">{q.email}</a></td>
                  <td className="px-5 py-3 whitespace-nowrap"><a href={`tel:${q.mobile.replace(/[^+0-9]/g, '')}`} className="text-google-blue-dark hover:underline">{q.mobile}</a></td>
                  <td className="px-5 py-3 text-google-gray-900 min-w-[18rem] max-w-md">{q.message}</td>
                  <td className="px-5 py-3 text-google-gray-600 whitespace-nowrap">{formatDay(q.received)}</td>
                  <td className="px-5 py-3 whitespace-nowrap">
                    <select
                      value={q.status}
                      disabled={saving === q.query_id}
                      onChange={(e) => move(q.query_id, e.target.value)}
                      aria-label={`Status of ${q.query_id}`}
                      className={`rounded-full border-0 py-1.5 pl-4 pr-9 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-google-blue/30 ${QUERY_PILLS[q.status] || ''}`}
                    >
                      {QUERY_STATUSES.map((st) => <option key={st} value={st}>{st}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PageShell>
  );
}
