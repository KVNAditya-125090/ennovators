import React, { useState, useEffect } from 'react';
import { Sparkles, Mail, Lock, AlertCircle, CheckCircle, Loader2, ExternalLink } from 'lucide-react';
import { resetPassword, readInvite, acceptInvite, readMailbox } from './index';
import { navigate } from '../../router';
import { loadSession, clearSession, saveSession } from './session';
import { login } from './index';
import { DEMO_ACCOUNTS } from './demoAccounts';

// The pages a mail links to. They work before anyone is signed in. In the demo, nothing is emailed: every "sent" mail
// is kept in an in-app mailbox, opened at /mailbox.
export const MAIL_PATHS = ['/mailbox', '/reset-password', '/accept-invite', '/demo-login'];
export const isMailPath = (path) => MAIL_PATHS.some((p) => path === p || path.startsWith(`${p}/`));

const FIELD = 'w-full rounded-lg border border-google-gray-300 px-3 py-2.5 text-sm text-google-gray-900 focus:outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue/20';
const tokenFromAddress = () => new URLSearchParams(window.location.search).get('token') || '';

function Shell({ title, subtitle, children }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-google-gray-50">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-8 shadow-xl border border-google-gray-200">
        <div className="flex items-center space-x-3 pb-4 border-b border-google-gray-200">
          <div className="h-10 w-10 rounded-xl google-gradient-diag flex items-center justify-center text-white shadow-sm"><Sparkles className="h-6 w-6" /></div>
          <div>
            <h1 className="font-semibold text-lg text-google-teal-dark">{title}</h1>
            {subtitle && <p className="text-xs text-google-gray-500">{subtitle}</p>}
          </div>
        </div>
        <div className="pt-5 space-y-4">{children}</div>
      </div>
    </div>
  );
}

const Problem = ({ text }) => text ? (
  <div role="alert" className="flex items-center gap-2 rounded-lg bg-google-red-light text-google-red px-3 py-2 text-sm"><AlertCircle className="h-4 w-4 shrink-0" /><span>{text}</span></div>
) : null;

const Done = ({ text }) => (
  <div className="flex items-center gap-2 rounded-lg bg-google-green-light text-google-green px-3 py-2 text-sm"><CheckCircle className="h-4 w-4 shrink-0" /><span>{text}</span></div>
);

// Someone may already be signed in on this browser (an invite is opened from another account): then go to sign in means sign out first
const GoSignIn = () => {
  const current = loadSession();
  const go = () => {
    if (!current) { navigate('/'); window.dispatchEvent(new Event('open-signin')); return; }
    clearSession();
    window.location.assign('/?signin=1'); // a fresh load, so nothing of the old account is left on screen
  };
  return (
    <div className="space-y-2">
      {current && <p className="text-sm text-google-gray-600">You are signed in as {current.email || current.name}. Signing in with this account will sign you out first.</p>}
      <button type="button" onClick={go} className="w-full google-btn-primary py-3 text-sm"><Lock className="h-4 w-4" /><span>{current ? 'Sign out and go to sign in' : 'Go to sign in'}</span></button>
    </div>
  );
};

function ResetPassword() {
  const token = tokenFromAddress();
  const [password, setPassword] = useState('');
  const [again, setAgain] = useState('');
  const [error, setError] = useState('');
  const [done, setDone] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (password !== again) { setError('The two passwords do not match.'); return; }
    setError(''); setBusy(true);
    try { setDone((await resetPassword(token, password)).email); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  return (
    <Shell title="Choose a new password" subtitle="Lakshmi demo">
      {done ? (<><Done text={`The password for ${done} was changed.`} /><GoSignIn /></>) : (
        <form onSubmit={submit} className="space-y-4">
          {!token && <Problem text="This page needs the link from the reset mail. Open it from the mailbox." />}
          <div><label htmlFor="new-password" className="block text-xs font-bold text-google-gray-700 uppercase tracking-wider mb-2">New password</label>
            <input id="new-password" type="password" autoComplete="new-password" required minLength={10} value={password} onChange={(e) => setPassword(e.target.value)} className={FIELD} placeholder="At least 10 characters" /></div>
          <div><label htmlFor="again-password" className="block text-xs font-bold text-google-gray-700 uppercase tracking-wider mb-2">Repeat it</label>
            <input id="again-password" type="password" autoComplete="new-password" required value={again} onChange={(e) => setAgain(e.target.value)} className={FIELD} /></div>
          <Problem text={error} />
          <button type="submit" disabled={busy || !token} className="w-full google-btn-primary py-3 text-sm disabled:opacity-70">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Lock className="h-4 w-4" />}<span>{busy ? 'Saving...' : 'Change password'}</span>
          </button>
        </form>
      )}
    </Shell>
  );
}

