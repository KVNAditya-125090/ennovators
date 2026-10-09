import React, { createContext, useContext, useState, useEffect, useCallback, useRef, useLayoutEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, MoreHorizontal, Search, CheckCircle, ChevronDown, ChevronLeft, ChevronRight, Check, Building2, Package, Truck, LifeBuoy } from 'lucide-react';
import { useRoute } from './consumerPages';

// What every Consumer page shares: which endpoints the workspace has opted into, and how to call them
export const ConsumerContext = createContext(null);
export const useConsumer = () => useContext(ConsumerContext);

export const label = (value) => String(value ?? '').replace(/[_-]/g, ' ').replace(/^./, (c) => c.toUpperCase());
export const money = (n) => `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export const FIELD = 'w-full rounded-lg border border-google-gray-300 bg-white px-3 py-1.5 text-base';

const PILLS = {
  paid: 'bg-google-blue-light text-google-blue-dark', placed: 'bg-google-yellow-light text-google-gray-900', shipped: 'bg-google-blue-light text-google-blue-dark',
  delivered: 'bg-google-green-light text-google-green', cancelled: 'bg-google-red-light text-google-red', created: 'bg-google-yellow-light text-google-gray-900',
  in_transit: 'bg-google-blue-light text-google-blue-dark', open: 'bg-google-yellow-light text-google-gray-900', in_progress: 'bg-google-blue-light text-google-blue-dark',
  resolved: 'bg-google-green-light text-google-green', closed: 'bg-google-gray-100 text-google-gray-600', requested: 'bg-google-yellow-light text-google-gray-900',
  approved: 'bg-google-blue-light text-google-blue-dark', rejected: 'bg-google-red-light text-google-red', refunded: 'bg-google-green-light text-google-green'
};
export const Pill = ({ value, label: text }) => <span className={`google-pill whitespace-nowrap shrink-0 ${PILLS[value] || 'bg-google-gray-100 text-google-gray-600'}`}>{text ?? label(value)}</span>;

// ---- Layout pieces ----

// A card. The header holds the title and the card's main action; search and filters go on their own row (toolbar).
export function Section({ title, subtitle, action, toolbar, children, className = '' }) {
  return (
    <section className={`google-card p-4 sm:p-5 ${className}`}>
      {(title || action) && (
        <div className={`flex flex-wrap justify-between items-center gap-3 mb-4 ${title ? 'pb-3 border-b border-google-gray-100' : ''}`}>
          <div className="min-w-0">
            {title && <h3 className="text-base font-semibold text-google-teal-dark">{title}</h3>}
            {subtitle && <p className="text-sm text-google-gray-500">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {toolbar && <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">{toolbar}</div>}
      {children}
    </section>
  );
}

export const Empty = ({ children }) => <div className="text-base text-google-gray-600 py-6 text-center">{children}</div>;

export function ErrorNote({ error }) {
  return error ? <div role="alert" className="mb-3 rounded-lg border border-google-red bg-google-red-light px-3 py-2 text-base text-google-red">{error}</div> : null;
}

// A row of page tabs inside a service
export function Tabs({ tabs, value, onChange }) {
  return (
    <div role="tablist" className="flex gap-1 border-b border-google-gray-200 mb-3 overflow-x-auto">
      {tabs.map((t) => (
        <button key={t.key} role="tab" aria-selected={value === t.key} onClick={() => onChange(t.key)}
          className={`px-3 py-2 text-base font-semibold whitespace-nowrap border-b-2 -mb-px transition-colors ${value === t.key ? 'border-google-blue text-google-teal' : 'border-transparent text-google-gray-600 hover:text-google-gray-900'}`}>
          {t.label}{t.count !== undefined && <span className="ml-1.5 text-sm font-normal text-google-gray-500">{t.count}</span>}
        </button>
      ))}
    </div>
  );
}

export const Stat = ({ label: text, value, hint }) => (
  <div className="rounded-xl bg-google-gray-50 border border-google-gray-200 px-3 py-2">
    <div className="text-sm text-google-gray-500">{text}</div>
    <div className="text-2xl font-bold text-google-teal-dark">{value}</div>
    {hint && <div className="text-sm text-google-gray-500">{hint}</div>}
  </div>
);

export function SearchBox({ value, onChange, placeholder = 'Search' }) {
  return (
    <label className="relative block w-full md:w-80">
      <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-google-gray-400" />
      <input type="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} aria-label={placeholder} className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-google-gray-300 bg-white focus:border-google-blue focus:outline-none focus:ring-2 focus:ring-google-blue/20" />
    </label>
  );
}

// Filter chips: options are { value, label, count }
export function Chips({ options, value, onChange }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((o) => (
        <button key={o.value} onClick={() => onChange(o.value)} aria-pressed={value === o.value}
          className={`rounded-full px-2.5 py-0.5 text-sm font-semibold border transition-colors ${value === o.value ? 'bg-google-blue-light text-google-blue-dark border-google-blue-light' : 'bg-white text-google-gray-700 border-google-gray-300 hover:bg-google-gray-100'}`}>
          {o.label}{o.count !== undefined && <span className="ml-1 font-normal text-google-gray-500">{o.count}</span>}
        </button>
      ))}
    </div>
  );
}

// columns: { key, header, render(row), className }. onRowClick makes a row selectable.
export function DataTable({ columns, rows, rowKey, empty = 'Nothing to show.', onRowClick, selectedKey }) {
  if (rows.length === 0) return <Empty>{empty}</Empty>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-google-gray-500 border-b border-google-gray-200">
            {columns.map((c) => <th key={c.key} className={`py-2.5 pr-4 font-medium ${c.className || ''}`}>{c.header}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={rowKey(r)} onClick={onRowClick ? () => onRowClick(r) : undefined}
              className={`border-b border-google-gray-100 last:border-0 hover:bg-google-gray-50/70 ${onRowClick ? 'cursor-pointer hover:bg-google-gray-50' : ''} ${selectedKey === rowKey(r) ? 'bg-google-blue-light/40' : ''}`}>
              {columns.map((c) => <td key={c.key} className={`py-3 pr-4 align-middle ${c.className || ''}`}>{c.render(r)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// A floating panel that sits under (or over) its trigger. It is drawn on the page itself, so a table or card can never clip it.
function Popover({ anchor, onClose, align = 'left', children }) {
  const ref = useRef(null);
  const [pos, setPos] = useState(null);
  useEffect(() => {
    const rect = anchor.current.getBoundingClientRect();
    const below = window.innerHeight - rect.bottom;
    const style = { minWidth: rect.width };
    if (below < 260 && rect.top > below) style.bottom = window.innerHeight - rect.top + 6; else style.top = rect.bottom + 6;
    if (align === 'right') style.right = window.innerWidth - rect.right; else style.left = rect.left;
    setPos(style);
    const onDown = (e) => { if (!ref.current?.contains(e.target) && !anchor.current?.contains(e.target)) onClose(); };
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    window.addEventListener('resize', onClose);
    window.addEventListener('scroll', onClose, true);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('resize', onClose);
      window.removeEventListener('scroll', onClose, true);
    };
  }, [anchor, onClose, align]);
  // keep the whole menu on screen, even when its trigger sits in a table scrolled sideways
  useLayoutEffect(() => {
    if (!pos || pos.fitted || !ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const vw = document.documentElement.clientWidth;
    const left = Math.max(8, Math.min(r.left, vw - 8 - r.width));
    if (Math.round(left) !== Math.round(r.left)) setPos({ ...pos, left, right: undefined, fitted: true });
  }, [pos]);
  if (!pos) return null;
  const { fitted, ...place } = pos;
  return createPortal(
    <div ref={ref} role="menu" style={{ position: 'fixed', zIndex: 70, maxWidth: 'calc(100vw - 16px)', ...place }} className="max-h-72 overflow-y-auto rounded-xl border border-google-gray-200 bg-white p-1 shadow-xl">{children}</div>,
    document.body
  );
}

const DOTS = {
  paid: 'bg-google-blue', placed: 'bg-google-yellow', shipped: 'bg-google-blue', delivered: 'bg-google-green', cancelled: 'bg-google-red', created: 'bg-google-yellow',
  in_transit: 'bg-google-blue', open: 'bg-google-yellow', in_progress: 'bg-google-blue', resolved: 'bg-google-green', closed: 'bg-google-gray-400'
};

// The "..." menu that holds a row's less common actions. items: { label, onClick, danger, hidden }
export function RowMenu({ items, disabled }) {
  const [open, setOpen] = useState(false);
  const anchor = useRef(null);
  const shown = items.filter((i) => !i.hidden);
  if (shown.length === 0) return null;
  return (
    <span onClick={(e) => e.stopPropagation()}>
      <button ref={anchor} aria-label="More actions" aria-haspopup="menu" aria-expanded={open} disabled={disabled} onClick={() => setOpen(!open)} className="rounded-md p-1.5 text-google-gray-500 hover:bg-google-gray-100 disabled:opacity-50">
        <MoreHorizontal className="h-4 w-4" />
      </button>
      {open && (
        <Popover anchor={anchor} align="right" onClose={() => setOpen(false)}>
          {shown.map((i) => (
            <button key={i.label} role="menuitem" onClick={() => { setOpen(false); i.onClick(); }}
              className={`block w-full whitespace-nowrap rounded-lg px-3 py-2 text-left text-base hover:bg-google-gray-100 ${i.danger ? 'text-google-red' : 'text-google-gray-800'}`}>{i.label}</button>
          ))}
        </Popover>
      )}
    </span>
  );
}

// A dropdown that looks like the rest of the interface. options: [{ value, label, dot }] or plain strings.
export function Dropdown({ value, options, onChange, placeholder = 'Choose', disabled, trigger, ariaLabel, align = 'left', className = '' }) {
  const [open, setOpen] = useState(false);
  const anchor = useRef(null);
  const list = options.map((o) => (typeof o === 'string' ? { value: o, label: label(o) } : o));
  const current = list.find((o) => o.value === value);
  const close = useCallback(() => setOpen(false), []);
  return (
    <>
      <button ref={anchor} type="button" aria-label={ariaLabel} aria-haspopup="listbox" aria-expanded={open} disabled={disabled} onClick={() => setOpen(!open)}
        className={`${trigger?.className ?? `${FIELD} flex items-center justify-between gap-2 text-left`} disabled:opacity-60 ${className}`}>
        {trigger?.render ? trigger.render(current) : <span className={current ? 'text-google-gray-900' : 'text-google-gray-400'}>{current?.label ?? placeholder}</span>}
        <ChevronDown className={`h-3.5 w-3.5 shrink-0 opacity-70 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <Popover anchor={anchor} align={align} onClose={close}>
          {list.map((o) => (
            <button key={o.value} type="button" role="option" aria-selected={o.value === value} onClick={() => { close(); if (o.value !== value) onChange(o.value); }}
              className={`flex w-full items-center gap-2.5 whitespace-nowrap rounded-lg px-3 py-2 text-left text-base hover:bg-google-gray-100 ${o.value === value ? 'font-semibold text-google-gray-900' : 'text-google-gray-700'}`}>
              {o.dot && <span className={`h-2 w-2 shrink-0 rounded-full ${o.dot}`} />}
              <span className="flex-1">{o.label}</span>
              {o.value === value && <Check className="h-4 w-4 text-google-teal" />}
            </button>
          ))}
        </Popover>
      )}
    </>
  );
}

