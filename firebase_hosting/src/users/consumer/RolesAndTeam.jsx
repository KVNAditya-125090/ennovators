import React, { useState } from 'react';
import { Plus, X, Crown, UserPlus, ShieldCheck } from 'lucide-react';
import { useConsumer, useLoad, useAction, Section, Empty, ErrorNote, FormModal, PageHeader, Avatar, Btn, Pill, RowMenu, SearchBox, Tabs, Chips, FIELD } from './ui';

const SERVICE_NAMES = { MaaS: 'Management', PaaS: 'Product', TaaS: 'Transport', SaaS: 'Support' };

// What the selected role may do: the allowed features as chips, and a picker to allow more
function Access({ role, onChanged }) {
  const { can, endpoints } = useConsumer();
  const { data, error, reload } = useLoad('/maas/role/permission/read/v1', { role_id: role.role_id });
  const act = useAction(async () => { await reload(); await onChanged(); });
  const [query, setQuery] = useState('');
  const [service, setService] = useState('');
  const granted = new Set(data?.permissions ?? []);
  const staff = Object.values(endpoints).filter((e) => ['Consumer staff', 'System', 'AI', 'Partner'].includes(e.actor));
  const allowed = staff.filter((e) => granted.has(e.path));
  const q = query.trim().toLowerCase();
  const options = staff.filter((e) => !granted.has(e.path) && (!service || e.service === service) && (!q || e.description.toLowerCase().includes(q)));
  const editable = role.active && can('/maas/role/permission/assign/v1');
  const revocable = role.active && can('/maas/role/permission/revoke/v1');
  const countFor = (code) => staff.filter((e) => !granted.has(e.path) && e.service === code).length;
  if (!can('/maas/role/permission/read/v1')) return null;
  return (
    <div className="space-y-3">
      <ErrorNote error={error || act.error} />
      <div>
        <div className="text-base font-semibold text-google-gray-900 mb-2">Allowed now <span className="font-normal text-google-gray-500">• {allowed.length}</span></div>
        <div className="flex flex-wrap gap-2">
          {allowed.map((e) => (
            <span key={e.path} className="inline-flex items-center gap-1.5 rounded-full bg-google-green-light pl-3 pr-2 py-1 text-sm font-medium text-google-gray-900">
              {e.description}
              {revocable && <button aria-label={`Stop allowing: ${e.description}`} disabled={act.busy} onClick={() => act.run('/maas/role/permission/revoke/v1', { role_id: role.role_id, endpoint_path: e.path })} className="text-google-gray-600 hover:text-google-red"><X className="h-3.5 w-3.5" /></button>}
            </span>
          ))}
          {allowed.length === 0 && <span className="text-base text-google-gray-500">This role cannot do anything yet. Add features below.</span>}
        </div>
      </div>
      {editable && (
        <div>
          <div className="text-base font-semibold text-google-gray-900 mb-2">Allow more</div>
          <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
            <Chips value={service} onChange={setService} options={[{ value: '', label: 'All' }, ...Object.entries(SERVICE_NAMES).map(([code, name]) => ({ value: code, label: name, count: countFor(code) }))]} />
            <SearchBox value={query} onChange={setQuery} placeholder="Search features" />
          </div>
          <ul className="max-h-64 overflow-y-auto rounded-xl border border-google-gray-200 divide-y divide-google-gray-100">
            {options.slice(0, 60).map((e) => (
              <li key={e.path} className="flex items-center justify-between gap-3 px-3 py-1 hover:bg-google-gray-50">
                <span className="text-base text-google-gray-800">{e.description} <span className="text-sm text-google-gray-400">• {SERVICE_NAMES[e.service]}</span></span>
                <Btn disabled={act.busy} onClick={() => act.run('/maas/role/permission/assign/v1', { role_id: role.role_id, endpoint_path: e.path })}>Allow</Btn>
              </li>
            ))}
            {options.length === 0 && <li className="px-4 py-6 text-center text-base text-google-gray-500">Nothing left to allow here.</li>}
            {options.length > 60 && <li className="px-4 py-2 text-center text-sm text-google-gray-500">Showing 60 of {options.length}. Search to narrow down.</li>}
          </ul>
        </div>
      )}
    </div>
  );
}

