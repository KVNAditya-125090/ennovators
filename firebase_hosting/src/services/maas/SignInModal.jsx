import React, { useState } from 'react';
import { X, Sparkles, Lock, Mail, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react';
import { login, requestPasswordReset } from './index';
import { navigate } from '../../router';
import { DEMO_ACCOUNTS } from './demoAccounts';
import { useSettings } from '../../settings/SettingsProvider';

export default function SignInModal({ isOpen, onClose, onSignInSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [forgot, setForgot] = useState(false);
  const [resetBusy, setResetBusy] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const { t } = useSettings();

  if (!isOpen) return null;

  const fillDemo = (account) => {
    setEmail(account.email);
    setPassword(account.password);
    setError('');
  };

  const sendReset = async () => {
    if (!email) { setError('Enter your email above first.'); return; }
    setError(''); setResetBusy(true);
    try { await requestPasswordReset(email); setResetSent(true); }
    catch (err) { setError(err.message || 'Could not send the reset link. Please try again.'); }
    finally { setResetBusy(false); }
  };

  const openMailbox = () => { onClose(); navigate(`/mailbox?email=${encodeURIComponent(email)}`); };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await login(email, password);
      setPassword('');
      onSignInSuccess(user);
    } catch (err) {
      setError(err.status === 401 ? 'Invalid email or password.' : 'Could not reach the server. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-google-gray-200 relative overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-start pb-4 border-b border-google-gray-200">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl google-gradient-diag flex items-center justify-center text-white shadow-sm">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-google-teal-dark">{t('signin.title')}</h3>
              <p className="text-xs text-google-gray-500">{t('signin.subtitle')}</p>
            </div>
          </div>
          <button onClick={onClose} aria-label="Close" className="p-1 text-google-gray-400 hover:text-google-gray-700 rounded-full hover:bg-google-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="py-6 space-y-4">
          <div>
            <label htmlFor="signin-email" className="block text-xs font-bold text-google-gray-700 uppercase tracking-wider mb-2">Email</label>
            <div className="relative">
              <Mail className="h-4 w-4 text-google-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                id="signin-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                required
                autoFocus
                placeholder="you@company.com"
                className="w-full rounded-lg border border-google-gray-300 pl-10 pr-3 py-2.5 text-sm text-google-gray-900 focus:outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue/20"
              />
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label htmlFor="signin-password" className="block text-xs font-bold text-google-gray-700 uppercase tracking-wider">Password</label>
              <button type="button" onClick={() => { setForgot((v) => !v); setError(''); }} className="text-xs font-medium text-google-teal hover:underline">Forgot password?</button>
            </div>
            <div className="relative">
              <Lock className="h-4 w-4 text-google-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                id="signin-password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                placeholder="Your password"
                className="w-full rounded-lg border border-google-gray-300 pl-10 pr-10 py-2.5 text-sm text-google-gray-900 focus:outline-none focus:border-google-blue focus:ring-2 focus:ring-google-blue/20"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-google-gray-500 hover:text-google-gray-800"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {forgot && (
            <div className="rounded-lg bg-google-blue-light px-3 py-2 text-sm text-google-gray-800 space-y-2">
              {resetSent ? (
                <>
                  <p>If {email} has an account, a reset link was sent. In this demo nothing is emailed: the mail is in the demo mailbox.</p>
                  <button type="button" onClick={openMailbox} className="font-medium text-google-teal hover:underline">Open the demo mailbox</button>
                </>
              ) : (
                <>
                  <p>We will send a reset link to the email above.</p>
                  <button type="button" onClick={sendReset} disabled={resetBusy} className="font-medium text-google-teal hover:underline disabled:opacity-60">
                    {resetBusy ? 'Sending...' : 'Send reset link'}
                  </button>
                </>
              )}
            </div>
          )}

          {error && (
            <div role="alert" className="flex items-center gap-2 rounded-lg bg-google-red-light text-google-red px-3 py-2 text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button type="submit" disabled={loading} className="w-full google-btn-primary py-3 text-sm disabled:opacity-70">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Lock className="h-4 w-4" />}
            <span>{loading ? 'Signing in...' : 'Sign in'}</span>
          </button>


          {/* Demo accounts, out of the way until asked for */}
          <details className="group pt-3 border-t border-google-gray-100">
            <summary className="cursor-pointer list-none text-center text-xs text-google-gray-500 hover:text-google-teal">{t('signin.demo')}</summary>
            <div className="mt-2 space-y-1 max-h-60 overflow-y-auto pr-1">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  onClick={() => fillDemo(account)}
                  className="w-full rounded-lg px-3 py-1.5 text-left hover:bg-google-gray-100 transition-colors"
                >
                  <span className="flex items-center justify-between gap-3">
                    <span className="text-xs font-medium text-google-gray-700">{account.group} · {account.role}</span>
                    <span className="text-[11px] text-google-gray-500">{account.password}</span>
                  </span>
                  <span className="block truncate text-xs text-google-gray-500">{account.email}</span>
                </button>
              ))}
            </div>
          </details>
        </form>
      </div>
    </div>
  );
}
