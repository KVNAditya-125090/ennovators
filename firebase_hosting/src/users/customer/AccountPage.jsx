import React, { useState, useEffect, useCallback } from 'react';
import { Download } from 'lucide-react';
import { Section, Dropdown, ErrorNote, FIELD, Pill, useToast } from '../consumer/ui';

// The signed-in shopper's own account: profile, language, password, their data, and closing the account.
// Registering, signing in and resetting a password are not here: they happen before sign-in (the sign-in screen).
const P = '/maas/customer-account';
const PATHS = {
  read: `${P}/profile/read/v1`, update: `${P}/profile/update/v1`, password: `${P}/password/change/v1`,
  language: '/maas/locale/language/customer-select/v1', exportData: `${P}/data/export/v1`,
  deactivate: `${P}/deactivate/v1`, erase: `${P}/data/delete/v1`
};
const LANGUAGES = [['en', 'English'], ['hi', 'Hindi'], ['ta', 'Tamil'], ['te', 'Telugu'], ['es', 'Spanish'], ['fr', 'French'], ['de', 'German']];

const Primary = ({ busy, children, ...rest }) => (
  <button type="submit" disabled={busy} {...rest} className="inline-flex items-center justify-center rounded-lg google-btn-gradient px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-60">{busy ? 'Working...' : children}</button>
);
const Label = ({ text, optional, children }) => (
  <label className="block">
    <span className="mb-1 block text-sm font-semibold text-google-gray-800">{text}{optional && <span className="font-normal text-google-gray-500"> (optional)</span>}</span>
    {children}
  </label>
);

// Runs one call, reporting success as a toast and failure beside the form
function useDo(call, toast) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const run = async (path, params, done) => {
    setBusy(true); setError('');
    try { const data = await call(path, params); if (done) toast(done); return data; }
    catch (err) { setError(err.message || 'The request failed.'); return null; }
    finally { setBusy(false); }
  };
  return { run, busy, error, setError };
}

function ProfileCard({ call, can }) {
  const toast = useToast();
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({ full_name: '', phone: '', preferred_language: 'en', line1: '', city: '', postcode: '', country: '' });
  const { run, busy, error } = useDo(call, toast);
  const [loadError, setLoadError] = useState('');
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const load = useCallback(async () => {
    if (!can(PATHS.read)) return;
    try {
      const p = (await call(PATHS.read, {})).profile;
      setProfile(p);
      setForm({ full_name: p.full_name || '', phone: p.phone || '', preferred_language: p.preferred_language || 'en',
        line1: p.address?.line1 || '', city: p.address?.city || '', postcode: p.address?.postcode || '', country: p.address?.country || '' });
    } catch (err) { setLoadError(err.message); }
  }, [call, can]);
  useEffect(() => { load(); }, [load]);
  const editable = can(PATHS.update);
  const showLanguage = !can(PATHS.language);
  const save = async (e) => {
    e.preventDefault();
    const address = Object.fromEntries([['line1', form.line1], ['city', form.city], ['postcode', form.postcode], ['country', form.country]].filter(([, v]) => v));
    const params = { full_name: form.full_name, phone: form.phone, ...(showLanguage ? { preferred_language: form.preferred_language } : {}), ...(Object.keys(address).length ? { address } : {}) };
    if (await run(PATHS.update, Object.fromEntries(Object.entries(params).filter(([, v]) => v !== '')), 'Profile saved')) await load();
  };
  return (
    <Section title="Your profile" subtitle={profile ? `${profile.email} · ${profile.account_type === 'business' ? 'Business' : 'Individual'} account` : undefined}
      action={profile && <Pill value={profile.verified ? 'resolved' : 'open'} label={profile.verified ? 'Email verified' : 'Email not verified'} />}>
      <ErrorNote error={loadError || error} />
      {!profile && !loadError && can(PATHS.read) && <p className="text-sm text-google-gray-500">Loading...</p>}
      {(profile || !can(PATHS.read)) && (
        <form onSubmit={save} className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <Label text="Full name"><input className={FIELD} disabled={!editable} value={form.full_name} onChange={set('full_name')} /></Label>
            <Label text="Phone" optional><input className={FIELD} disabled={!editable} value={form.phone} onChange={set('phone')} /></Label>
            {showLanguage && (
              <Label text="Preferred language">
                <Dropdown ariaLabel="Preferred language" value={form.preferred_language} onChange={(v) => setForm((f) => ({ ...f, preferred_language: v }))} options={LANGUAGES.map(([value, text]) => ({ value, label: text }))} />
              </Label>
            )}
          </div>
          <fieldset className="grid gap-3 md:grid-cols-2">
            <legend className="mb-1 text-sm font-semibold text-google-gray-800">Delivery address</legend>
            <div className="md:col-span-2"><Label text="Street address" optional><input className={FIELD} disabled={!editable} value={form.line1} onChange={set('line1')} /></Label></div>
            <Label text="City" optional><input className={FIELD} disabled={!editable} value={form.city} onChange={set('city')} /></Label>
            <Label text="Postcode" optional><input className={FIELD} disabled={!editable} value={form.postcode} onChange={set('postcode')} /></Label>
            <Label text="Country" optional><input className={FIELD} disabled={!editable} value={form.country} onChange={set('country')} /></Label>
          </fieldset>
          {editable ? <Primary busy={busy}>Save profile</Primary> : <p className="text-sm text-google-gray-500">This seller does not let you edit your profile here.</p>}
        </form>
      )}
    </Section>
  );
}