function People({ role, mails, afterChange }) {
  const { can } = useConsumer();
  const act = useAction(afterChange);
  const [mail, setMail] = useState('');
  const invite = async (e) => {
    e.preventDefault();
    if (await act.run('/maas/role-mail/assign/v1', { role_id: role.role_id, mail }, `Invite sent to ${mail}`)) setMail('');
  };
  return (
    <div>
      <div className="mb-2 text-base font-semibold text-google-gray-900">People <span className="font-normal text-google-gray-500">• {mails.length}</span></div>
      <div className="mb-3">
        {can('/maas/role-mail/assign/v1') && role.active && (
          <form onSubmit={invite} className="flex w-full gap-2 md:max-w-md">
            <input type="email" required value={mail} onChange={(e) => setMail(e.target.value)} placeholder="Invite by email: name@company.com" aria-label="Email to invite" className={`${FIELD} min-w-0 flex-1`} />
            <Btn kind="primary" type="submit" disabled={act.busy}><UserPlus className="h-3.5 w-3.5 inline mr-1" />Invite</Btn>
          </form>
        )}
      </div>
      <ErrorNote error={act.error} />
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-2">
        {mails.map((m) => (
          <div key={m.mail} className="flex items-center gap-3 rounded-xl border border-google-gray-200 px-3 py-1.5">
            <Avatar name={m.mail} />
            <div className="min-w-0 flex-1"><div className="text-base font-medium text-google-gray-900 truncate">{m.mail}</div><div className="text-sm text-google-gray-500">{m.status === 'invited' ? 'Invite sent' : 'Active'}</div></div>
            {can('/maas/role-mail/remove/v1') && <button aria-label={`Remove ${m.mail}`} disabled={act.busy} onClick={() => act.run('/maas/role-mail/remove/v1', { role_id: role.role_id, mail: m.mail }, `${m.mail} removed`)} className="text-google-gray-400 hover:text-google-red"><X className="h-4 w-4" /></button>}
          </div>
        ))}
        {mails.length === 0 && <div className="text-base text-google-gray-500">Nobody holds this role yet.</div>}
      </div>
    </div>
  );
}

// The two things to do with a role: choose what it may do, and see what has happened to it
function RoleDetail({ role, sent, canLog, onChanged }) {
  const { can } = useConsumer();
  const tabs = [
    { key: 'access', label: 'Access', show: can('/maas/role/permission/read/v1') },
    { key: 'log', label: 'Activity log', count: sent.length, show: canLog }
  ].filter((t) => t.show);
  const [tab, setTab] = useState(tabs[0]?.key);
  const current = tabs.some((t) => t.key === tab) ? tab : tabs[0]?.key;
  if (!current) return null;
  return (
    <div>
      <Tabs tabs={tabs} value={current} onChange={setTab} />
      {current === 'access' && <Access role={role} onChanged={onChanged} />}
      {current === 'log' && (sent.length === 0 ? <Empty>Nothing has happened to this role yet.</Empty> : (
        <div className="divide-y divide-google-gray-100 text-base text-google-gray-700">
          {sent.map((m, i) => <div key={i} className="py-2.5 flex gap-4"><span className="text-sm text-google-gray-500 whitespace-nowrap pt-0.5">{m.at}</span><span>{m.message}{m.actor && <span className="text-google-gray-500"> — by {m.actor}</span>}</span></div>)}
        </div>
      ))}
    </div>
  );
}

