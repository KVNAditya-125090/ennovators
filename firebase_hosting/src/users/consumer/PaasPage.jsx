import React, { useState } from 'react';
import { Plus, Package, Boxes, AlertTriangle, Wallet, ShoppingBag, Clock, Truck, CheckCircle2, Info } from 'lucide-react';
import { useAllowedPages, useCurrentPage } from './consumerPages';
import { useConsumer, useLoad, useAction, Section, Empty, ErrorNote, FormModal, PageHeader, Kpi, Kpis, Thumb, Dropdown, DataTable, SearchBox, RowMenu, StatusSelect, Btn, label, money, FIELD } from './ui';
import { PageExtras } from './MoreFeatures';

// An order only moves forward; delivered and cancelled orders are final (the API enforces the same)
const ORDER_FLOW = { placed: ['paid', 'cancelled'], paid: ['shipped', 'cancelled'], shipped: ['delivered'], delivered: [], cancelled: [] };

// A stock count you click to change. Enter saves, Escape cancels.
function StockCell({ product, editable, onSave }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState('');
  const low = product.stock < 10;
  if (!editing) {
    return (
      <button disabled={!editable} onClick={(e) => { e.stopPropagation(); setValue(String(product.stock)); setEditing(true); }} title={editable ? 'Click to change' : undefined}
        className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-base font-semibold ${low ? 'bg-google-red-light text-google-red' : 'bg-google-gray-100 text-google-gray-900'} ${editable ? 'hover:ring-2 hover:ring-google-blue-light' : ''}`}>
        {product.stock}{low && <span className="text-sm font-medium">low</span>}
      </button>
    );
  }
  const save = async () => { setEditing(false); if (value !== '' && Number(value) !== product.stock) await onSave(Number(value)); };
  return (
    <input autoFocus type="number" min="0" step="1" value={value} onChange={(e) => setValue(e.target.value)} onBlur={save} aria-label={`Stock for ${product.name}`}
      onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); if (e.key === 'Escape') setEditing(false); }} className={`${FIELD} w-20 py-1`} />
  );
}

function Products() {
  const { can, enumValues } = useConsumer();
  const { data, error, reload } = useLoad('/paas/catalog/product/read/v1');
  const act = useAction(reload);
  const [query, setQuery] = useState('');
  const [dialog, setDialog] = useState(null); // { kind: 'new' | 'edit' | 'adjust', product }
  const open = (d) => { act.setError(''); setDialog(d); };
  const products = data?.products ?? [];
  const q = query.trim().toLowerCase();
  const rows = products.filter((p) => !q || `${p.name} ${p.sku} ${p.category}`.toLowerCase().includes(q));
  const units = products.reduce((n, p) => n + p.stock, 0);
  const lowCount = products.filter((p) => p.stock < 10).length;
  const value = products.reduce((n, p) => n + p.stock * p.retail_price, 0);

  const createFields = [
    { name: 'name', label: 'Product name', required: true }, { name: 'sku', label: 'SKU', required: true, hint: 'A unique code for this product' },
    { name: 'category_id', label: 'Category', required: true }, { name: 'price', label: 'Price (USD)', type: 'number', min: 0, required: true },
    { name: 'stock', label: 'Opening stock', type: 'number', step: 1, min: 0 }, { name: 'condition', label: 'Condition', type: 'select', options: enumValues('/paas/catalog/product/create/v1', 'condition') },
    { name: 'description', label: 'Description', type: 'textarea' }
  ];
  const editFields = createFields.filter((f) => !['sku', 'stock'].includes(f.name)).map((f) => ({ ...f, required: f.name === 'name' }));
  const adjustFields = [
    { name: 'quantity_change', label: 'Change', type: 'number', step: 1, required: true, hint: 'Use a minus to take stock out, for example -2' },
    { name: 'reason', label: 'Reason', type: 'select', options: enumValues('/paas/inventory/stock/adjust/v1', 'reason'), required: true }
  ];

  return (
    <div>
      <PageHeader title="Products and Stock" subtitle="What you sell, and how much of it you have"
        action={can('/paas/catalog/product/create/v1') && <Btn kind="primary" className="px-3 py-1.5 text-sm" onClick={() => open({ kind: 'new' })}><Plus className="h-4 w-4 inline mr-1" />Add product</Btn>} />
      <ErrorNote error={error || (!dialog && act.error)} />
      <Kpis>
        <Kpi icon={Package} tone="blue" label="Products on sale" value={products.length} />
        <Kpi icon={Boxes} tone="teal" label="Units in stock" value={units.toLocaleString()} />
        <Kpi icon={AlertTriangle} tone={lowCount ? 'red' : 'green'} label="Running low" value={lowCount} hint={lowCount ? 'Fewer than 10 left' : 'All well stocked'} />
        <Kpi icon={Wallet} tone="green" label="Stock value" value={money(value)} hint="At retail price" />
      </Kpis>
      <Section title="All products" toolbar={<SearchBox value={query} onChange={setQuery} placeholder="Search products" />}>
        <DataTable rowKey={(p) => p.id} rows={rows} empty={data ? (q ? 'No products match.' : 'No products listed yet. Add your first one.') : 'Loading...'} columns={[
          { key: 'p', header: 'Product', render: (p) => (
            <div className="flex items-center gap-3"><Thumb src={p.image_url} alt={p.name} /><div><div className="font-semibold text-google-gray-900">{p.name}</div><div className="text-sm text-google-gray-500">{p.sku}</div></div></div>
          ) },
          { key: 'c', header: 'Category', render: (p) => <span className="text-google-gray-700">{p.category}</span> },
          { key: 'u', header: 'Condition', render: (p) => <span className="text-sm text-google-gray-600">{p.condition}</span> },
          { key: 'r', header: 'Price', render: (p) => <span className="font-semibold text-google-gray-900">{money(p.retail_price)}</span> },
          { key: 's', header: 'In stock', render: (p) => <StockCell product={p} editable={can('/paas/inventory/stock/update/v1')} onSave={(quantity) => act.run('/paas/inventory/stock/update/v1', { sku: p.sku, quantity }, 'Stock updated')} /> },
          { key: 'a', header: '', className: 'text-right', render: (p) => (
            <RowMenu items={[
              { label: 'Edit details', hidden: !can('/paas/catalog/product/update/v1'), onClick: () => open({ kind: 'edit', product: p }) },
              { label: 'Adjust stock', hidden: !can('/paas/inventory/stock/adjust/v1'), onClick: () => open({ kind: 'adjust', product: p }) },
              { label: 'Remove from sale', danger: true, hidden: !can('/paas/catalog/product/archive/v1'), onClick: async () => { if (window.confirm(`Remove ${p.name} from sale?`)) await act.run('/paas/catalog/product/archive/v1', { product_id: p.id }, 'Product removed'); } }
            ]} />
          ) }
        ]} />
      </Section>
      {dialog?.kind === 'new' && <FormModal title="Add product" fields={createFields} submitLabel="Add product" error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/paas/catalog/product/create/v1', v, 'Product added'))} />}
      {dialog?.kind === 'edit' && <FormModal title={`Edit ${dialog.product.name}`} fields={editFields} initial={{ ...dialog.product, category_id: dialog.product.category, price: dialog.product.retail_price }} error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/paas/catalog/product/update/v1', { ...v, product_id: dialog.product.id }, 'Product saved'))} />}
      {dialog?.kind === 'adjust' && <FormModal title={`Adjust stock: ${dialog.product.name}`} fields={adjustFields} submitLabel="Adjust" error={act.error} busy={act.busy} onClose={() => setDialog(null)}
        onSubmit={async (v) => Boolean(await act.run('/paas/inventory/stock/adjust/v1', { ...v, sku: dialog.product.sku }, 'Stock adjusted'))} />}
    </div>
  );
}

function Orders() {
  const { can, enumValues } = useConsumer();
  const { data, error, reload } = useLoad('/paas/order/read/staff/v1');
  const act = useAction(reload);
  const [query, setQuery] = useState('');
  const statuses = enumValues('/paas/order/status/update/v1', 'status');
  const orders = data?.orders ?? [];
  const q = query.trim().toLowerCase();
  const rows = orders.filter((o) => (!q || `${o.order_id} ${o.customer} ${o.items}`.toLowerCase().includes(q)));
  const count = (...s) => orders.filter((o) => s.includes(o.status)).length;
  const revenue = orders.filter((o) => o.status !== 'cancelled').reduce((n, o) => n + o.total, 0);
  return (
    <div>
      <PageHeader title="Orders" subtitle="What your customers have bought, and where each order is" />
      <ErrorNote error={error || act.error} />
      <Kpis>
        <Kpi icon={Clock} tone="yellow" label="Waiting for you" value={count('placed', 'paid')} hint="Placed or paid" />
        <Kpi icon={Truck} tone="blue" label="On the way" value={count('shipped')} />
        <Kpi icon={CheckCircle2} tone="green" label="Delivered" value={count('delivered')} />
        <Kpi icon={ShoppingBag} tone="teal" label="Order value" value={money(revenue)} hint="Without cancelled" />
      </Kpis>
      <Section title="All orders" toolbar={<SearchBox value={query} onChange={setQuery} placeholder="Search orders" />}>
        <DataTable rowKey={(o) => o.order_id} rows={rows} empty={data ? 'No orders match.' : 'Loading...'} columns={[
          { key: 'o', header: 'Order', render: (o) => <><div className="font-semibold text-google-gray-900">{o.order_id}</div><div className="text-sm text-google-gray-500">{o.placed}</div></> },
          { key: 'c', header: 'Customer', render: (o) => o.customer },
          { key: 'i', header: 'Items', render: (o) => <span className="text-google-gray-700">{o.items}</span> },
          { key: 't', header: 'Total', render: (o) => <span className="font-semibold text-google-gray-900">{money(o.total)}</span> },
          { key: 's', header: 'Status', className: 'text-right', render: (o) => <StatusSelect value={o.status} options={statuses.filter((st) => st === o.status || ORDER_FLOW[o.status]?.includes(st))} disabled={act.busy || !can('/paas/order/status/update/v1') || !ORDER_FLOW[o.status]?.length} onChange={(status) => act.run('/paas/order/status/update/v1', { order_id: o.order_id, status }, `${o.order_id} marked ${label(status).toLowerCase()}`)} /> }
        ]} />
      </Section>
    </div>
  );
}

function Forecast() {
  const products = useLoad('/paas/catalog/product/read/v1');
  const [sku, setSku] = useState('SKU-WATCH-G3');
  const { data, error } = useLoad('/paas/forecast/demand/read/v1', { sku });
  const days = data?.daily_forecast?.slice(0, 14) ?? [];
  const peak = Math.max(60, ...days.map((d) => d.predicted_demand));
  const total = days.reduce((n, d) => n + d.predicted_demand, 0);
  return (
    <div>
      <PageHeader title="Demand Forecast" subtitle="Expected demand for the next two weeks, so you restock in time"
        action={<Dropdown ariaLabel="Product" value={sku} onChange={setSku} className="min-w-[14rem]" options={(products.data?.products ?? [{ sku, name: sku }]).map((x) => ({ value: x.sku, label: x.name }))} />} />
      <ErrorNote error={error} />
      {data && (
        <>
          <Kpis>
            <Kpi icon={ShoppingBag} tone="blue" label="Expected in 14 days" value={total.toLocaleString()} hint="Units" />
            <Kpi icon={Clock} tone="yellow" label="Busiest day" value={Math.max(...days.map((d) => d.predicted_demand))} hint="Units" />
            <Kpi icon={AlertTriangle} tone="red" label="Reorder when stock hits" value={`${data.recommended_reorder_point} units`} />
          </Kpis>
          <Section title="Day by day">
            <div className="h-44 flex items-end gap-2 px-1">
              {days.map((d) => (
                <div key={d.date} className="flex-1 flex flex-col items-center gap-1.5" title={`${d.date}: ${d.predicted_demand} units`}>
                  <span className="text-[11px] text-google-gray-500">{d.predicted_demand}</span>
                  <div className="w-full rounded-t-md bg-google-blue" style={{ height: `${(d.predicted_demand / peak) * 110}px` }} />
                  <span className="text-[11px] text-google-gray-500">{d.date.slice(-2)}</span>
                </div>
              ))}
            </div>
          </Section>
          {data.explanation && (
            <Section title="Why this forecast">
              <ul className="space-y-2 text-base text-google-gray-700">
                {data.explanation.reasons.map((r) => (
                  <li key={r} className="flex gap-2"><Info className="h-4 w-4 mt-1 shrink-0 text-google-teal" />{r}</li>
                ))}
              </ul>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

export default function PaasPage() {
  const { can } = useConsumer();
  const pages = useAllowedPages('paas', can);
  const page = useCurrentPage('paas', pages);
  if (!page) return <Empty>Your workspace has not opted into any Product features.</Empty>;
  return (
    <div>
      {page === 'products' && <Products />}
      {page === 'orders' && <Orders />}
      {page === 'forecast' && <Forecast />}
      <PageExtras service="paas" page={page} />
    </div>
  );
}
