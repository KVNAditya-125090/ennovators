import React, { useState, useEffect, useMemo } from 'react';
import { Server, TrendingUp, LifeBuoy, Activity, CheckCircle, Users, AlertCircle, Loader2, ChevronRight, ArrowLeft, Search, ArrowUp, ArrowDown, ArrowUpDown, X } from 'lucide-react';
import Analytics from './Analytics';
import { getOverview, getConsumer } from './api';
import { ApisPage, TelemetryPage, QueriesPage, PageTitle } from './Pages';
import { PRIORITY_PILLS, QUERY_STATUS_PILLS } from './shared';
import EndpointsSection from './Endpoints';
import OperationsPage from './Operations';
import { href, navigate, restSegments, usePath } from '../../router';

const usd = (value) => `$${Number(value).toFixed(2)}`;

// The console is a set of sections, each with its own address under /owner/<role>/maas:
//   dashboard[/<card>]            health, budget, consumers, revenue or queries
//   consumers                     the list
//   consumers/<id>                one consumer, Details tab
//   consumers/<id>/services       one consumer, Services tab
//   consumers/<id>/tickets        one consumer, Tickets tab (add /opened or /closed for one kind)
//   consumers/<id>/<service>      one service of that consumer (maas, paas, taas or saas)
//   monitor[/<service>]           every API on the platform and how it is responding
//   telemetry[/errors|warnings]   the logs of the Google Cloud services behind the platform
//   queries[/new|in-conversation|closed]   the questions visitors send from the home page
//   operations[/<tab>]            the Owner's own catalog features (onboarding, tickets, partners, team, developer, audit, account)
const SERVICE_CODES = ['MaaS', 'PaaS', 'TaaS', 'SaaS'];
export const serviceCode = (value) => SERVICE_CODES.find((c) => c.toLowerCase() === String(value ?? '').toLowerCase()) ?? null;
const CARD_METRICS = { health: 'health', budget: 'hosting', consumers: 'consumers', revenue: 'revenue', queries: 'support' };
const METRIC_CARDS = Object.fromEntries(Object.entries(CARD_METRICS).map(([card, metric]) => [metric, card]));
const readRoute = () => {
  const [, section = '', a, b, c] = restSegments();
  if (section === 'consumers') {
    return {
      section, id: a || null, service: serviceCode(b),
      tab: b === 'services' ? 'services' : b === 'tickets' || b === 'queries' ? 'tickets' : 'details',
      ticketFilter: c === 'opened' || c === 'closed' ? c : null
    };
  }
  if (['monitor', 'telemetry', 'queries', 'operations'].includes(section)) return { section, id: null, service: null, tab: 'details', filter: a || null, filter2: b || null };
  return { section: 'dashboard', id: null, service: null, tab: 'details', metric: CARD_METRICS[a] || null };
};
const listHref = () => href('maas/consumers');
const pageHash = (tenantId) => href(`maas/consumers/${encodeURIComponent(tenantId)}`);
const servicePageHash = (tenantId, code) => `${pageHash(tenantId)}/${code.toLowerCase()}`;
const ticketsTabHash = (tenantId) => `${pageHash(tenantId)}/tickets`;
const servicesTabHash = (tenantId) => `${pageHash(tenantId)}/services`;

const SERVICE_STYLES = {
  MaaS: { label: 'Management', title: 'Management as a Service', badge: 'bg-google-red-light text-google-red', ring: 'ring-google-red' },
  PaaS: { label: 'Product', title: 'Product as a Service', badge: 'bg-google-blue-light text-google-blue-dark', ring: 'ring-google-blue' },
  TaaS: { label: 'Transport', title: 'Transport as a Service', badge: 'bg-google-green-light text-[#137333]', ring: 'ring-google-green' },
  SaaS: { label: 'Support', title: 'Support as a Service', badge: 'bg-google-yellow-light text-[#B06000]', ring: 'ring-google-yellow' }
};

function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div role="alert" className="flex items-center gap-2 rounded-xl bg-google-red-light text-google-red px-4 py-3 text-sm">
      <AlertCircle className="h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