function LanguageCard({ call }) {
  const toast = useToast();
  const [language, setLanguage] = useState('en');
  const { run, busy, error } = useDo(call, toast);
  return (
    <Section title="Language" subtitle="The language this store shows you">
      <ErrorNote error={error} />
      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); run(PATHS.language, { language }, 'Language updated'); }}>
        <div className="w-56"><Dropdown ariaLabel="Display language" value={language} onChange={setLanguage} options={LANGUAGES.map(([value, text]) => ({ value, label: text }))} /></div>
        <Primary busy={busy}>Use this language</Primary>
      </form>
    </Section>
  );
}

function PasswordCard({ call }) {
  const toast = useToast();
  const [v, setV] = useState({ current: '', next: '', again: '' });
  const { run, busy, error, setError } = useDo(call, toast);
  const set = (k) => (e) => setV((x) => ({ ...x, [k]: e.target.value }));
  const submit = async (e) => {
    e.preventDefault();
    if (v.next.length < 8) { setError('Use at least 8 characters for the new password.'); return; }
    if (v.next !== v.again) { setError('The new password and its confirmation do not match.'); return; }
    if (await run(PATHS.password, { current_password: v.current, new_password: v.next }, 'Password changed')) setV({ current: '', next: '', again: '' });
  };
  return (
    <Section title="Password" subtitle="Change the password you sign in with">
      <ErrorNote error={error} />
      <form onSubmit={submit} className="grid gap-3 md:grid-cols-3">
        <Label text="Current password"><input className={FIELD} type="password" autoComplete="current-password" value={v.current} onChange={set('current')} required /></Label>
        <Label text="New password"><input className={FIELD} type="password" autoComplete="new-password" value={v.next} onChange={set('next')} required /></Label>
        <Label text="Confirm new password"><input className={FIELD} type="password" autoComplete="new-password" value={v.again} onChange={set('again')} required /></Label>
        <div className="md:col-span-3"><Primary busy={busy}>Change password</Primary></div>
      </form>
    </Section>
  );
}

function DataCard({ call }) {
  const toast = useToast();
  const { run, busy, error } = useDo(call, toast);
  const download = async () => {
    const data = await run(PATHS.exportData, {}, 'Your data is downloading');
    if (!data) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(data.data ?? data, null, 2)], { type: 'application/json' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: 'my-data.json' });
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <Section title="Your data" subtitle="Everything this store holds about you: profile, orders, tickets and more">
      <ErrorNote error={error} />
      <button type="button" onClick={download} disabled={busy} className="google-btn-secondary inline-flex items-center gap-2 px-4 py-2 text-sm disabled:opacity-60"><Download className="h-4 w-4" />{busy ? 'Preparing...' : 'Download my data'}</button>
    </Section>
  );
}

// Closing the account or erasing the data: needs the password and a second, explicit confirmation
function DangerCard({ call, can }) {
  const toast = useToast();
  const [action, setAction] = useState(null); // 'deactivate' | 'erase'
  const [v, setV] = useState({ password: '', reason: '' });
  const [message, setMessage] = useState('');
  const { run, busy, error } = useDo(call, toast);
  const options = [
    can(PATHS.deactivate) && { key: 'deactivate', path: PATHS.deactivate, title: 'Deactivate my account', text: 'Your account is closed and you are signed out. Your orders stay on record.', go: 'Yes, deactivate my account' },
    can(PATHS.erase) && { key: 'erase', path: PATHS.erase, title: 'Delete my data', text: 'Asks the store to erase the data it holds about you. This cannot be undone.', go: 'Yes, delete my data' }
  ].filter(Boolean);
  if (options.length === 0) return null;
  const chosen = options.find((o) => o.key === action);
  const submit = async (e) => {
    e.preventDefault();
    const data = await run(chosen.path, { password: v.password, ...(v.reason ? { reason: v.reason } : {}) });
    if (data) { setMessage(data.message || 'Your request was received.'); setAction(null); setV({ password: '', reason: '' }); }
  };
  return (
    <Section title="Close your account" subtitle="These actions need your password" className="border-google-red/40">
      {message && <div role="status" className="mb-3 rounded-lg bg-google-green-light px-3 py-2 text-sm font-medium text-google-green">{message}</div>}
      <div className="flex flex-wrap gap-2">
        {options.map((o) => (
          <button key={o.key} type="button" onClick={() => { setAction(o.key); setMessage(''); }} aria-pressed={action === o.key}
            className="rounded-lg border border-google-red px-4 py-2 text-sm font-semibold text-google-red hover:bg-google-red-light">{o.title}</button>
        ))}
      </div>
      {chosen && (
        <form onSubmit={submit} className="mt-4 space-y-3 rounded-xl bg-google-red-light p-4">
          <p className="text-sm text-google-gray-900">{chosen.text}</p>
          <ErrorNote error={error} />
          <Label text="Your password"><input className={FIELD} type="password" autoComplete="current-password" value={v.password} onChange={(e) => setV((x) => ({ ...x, password: e.target.value }))} required /></Label>
          <Label text="Why are you leaving?" optional><input className={FIELD} value={v.reason} onChange={(e) => setV((x) => ({ ...x, reason: e.target.value }))} /></Label>
          <div className="flex gap-2">
            <button type="submit" disabled={busy} className="rounded-lg bg-google-red px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">{busy ? 'Working...' : chosen.go}</button>
            <button type="button" onClick={() => setAction(null)} className="google-btn-secondary px-4 py-2 text-sm">Keep my account</button>
          </div>
        </form>
      )}
    </Section>
  );
}

export default function AccountPage({ call, can }) {
  return (
    <div className="space-y-4">
      {(can(PATHS.read) || can(PATHS.update)) && <ProfileCard call={call} can={can} />}
      {can(PATHS.language) && <LanguageCard call={call} />}
      {can(PATHS.password) && <PasswordCard call={call} />}
      {can(PATHS.exportData) && <DataCard call={call} />}
      <DangerCard call={call} can={can} />
    </div>
  );
}