function AcceptInvite() {
  const token = tokenFromAddress();
  const [invite, setInvite] = useState(null);
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [done, setDone] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) { setError('This page needs the link from the invite mail. Open it from the mailbox.'); return; }
    readInvite(token).then(setInvite).catch((err) => setError(err.message));
  }, [token]);

  const submit = async (e) => {
    e.preventDefault();
    setError(''); setBusy(true);
    try { setDone(await acceptInvite(token, name, password)); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  return (
    <Shell title="Join your team" subtitle="Lakshmi demo">
      {done ? (<><Done text={`You joined ${done.workspace} as ${done.role}. Sign in with ${done.email}.`} /><GoSignIn /></>) : (
        <form onSubmit={submit} className="space-y-4">
          {invite && <p className="text-sm text-google-gray-700">You are invited to <strong>{invite.workspace}</strong> as <strong>{invite.role}</strong>. Your email is <strong>{invite.mail}</strong>.</p>}
          <div><label htmlFor="invite-name" className="block text-xs font-bold text-google-gray-700 uppercase tracking-wider mb-2">Your name</label>
            <input id="invite-name" required value={name} onChange={(e) => setName(e.target.value)} className={FIELD} autoComplete="name" /></div>
          <div><label htmlFor="invite-password" className="block text-xs font-bold text-google-gray-700 uppercase tracking-wider mb-2">Choose a password</label>
            <input id="invite-password" type="password" autoComplete="new-password" required minLength={10} value={password} onChange={(e) => setPassword(e.target.value)} className={FIELD} placeholder="At least 10 characters" /></div>
          <Problem text={error} />
          <button type="submit" disabled={busy || !invite} className="w-full google-btn-primary py-3 text-sm disabled:opacity-70">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}<span>{busy ? 'Joining...' : 'Accept invite'}</span>
          </button>
        </form>
      )}
    </Shell>
  );
}

function Mailbox() {
  const [email, setEmail] = useState(new URLSearchParams(window.location.search).get('email') || '');
  const [mails, setMails] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const open = async (address) => {
    setError(''); setBusy(true);
    try { setMails((await readMailbox(address)).mails); }
    catch (err) { setMails(null); setError(err.status === 404 ? 'The demo mailbox is switched off on this server.' : err.message); }
    finally { setBusy(false); }
  };
  useEffect(() => { if (email) open(email); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  return (
    <Shell title="Demo mailbox" subtitle="Nothing is emailed in the demo. Every mail the app sends is kept here.">
      <form onSubmit={(e) => { e.preventDefault(); open(email); }} className="flex gap-2">
        <div className="relative flex-1">
          <Mail className="h-4 w-4 text-google-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@company.com" aria-label="Mailbox address" className={`${FIELD} pl-10`} />
        </div>
        <button type="submit" disabled={busy} className="google-btn-primary px-4 text-sm disabled:opacity-70">{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Open'}</button>
      </form>
      <Problem text={error} />
      {mails && mails.length === 0 && <p className="text-sm text-google-gray-500">No mail for this address yet.</p>}
      {mails && mails.map((m) => (
        <div key={m.id} className="rounded-xl border border-google-gray-200 p-4 space-y-2">
          <div className="flex items-start justify-between gap-3"><div className="text-sm font-semibold text-google-gray-900">{m.subject}</div><div className="text-xs text-google-gray-500 whitespace-nowrap">{m.at} UTC</div></div>
          <p className="text-sm text-google-gray-700">{m.body}</p>
          {m.link && <a href={m.link} className="inline-flex items-center gap-1.5 text-sm font-medium text-google-teal hover:underline"><ExternalLink className="h-4 w-4" />Open the link in this mail</a>}
        </div>
      ))}
      <button type="button" onClick={() => navigate('/')} className="text-xs text-google-gray-500 hover:text-google-teal">Back to the home page</button>
    </Shell>
  );
}

// /demo-login/<key>: signs in as one of the demo accounts and opens its portal, so nobody has to type a password.
// The accounts and their passwords are made up and already listed on the sign-in screen, so this exposes nothing new.
function DemoLogin({ account }) {
  const [error, setError] = useState('');
  useEffect(() => {
    const found = DEMO_ACCOUNTS.find((a) => a.key === account);
    if (!found) { setError(`There is no demo account called "${account}". Use one of: ${DEMO_ACCOUNTS.map((a) => a.key).join(', ')}.`); return; }
    login(found.email, found.password)
      .then((user) => { saveSession(user); window.location.replace('/'); })
      .catch((err) => setError(err.status === 401 ? 'The demo account did not accept its password. It may have been changed.' : 'Could not reach the server.'));
  }, [account]);
  return (
    <Shell title="Demo sign-in" subtitle="Signing you in with a demo account">
      {error ? <Problem text={error} /> : <p className="flex items-center gap-2 text-sm text-google-gray-700"><Loader2 className="h-4 w-4 animate-spin" />Signing in as {account}...</p>}
    </Shell>
  );
}

export default function MailPages({ path }) {
  if (path.startsWith('/demo-login')) return <DemoLogin account={path.split('/')[2] || ''} />;
  if (path.startsWith('/reset-password')) return <ResetPassword />;
  if (path.startsWith('/accept-invite')) return <AcceptInvite />;
  return <Mailbox />;
}