const COLUMNS = [
  { key: 'name', label: 'Consumer', align: 'left', className: 'px-6 py-3' },
  { key: 'status', label: 'Status', align: 'left', className: 'px-4 py-3' },
  { key: 'opted_services', label: 'Opted services', align: 'left', className: 'px-4 py-3' },
  { key: 'enabled_apis', label: 'Endpoints on', align: 'right', className: 'px-4 py-3' },
  { key: 'monthly_cost_usd', label: 'Cost this month', align: 'right', className: 'px-4 py-3' }
];

const selectClass = 'rounded-lg border border-google-gray-300 bg-white px-3 py-2 text-sm text-google-gray-900 focus:outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue/20';

// The consumers table: search, filters and sortable columns
function ConsumersTable({ consumers }) {
  const [query, setQuery] = useState('');
  const [service, setService] = useState('All');
  const [status, setStatus] = useState('All');
  const [sortKey, setSortKey] = useState('name');
  const [sortDir, setSortDir] = useState('asc');

  const statuses = useMemo(() => [...new Set(consumers.map((c) => c.status))].sort(), [consumers]);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = consumers.filter(
      (c) =>
        (service === 'All' || c.opted_services.includes(service)) &&
        (status === 'All' || c.status === status) &&
        (!q || c.name.toLowerCase().includes(q) || c.tenant_id.toLowerCase().includes(q))
    );
    const direction = sortDir === 'asc' ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const x = sortKey === 'opted_services' ? a.opted_services.length : a[sortKey];
      const y = sortKey === 'opted_services' ? b.opted_services.length : b[sortKey];
      const result = typeof x === 'number' ? x - y : String(x).localeCompare(String(y));
      return result * direction || a.name.localeCompare(b.name);
    });
  }, [consumers, query, service, status, sortKey, sortDir]);

  const filtersActive = query !== '' || service !== 'All' || status !== 'All';
  const clearFilters = () => { setQuery(''); setService('All'); setStatus('All'); };
  const sortBy = (key) => {
    if (key === sortKey) setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir(typeof consumers[0]?.[key] === 'number' || key === 'opted_services' ? 'desc' : 'asc'); }
  };

  return (
    <div className="space-y-3">
      {/* Search on the left, filters on the right, on their own bar */}
      <div className="flex flex-col gap-3 rounded-xl border border-google-gray-200 bg-white p-3 shadow-sm md:flex-row md:items-center md:justify-between">
        <div className="relative w-full md:max-w-md">
            <Search className="h-4 w-4 text-google-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name or ID"
              aria-label="Search consumers"
              className={`${selectClass} w-full pl-9`}
            />
        </div>
        <div className="flex flex-wrap items-center gap-3 md:justify-end">
          <label className="flex items-center gap-2 text-sm text-google-gray-700">
            <span>Opted services</span>
            <select value={service} onChange={(e) => setService(e.target.value)} className={selectClass}>
              <option value="All">All services</option>
              {Object.entries(SERVICE_STYLES).map(([code, meta]) => <option key={code} value={code}>{code} · {meta.label}</option>)}
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm text-google-gray-700">
            <span>Status</span>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className={selectClass}>
              <option value="All">All statuses</option>
              {statuses.map((st) => <option key={st} value={st}>{st}</option>)}
            </select>
          </label>
          {filtersActive && (
            <button onClick={clearFilters} className="inline-flex items-center gap-1.5 text-sm font-semibold text-google-teal hover:underline">
              <X className="h-4 w-4" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>
      <span className="sr-only" aria-live="polite">{rows.length} of {consumers.length} consumers shown</span>

      <div className="google-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-google-gray-50 text-xs font-semibold uppercase tracking-wider text-google-gray-600">
              {COLUMNS.map((col) => {
                const active = col.key === sortKey;
                const Icon = !active ? ArrowUpDown : sortDir === 'asc' ? ArrowUp : ArrowDown;
                return (
                  <th
                    key={col.key}
                    scope="col"
                    aria-sort={active ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                    className={`${col.className} ${col.align === 'right' ? 'text-right' : 'text-left'}`}
                  >
                    <button
                      onClick={() => sortBy(col.key)}
                      className={`inline-flex items-center gap-1.5 uppercase tracking-wider font-semibold hover:text-google-gray-900 ${active ? 'text-google-teal' : ''}`}
                    >
                      <span>{col.label}</span>
                      <Icon className={`h-3.5 w-3.5 ${active ? '' : 'opacity-50'}`} />
                    </button>
                  </th>
                );
              })}
              <th scope="col" className="px-6 py-3"><span className="sr-only">Open</span></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-google-gray-200">
            {rows.map((c) => (
              <tr
                key={c.tenant_id}
                onClick={() => navigate(pageHash(c.tenant_id))}
                className="cursor-pointer hover:bg-google-blue-light/40 transition-colors"
              >
                <td className="px-6 py-4">
                  <a href={pageHash(c.tenant_id)} onClick={(e) => e.stopPropagation()} className="font-semibold text-google-gray-900 hover:text-google-teal-dark">
                    {c.name}
                  </a>
                  <div className="text-xs text-google-gray-500">{c.tenant_id}</div>
                </td>
                <td className="px-4 py-4"><span className="google-pill bg-google-green-light text-google-green">{c.status}</span></td>
                <td className="px-4 py-4">
                  <div className="flex flex-wrap gap-1.5">
                    {c.opted_services.length
                      ? c.opted_services.map((code) => <span key={code} className={`google-pill ${SERVICE_STYLES[code].badge}`}>{code}</span>)
                      : <span className="text-google-gray-500">None</span>}
                  </div>
                </td>
                <td className="px-4 py-4 text-right text-google-gray-900">{c.enabled_apis} of {c.total_apis}</td>
                <td className="px-4 py-4 text-right font-bold text-google-gray-900">{usd(c.monthly_cost_usd)}</td>
                <td className="px-6 py-4 text-right text-google-gray-400"><ChevronRight className="h-4 w-4 inline" /></td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-10 text-center text-google-gray-600">
                  <div>No consumers match your search or filters.</div>
                  <button onClick={clearFilters} className="mt-2 text-sm font-semibold text-google-teal hover:underline">Clear filters</button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      </div>
    </div>
  );
}

// A top card. The selected card decides which metric's history Analytics shows.
function MetricCard({ id, active, onSelect, label, icon: Icon, iconClass, children }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(id)}
      aria-pressed={active}
      className={`google-card p-5 text-left w-full flex flex-col justify-start transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-google-blue ${active ? 'ring-2 ring-google-blue' : ''}`}
    >
      <div className="flex justify-between items-center text-google-gray-600 mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider">{label}</span>
        <Icon className={`h-4 w-4 ${iconClass}`} />
      </div>
      {children}
    </button>
  );
}

// List page: metrics and the table of consumers
function DashboardPage({ budget, health, consumers, totalCost, support, metric, onSelectMetric }) {
  return (
    <div className="space-y-4">
      <PageTitle title="Dashboard" subtitle="Platform health, cost, consumers, revenue and visitor questions" />
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
        <MetricCard id="health" active={metric === 'health'} onSelect={onSelectMetric} label="Health" icon={Activity} iconClass="text-google-green">
          {(() => {
            // live, from the calls the gate handled: the share of built endpoints that are working
            const built = health ? health.endpoints_total - health.endpoints_not_built : 0;
            const share = built ? Math.round((health.endpoints_working / built) * 1000) / 10 : 0;
            const tone = !health ? 'text-google-teal-dark' : health.endpoints_failing ? 'text-google-red' : health.endpoints_slow ? 'text-google-teal-dark' : 'text-google-green';
            const icon = !health ? '' : health.endpoints_failing ? 'text-google-red' : health.endpoints_slow ? 'text-google-yellow' : '';
            return (
              <>
                <div className={`text-2xl font-bold flex items-center gap-2 ${tone}`}>
                  <CheckCircle className={`h-5 w-5 ${icon}`} />
                  <span>{health ? `${share}%` : 'Checking...'}</span>
                </div>
                <p className="text-xs text-google-gray-600 mt-1">
                  {health ? `${health.endpoints_working} of ${built} built endpoints working` : 'Working endpoints'}
                </p>
                {health && (
                  <p className="text-xs mt-0.5">
                    {health.endpoints_failing > 0 && <span className="font-semibold text-google-red">{health.endpoints_failing} failing · </span>}
                    {health.endpoints_slow > 0 && <span className="font-semibold text-[#B06000]">{health.endpoints_slow} slow · </span>}
                    <span className="text-google-gray-500">{health.endpoints_not_built} not built yet{health.success_rate_24h !== null ? ` · ${health.success_rate_24h}% of calls OK (24 h)` : ''}</span>
                  </p>
                )}
              </>
            );
          })()}
        </MetricCard>

        <MetricCard id="hosting" active={metric === 'hosting'} onSelect={onSelectMetric} label="Budget" icon={Server} iconClass="text-google-teal">
          <div className="text-2xl font-bold text-google-teal-dark">{budget ? usd(budget.spent_to_date_usd) : '-'}</div>
          <p className="text-xs text-google-gray-600 mt-1">Cost to run the platform</p>
        </MetricCard>

        <MetricCard id="consumers" active={metric === 'consumers'} onSelect={onSelectMetric} label="Consumers" icon={Users} iconClass="text-google-teal">
          <div className="text-2xl font-bold text-google-teal-dark">{consumers.length}</div>
          <p className="text-xs text-google-gray-600 mt-1">Consumption of services</p>
        </MetricCard>

        <MetricCard id="revenue" active={metric === 'revenue'} onSelect={onSelectMetric} label="Revenue" icon={TrendingUp} iconClass="text-google-green">
          <div className="text-2xl font-bold text-google-teal-dark">{usd(totalCost)}</div>
          <p className="text-xs text-google-gray-600 mt-1">Generated by consumers this month</p>
        </MetricCard>

        <MetricCard id="support" active={metric === 'support'} onSelect={onSelectMetric} label="Queries" icon={LifeBuoy} iconClass="text-google-yellow">
          <div className="text-2xl font-bold text-google-teal-dark">{support ? support.open : '-'}</div>
          <p className="text-xs text-google-gray-600 mt-1">Open questions from visitors</p>
        </MetricCard>
      </div>

      <Analytics metric={metric} />
    </div>
  );
}

function ConsumersListPage({ consumers }) {
  return (
    <div className="space-y-4">
      <PageTitle title="Consumers" subtitle="The companies using the platform, the services they opted into and what they cost" />
      <ConsumersTable consumers={consumers} />
    </div>
  );
}

const AVATAR_COLORS = ['#4285F4', '#EA4335', '#F9AB00', '#34A853'];
const initials = (name) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join('');
const avatarColor = (id) => AVATAR_COLORS[[...id].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % AVATAR_COLORS.length];

const formatDate = (iso) => new Date(`${iso}T00:00:00Z`).toLocaleDateString('en', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
const PAYMENT_PILLS = {
  Paid: 'bg-google-green-light text-google-green',
  Due: 'bg-google-yellow-light text-[#B06000]',
  Overdue: 'bg-google-red-light text-google-red'
};

const FACTS_ALIGN = { left: 'text-left', center: 'text-center', right: 'text-right' };

function Facts({ title, rows, align = 'left' }) {
  return (
    <div className={FACTS_ALIGN[align]}>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-google-gray-600 mb-3">{title}</h3>
      <dl className="space-y-3">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs text-google-gray-500">{label}</dt>
            <dd className="text-sm font-medium text-google-gray-900 break-words">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

// The account this page is about: avatar, name, id and member-since date
function AccountHeader({ detail }) {
  const c = detail.consumer;
  return (
    <div className="flex items-center gap-4">
      <div
        className="h-12 w-12 shrink-0 rounded-xl flex items-center justify-center text-white text-base font-bold"
        style={{ backgroundColor: avatarColor(c.tenant_id) }}
        aria-hidden="true"
      >
        {initials(c.name)}
      </div>
      <div>
        <h1 className="text-2xl font-semibold text-google-teal-dark leading-tight">{c.name}</h1>
        <div className="text-sm text-google-gray-600">
          {c.tenant_id}
        </div>
      </div>
      <div className="ml-auto text-right">
        <div className="flex items-center justify-end gap-2">
          <span className="text-xs text-google-gray-500">Account status</span>
          <span className={`google-pill ${c.status === 'Active' ? 'bg-google-green-light text-google-green' : 'bg-google-gray-100 text-google-gray-600'}`}>{c.status}</span>
        </div>
        {detail.profile && <div className="text-sm text-google-gray-600 mt-1.5">Member since <span className="font-semibold text-google-gray-900">{detail.profile.company.joined}</span></div>}
      </div>
    </div>
  );
}

// A consumer's profile: who they are, what they use and what it costs
function ProfileCard({ detail }) {
  const c = detail.consumer;
  return (
    <div className="space-y-6">
        {detail.profile && (
          <section className="google-card p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-x-8 gap-y-6">
            <Facts align="left" title="Company" rows={[
              ['Legal name', detail.profile.company.legal_name],
              ['Industry', detail.profile.company.industry],
              ['Address', detail.profile.company.address],
              ['Website', detail.profile.company.website]
            ]} />
            <Facts align="center" title="Contact" rows={[
              ['Name', detail.profile.contact.name],
              ['Role', detail.profile.contact.title],
              ['Department', detail.profile.contact.department],
              ['Mobile number', detail.profile.contact.phone],
              ['Email', <a key="mail" href={`mailto:${detail.profile.contact.email}`} className="text-google-teal hover:underline [overflow-wrap:anywhere]">{detail.profile.contact.email}</a>],
              ['Working hours', detail.profile.contact.working_hours]
            ]} />
            <Facts align="right" title="Billing" rows={[
              ['Plan', detail.profile.billing.plan],
              ['Billing cycle', detail.profile.billing.billing_cycle],
              ['Payment status', <span key="pay" className={`google-pill ${PAYMENT_PILLS[detail.profile.billing.payment_status] || ''}`}>{detail.profile.billing.payment_status}</span>],
              ['Next invoice', formatDate(detail.profile.billing.next_invoice)]
            ]} />
          </div>
          </section>
        )}

        {/* A fixed template: the same slots, in the same places, for every consumer */}
        <section className="google-card p-6 space-y-4 text-center">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-google-gray-600 mb-2">Opted services</div>
            <div className="flex flex-wrap justify-center gap-4">
              {SERVICE_CODES.map((code) => {
                const opted = c.opted_services.includes(code);
                return (
                  <span
                    key={code}
                    title={opted ? `Opted for ${SERVICE_STYLES[code].title}` : `Not opted for ${SERVICE_STYLES[code].title}`}
                    className={`google-pill ${opted ? SERVICE_STYLES[code].badge : 'bg-google-gray-100 text-google-gray-500'}`}
                  >
                    {code} · {SERVICE_STYLES[code].label}
                  </span>
                );
              })}
            </div>
          </div>
          <div className="flex flex-wrap justify-center gap-x-20 gap-y-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-google-gray-600 mb-1">Endpoints opted</div>
            <div className="text-2xl font-bold text-google-teal-dark">{c.enabled_apis} <span className="text-base font-normal text-google-gray-600">of {c.total_apis}</span></div>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-google-gray-600 mb-1">Cost this month</div>
            <div className="text-2xl font-bold text-google-teal-dark">{usd(detail.monthly_cost_usd)}</div>
          </div>
          </div>
        </section>
    </div>
  );
}

// What a service costs and how much of it a consumer uses
function groupByService(detail) {
  return Object.keys(SERVICE_STYLES).map((code) => {
    return { code, endpoints: detail.endpoint_services.find((e) => e.code === code) };
  });
}

// One consumer's own page: its details, then its services. Each service opens on a page of its own.

// The queries one consumer has raised with the platform team
function QueriesTab({ queries, empty = 'This consumer has not raised any tickets.' }) {
  if (!queries.length) {
    return <div className="google-card p-8 text-center text-sm text-google-gray-600">{empty}</div>;
  }
  return (
    <div className="google-card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wider text-google-gray-600 border-b border-google-gray-200">
            <th className="px-5 py-3 font-semibold">Ticket</th>
            <th className="px-5 py-3 font-semibold">Subject</th>
            <th className="px-5 py-3 font-semibold">Priority</th>
            <th className="px-5 py-3 font-semibold">Status</th>
            <th className="px-5 py-3 font-semibold">Raised</th>
            <th className="px-5 py-3 font-semibold text-right">First response</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-google-gray-100">
          {queries.map((q) => (
            <tr key={q.ticket_id}>
              <td className="px-5 py-3 font-semibold text-google-gray-900">{q.ticket_id}</td>
              <td className="px-5 py-3 text-google-gray-900">{q.subject}</td>
              <td className="px-5 py-3"><span className={`google-pill ${PRIORITY_PILLS[q.priority] || ''}`}>{q.priority}</span></td>
              <td className="px-5 py-3"><span className={`google-pill ${QUERY_STATUS_PILLS[q.status] || ''}`}>{q.status}</span></td>
              <td className="px-5 py-3 text-google-gray-600 whitespace-nowrap">{formatDate(q.opened)}</td>
              <td className="px-5 py-3 text-right text-google-gray-600 whitespace-nowrap">{q.first_response_hours === null ? 'Waiting' : `${q.first_response_hours} h`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ServiceCards({ detail }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {groupByService(detail).map((g) => {
        const meta = SERVICE_STYLES[g.code];
        return (
          <a
            key={g.code}
            href={servicePageHash(detail.consumer.tenant_id, g.code)}
            className="google-card p-5 block transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-google-blue"
          >
            <div className="flex justify-between items-center mb-3">
              <span className={`google-pill ${meta.badge}`}>{g.code}</span>
              <span className={`text-xs font-semibold ${g.endpoints.opted ? 'text-google-green' : 'text-google-gray-500'}`}>{g.endpoints.opted ? 'Opted' : 'Not opted'}</span>
            </div>
            <div className="font-bold text-google-gray-900">{meta.title}</div>
            <div className="text-sm text-google-gray-600 mt-1">{g.endpoints.on} of {g.endpoints.total} endpoints opted</div>
            <div className="flex justify-between items-end mt-3">
              <div className="text-lg font-bold text-google-gray-900">{usd(g.endpoints.cost_usd)}<span className="text-xs font-normal text-google-gray-500"> this month</span></div>
              <ChevronRight className="h-4 w-4 text-google-gray-400" />
            </div>
          </a>
        );
      })}
    </div>
  );
}

// Tickets in two kinds. Each is a link to the tickets of that kind.
function TicketCategories({ detail }) {
  const id = detail.consumer.tenant_id;
  const opened = detail.tickets.filter((q) => q.status !== 'Resolved').length;
  const closed = detail.tickets.length - opened;
  const kinds = [
    { key: 'opened', label: 'Opened', count: opened },
    { key: 'closed', label: 'Closed', count: closed }
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {kinds.map((k) => (
        <a
          key={k.key}
          href={`${ticketsTabHash(id)}/${k.key}`}
          className="google-card px-5 py-4 text-center block transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-google-blue"
        >
          <div className="text-xs font-semibold uppercase tracking-wider text-google-gray-600">{k.label}</div>
          <div className="text-2xl font-bold text-google-teal-dark mt-1">{k.count}</div>
        </a>
      ))}
    </div>
  );
}

function ConsumerPage({ detail, loading, error, tab, ticketFilter }) {
  return (
    <div className="space-y-6">
      <a href={listHref()} className="inline-flex items-center gap-2 text-sm font-semibold text-google-teal hover:underline">
        <ArrowLeft className="h-4 w-4" />
        <span>Consumers</span>
      </a>

      <ErrorBanner message={error} />

      {!detail && loading && (
        <div className="flex items-center gap-2 text-sm text-google-gray-600"><Loader2 className="h-4 w-4 animate-spin" /> Loading...</div>
      )}

      {detail && (
        <div className="space-y-6">
          <AccountHeader detail={detail} />

          {/* The Details page carries everything about the consumer; Services and Tickets also open on their own */}
          {tab === 'details' && (
            <div className="space-y-8">
              <section>
                <h2 className="text-center text-lg font-semibold text-google-teal-dark mb-4">Details</h2>
                <ProfileCard detail={detail} />
              </section>
              <section>
                <h2 className="text-center text-lg font-semibold text-google-teal-dark mb-4">Services</h2>
                <ServiceCards detail={detail} />
              </section>
              <section>
                <h2 className="text-center text-lg font-semibold text-google-teal-dark mb-4">Tickets</h2>
                <TicketCategories detail={detail} />
              </section>
            </div>
          )}

          {tab === 'services' && <ServiceCards detail={detail} />}

          {/* choosing Opened or Closed on the Details page lands here: just the tickets of that kind */}
          {tab === 'tickets' && (
            <QueriesTab
              queries={detail.tickets.filter((q) => !ticketFilter || (ticketFilter === 'closed') === (q.status === 'Resolved'))}
              empty={ticketFilter ? `No ${ticketFilter} tickets.` : undefined}
            />
          )}
        </div>
      )}
    </div>
  );
}

// One service of one consumer, on its own page: the APIs it includes, each with an on/off switch
function ServicePage({ tenantId, service, detail, loading, error, onEndpointsChanged }) {
  const group = detail ? groupByService(detail).find((g) => g.code === service) : null;
  const meta = SERVICE_STYLES[service];

  return (
    <div className="space-y-6">
      <a href={servicesTabHash(tenantId)} className="inline-flex items-center gap-2 text-sm font-semibold text-google-teal hover:underline">
        <ArrowLeft className="h-4 w-4" />
        <span>Console</span>
      </a>

      <ErrorBanner message={error} />

      {!detail && loading && (
        <div className="flex items-center gap-2 text-sm text-google-gray-600"><Loader2 className="h-4 w-4 animate-spin" /> Loading...</div>
      )}

      {detail && group && (
        <div className="space-y-6">
          <AccountHeader detail={detail} />

          <div className="google-card p-6 flex flex-wrap justify-between items-start gap-4">
            <div>
              <div className="flex items-center gap-3">
                <span className={`google-pill ${meta.badge}`}>{service}</span>
                <h2 className="text-2xl font-semibold text-google-teal-dark">{meta.title}</h2>
              </div>
            </div>
          </div>

          <EndpointsSection tenantId={tenantId} service={service} consumerName={detail.consumer.name} onChanged={onEndpointsChanged} />
        </div>
      )}
    </div>
  );
}

export default function OwnerView() {
  const [budget, setBudget] = useState(null);
  const [health, setHealth] = useState(null);
  const [consumers, setConsumers] = useState([]);
  const [route, setRoute] = useState(readRoute);
  const selectedId = route.section === 'consumers' ? route.id : null;
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState('');
  const [support, setSupport] = useState(null);
  const [metric, setMetric] = useState('health');

  useEffect(() => {
    getOverview()
      .then((overview) => {
        setBudget(overview.budget);
        setHealth(overview.health);
        setConsumers(overview.consumers);
        setSupport(overview.support);
      })
      .catch(() => setError('Could not load the dashboard. Please try again.'));
  }, []);

  // a dashboard card chosen from the top menu
  useEffect(() => { if (route.metric) setMetric(route.metric); }, [route.metric]);

  // keep the page in step with the address, so the browser's Back button works
  const path = usePath();
  useEffect(() => { setRoute(readRoute()); }, [path]);

  useEffect(() => {
    setDetail(null);
    setError('');
    if (!selectedId) return undefined;
    let cancelled = false;
    setDetailLoading(true);
    getConsumer(selectedId)
      .then((data) => { if (!cancelled) setDetail(data); })
      .catch((err) => { if (!cancelled) setError(err.status === 404 ? 'This consumer does not exist.' : 'Could not load this consumer. Please try again.'); })
      .finally(() => { if (!cancelled) setDetailLoading(false); });
    return () => { cancelled = true; };
  }, [selectedId]);

  // every page starts at the top
  useEffect(() => { document.getElementById('app-scroll')?.scrollTo(0, 0); }, [route.section, route.id, route.service, route.filter, route.filter2]);

  // the consumer's own figures follow an endpoint change, without a loading screen
  const refreshDetail = () => {
    getConsumer(selectedId)
      .then((data) => {
        setDetail(data);
        setConsumers((list) => list.map((c) => (c.tenant_id === selectedId ? data.consumer : c)));
      })
      .catch(() => {});
  };

  const totalCost = consumers.reduce((sum, c) => sum + c.monthly_cost_usd, 0);

  if (selectedId && route.service) {
    return <ServicePage tenantId={selectedId} service={route.service} detail={detail} loading={detailLoading} error={error} onEndpointsChanged={refreshDetail} />;
  }

  if (selectedId) {
    return <ConsumerPage detail={detail} loading={detailLoading} error={error} tab={route.tab} ticketFilter={route.ticketFilter} />;
  }

  if (route.section === 'monitor') return <ApisPage service={serviceCode(route.filter)} />;
  if (route.section === 'telemetry') return <TelemetryPage level={route.filter} />;
  if (route.section === 'queries') return <QueriesPage filter={route.filter} />;
  if (route.section === 'operations') return <OperationsPage tab={route.filter} />;

  if (route.section === 'consumers') {
    return (
      <div className="space-y-6">
        <ErrorBanner message={error} />
        <ConsumersListPage consumers={consumers} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ErrorBanner message={error} />
      <DashboardPage budget={budget} health={health} consumers={consumers} totalCost={totalCost} support={support} metric={metric} onSelectMetric={(m) => { setMetric(m); navigate(href(`maas/dashboard/${METRIC_CARDS[m]}`), { replace: true }); }} />
    </div>
  );
}