export const Btn = ({ children, kind = 'secondary', ...rest }) => (
  <button type="button" {...rest} className={`${kind === 'primary' ? 'inline-flex items-center justify-center rounded-lg google-btn-gradient font-semibold text-white shadow-sm transition-[filter]' : 'google-btn-secondary !py-1 !px-3 !text-sm'} text-sm py-1.5 px-3 disabled:opacity-60 ${rest.className || ''}`}>{children}</button>
);

// A status you can change in place: the coloured pill is the control, and the menu lists the choices with their colours.
export function StatusSelect({ value, options, onChange, disabled }) {
  return (
    <Dropdown ariaLabel="Change status" align="right" value={value} disabled={disabled} onChange={onChange}
      options={options.map((o) => ({ value: o, label: label(o), dot: DOTS[o] }))}
      trigger={{ className: `relative inline-flex h-8 w-36 items-center justify-center whitespace-nowrap rounded-lg px-7 [&>svg]:absolute [&>svg]:right-2 [&>svg]:h-3 [&>svg]:w-3 text-sm font-semibold transition-shadow hover:shadow-sm ${PILLS[value] || 'bg-google-gray-100 text-google-gray-600'}`, render: () => label(value) }} />
  );
}

// ---- Feedback ----

const ToastContext = createContext(() => {});
export const useToast = () => useContext(ToastContext);

