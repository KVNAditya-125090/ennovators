import React, { useState, useEffect } from 'react';
import { Layers, Activity, Wallet, CalendarDays, Banknote, TrendingUp, TrendingDown } from 'lucide-react';
import RolesAndTeam from './RolesAndTeam';
import Customize from './Customize';
import { useAllowedPages, useCurrentPage, availablePages, pageForPath, SERVICES } from './consumerPages';
import { useViewState, activeView } from './consumerViews';
import { useConsumer, useLoad, useAction, Section, Empty, ErrorNote, PageHeader, Kpi, Kpis, Bar, Pill, Pager, SERVICE_LOOK, DataTable, SearchBox, Btn, FIELD, money } from './ui';
import { PageExtras } from './MoreFeatures';
import { href } from '../../router';

const SETTINGS_FIELDS = [
  { name: 'company_name', label: 'Company name' },
  { name: 'contact_mail', label: 'Contact mail', type: 'email' },
  { name: 'timezone', label: 'Time zone' },
  { name: 'default_language', label: 'Default language' },
  { name: 'default_currency', label: 'Default currency' }
];
const SERVICE_NAMES = { MaaS: 'Management', PaaS: 'Product', TaaS: 'Transport', SaaS: 'Support' };
const SERVICE_TONES = { MaaS: 'blue', PaaS: 'green', TaaS: 'yellow', SaaS: 'red' };

