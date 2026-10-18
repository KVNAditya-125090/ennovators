import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { DEFAULT_PREFERENCES, speechCode } from './languages';
import { translate } from './strings';
import { canListen, canSpeak, stopSpeaking } from './speech';
import { loadSession, saveSession } from '../services/maas/session';
import { savePreferences } from '../services/maas';
import SettingsModal from './SettingsModal';

// The person's language and the way they talk to the assistants, available to every screen:
//   t(key)            a word of the app's shell in their language
//   language, speech  the language code and the browser's voice code for it ("hi", "hi-IN")
//   modes             { t2t, t2s, s2t, s2s }
//   openSettings()    shows the settings panel (the account menu calls it)
// Signed in, the choice is kept with their account. Signed out, the language is remembered in this browser.
const Context = createContext(null);
const LOCAL_KEY = 'lakshmi.language';

const readLocalLanguage = () => {
  try { return window.localStorage.getItem(LOCAL_KEY) || 'en'; } catch { return 'en'; }
};

const initial = (user) => ({
  language: user?.preferences?.language || (user ? 'en' : readLocalLanguage()),
  modes: { ...DEFAULT_PREFERENCES.modes, ...(user?.preferences?.modes || {}) }
});

export function SettingsProvider({ user, children }) {
  const [prefs, setPrefs] = useState(() => initial(user));
  const [open, setOpen] = useState(false);
  const [state, setState] = useState('idle'); // idle | saving | saved | failed
  const email = user?.email;
  const timer = useRef(null);

  // a different person signs in or out: take their choice
  useEffect(() => { setPrefs(initial(user)); }, [email]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { document.documentElement.lang = prefs.language; }, [prefs.language]);
  useEffect(() => () => clearTimeout(timer.current), []);

  const update = useCallback((next) => {
    setPrefs(next);
    stopSpeaking();
    if (!email) {
      try { window.localStorage.setItem(LOCAL_KEY, next.language); } catch { /* storage may be blocked */ }
      return;
    }
    const session = loadSession();
    if (session) saveSession({ ...session, preferences: next });
    setState('saving');
    savePreferences(next)
      .then(() => { setState('saved'); clearTimeout(timer.current); timer.current = setTimeout(() => setState('idle'), 2000); })
      .catch(() => setState('failed'));
  }, [email]);

  const value = useMemo(() => ({
    language: prefs.language,
    speech: speechCode(prefs.language),
    modes: prefs.modes,
    canSpeak, canListen,
    t: (key) => translate(prefs.language, key),
    setLanguage: (language) => update({ ...prefs, language }),
    setMode: (mode, on) => update({ ...prefs, modes: { ...prefs.modes, [mode]: mode === 't2t' ? true : on } }),
    state, open, openSettings: () => setOpen(true), closeSettings: () => setOpen(false)
  }), [prefs, state, open, update]);

  return (
    <Context.Provider value={value}>
      {children}
      {open && <SettingsModal />}
    </Context.Provider>
  );
}

export const useSettings = () => useContext(Context);
