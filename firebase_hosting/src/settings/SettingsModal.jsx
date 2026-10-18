import React, { useEffect } from 'react';
import { X, Settings, Volume2, Mic, Check, Loader2, AlertCircle } from 'lucide-react';
import { useSettings } from './SettingsProvider';
import { LANGUAGES, MODES } from './languages';
import { speak } from './speech';

// The account's settings: the language used across the app, and how to talk to the assistants.
const NEEDS = { t2s: 'speak', s2t: 'listen', s2s: 'both' }; // which browser features a mode needs

export default function SettingsModal() {
  const { t, language, speech, modes, setLanguage, setMode, closeSettings, canSpeak, canListen, state } = useSettings();

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') closeSettings(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [closeSettings]);

  const missing = (mode) => (NEEDS[mode] === 'speak' && !canSpeak) || (NEEDS[mode] === 'listen' && !canListen) || (NEEDS[mode] === 'both' && (!canSpeak || !canListen));
  const anyMissing = MODES.some((m) => modes[m] && missing(m));

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs animate-fade-in" onMouseDown={(e) => { if (e.target === e.currentTarget) closeSettings(); }}>
      <div role="dialog" aria-modal="true" aria-label={t('settings.title')} className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-google-gray-200 bg-white p-6 shadow-2xl sm:p-7">
        <div className="mb-5 flex items-start justify-between border-b border-google-gray-200 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl google-gradient-diag text-white shadow-sm"><Settings className="h-5 w-5" /></div>
            <h3 className="text-lg font-semibold text-google-teal-dark">{t('settings.title')}</h3>
          </div>
          <button onClick={closeSettings} aria-label="Close" className="rounded-lg p-1.5 text-google-gray-500 hover:bg-google-gray-100"><X className="h-5 w-5" /></button>
        </div>

        <section className="mb-6">
          <label htmlFor="language" className="mb-1 block text-sm font-semibold text-google-gray-900">{t('settings.language')}</label>
          <p className="mb-2 text-sm text-google-gray-600">{t('settings.language_help')}</p>
          <select id="language" value={language} onChange={(e) => setLanguage(e.target.value)}
            className="w-full rounded-lg border border-google-gray-300 bg-white px-3 py-2.5 text-base focus:border-google-blue focus:outline-none focus:ring-4 focus:ring-google-blue/15">
            {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.native}{l.native !== l.label ? ` (${l.label})` : ''}</option>)}
          </select>
        </section>

        <section>
          <div className="mb-1 text-sm font-semibold text-google-gray-900">{t('settings.modes')}</div>
          <p className="mb-2 text-sm text-google-gray-600">{t('settings.modes_help')}</p>
          <ul className="space-y-2">
            {MODES.map((mode) => (
              <li key={mode}>
                <label className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition ${modes[mode] ? 'border-google-blue bg-google-blue-light/40' : 'border-google-gray-200 hover:bg-google-gray-50'}`}>
                  <input type="checkbox" checked={Boolean(modes[mode])} disabled={mode === 't2t'} onChange={(e) => setMode(mode, e.target.checked)} className="mt-1 h-4 w-4 accent-google-blue" />
                  <span className="min-w-0 flex-1">
                    <span className="block text-base font-medium text-google-gray-900">{t(`mode.${mode}`)}</span>
                    <span className="block text-sm text-google-gray-600">{t(`mode.${mode}_help`)}</span>
                  </span>
                  {mode === 't2s' && <Volume2 className="mt-1 h-4 w-4 shrink-0 text-google-gray-500" aria-hidden="true" />}
                  {mode === 's2t' && <Mic className="mt-1 h-4 w-4 shrink-0 text-google-gray-500" aria-hidden="true" />}
                  {mode === 's2s' && <><Mic className="mt-1 h-4 w-4 shrink-0 text-google-gray-500" aria-hidden="true" /><Volume2 className="mt-1 h-4 w-4 shrink-0 text-google-gray-500" aria-hidden="true" /></>}
                </label>
              </li>
            ))}
          </ul>
          {anyMissing && (
            <div role="alert" className="mt-3 flex items-start gap-2 rounded-lg bg-google-yellow-light px-3 py-2 text-sm text-[#B06000]">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{!canSpeak ? t('settings.unsupported_speak') : t('settings.unsupported_listen')}</span>
            </div>
          )}
          <button type="button" disabled={!canSpeak} onClick={() => speak(t('settings.test_sentence'), speech)}
            className="mt-3 inline-flex items-center gap-2 rounded-lg border border-google-gray-300 px-3 py-2 text-sm font-medium text-google-gray-800 hover:bg-google-gray-50 disabled:opacity-50">
            <Volume2 className="h-4 w-4" />{t('settings.test_voice')}
          </button>
        </section>

        <div className="mt-6 flex items-center justify-between border-t border-google-gray-100 pt-4">
          <span className="flex items-center gap-1.5 text-sm text-google-gray-500" aria-live="polite">
            {state === 'saving' && <><Loader2 className="h-4 w-4 animate-spin" />{t('settings.saving')}</>}
            {state === 'saved' && <><Check className="h-4 w-4 text-google-green" />{t('settings.saved')}</>}
            {state === 'failed' && <><AlertCircle className="h-4 w-4 text-google-red" />Not saved</>}
          </span>
          <button onClick={closeSettings} className="rounded-lg google-btn-gradient px-5 py-2 text-sm font-semibold text-white shadow-sm">{t('settings.done')}</button>
        </div>
      </div>
    </div>
  );
}