function Overview() {
  const dashboard = useLoad('/maas/analytics/dashboard/read/v1');
  const account = useLoad('/maas/root-account/read/v1');
  const usage = useLoad('/maas/analytics/usage/read/v1');
  const d = dashboard.data;
  const a = account.data;
  const top = (usage.data?.usage ?? []).slice(0, 5);
  const topPeak = top[0]?.calls || 1;
  const callPeak = Math.max(1, ...(d?.services ?? []).map((s) => s.calls));
  const { can } = useConsumer();
  const view = activeView(useViewState());
  // the jobs this person does most, limited to the pages they can open
  const seen = new Set();
  const quick = (usage.data?.usage ?? []).reduce((list, u) => {
    const target = pageForPath(u.path);
    if (!target || list.length >= 6) return list;
    const page = availablePages(target.service, can, view).find((p) => p.key === target.page);
    if (!page || seen.has(`${target.service}/${target.page}`)) return list;
    seen.add(`${target.service}/${target.page}`);
    return [...list, { ...target, label: page.label, title: u.description, serviceLabel: SERVICES.find((x) => x.key === target.service).label }];
  }, []);
  return (
    <div>
      <PageHeader title="Overview" subtitle="Your workspace at a glance" />
      <ErrorNote error={dashboard.error || account.error || usage.error} />

      {/* 1. Who you are */}
      {a && (
        <section className="google-card p-5 mb-3">
          <div className="grid gap-x-10 gap-y-6 md:grid-cols-3">
            {[
              ['Company', [['Legal name', a.company.legal_name], ['Industry', a.company.industry], ['Address', a.company.address], ['Website', a.company.website]]],
              ['Contact', [['Name', a.contact.name], ['Role', a.contact.title], ['Department', a.contact.department], ['Mobile number', a.contact.phone], ['Email', <a key="m" href={`mailto:${a.contact.email}`} className="text-google-teal hover:underline">{a.contact.email}</a>], ['Working hours', a.contact.working_hours]]],
              ['Billing', [['Plan', a.billing.plan], ['Billing cycle', a.billing.billing_cycle], ['Payment status', <Pill key="p" value={a.billing.payment_status === 'Paid' ? 'resolved' : 'placed'} label={a.billing.payment_status} />], ['Next invoice', new Date(`${a.billing.next_invoice}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })]]]
            ].map(([group, rows], i) => (
              <div key={group} className={['md:text-left', 'md:text-center', 'md:text-right'][i]}>
                <div className="mb-3 text-sm font-bold uppercase tracking-wider text-google-gray-600">{group}</div>
                <dl className="space-y-3">
                  {rows.map(([k, v]) => (
                    <div key={k}><dt className="text-sm text-google-gray-500">{k}</dt><dd className="text-base font-medium text-google-gray-900">{v}</dd></div>
                  ))}
                </dl>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 2. The numbers */}
      {d && (
        <Kpis>
          <Kpi icon={Layers} tone="blue" label="Features in use" value={`${d.endpoints_opted.toLocaleString()}/${d.endpoints_total.toLocaleString()}`} hint="Opted into, of all available" />
          <Kpi icon={Activity} tone="teal" label="Calls this month" value={d.calls.toLocaleString()} />
          <Kpi icon={Wallet} tone="green" label="Charges this month" value={money(d.cost_usd)} />
          {a && <Kpi icon={CalendarDays} tone="yellow" label="Next invoice" value={a.billing.next_invoice} hint={`${a.billing.plan} plan • ${a.billing.payment_status}`} />}
        </Kpis>
      )}

      {/* 3. Where to go first */}
      {quick.length > 0 && (
        <Section title="Quick actions" subtitle={view ? 'The pages most useful to this role' : 'The pages you use most'}
          action={<Btn onClick={() => window.dispatchEvent(new Event('open-palette'))}>See all features</Btn>}>
          <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
            {quick.map((q) => {
              const look = SERVICE_LOOK[q.service];
              const Icon = look.icon;
              return (
                <a key={`${q.service}/${q.page}`} href={href(`${q.service}/${q.page}`)} className="flex items-center gap-3 rounded-xl border border-google-gray-200 px-3 py-2.5 transition-colors hover:border-google-gray-300 hover:bg-google-gray-50">
                  <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${look.tint}`}><Icon className="h-5 w-5" /></span>
                  <span className="min-w-0"><span className="block truncate text-base font-semibold text-google-gray-900">{q.label}</span><span className="block truncate text-sm text-google-gray-500">{q.serviceLabel}</span></span>
                </a>
              );
            })}
          </div>
        </Section>
      )}
      <div className="h-3" />

      {/* 4. The detail, in two columns */}
      <div className="grid lg:grid-cols-2 gap-3 items-stretch">
        {d && (
          <Section title="Usage by service" subtitle="Calls and charges this month">
            <div className="space-y-3">
              {d.services.map((s) => (
                <div key={s.service}>
                  <div className="flex justify-between items-baseline mb-1">
                    <div className="text-base font-semibold text-google-gray-900">{SERVICE_NAMES[s.service]} <span className="font-normal text-google-gray-500">• {s.endpoints} features</span></div>
                    <div className="text-base text-google-gray-700"><span className="font-semibold text-google-gray-900">{money(s.cost_usd)}</span> • {s.calls.toLocaleString()} calls</div>
                  </div>
                  <Bar value={s.calls} max={callPeak} tone={SERVICE_TONES[s.service]} />
                </div>
              ))}
            </div>
          </Section>
        )}
        {top.length > 0 && (
          <Section title="Most used features" subtitle="Calls this month">
            <div className="space-y-3">
              {top.map((u, i) => (
                <div key={u.path} className="flex items-center gap-3">
                  <span className="w-4 text-sm font-bold text-google-gray-400">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between text-base mb-1"><span className="text-google-gray-800 truncate pr-3">{u.description}</span><span className="font-semibold text-google-gray-900">{u.calls.toLocaleString()}</span></div>
                    <Bar value={u.calls} max={topPeak} tone="blue" />
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}

const DOT = { MaaS: 'bg-google-blue', PaaS: 'bg-google-green', TaaS: 'bg-google-yellow', SaaS: 'bg-google-red' };
const dayLabel = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

function Billing() {
  const invoices = useLoad('/maas/billing/invoice/read/v1');
  const usage = useLoad('/maas/billing/usage/read/v1');
  const account = useLoad('/maas/root-account/read/v1');
  const orders = useLoad('/paas/order/read/staff/v1');
  const [query, setQuery] = useState('');
  const [pageNo, setPageNo] = useState(0);
  const invoice = invoices.data?.invoices?.[0];
  const billing = account.data?.billing;
  const q = query.trim().toLowerCase();
  const charges = (usage.data?.charges ?? []).filter((c) => !q || c.description.toLowerCase().includes(q));
  const PAGE = 10;
  const shown = charges.slice(pageNo * PAGE, (pageNo + 1) * PAGE);
  const services = invoice?.by_service ?? [];
  const total = invoice?.total_usd || 0;
  const calls = services.reduce((n, x) => n + x.calls, 0);
  const biggest = [...services].sort((x, y) => y.cost_usd - x.cost_usd)[0];
  const fixedFees = (usage.data?.charges ?? []).reduce((n, c) => n + c.monthly_fee_usd, 0);
  const usageCharges = Math.max(0, total - fixedFees);
  const revenue = (orders.data?.orders ?? []).filter((o) => o.status !== 'cancelled').reduce((n, o) => n + o.total, 0);
  const orderCount = (orders.data?.orders ?? []).filter((o) => o.status !== 'cancelled').length;
  const left = revenue - total;
  return (
    <div>
      <PageHeader title="Billing and Cost" subtitle="What you are charged for the features you use" />
      <ErrorNote error={invoices.error || usage.error || account.error} />
      {invoice && (
        <Kpis>
          <Kpi icon={Wallet} tone="green" label="This month so far" value={money(total)} hint={`Invoice ${invoice.status.toLowerCase()}`} />
          <Kpi icon={CalendarDays} tone="yellow" label="Invoice due" value={dayLabel(invoice.due)} />
          <Kpi icon={Activity} tone="blue" label="Calls billed" value={calls.toLocaleString()} />
          {biggest && <Kpi icon={Layers} tone="red" label="Biggest cost" value={SERVICE_NAMES[biggest.service]} hint={`${money(biggest.cost_usd)} • ${Math.round((biggest.cost_usd / total) * 100)}% of the total`} />}
        </Kpis>
      )}
      <div className="grid xl:grid-cols-3 gap-3 items-start">
        <div className="space-y-3">
          {invoice && (
            <Section title="Where the cost goes" subtitle="Share of this month's charges">
              <div className="flex h-3 overflow-hidden rounded-full bg-google-gray-100" role="img" aria-label="Cost share by service">
                {services.map((x) => <div key={x.service} className={DOT[x.service]} style={{ width: `${(x.cost_usd / total) * 100}%` }} title={`${SERVICE_NAMES[x.service]} ${money(x.cost_usd)}`} />)}
              </div>
              <ul className="mt-4 space-y-2.5">
                {services.map((x) => (
                  <li key={x.service} className="flex items-center gap-3 text-base">
                    <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${DOT[x.service]}`} />
                    <span className="flex-1 font-medium text-google-gray-900">{SERVICE_NAMES[x.service]}</span>
                    <span className="text-sm text-google-gray-500">{Math.round((x.cost_usd / total) * 100)}%</span>
                    <span className="w-24 text-right font-semibold text-google-gray-900">{money(x.cost_usd)}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}
          {usage.data && total > 0 && (
            <Section title="Fixed fees and usage" subtitle="What you pay for having a feature, and for using it">
              <div className="flex h-3 overflow-hidden rounded-full bg-google-gray-100" role="img" aria-label="Fixed fees compared with usage charges">
                <div className="bg-google-gray-400" style={{ width: `${(fixedFees / total) * 100}%` }} />
                <div className="bg-google-blue" style={{ width: `${(usageCharges / total) * 100}%` }} />
              </div>
              <ul className="mt-4 space-y-2.5">
                <li className="flex items-center gap-3 text-base"><span className="h-2.5 w-2.5 shrink-0 rounded-full bg-google-gray-400" /><span className="flex-1 font-medium text-google-gray-900">Monthly fees</span><span className="text-sm text-google-gray-500">{Math.round((fixedFees / total) * 100)}%</span><span className="w-24 text-right font-semibold text-google-gray-900">{money(fixedFees)}</span></li>
                <li className="flex items-center gap-3 text-base"><span className="h-2.5 w-2.5 shrink-0 rounded-full bg-google-blue" /><span className="flex-1 font-medium text-google-gray-900">Usage charges</span><span className="text-sm text-google-gray-500">{Math.round((usageCharges / total) * 100)}%</span><span className="w-24 text-right font-semibold text-google-gray-900">{money(usageCharges)}</span></li>
              </ul>
            </Section>
          )}
          {billing && invoice && (
            <Section title="Plan and invoice">
              <dl className="space-y-3">
                {[['Plan', billing.plan], ['Billing cycle', billing.billing_cycle], ['Payment status', <Pill key="p" value={billing.payment_status === 'Paid' ? 'resolved' : 'placed'} label={billing.payment_status} />], ['Next invoice', dayLabel(billing.next_invoice)]].map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between gap-3"><dt className="text-sm text-google-gray-500">{k}</dt><dd className="text-base font-medium text-google-gray-900">{v}</dd></div>
                ))}
              </dl>
            </Section>
          )}
        </div>
        {usage.data && (
          <div className="xl:col-span-2">
            <Section title="Charges by feature" subtitle={`${charges.length} features with charges this month`} toolbar={<SearchBox value={query} onChange={(v) => { setQuery(v); setPageNo(0); }} placeholder="Search features" />}>
              <DataTable rowKey={(c) => c.path} rows={shown} empty="No features match." columns={[
                { key: 'd', header: 'Feature', render: (c) => <span className="text-google-gray-900">{c.description}</span> },
                { key: 's', header: 'Service', render: (c) => <span className="inline-flex items-center gap-2 text-google-gray-700"><span className={`h-2 w-2 rounded-full ${DOT[c.service]}`} />{SERVICE_NAMES[c.service]}</span> },
                { key: 'n', header: 'Calls', className: 'text-right', render: (c) => c.calls.toLocaleString() },
                { key: 'm', header: 'Charge', className: 'text-right font-semibold', render: (c) => money(c.cost_usd) }
              ]} />
              <Pager page={pageNo} pageSize={PAGE} total={charges.length} onChange={setPageNo} />
            </Section>
            {orders.data && invoice && (
              <div className="mt-3">
                <Section title="Revenue and cost" subtitle={`Earned from ${orderCount} order${orderCount === 1 ? '' : 's'}, compared with what the platform costs you`}>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <Kpi icon={Banknote} tone="green" label="Revenue from orders" value={money(revenue)} />
                    <Kpi icon={Wallet} tone="red" label="Platform cost" value={money(total)} />
                    <Kpi icon={left >= 0 ? TrendingUp : TrendingDown} tone={left >= 0 ? 'green' : 'red'} label={left >= 0 ? 'Left after cost' : 'Short by'} value={money(Math.abs(left))} />
                  </div>
                  <div className="mt-4">
                    <div className="mb-1.5 flex justify-between text-sm text-google-gray-600"><span>Cost is {revenue ? Math.round((total / revenue) * 100) : 0}% of your revenue</span><span>{money(total)} of {money(revenue)}</span></div>
                    <div className="h-3 overflow-hidden rounded-full bg-google-green-light"><div className={`h-full rounded-full ${total > revenue ? 'bg-google-red' : 'bg-google-green'}`} style={{ width: `${revenue ? Math.min(100, (total / revenue) * 100) : 0}%` }} /></div>
                  </div>
                </Section>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Settings() {
  const { can } = useConsumer();
  const { data, error, reload } = useLoad('/maas/root-account/settings/read/v1');
  const act = useAction(reload);
  const [values, setValues] = useState({});
  useEffect(() => { if (data) setValues(Object.fromEntries(SETTINGS_FIELDS.map((f) => [f.name, data[f.name] ?? '']))); }, [data]);
  const editable = can('/maas/root-account/settings/update/v1');
  const changed = data && SETTINGS_FIELDS.some((f) => values[f.name] !== data[f.name]);
  const save = (e) => {
    e.preventDefault();
    act.run('/maas/root-account/settings/update/v1', values, 'Settings saved');
  };
  return (
    <div>
      <PageHeader title="Settings" subtitle="Company details. Only the root account can change them." />
      <ErrorNote error={error || act.error} />
      {data && (
        <Section>
          <form onSubmit={save} className="space-y-4 max-w-3xl">
            <div className="grid sm:grid-cols-2 gap-4">
              {SETTINGS_FIELDS.map((f) => (
                <label key={f.name} className="block">
                  <span className="block mb-1 text-base font-semibold text-google-gray-800">{f.label}</span>
                  <input className={FIELD} type={f.type || 'text'} disabled={!editable} value={values[f.name] ?? ''} onChange={(e) => setValues({ ...values, [f.name]: e.target.value })} />
                </label>
              ))}
            </div>
            {editable && <Btn kind="primary" type="submit" disabled={!changed || act.busy} className="px-5 py-2 text-base">{act.busy ? 'Saving...' : 'Save changes'}</Btn>}
          </form>
        </Section>
      )}
    </div>
  );
}

export default function MaasPage() {
  const { can } = useConsumer();
  const pages = useAllowedPages('maas', can);
  const page = useCurrentPage('maas', pages);
  if (!page) return <Empty>Your workspace has not opted into any Management features.</Empty>;
  return (
    <div>
      {page === 'overview' && <Overview />}
      {page === 'billing' && <Billing />}
      {page === 'team' && <RolesAndTeam />}
      {page === 'customize' && <Customize />}
      {page === 'settings' && <Settings />}
      <PageExtras service="maas" page={page} />
    </div>
  );
}