export function ToastProvider({ children }) {
  const [message, setMessage] = useState('');
  const timer = useRef(null);
  const show = useCallback((text) => {
    setMessage(text);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setMessage(''), 3000);
  }, []);
  useEffect(() => () => clearTimeout(timer.current), []);
  return (
    <ToastContext.Provider value={show}>
      {children}
      {message && (
        <div role="status" className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] flex items-center gap-2 rounded-lg bg-google-gray-900 px-4 py-2.5 text-base text-white shadow-lg">
          <CheckCircle className="h-4 w-4 text-google-green" />{message}
        </div>
      )}
    </ToastContext.Provider>
  );
}

// ---- Data ----

// Loads one read endpoint and reloads it on demand. Does nothing when the workspace has not opted into it.
export function useLoad(path, params) {
  const { can, call } = useConsumer();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const key = JSON.stringify(params || {});
  const reload = useCallback(async () => {
    if (!can(path)) return;
    try {
      setData(await call(path, JSON.parse(key)));
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }, [path, key, can, call]);
  useEffect(() => { reload(); }, [reload]);
  return { data, error, reload };
}

// Runs an action (one endpoint call). On success it says so (when given a message), reloads, and returns the result.
export function useAction(reload) {
  const { call } = useConsumer();
  const toast = useToast();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const run = async (path, params, done) => {
    setBusy(true);
    try {
      const result = await call(path, params);
      setError('');
      if (done) toast(done);
      await reload?.();
      return result;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setBusy(false);
    }
  };
  return { run, error, busy, setError };
}

// ---- Panels ----

function useEscape(onClose) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);
}

