import React, { useState } from 'react';
import { Send, CheckCircle, Loader2 } from 'lucide-react';
import { sendQuery } from './api';

const FIELD = 'w-full resize-none rounded-lg border border-google-gray-300 bg-white px-3 py-2.5 text-sm text-google-gray-900 focus:border-google-blue focus:outline-none focus:ring-2 focus:ring-google-blue/20';
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/;
const MOBILE = /^\+?[0-9][0-9 ()-]{6,18}[0-9]$/;

// Anyone can ask a question from the home page. The team replies by email or phone.
export default function QueryForm() {
  const [form, setForm] = useState({ name: '', email: '', mobile: '', message: '' });
  const [touched, setTouched] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(null);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const problems = {
    name: form.name.trim().length < 2 ? 'Enter your name.' : '',
    email: !EMAIL.test(form.email.trim()) ? 'Enter a valid email address.' : '',
    mobile: !MOBILE.test(form.mobile.trim()) ? 'Enter a valid mobile number.' : '',
    message: form.message.trim().length < 5 ? 'Tell us what you would like to know.' : ''
  };
  const valid = Object.values(problems).every((p) => !p);

  const submit = async (e) => {
    e.preventDefault();
    setTouched(true);
    setError('');
    if (!valid) return;
    setSending(true);
    try {
      const result = await sendQuery({ name: form.name.trim(), email: form.email.trim(), mobile: form.mobile.trim(), message: form.message.trim() });
      setSent({ id: result.query_id, email: form.email.trim() });
      setForm({ name: '', email: '', mobile: '', message: '' });
      setTouched(false);
    } catch (err) {
      setError(err.status === 422 ? 'Some details look wrong. Please check them and try again.' : 'We could not send your query. Please try again.');
    } finally {
      setSending(false);
    }
  };

  if (sent) {
    return (
      <div className="google-card w-full p-8 text-center" role="status">
        <CheckCircle className="h-10 w-10 text-google-green mx-auto" />
        <h3 className="mt-3 text-xl font-bold text-google-gray-900">Thank you, we have your query</h3>
        <p className="mt-2 text-sm text-google-gray-600">Reference <span className="font-semibold text-google-gray-900">{sent.id}</span>. We will reply to {sent.email}, or give you a call.</p>
        <button onClick={() => setSent(null)} className="mt-5 text-sm font-semibold text-google-blue-dark hover:underline">Ask another query</button>
      </div>
    );
  }

  const field = (key, label, props) => (
    <label className="block">
      <span className="block text-xs font-semibold uppercase tracking-wider text-google-gray-600 mb-1.5">{label}</span>
      {key === 'message'
        ? <textarea rows={5} value={form[key]} onChange={set(key)} maxLength={2000} aria-invalid={touched && Boolean(problems[key])} className={FIELD} {...props} />
        : <input value={form[key]} onChange={set(key)} aria-invalid={touched && Boolean(problems[key])} className={FIELD} {...props} />}
      {touched && problems[key] && <span className="block text-xs text-google-red mt-1">{problems[key]}</span>}
    </label>
  );

  return (
    <form onSubmit={submit} noValidate className="google-card w-full p-6 sm:p-8 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {field('name', 'Name', { type: 'text', autoComplete: 'name', maxLength: 80, placeholder: 'Your name' })}
        {field('mobile', 'Mobile number', { type: 'tel', autoComplete: 'tel', maxLength: 20, placeholder: '+91 98765 43210' })}
        {field('email', 'Email', { type: 'email', autoComplete: 'email', maxLength: 120, placeholder: 'you@example.com' })}
      </div>
      {field('message', 'Your query', { placeholder: 'What would you like to know?' })}
      {error && <div className="rounded-lg bg-google-red-light text-google-red px-4 py-3 text-sm" role="alert">{error}</div>}
      <button type="submit" disabled={sending} className="google-btn-primary w-full justify-center py-2.5 disabled:opacity-60">
        {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        <span>{sending ? 'Sending...' : 'Send query'}</span>
      </button>
    </form>
  );
}
