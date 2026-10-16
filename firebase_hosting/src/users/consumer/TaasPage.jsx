import React, { useState } from 'react';
import { Plus, Truck, Clock, CheckCircle2, Leaf, RotateCcw, CalendarClock, Navigation, Timer, MapPin, Zap, Recycle } from 'lucide-react';
import { useAllowedPages, useCurrentPage } from './consumerPages';
import { useConsumer, useLoad, useAction, Section, ErrorNote, FormModal, PageHeader, Kpi, Kpis, Bar, DataTable, SearchBox, RowMenu, StatusSelect, Dropdown, Btn, Pill, Empty, label } from './ui';
import { PageExtras } from './MoreFeatures';
import DeliveryPlanner, { PLANNER_PATHS } from './DeliveryPlanner';

function Shipments() {
  const { can, enumValues } = useConsumer();
  const { data, error, reload } = useLoad('/taas/shipment/read/staff/v1');
  const orders = useLoad('/paas/order/read/staff/v1');
  const act = useAction(reload);
  const [query, setQuery] = useState('');
  const [dialog, setDialog] = useState(null); // 'new' or the shipment being cancelled
  const [planning, setPlanning] = useState(null); // the shipment id being planned with AI

  const statuses = enumValues('/taas/shipment/status/update/v1', 'status');
  const shipments = data?.shipments ?? [];
  const q = query.trim().toLowerCase();
  const rows = shipments.filter((s) => (!q || `${s.shipment_id} ${s.origin} ${s.destination} ${s.carrier}`.toLowerCase().includes(q)));
  const count = (status) => shipments.filter((s) => s.status === status).length;
  const co2 = shipments.filter((s) => s.status !== 'cancelled').reduce((n, s) => n + (s.co2_saved_kg || 0), 0);
  const open = (d) => { act.setError(''); setDialog(d); };
  const orderOptions = (orders.data?.orders ?? []).map((o) => ({ value: o.order_id, label: `${o.order_id} • ${o.customer}` }));
  const createFields = [
    { name: 'order_id', label: 'Order', required: true, ...(orderOptions.length ? { type: 'select', options: orderOptions } : {}) },
    { name: 'carrier', label: 'Carrier', hint: 'Leave empty to use the default carrier' }
  ];

  return (
    <div>
      <PageHeader title="Shipments" subtitle="Goods moving to your customers, between stores and back for recovery"
        action={can('/taas/shipment/create/v1') && <Btn kind="primary" className="px-3 py-1.5 text-xs" onClick={() => open('new')}><Plus className="h-4 w-4 inline mr-1" />New shipment</Btn>} />
      <ErrorNote error={error || (!dialog && act.error)} />
      <Kpis>
        <Kpi icon={Clock} tone="yellow" label="Ready to go" value={count('created')} hint="Created, not moving yet" />
        <Kpi icon={Truck} tone="blue" label="On the way" value={count('in_transit')} />
        <Kpi icon={CheckCircle2} tone="green" label="Delivered" value={count('delivered')} />
        <Kpi icon={Leaf} tone="green" label="CO2 saved" value={`${co2.toFixed(1)} kg`} hint="By your routes" />
      </Kpis>
      <Section title="All shipments" toolbar={<SearchBox value={query} onChange={setQuery} placeholder="Search shipments" />}>
        <DataTable rowKey={(s) => s.shipment_id} rows={rows} empty={data ? 'No shipments match.' : 'Loading...'} columns={[
          { key: 'i', header: 'Shipment', render: (s) => <><div className="font-semibold text-google-gray-900">{s.shipment_id}</div><div className="text-xs text-google-gray-500">{s.type}</div></> },
          { key: 'r', header: 'Route', render: (s) => <span className="text-google-gray-700">{s.origin} <span className="text-google-gray-400">to</span> {s.destination}</span> },
          { key: 'c', header: 'Carrier', render: (s) => <><div className="text-google-gray-700">{s.carrier}</div>{(s.vehicle || s.route || s.delivery_slot) && <div className="text-xs text-google-gray-500">{[s.vehicle, s.route, s.delivery_slot].filter(Boolean).join(' • ')}</div>}</> },
          { key: 'e', header: 'Arrives', render: (s) => s.eta },
          { key: 's', header: 'Status', render: (s) => (can('/taas/shipment/status/update/v1') && s.status !== 'cancelled'
            ? <StatusSelect value={s.status} options={statuses} disabled={act.busy} onChange={(status) => act.run('/taas/shipment/status/update/v1', { shipment_id: s.shipment_id, status }, `${s.shipment_id} marked ${label(status).toLowerCase()}`)} />
            : <Pill value={s.status} />) },
          { key: 'a', header: '', className: 'text-right', render: (s) => (
            <RowMenu items={[{ label: 'Plan delivery with AI', hidden: !PLANNER_PATHS.some(can) || ['cancelled', 'delivered'].includes(s.status), onClick: () => setPlanning(s.shipment_id) }, { label: 'Cancel shipment', danger: true, hidden: !can('/taas/shipment/cancel/v1') || ['cancelled', 'delivered'].includes(s.status), onClick: () => open(s) }]} />
          ) }
        ]} />
      </Section>
      {planning && shipments.find((x) => x.shipment_id === planning) && <DeliveryPlanner shipment={shipments.find((x) => x.shipment_id === planning)} onClose={() => setPlanning(null)} onApplied={reload} />}
      {dialog === 'new' && <FormModal title="New shipment" fields={createFields} submitLabel="Create shipment" error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/taas/shipment/create/v1', v, 'Shipment created'))} />}
      {dialog && dialog !== 'new' && <FormModal title={`Cancel ${dialog.shipment_id}`} fields={[{ name: 'reason', label: 'Reason', type: 'textarea' }]} submitLabel="Cancel shipment" error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/taas/shipment/cancel/v1', { ...v, shipment_id: dialog.shipment_id }, 'Shipment cancelled'))} />}
    </div>
  );
}

const ROUTES = [
  { value: 'resale', label: 'Resale', path: '/taas/reverse/route/resale/assign/v1' },
  { value: 'refurbish', label: 'Refurbish', path: '/taas/reverse/route/refurbish/assign/v1' },
  { value: 'donate', label: 'Donate', path: '/taas/reverse/route/donate/assign/v1' },
  { value: 'parts', label: 'Parts harvesting', path: '/taas/reverse/route/parts/assign/v1' },
  { value: 'recycle', label: 'Recycle', path: '/taas/reverse/route/recycle/assign/v1' }
];

// Where each returned item goes next, and when it is collected
function ReturnRoutes() {
  const { can } = useConsumer();
  const { data, error, reload } = useLoad('/saas/return/request/read/v1');
  const act = useAction(reload);
  const [dialog, setDialog] = useState(null); // the return a pickup is being scheduled for
  const returns = (data?.returns ?? []).filter((r) => ['approved', 'refunded'].includes(r.status));
  const options = ROUTES.filter((r) => can(r.path));
  const toRoute = returns.filter((r) => !r.route).length;
  const routed = returns.filter((r) => r.route).length;
  const pickups = returns.filter((r) => r.pickup).length;
  const route = (ret, kind) => act.run(ROUTES.find((r) => r.value === kind).path, { return_id: ret.return_id }, `${ret.item} routed to ${label(kind).toLowerCase()}`);
  return (
    <div>
      <PageHeader title="Return Routes" subtitle="Decide where each returned item goes next, and schedule its pickup" />
      <ErrorNote error={error || (!dialog && act.error)} />
      <Kpis>
        <Kpi icon={RotateCcw} tone="yellow" label="Waiting for a route" value={toRoute} />
        <Kpi icon={Navigation} tone="blue" label="Routed" value={routed} />
        <Kpi icon={CalendarClock} tone="green" label="Pickups scheduled" value={pickups} />
        <Kpi icon={Recycle} tone="green" label="Returns this month" value={returns.length} hint="Approved or refunded" />
      </Kpis>
      <Section title="Approved returns" subtitle="Only approved returns can be routed">
        <DataTable rowKey={(r) => r.return_id} rows={returns} empty={data ? 'No approved returns to route yet.' : 'Loading...'} columns={[
          { key: 'i', header: 'Return', render: (r) => <><div className="font-semibold text-google-gray-900">{r.item}</div><div className="text-xs text-google-gray-500">{r.return_id} • {r.customer}</div></> },
          { key: 'r', header: 'Route', render: (r) => options.length === 0 ? <span className="text-google-gray-500">-</span> : (
            <Dropdown ariaLabel={`Route for ${r.return_id}`} value={r.route || ''} placeholder="Choose a route" disabled={act.busy} options={options} onChange={(kind) => route(r, kind)}
              trigger={{ className: `inline-flex items-center gap-2 rounded-lg border px-3 py-1 text-sm ${r.route ? 'border-google-green bg-google-green-light text-google-gray-900 font-medium' : 'border-google-gray-300 bg-white text-google-gray-500'}`, render: () => (r.route ? label(r.route) : 'Choose a route') }} />
          ) },
          { key: 'p', header: 'Pickup', render: (r) => r.pickup ? <span className="text-google-gray-800">{r.pickup.at.replace('T', ' ')} <span className="text-xs text-google-gray-500">• {r.pickup.carrier}</span></span> : <span className="text-google-gray-400">Not scheduled</span> },
          { key: 'x', header: '', className: 'text-right', render: (r) => can('/taas/reverse/pickup/schedule/v1') && <Btn onClick={() => { act.setError(''); setDialog(r); }}>{r.pickup ? 'Reschedule' : 'Schedule pickup'}</Btn> }
        ]} />
      </Section>
      {dialog && <FormModal title={`Pickup for ${dialog.item}`} fields={[
        { name: 'pickup_at', label: 'Pickup date and time', type: 'datetime-local', required: true },
        { name: 'carrier', label: 'Carrier', hint: 'Leave empty to use the default carrier' }
      ]} submitLabel="Schedule" error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/taas/reverse/pickup/schedule/v1', { ...v, return_id: dialog.return_id }, 'Pickup scheduled'))} />}
    </div>
  );
}

// How you deliver, and where
function DeliveryRules() {
  const { can, enumValues } = useConsumer();
  const { data, error, reload } = useLoad('/taas/analytics/delivery/read/v1');
  const act = useAction(reload);
  const [dialog, setDialog] = useState(null); // 'rules' | 'area'
  const rules = data?.rules;
  const area = data?.service_area;
  const open = (d) => { act.setError(''); setDialog(d); };
  const chips = (list) => <div className="flex flex-wrap gap-2">{list.map((x) => <span key={x} className="rounded-full bg-google-gray-100 px-3 py-1 text-sm text-google-gray-800">{x}</span>)}</div>;
  return (
    <div>
      <PageHeader title="Delivery Rules" subtitle="The delivery options you offer, your cut-off time and where you deliver" />
      <ErrorNote error={error || (!dialog && act.error)} />
      {data && (
        <Kpis>
          <Kpi icon={Timer} tone="green" label="On time" value={`${data.on_time_pct}%`} />
          <Kpi icon={Truck} tone="blue" label="Average delivery" value={`${data.avg_days} days`} />
          <Kpi icon={CheckCircle2} tone="green" label="Delivered" value={`${data.delivered}/${data.shipments}`} hint="Shipments" />
          <Kpi icon={MapPin} tone="yellow" label="Service area" value={area ? label(area.mode) : '-'} hint={area?.mode === 'global' ? 'Worldwide' : `${area?.regions.length} regions`} />
        </Kpis>
      )}
      <div className="grid lg:grid-cols-2 gap-3 items-start">
        {rules && (
          <Section title="Delivery options" subtitle="What your customers can choose at checkout" action={can('/taas/delivery/rules/set/v1') && <Btn onClick={() => open('rules')}>Edit</Btn>}>
            <div className="space-y-4">
              <div><div className="mb-1.5 text-sm text-google-gray-500">Options</div>{chips(rules.options)}</div>
              <div><div className="mb-1.5 text-sm text-google-gray-500">Order by (same-day cut-off)</div><div className="text-base font-medium text-google-gray-900">{rules.cutoff_time}</div></div>
              <div><div className="mb-1.5 text-sm text-google-gray-500">Regions</div>{chips(rules.regions)}</div>
            </div>
          </Section>
        )}
        {area && (
          <Section title="Service area" subtitle="Local or worldwide delivery" action={can('/taas/locale/service-area/set/v1') && <Btn onClick={() => open('area')}>Edit</Btn>}>
            <div className="space-y-4">
              <div><div className="mb-1.5 text-sm text-google-gray-500">Mode</div><Pill value={area.mode === 'global' ? 'delivered' : 'in_transit'} label={area.mode === 'global' ? 'Global' : 'Local'} /></div>
              <div><div className="mb-1.5 text-sm text-google-gray-500">Regions</div>{area.mode === 'global' ? <span className="text-base text-google-gray-900">Worldwide</span> : chips(area.regions)}</div>
            </div>
          </Section>
        )}
      </div>
      {dialog === 'rules' && <FormModal title="Delivery options" fields={[
        { name: 'options', label: 'Options, one per line', type: 'lines', required: true },
        { name: 'cutoff_time', label: 'Order by (cut-off time)', hint: 'For example 16:00' },
        { name: 'regions', label: 'Regions, one per line', type: 'lines' }
      ]} initial={rules} error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/taas/delivery/rules/set/v1', v, 'Delivery rules saved'))} />}
      {dialog === 'area' && <FormModal title="Service area" fields={[
        { name: 'mode', label: 'Where do you deliver?', type: 'select', required: true, options: enumValues('/taas/locale/service-area/set/v1', 'mode').map((m) => ({ value: m, label: m === 'global' ? 'Worldwide' : 'Only these regions' })) },
        { name: 'regions', label: 'Regions, one per line', type: 'lines', hint: 'Only used for local delivery' }
      ]} initial={area} error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/taas/locale/service-area/set/v1', { mode: v.mode, regions: v.mode === 'global' ? ['Worldwide'] : v.regions ?? [] }, 'Service area saved'))} />}
    </div>
  );
}

const TONE_BAR = { yellow: 'bg-google-yellow-light text-[#8A5A00]', red: 'bg-google-red-light text-google-red', green: 'bg-google-green-light text-google-green' };

// What the deliveries are telling you
function Insights() {
  const { can } = useConsumer();
  const analytics = useLoad('/taas/analytics/delivery/read/v1');
  const insights = useLoad('/taas/insights/delivery/read/v1');
  const impact = useLoad('/taas/impact/report/read/v1');
  const a = analytics.data;
  const peak = Math.max(1, ...(a?.by_carrier ?? []).map((c) => c.shipments));
  return (
    <div>
      <PageHeader title="Delivery Insights" subtitle="Patterns in delays and complaints, and the carbon you save" />
      <ErrorNote error={analytics.error || insights.error || impact.error} />
      <Kpis>
        {a && <Kpi icon={Timer} tone="green" label="On time" value={`${a.on_time_pct}%`} />}
        {a && <Kpi icon={Truck} tone="blue" label="Average delivery" value={`${a.avg_days} days`} />}
        {impact.data && <Kpi icon={Leaf} tone="green" label="CO2 saved" value={`${impact.data.co2_saved_kg} kg`} />}
        {impact.data && <Kpi icon={Zap} tone="yellow" label="Electric carriers" value={`${impact.data.electric_share_pct}%`} hint={`${impact.data.returns_recovered} returns recovered`} />}
      </Kpis>
      <div className="grid lg:grid-cols-2 gap-3 items-start">
        {can('/taas/insights/delivery/read/v1') && insights.data && (
          <Section title="What we noticed" subtitle="Delays and complaints">
            <ul className="space-y-2.5">
              {insights.data.patterns.map((p) => (
                <li key={p.title} className={`rounded-xl px-4 py-3 ${TONE_BAR[p.tone]}`}><div className="text-base font-semibold">{p.title}</div><div className="text-sm opacity-90">{p.detail}</div></li>
              ))}
            </ul>
          </Section>
        )}
        {a && (
          <Section title="Shipments by carrier">
            <div className="space-y-3">
              {a.by_carrier.map((c) => (
                <div key={c.carrier}>
                  <div className="mb-1 flex justify-between text-base"><span className="text-google-gray-800">{c.carrier}</span><span className="font-semibold text-google-gray-900">{c.shipments}</span></div>
                  <Bar value={c.shipments} max={peak} tone="yellow" />
                </div>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}

export default function TaasPage() {
  const { can } = useConsumer();
  const pages = useAllowedPages('taas', can);
  const page = useCurrentPage('taas', pages);
  if (!page) return <Empty>Your workspace has not opted into any Transport features.</Empty>;
  return (
    <div>
      {page === 'shipments' && <Shipments />}
      {page === 'returns' && <ReturnRoutes />}
      {page === 'delivery' && <DeliveryRules />}
      {page === 'insights' && <Insights />}
      <PageExtras service="taas" page={page} />
    </div>
  );
}