export default function RolesAndTeam() {
  const { can } = useConsumer();
  const roles = useLoad('/maas/role/read/v1');
  const mails = useLoad('/maas/role-mail/list/v1');
  const staff = useLoad('/maas/user/staff/list/v1');
  const log = useLoad('/maas/notification/root-mail/log/read/v1');
  const act = useAction(async () => { await roles.reload(); await log.reload(); });
  const [selectedId, setSelectedId] = useState(null);
  const [dialog, setDialog] = useState(null); // 'new' or the role being edited
  if (!can('/maas/role/read/v1')) return null;

  const list = roles.data?.roles ?? [];
  const selected = list.find((r) => r.role_id === selectedId) ?? list[0];
  const allMails = mails.data?.role_mails ?? [];
  const countFor = (r) => allMails.filter((m) => m.role_id === r.role_id).length;
  const root = (staff.data?.staff ?? []).find((m) => m.role.endsWith('Root'));
  const sent = log.data?.mails ?? [];
  const afterChange = async () => { await mails.reload(); await log.reload(); };
  const open = (d) => { act.setError(''); setDialog(d); };
  const fields = [{ name: 'name', label: 'Role name', required: true }, { name: 'description', label: 'What this role does', type: 'textarea' }];

  return (
    <div>
      <PageHeader title="Roles and Team" subtitle="Create the jobs in your company, invite people into them and choose what each job can do"
        action={can('/maas/role/create/v1') && <Btn kind="primary" className="px-3 py-1.5 text-sm" onClick={() => open('new')}><Plus className="h-4 w-4 inline mr-1" />New role</Btn>} />
      <ErrorNote error={roles.error || mails.error || (!dialog && act.error)} />
      <div className="grid lg:grid-cols-[16rem_1fr] gap-3 items-start">
        <div className="space-y-2.5">
          {root && (
            <div className="flex items-center gap-3 rounded-2xl border border-google-blue-light bg-google-blue-light/40 px-4 py-3">
              <Crown className="h-5 w-5 text-google-teal shrink-0" />
              <div className="min-w-0"><div className="text-base font-semibold text-google-gray-900 truncate">{root.name}</div><div className="text-sm text-google-gray-600">Root • full access</div></div>
            </div>
          )}
          <Section>
            <ul className="space-y-1 -m-2">
              {list.map((r) => (
                <li key={r.role_id}>
                  <button onClick={() => setSelectedId(r.role_id)} aria-current={selected?.role_id === r.role_id}
                    className={`w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-base transition-colors ${selected?.role_id === r.role_id ? 'bg-google-blue-light/60 font-semibold text-google-gray-900' : 'text-google-gray-700 hover:bg-google-gray-50'}`}>
                    <ShieldCheck className={`h-4 w-4 shrink-0 ${selected?.role_id === r.role_id ? 'text-google-teal' : 'text-google-gray-400'}`} />
                    <span className={`flex-1 truncate ${r.active ? '' : 'line-through text-google-gray-500'}`}>{r.name}</span>
                    <span className="text-sm font-normal text-google-gray-500">{countFor(r)}</span>
                  </button>
                </li>
              ))}
              {list.length === 0 && <li><Empty>No roles yet.</Empty></li>}
            </ul>
          </Section>
        </div>

        <div className="space-y-3 min-w-0">
          {!selected ? <Section><Empty>Create the first role to get started.</Empty></Section> : (
            <>
              <Section>
                <div className="flex flex-wrap justify-between items-start gap-3 mb-3">
                  <div>
                    <div className="flex items-center gap-2"><h3 className="text-xl font-bold text-google-teal-dark">{selected.name}</h3><Pill value={selected.active ? 'resolved' : 'closed'} label={selected.active ? 'Active' : 'Inactive'} /></div>
                    <div className="text-base text-google-gray-600">{selected.description || 'No description'}</div>
                  </div>
                  <RowMenu items={[
                    { label: 'Edit role', hidden: !(can('/maas/role/update/v1') && selected.active), onClick: () => open(selected) },
                    { label: 'Deactivate', danger: true, hidden: !(can('/maas/role/deactivate/v1') && selected.active), onClick: async () => { if (window.confirm(`Deactivate the ${selected.name} role?`)) await act.run('/maas/role/deactivate/v1', { role_id: selected.role_id }, `${selected.name} deactivated`); } }
                  ]} />
                </div>
                <People key={`p-${selected.role_id}`} role={selected} mails={allMails.filter((m) => m.role_id === selected.role_id)} afterChange={afterChange} />
              </Section>
              <Section>
                <RoleDetail key={`d-${selected.role_id}`} role={selected} sent={sent.filter((m) => m.role_id === selected.role_id)} canLog={can('/maas/notification/root-mail/log/read/v1')} onChanged={log.reload} />
              </Section>
            </>
          )}
        </div>
      </div>
      {dialog && (
        <FormModal title={dialog === 'new' ? 'New role' : `Edit ${dialog.name}`} fields={fields} initial={dialog === 'new' ? {} : dialog} error={act.error} busy={act.busy} onClose={() => setDialog(null)}
          submitLabel={dialog === 'new' ? 'Create role' : 'Save'}
          onSubmit={async (v) => {
            const result = await act.run(dialog === 'new' ? '/maas/role/create/v1' : '/maas/role/update/v1', dialog === 'new' ? v : { ...v, role_id: dialog.role_id }, dialog === 'new' ? 'Role created' : 'Role saved');
            if (result && dialog === 'new') setSelectedId(result.role_id);
            return Boolean(result);
          }} />
      )}
    </div>
  );
}
