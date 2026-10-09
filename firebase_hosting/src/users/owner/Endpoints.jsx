import React, { useState, useEffect, useMemo } from 'react';
import { Loader2, Search } from 'lucide-react';
import { getConsumerEndpoints, setEndpointEnabled, setServiceEnabled, updateEndpointSettings } from './api';
import { Switch } from './shared';

const FILTERS = [['all', 'All'], ['on', 'Opted'], ['off', 'Not opted']];
const CATEGORIES = [['consumer', 'Consumer'], ['customer', 'Customer'], ['partner', 'Partner'], ['intelligence', 'Intelligence'], ['system', 'System']];

// Why a switch change was refused
const reason = (err) => (err.status === 409
  ? 'MaaS is required while another service is in use. Switch the other services off first.'
  : 'Could not change this. Please try again.');

// What an endpoint takes in: required ones carry a star; with none, it returns its data directly
function Parameters({ parameters }) {
  return (
    <div className="mt-3">
      <div className="text-xs font-semibold uppercase tracking-wider text-google-gray-600 mb-1.5">Parameters</div>
      {!parameters.length ? (
        <p className="text-xs text-google-gray-500">None. Returns the data directly.</p>
      ) : (
        <ul className="flex flex-wrap gap-1.5">
          {parameters.map((p) => (
            <li
              key={p.name}
              title={`${p.required ? 'Required' : 'Optional'} · ${p.type === 'enum' ? p.values.join(' | ') : p.type}`}
              className={`rounded-md px-2 py-0.5 text-xs ${p.required ? 'bg-google-blue-light text-google-blue-dark font-semibold' : 'bg-google-gray-100 text-google-gray-700'}`}
            >
              <span className="font-mono">{p.name}{p.required && '*'}</span>
              <span className="ml-1 opacity-70">{p.type === 'enum' ? 'choice' : p.type}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const usd = (value) => `$${Number(value).toFixed(2)}`;

// One number the Owner can change, with its default to come back to
function SettingField({ label, value, onChange, prefix, suffix, step, invalid, defaultText, ariaLabel }) {
  return (
    <label className="block">
      <span className="block text-xs font-semibold uppercase tracking-wider text-google-gray-600 mb-1.5">{label}</span>
      <div className={`flex items-center rounded-lg border bg-white px-3 ${invalid ? 'border-google-red' : 'border-google-gray-300 focus-within:border-google-blue focus-within:ring-2 focus-within:ring-google-blue/20'}`}>
        {prefix && <span className="text-sm text-google-gray-500 mr-1">{prefix}</span>}
        <input
          type="number"
          inputMode="decimal"
          min="0"
          step={step}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-label={ariaLabel}
          aria-invalid={invalid}
          className="w-full min-w-0 py-2 text-sm font-semibold text-google-gray-900 bg-transparent focus:outline-none"
        />
        {suffix && <span className="text-xs text-google-gray-500 ml-1 whitespace-nowrap">{suffix}</span>}
      </div>
      <span className="block text-xs text-google-gray-500 mt-1">Default {defaultText}</span>
    </label>
  );
}

// An endpoint's rate limit and price for this consumer, editable by the Owner, with what it cost this month
function Settings({ endpoint, limits, busy, onSave }) {
  const saved = {
    rate: String(endpoint.rate_limit_per_min),
    fee: String(endpoint.monthly_fee_usd),
    price: String(endpoint.price_per_1k_calls_usd)
  };
  const [rate, setRate] = useState(saved.rate);
  const [fee, setFee] = useState(saved.fee);
  const [price, setPrice] = useState(saved.price);
  const savedKey = JSON.stringify(saved);
  // follow the saved values (after a save, a reset or a refresh)
  useEffect(() => {
    const now = JSON.parse(savedKey);
    setRate(now.rate); setFee(now.fee); setPrice(now.price);
  }, [savedKey]);

  const within = (text, max, whole) => {
    const n = Number(text);
    return text.trim() !== '' && Number.isFinite(n) && n >= (whole ? 1 : 0) && n <= max && (!whole || Number.isInteger(n));
  };
  const rateOk = within(rate, limits.rate_limit_per_min, true);
  const feeOk = within(fee, limits.monthly_fee_usd);
  const priceOk = within(price, limits.price_per_1k_calls_usd);
  const valid = rateOk && feeOk && priceOk;

  const changes = {};
  if (rateOk && Number(rate) !== endpoint.rate_limit_per_min) changes.rate_limit_per_min = Number(rate);
  if (feeOk && Number(fee) !== endpoint.monthly_fee_usd) changes.monthly_fee_usd = Number(fee);
  if (priceOk && Number(price) !== endpoint.price_per_1k_calls_usd) changes.price_per_1k_calls_usd = Number(price);
  const dirty = Object.keys(changes).length > 0;
  const customised = Object.keys(endpoint.defaults).some((k) => endpoint.defaults[k] !== endpoint[k]);
  const cancel = () => { setRate(saved.rate); setFee(saved.fee); setPrice(saved.price); };

  return (
    <div className="mt-auto border-t border-google-gray-200 pt-3">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <SettingField label="Rate limit" suffix="calls / min" step="1" value={rate} onChange={setRate} invalid={!rateOk} defaultText={endpoint.defaults.rate_limit_per_min.toLocaleString()} ariaLabel={`Rate limit of ${endpoint.path}, calls per minute`} />
        <SettingField label="Monthly fee" prefix="$" step="0.01" value={fee} onChange={setFee} invalid={!feeOk} defaultText={usd(endpoint.defaults.monthly_fee_usd)} ariaLabel={`Monthly fee of ${endpoint.path}, US dollars`} />
        <SettingField label="Per 1,000 calls" prefix="$" step="0.01" value={price} onChange={setPrice} invalid={!priceOk} defaultText={usd(endpoint.defaults.price_per_1k_calls_usd)} ariaLabel={`Price per 1,000 calls of ${endpoint.path}, US dollars`} />
      </div>

      {(dirty || !valid || customised) && (
        <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
          {!valid && <span className="text-google-red">Enter a whole rate limit from 1 to {limits.rate_limit_per_min.toLocaleString()}; prices can have decimals.</span>}
          {dirty && (
            <>
              <button onClick={() => onSave(endpoint.path, changes)} disabled={busy || !valid} className="rounded-lg google-btn-gradient text-white px-4 py-1.5 font-semibold hover:bg-google-blue-dark disabled:opacity-50">Save changes</button>
              <button onClick={cancel} disabled={busy} className="font-semibold text-google-gray-700 hover:underline">Cancel</button>
            </>
          )}
          {!dirty && customised && (
            <>
              <span className="text-google-gray-600">Changed from the defaults</span>
              <button onClick={() => onSave(endpoint.path, { reset: true })} disabled={busy} className="font-semibold text-google-teal hover:underline">Reset to defaults</button>
            </>
          )}
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-google-gray-200 flex justify-between items-baseline gap-3 text-sm">
        <span className="text-google-gray-600">
          {endpoint.enabled ? `${endpoint.calls_this_month.toLocaleString()} calls this month` : 'Not opted, no cost'}
        </span>
        <span className={`font-bold ${endpoint.enabled ? 'text-google-gray-900' : 'text-google-gray-500'}`}>{usd(endpoint.cost_usd)}</span>
      </div>
    </div>
  );
}

// One endpoint as a block: opt in or out at the top right, with its path below
function EndpointBlock({ endpoint, busy, onToggle, consumerName, limits, onSaveSettings }) {
  const needs = endpoint.depends_on.filter((d) => d !== 'maas');
  return (
    <article className={`google-card p-5 flex flex-col ${endpoint.enabled ? '' : 'bg-google-gray-50'}`}>
      <div className="flex items-start justify-between gap-4">
        <h3 className={`font-bold ${endpoint.enabled ? 'text-google-gray-900' : 'text-google-gray-600'}`}>{endpoint.description}</h3>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs font-semibold ${endpoint.enabled ? 'text-google-green' : 'text-google-gray-500'}`}>{endpoint.enabled ? 'Opted' : 'Not opted'}</span>
          <Switch checked={endpoint.enabled} disabled={busy} label={`${endpoint.enabled ? 'Opt out of' : 'Opt in to'} ${endpoint.path} for ${consumerName}`} onChange={(next) => onToggle(endpoint.path, next)} />
        </div>
      </div>
      <p className="mt-2 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded bg-google-gray-100 px-1.5 py-0.5 font-bold text-google-gray-700">{endpoint.method}</span>
        <code className="font-mono text-google-gray-700 break-all">{endpoint.path}</code>
        {needs.map((d) => <span key={d} className="google-pill bg-google-yellow-light text-google-gray-900 ml-auto">Needs {d}</span>)}
      </p>
      <div className="flex-1 pb-3"><Parameters parameters={endpoint.parameters} /></div>
      <Settings endpoint={endpoint} limits={limits} busy={busy} onSave={onSaveSettings} />
    </article>
  );
}

// The endpoints of one service for one consumer, grouped by feature, each opted in or out on its own
export default function EndpointsSection({ tenantId, service, consumerName, onChanged }) {
  const [listing, setListing] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [category, setCategory] = useState('consumer');

  useEffect(() => {
    let cancelled = false;
    setListing(null);
    setError('');
    getConsumerEndpoints(tenantId, service)
      .then((data) => { if (!cancelled) setListing(data); })
      .catch(() => { if (!cancelled) setError('Could not load the endpoints. Please try again.'); });
    return () => { cancelled = true; };
  }, [tenantId, service]);

  const change = async (call) => {
    setBusy(true);
    setError('');
    try {
      setListing(await call());
      onChanged?.();
    } catch (err) {
      setError(reason(err));
    } finally {
      setBusy(false);
    }
  };
  const toggleEndpoint = (path, enabled) => change(() => setEndpointEnabled(tenantId, path, enabled));
  const saveSettings = (path, changes) => change(() => updateEndpointSettings(tenantId, path, changes));
  const toggleService = (enabled) => change(() => setServiceEnabled(tenantId, service, enabled));

  const needle = query.trim().toLowerCase();
  const rows = useMemo(() => (listing ? listing.endpoints
    .filter((e) => e.category === category
      && (filter === 'all' || (filter === 'on' && e.enabled) || (filter === 'off' && !e.enabled))
      && (!needle || [e.path, e.description, e.actor, e.feature].some((v) => v.toLowerCase().includes(needle)))) : []),
  [listing, filter, category, needle]);

  const s = listing?.summary;
  return (
    <section>
      <h2 className="text-lg font-semibold text-google-teal-dark">Endpoints</h2>
      <p className="text-sm text-google-gray-500 mt-0.5 mb-4 max-w-3xl">
        Each endpoint is one event, one actor, one permission. Opt this consumer in or out of them one by one, and set each one's rate limit and price (* marks a required parameter; the consumer and caller come from the sign-in, not from parameters){service !== 'MaaS' && ', or the whole service (MaaS comes with it)'}.
      </p>

      {error && <div role="alert" className="mb-4 rounded-xl bg-google-red-light text-google-red px-4 py-3 text-sm">{error}</div>}
      {!listing && !error && <div className="flex items-center gap-2 text-sm text-google-gray-600"><Loader2 className="h-4 w-4 animate-spin" /> Loading...</div>}

      {listing && (
        <div className="space-y-4">
          <div className="google-card p-5 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-google-gray-600">{service} for {consumerName}</div>
              <div className="text-2xl font-bold text-google-teal-dark mt-1">
                {s.on} <span className="text-base font-normal text-google-gray-600">of {s.total} endpoints opted</span>
              </div>
              <div className="text-sm text-google-gray-600 mt-1">{listing.service_figures.calls.toLocaleString()} calls this month, <span className="font-bold text-google-gray-900">{usd(listing.service_figures.cost_usd)}</span></div>
            </div>
            <div className="flex items-center gap-3">
              {busy && <Loader2 className="h-4 w-4 animate-spin text-google-gray-500" />}
              <span className={`text-sm font-semibold ${s.opted ? 'text-google-green' : 'text-google-gray-500'}`}>{s.opted ? 'Service opted' : 'Not opted'}</span>
              <Switch checked={s.opted} disabled={busy} label={`${s.opted ? 'Opt out of' : 'Opt in to'} ${service} for ${consumerName}`} onChange={toggleService} />
            </div>
          </div>

          <div className="flex flex-wrap gap-1 border-b border-google-gray-200" role="tablist" aria-label="Endpoint categories">
            {CATEGORIES.map(([key, label]) => {
              const count = listing.endpoints.filter((e) => e.category === key).length;
              return (
                <button
                  key={key}
                  type="button"
                  role="tab"
                  aria-selected={category === key}
                  onClick={() => setCategory(key)}
                  className={`-mb-px border-b-2 px-4 py-2 text-sm font-semibold ${category === key ? 'border-google-blue text-google-teal' : 'border-transparent text-google-gray-600 hover:text-google-gray-900'}`}
                >
                  {label} <span className="ml-1 text-xs font-normal text-google-gray-500">{count}</span>
                </button>
              );
            })}
          </div>

          <div className="flex flex-col gap-3 rounded-xl border border-google-gray-200 bg-white p-3 shadow-sm md:flex-row md:items-center md:justify-between">
            <div className="relative w-full md:max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-google-gray-400" />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by path, feature, actor or description"
                aria-label={`Search the ${service} endpoints`}
                className="w-full rounded-lg border border-google-gray-300 bg-white py-2 pl-9 pr-3 text-sm focus:border-google-blue focus:outline-none focus:ring-2 focus:ring-google-blue/20"
              />
            </div>
            <div className="inline-flex gap-1 self-start rounded-lg bg-google-gray-100 p-1 md:self-auto" role="group" aria-label="Filter the endpoints">
              {FILTERS.map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setFilter(key)}
                  aria-pressed={filter === key}
                  className={`rounded-lg px-3 py-1 text-sm font-semibold ${filter === key ? 'bg-white text-google-teal-dark shadow-sm' : 'text-google-gray-600 hover:text-google-gray-900'}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {rows.length === 0 ? (
            <div className="google-card p-8 text-center text-sm text-google-gray-600">No endpoints match.</div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              {rows.map((e) => <EndpointBlock key={e.path} endpoint={e} busy={busy} onToggle={toggleEndpoint} consumerName={consumerName} limits={listing.limits} onSaveSettings={saveSettings} />)}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
