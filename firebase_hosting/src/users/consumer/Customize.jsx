import React, { useState, useEffect } from 'react';
import { Store, Layers } from 'lucide-react';
import { Switch } from '../owner/shared';
import { SERVICES, availablePages, pageId } from './consumerPages';
import { useConsumer, useLoad, useAction, Section, Empty, ErrorNote, PageHeader, Tabs, Btn, Dropdown, SearchBox, Pill, FormModal, SERVICE_LOOK, FIELD } from './ui';

// ---------- 1. How each role sees the workspace ----------

function RoleWorkspace({ role, view, onSave, busy, can }) {
  const allIds = SERVICES.flatMap((s) => availablePages(s.key, can).map((p) => pageId(s.key, p.key)));
  const pages = new Set(view?.pages ?? allIds);
  const landing = view?.landing && pages.has(view.landing) ? view.landing : [...pages][0] ?? 'maas/overview';
  const labelOf = (id) => { const [svc, key] = id.split('/'); return SERVICES.find((s) => s.key === svc)?.pages.find((p) => p.key === key)?.label ?? id; };

  const save = (nextPages, nextLanding) => {
    const list = allIds.filter((id) => nextPages.has(id));
    onSave({ landing: nextLanding && list.includes(nextLanding) ? nextLanding : list[0], pages: list });
  };
  const toggle = (id, on) => {
    const next = new Set(pages);
    if (on) next.add(id); else next.delete(id);
    save(next, landing);
  };
  const toggleService = (svc, on) => {
    const next = new Set(pages);
    availablePages(svc, can).forEach((p) => (on ? next.add(pageId(svc, p.key)) : next.delete(pageId(svc, p.key))));
    save(next, landing);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-lg font-bold text-google-gray-900">{role.name}</div>
          <div className="text-sm text-google-gray-600">{view ? 'Sees only what you tick below.' : 'Sees everything. Untick what this role does not need.'} A page also needs the role to be allowed its features on Roles and Team.</div>
        </div>
        <div className="flex items-center gap-2">
          {view && <Btn disabled={busy} onClick={() => onSave({ landing: 'maas/overview', pages: allIds })}>Reset to everything</Btn>}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-xl bg-google-blue-light/50 px-4 py-3">
        <span className="text-base font-medium text-google-gray-900">First page after sign-in</span>
        <Dropdown ariaLabel="First page" value={landing} disabled={busy || pages.size === 0} onChange={(id) => save(pages, id)}
          options={[...pages].map((id) => ({ value: id, label: labelOf(id) }))} className="min-w-[14rem]" />
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {SERVICES.map((svc) => {
          const list = availablePages(svc.key, can);
          if (list.length === 0) return null;
          const look = SERVICE_LOOK[svc.key];
          const Icon = look.icon;
          const on = list.filter((p) => pages.has(pageId(svc.key, p.key))).length;
          return (
            <div key={svc.key} className="rounded-xl border border-google-gray-200 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5"><span className={`flex h-8 w-8 items-center justify-center rounded-lg ${look.tint}`}><Icon className="h-4 w-4" /></span><div><div className="text-base font-semibold text-google-gray-900">{svc.label}</div><div className="text-sm text-google-gray-500">{on} of {list.length} pages</div></div></div>
                <Switch checked={on > 0} disabled={busy} label={`Show ${svc.label}`} onChange={(v) => toggleService(svc.key, v)} />
              </div>
              <ul className="space-y-1.5">
                {list.map((p) => (
                  <li key={p.key}>
                    <label className="flex items-center gap-2.5 rounded-lg px-2 py-1 text-base text-google-gray-800 hover:bg-google-gray-50">
                      <input type="checkbox" checked={pages.has(pageId(svc.key, p.key))} disabled={busy} onChange={(e) => toggle(pageId(svc.key, p.key), e.target.checked)} />
                      {p.label}
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TeamWorkspaces() {
  const { can } = useConsumer();
  const roles = useLoad('/maas/role/read/v1');
  const template = useLoad('/maas/interface/template/read/v1');
  const act = useAction(template.reload);
  const [selectedId, setSelectedId] = useState(null);
  const list = (roles.data?.roles ?? []).filter((r) => r.active);
  const selected = list.find((r) => r.role_id === selectedId) ?? list[0];
  const views = template.data?.role_views ?? {};
  const save = async (view) => {
    await act.run('/maas/interface/template/role-view/update/v1', { role_id: selected.role_id, view }, `${selected.name} workspace saved`);
  };
  return (
    <div>
      <ErrorNote error={roles.error || template.error || act.error} />
      <div className="grid gap-4 lg:grid-cols-[16rem_1fr] items-start">
        <Section>
          <ul className="-m-2 space-y-1">
            {list.map((r) => (
              <li key={r.role_id}>
                <button onClick={() => setSelectedId(r.role_id)} aria-current={selected?.role_id === r.role_id}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-base transition-colors ${selected?.role_id === r.role_id ? 'bg-google-blue-light/60 font-semibold text-google-gray-900' : 'text-google-gray-700 hover:bg-google-gray-50'}`}>
                  <span className="flex-1 truncate">{r.name}</span>
                  <span className={`text-sm font-normal ${views[r.role_id] ? 'text-google-teal' : 'text-google-gray-400'}`}>{views[r.role_id] ? 'Custom' : 'Default'}</span>
                </button>
              </li>
            ))}
            {list.length === 0 && <li><Empty>Create a role first.</Empty></li>}
          </ul>
        </Section>
        <Section>
          {selected ? <RoleWorkspace key={selected.role_id} role={selected} view={views[selected.role_id]} onSave={save} busy={act.busy} can={can} /> : <Empty>Pick a role to set what it sees.</Empty>}
        </Section>
      </div>
    </div>
  );
}

// ---------- 2. The storefront your customers see ----------

const COLOURS = ['#1A73E8', '#188038', '#E37400', '#D93025', '#8430CE', '#202124'];
const DEFAULTS = (name) => ({ layout: { style: 'grid', hero: true }, branding: { brand_name: name, tagline: 'Good things, given a second life', colour: COLOURS[0], logo: '' }, sections: [] });

function StorefrontPreview({ draft, features }) {
  const { branding, layout } = draft;
  const colour = branding.colour || COLOURS[0];
  const shown = features.filter((f) => draft.sections.includes(f.path));
  return (
    <div className="overflow-hidden rounded-2xl border border-google-gray-300 bg-white shadow-sm">
      <div className="flex items-center gap-1.5 border-b border-google-gray-200 bg-google-gray-50 px-3 py-2">
        <span className="h-2.5 w-2.5 rounded-full bg-google-red" /><span className="h-2.5 w-2.5 rounded-full bg-google-yellow" /><span className="h-2.5 w-2.5 rounded-full bg-google-green" />
        <span className="ml-3 truncate rounded-md bg-white px-3 py-0.5 text-xs text-google-gray-500">{(branding.brand_name || 'your-store').toLowerCase().replace(/\s+/g, '')}.example</span>
      </div>
      <div className="flex items-center gap-2.5 border-b border-google-gray-100 px-5 py-3">
        {branding.logo ? <img src={branding.logo} alt="" className="h-8 w-8 rounded-lg object-cover" /> : <span className="flex h-8 w-8 items-center justify-center rounded-lg font-bold text-white" style={{ background: colour }}>{(branding.brand_name || '?').charAt(0).toUpperCase()}</span>}
        <span className="text-lg font-bold text-google-gray-900">{branding.brand_name || 'Your brand'}</span>
      </div>
      {layout.hero && (
        <div className="px-5 py-8 text-white" style={{ background: `linear-gradient(135deg, ${colour}, ${colour}CC)` }}>
          <div className="text-2xl font-extrabold">{branding.brand_name || 'Your brand'}</div>
          <div className="mt-1 text-base opacity-90">{branding.tagline || 'Your tagline goes here'}</div>
        </div>
      )}
      <div className="p-5">
        {shown.length === 0 ? <div className="py-6 text-center text-base text-google-gray-500">Pick features to show your customers.</div> : (
          <div className={layout.style === 'list' ? 'space-y-2' : 'grid gap-3 sm:grid-cols-2'}>
            {shown.slice(0, 8).map((f) => (
              <div key={f.path} className="flex items-center gap-3 rounded-xl border border-google-gray-200 p-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white" style={{ background: colour }}><Layers className="h-4 w-4" /></span>
                <span className="text-base font-medium text-google-gray-900">{f.description}</span>
              </div>
            ))}
            {shown.length > 8 && <div className="text-sm text-google-gray-500">and {shown.length - 8} more</div>}
          </div>
        )}
      </div>
    </div>
  );
}

function Storefront() {
  const { can, endpoints, workspace } = useConsumer();
  const template = useLoad('/maas/interface/template/read/v1');
  const act = useAction(template.reload);
  const t = template.data;
  const [draft, setDraft] = useState(null);
  const [query, setQuery] = useState('');
  const [publishing, setPublishing] = useState(false);
  const features = Object.values(endpoints).filter((e) => e.actor === 'Customer');

  useEffect(() => {
    // fields that were never filled in start from sensible defaults, so the editor is never blank
    if (t?.exists) setDraft({ layout: t.layout, branding: { ...DEFAULTS(workspace?.tenant?.name ?? '').branding, ...Object.fromEntries(Object.entries(t.branding).filter(([, v]) => v)) }, sections: t.sections.map((s) => (typeof s === 'string' ? s : s.path)) });
  }, [t]);

  if (!t) return <ErrorNote error={template.error} />;
  if (!t.exists) {
    return (
      <Section>
        <div className="mx-auto max-w-md py-8 text-center">
          <span className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-google-blue-light text-google-blue-dark"><Store className="h-6 w-6" /></span>
          <div className="text-lg font-bold text-google-gray-900">Build the storefront your customers see</div>
          <p className="mb-4 mt-1 text-base text-google-gray-600">Choose your branding, layout and which features customers can use. They only ever see your brand.</p>
          <ErrorNote error={act.error} />
          {can('/maas/interface/template/create/v1') && <Btn kind="primary" className="px-5 py-2 text-sm" disabled={act.busy}
            onClick={() => act.run('/maas/interface/template/create/v1', { name: 'Customer storefront', ...DEFAULTS(workspace?.tenant?.name ?? '') }, 'Storefront created')}>Create storefront</Btn>}
        </div>
      </Section>
    );
  }
  if (!draft) return null;

  const saved = { layout: t.layout, branding: t.branding, sections: t.sections.map((s) => (typeof s === 'string' ? s : s.path)) };
  const dirty = JSON.stringify(saved) !== JSON.stringify(draft);
  const setBrand = (k, v) => setDraft({ ...draft, branding: { ...draft.branding, [k]: v } });
  const q = query.trim().toLowerCase();
  const matches = features.filter((f) => !q || f.description.toLowerCase().includes(q));
  const toggleFeature = (path, on) => setDraft({ ...draft, sections: on ? [...draft.sections, path] : draft.sections.filter((p) => p !== path) });
  const status = t.published && !dirty && !t.unpublished_changes ? <Pill value="resolved" label={`Published v${t.version}`} /> : <Pill value="placed" label={t.version ? `Published v${t.version}, unpublished changes` : 'Draft'} />;

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-base text-google-gray-700">Your customer storefront {status}</div>
        <div className="flex items-center gap-2">
          <Btn disabled={!dirty || act.busy} onClick={() => act.run('/maas/interface/template/update/v1', draft, 'Draft saved')}>Save draft</Btn>
          {can('/maas/interface/template/publish/v1') && <Btn kind="primary" disabled={dirty || act.busy} onClick={() => { act.setError(''); setPublishing(true); }} className="px-4">Publish</Btn>}
        </div>
      </div>
      <ErrorNote error={act.error && !publishing ? act.error : ''} />
      <div className="grid gap-4 xl:grid-cols-[1fr_1.1fr] items-start">
        <div className="space-y-3">
          <Section title="Brand">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block"><span className="mb-1 block text-sm font-semibold text-google-gray-800">Brand name</span><input className={FIELD} value={draft.branding.brand_name ?? ''} onChange={(e) => setBrand('brand_name', e.target.value)} /></label>
              <label className="block"><span className="mb-1 block text-sm font-semibold text-google-gray-800">Logo address <span className="font-normal text-google-gray-500">(optional)</span></span><input className={FIELD} value={draft.branding.logo ?? ''} onChange={(e) => setBrand('logo', e.target.value)} placeholder="https://" /></label>
              <label className="block sm:col-span-2"><span className="mb-1 block text-sm font-semibold text-google-gray-800">Tagline</span><input className={FIELD} value={draft.branding.tagline ?? ''} onChange={(e) => setBrand('tagline', e.target.value)} /></label>
            </div>
            <div className="mt-3"><span className="mb-1.5 block text-sm font-semibold text-google-gray-800">Colour</span>
              <div className="flex gap-2">{COLOURS.map((c) => <button key={c} type="button" aria-label={`Colour ${c}`} aria-pressed={draft.branding.colour === c} onClick={() => setBrand('colour', c)} className={`h-8 w-8 rounded-full border-2 ${draft.branding.colour === c ? 'border-google-gray-900' : 'border-transparent'}`} style={{ background: c }} />)}</div>
            </div>
          </Section>
          <Section title="Layout">
            <div className="flex flex-wrap items-center gap-4">
              <Dropdown ariaLabel="Layout style" value={draft.layout.style} onChange={(v) => setDraft({ ...draft, layout: { ...draft.layout, style: v } })} options={[{ value: 'grid', label: 'Grid of cards' }, { value: 'list', label: 'Simple list' }]} className="min-w-[12rem]" />
              <label className="flex items-center gap-2 text-base text-google-gray-800"><Switch checked={Boolean(draft.layout.hero)} label="Show a banner" onChange={(v) => setDraft({ ...draft, layout: { ...draft.layout, hero: v } })} />Show a banner at the top</label>
            </div>
          </Section>
          <Section title="What customers can do" subtitle={`${draft.sections.length} of ${features.length} features shown`} toolbar={<SearchBox value={query} onChange={setQuery} placeholder="Search features" />}>
            <ul className="max-h-64 divide-y divide-google-gray-100 overflow-y-auto rounded-xl border border-google-gray-200">
              {matches.map((f) => (
                <li key={f.path}><label className="flex items-center gap-3 px-3 py-2 text-base text-google-gray-800 hover:bg-google-gray-50">
                  <input type="checkbox" checked={draft.sections.includes(f.path)} onChange={(e) => toggleFeature(f.path, e.target.checked)} />
                  <span className="flex-1">{f.description}</span><span className="text-sm text-google-gray-400">{SERVICE_LOOK[f.service.toLowerCase()]?.name.split(' ')[0]}</span>
                </label></li>
              ))}
              {matches.length === 0 && <li className="px-4 py-6 text-center text-base text-google-gray-500">No features match.</li>}
            </ul>
          </Section>
        </div>
        <div className="xl:sticky xl:top-2"><div className="mb-2 text-sm font-semibold text-google-gray-500">Live preview</div><StorefrontPreview draft={draft} features={features} /></div>
      </div>
      {publishing && <FormModal title="Publish storefront" fields={[{ name: 'version_note', label: 'What changed?', type: 'textarea' }]} submitLabel="Publish" error={act.error} busy={act.busy} onClose={() => setPublishing(false)}
        onSubmit={async (v) => Boolean(await act.run('/maas/interface/template/publish/v1', v, 'Storefront published'))} />}
    </div>
  );
}

export default function Customize() {
  const { can } = useConsumer();
  const tabs = [
    { key: 'team', label: 'Team workspaces', show: can('/maas/interface/template/role-view/update/v1') && can('/maas/role/read/v1') },
    { key: 'store', label: 'Customer storefront', show: can('/maas/interface/template/read/v1') }
  ].filter((t) => t.show);
  const [tab, setTab] = useState(tabs[0]?.key);
  const current = tabs.some((t) => t.key === tab) ? tab : tabs[0]?.key;
  return (
    <div>
      <PageHeader title="Customization" subtitle="Choose what each role sees, and design what your customers see" />
      {tabs.length > 1 && <Tabs tabs={tabs} value={current} onChange={setTab} />}
      {current === 'team' && <TeamWorkspaces />}
      {current === 'store' && <Storefront />}
      {!current && <Empty>Your workspace has not opted into customization.</Empty>}
    </div>
  );
}