// A small centred dialog, for a quick confirmation
export function Modal({ title, onClose, children }) {
  useEscape(onClose);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div role="dialog" aria-modal="true" aria-label={title} className="w-full max-w-md max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold text-xl text-google-teal-dark">{title}</h3>
          <button onClick={onClose} aria-label="Close" className="text-google-gray-500 hover:text-google-gray-900"><X className="h-5 w-5" /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

// A side panel: the page stays visible behind it, so adding or editing feels light
export function Drawer({ title, onClose, children }) {
  useEscape(onClose);
  return (
    <div className="fixed inset-0 z-50 bg-black/30" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <aside role="dialog" aria-modal="true" aria-label={title} className="absolute right-0 top-0 h-full w-full max-w-md overflow-y-auto bg-white p-6 shadow-2xl">
        <div className="flex justify-between items-center mb-5">
          <h3 className="font-bold text-xl text-google-teal-dark">{title}</h3>
          <button onClick={onClose} aria-label="Close" className="text-google-gray-500 hover:text-google-gray-900"><X className="h-5 w-5" /></button>
        </div>
        {children}
      </aside>
    </div>
  );
}

// A form in a side panel. fields: { name, label, type: text|number|select|textarea|email, options, required, step, hint }.
// onSubmit gets the values and returns true when it worked, which closes the panel.
export function FormModal({ title, fields, initial = {}, submitLabel = 'Save', onSubmit, onClose, error, busy }) {
  const [values, setValues] = useState(() => Object.fromEntries(fields.map((f) => [f.name, Array.isArray(initial[f.name]) ? initial[f.name].join('\n') : initial[f.name] ?? ''])));
  const [localError, setLocalError] = useState('');
  const set = (name, value) => setValues((cur) => ({ ...cur, [name]: value }));
  const submit = async (e) => {
    e.preventDefault();
    const missing = fields.find((f) => f.required && f.type === 'select' && !values[f.name]);
    if (missing) { setLocalError(`Choose a value for ${missing.label.toLowerCase()}.`); return; }
    setLocalError('');
    const params = {};
    fields.forEach((f) => {
      const raw = values[f.name];
      if (raw === '' || raw === undefined) return;
      params[f.name] = f.type === 'number' ? Number(raw) : f.type === 'lines' ? String(raw).split('\n').map((x) => x.trim()).filter(Boolean) : raw;
    });
    if (await onSubmit(params)) onClose();
  };
  return (
    <Drawer title={title} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <ErrorNote error={localError || error} />
        {fields.map((f) => (
          <label key={f.name} className="block">
            <span className="block mb-1 text-base font-semibold text-google-gray-800">{f.label}{f.required ? '' : <span className="font-normal text-google-gray-500"> (optional)</span>}</span>
            {f.type === 'select' ? (
              <Dropdown ariaLabel={f.label} value={values[f.name]} onChange={(v) => set(f.name, v)}
                options={f.options.map((o) => (typeof o === 'string' ? { value: o, label: label(o) } : { value: o.value, label: o.label }))} />
            ) : f.type === 'textarea' || f.type === 'lines' ? (
              <textarea className={FIELD} rows={3} aria-label={f.label} required={f.required} value={values[f.name]} onChange={(e) => set(f.name, e.target.value)} />
            ) : (
              <input className={FIELD} aria-label={f.label} type={f.type || 'text'} step={f.type === 'number' ? (f.step ?? 'any') : undefined} min={f.min} required={f.required}
                value={values[f.name]} onChange={(e) => set(f.name, e.target.value)} />
            )}
            {f.hint && <span className="block mt-1 text-sm text-google-gray-500">{f.hint}</span>}
          </label>
        ))}
        <div className="flex gap-2 pt-2">
          <button type="submit" disabled={busy} className="inline-flex items-center justify-center rounded-lg google-btn-gradient font-semibold text-white shadow-sm transition-[filter] text-base py-2 px-5 disabled:opacity-60">{busy ? 'Saving...' : submitLabel}</button>
          <button type="button" onClick={onClose} className="google-btn-secondary text-base py-2 px-4">Cancel</button>
        </div>
      </form>
    </Drawer>
  );
}

// ---- Page furniture ----

// Each service has its own colour, used in the menu, the page header and the highlights
export const SERVICE_LOOK = {
  maas: { name: 'Management as a Service', icon: Building2, tint: 'bg-google-blue-light text-google-blue-dark', solid: 'bg-google-blue', edge: 'border-google-blue', text: 'text-google-blue-dark' },
  paas: { name: 'Product as a Service', icon: Package, tint: 'bg-google-green-light text-google-green', solid: 'bg-google-green', edge: 'border-google-green', text: 'text-google-green' },
  taas: { name: 'Transport as a Service', icon: Truck, tint: 'bg-google-yellow-light text-[#B06000]', solid: 'bg-google-yellow', edge: 'border-google-yellow', text: 'text-[#B06000]' },
  saas: { name: 'Support as a Service', icon: LifeBuoy, tint: 'bg-google-red-light text-google-red', solid: 'bg-google-red', edge: 'border-google-red', text: 'text-google-red' }
};

// The title of a page, what it is for, and its one main action
export function PageHeader({ title, subtitle, action }) {
  const look = SERVICE_LOOK[useRoute().service];
  const Icon = look.icon;
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div className="min-w-0">
        <div className="mb-1 flex items-center gap-1.5 text-xs font-medium text-google-gray-500">
          <Icon className={`h-3.5 w-3.5 ${look.text}`} />{look.name}<span aria-hidden="true">›</span><span className="text-google-gray-700">{title}</span>
        </div>
        <h2 className="text-2xl font-semibold leading-tight tracking-tight text-google-teal-dark">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-google-gray-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

const TONES = {
  blue: 'bg-google-blue-light text-google-blue-dark', green: 'bg-google-green-light text-google-green', yellow: 'bg-google-yellow-light text-[#B06000]',
  red: 'bg-google-red-light text-google-red', teal: 'bg-google-blue-light text-google-teal'
};

// One number worth seeing at a glance
export function Kpi({ icon: Icon, label: text, value, hint, tone = 'blue' }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-google-gray-200 bg-white px-4 py-3 shadow-sm">
      <div className="min-w-0">
        <div className="text-xs font-medium uppercase tracking-wide text-google-gray-500">{text}</div>
        <div className="mt-1 text-2xl font-semibold leading-tight text-google-teal-dark truncate">{value}</div>
        {hint && <div className="mt-0.5 text-xs text-google-gray-500 truncate">{hint}</div>}
      </div>
      {Icon && <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${TONES[tone]}`}><Icon className="h-4 w-4" /></span>}
    </div>
  );
}

// The cards share the full width: 3 cards split it in thirds, anything else in 4 columns.
export const Kpis = ({ children }) => (
  <div className={`grid grid-cols-2 ${React.Children.toArray(children).length === 3 ? 'lg:grid-cols-3' : 'lg:grid-cols-4'} gap-3 mb-4`}>{children}</div>
);

// A solid, calm progress bar
export function Bar({ value, max, tone = 'blue' }) {
  const colour = { blue: 'bg-google-blue', green: 'bg-google-green', yellow: 'bg-google-yellow', red: 'bg-google-red', teal: 'bg-google-blue-dark' }[tone];
  return <div className="h-1.5 rounded-full bg-google-gray-100 overflow-hidden"><div className={`h-full rounded-full ${colour}`} style={{ width: `${max ? Math.max(2, (value / max) * 100) : 0}%` }} /></div>;
}

// A round badge with someone's first letter
export const Avatar = ({ name }) => (
  <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-google-blue-light text-sm font-bold text-google-blue-dark">{(name || '?').trim().charAt(0).toUpperCase()}</span>
);

// A product picture that shows a neutral tile when the image cannot load
export function Thumb({ src, alt = '' }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) return <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-google-gray-100 text-google-gray-400 text-sm font-bold">{(alt || '?').charAt(0)}</span>;
  return <img src={src} alt={alt} onError={() => setFailed(true)} className="h-10 w-10 shrink-0 rounded-lg border border-google-gray-200 object-cover" />;
}

// Previous / next for a long list, so the page never grows with the data. page starts at 0.
export function Pager({ page, pageSize, total, onChange }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (total <= pageSize) return null;
  const from = page * pageSize + 1;
  const to = Math.min(total, (page + 1) * pageSize);
  const step = 'rounded-lg border border-google-gray-300 bg-white p-1.5 text-google-gray-700 hover:bg-google-gray-50 disabled:opacity-40 disabled:hover:bg-white';
  return (
    <div className="mt-3 flex items-center justify-between gap-3 border-t border-google-gray-100 pt-3 text-sm text-google-gray-600">
      <span>{from}-{to} of {total.toLocaleString()}</span>
      <div className="flex items-center gap-2">
        <button aria-label="Previous page" disabled={page === 0} onClick={() => onChange(page - 1)} className={step}><ChevronLeft className="h-4 w-4" /></button>
        <span className="min-w-[5rem] text-center">Page {page + 1} of {pages}</span>
        <button aria-label="Next page" disabled={page >= pages - 1} onClick={() => onChange(page + 1)} className={step}><ChevronRight className="h-4 w-4" /></button>
      </div>
    </div>
  );
}
