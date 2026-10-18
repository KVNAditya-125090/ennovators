// The languages a person can choose. `speech` is the language code the browser's voice features use.
export const LANGUAGES = [
  { code: 'en', label: 'English', native: 'English', speech: 'en-IN' },
  { code: 'hi', label: 'Hindi', native: 'हिन्दी', speech: 'hi-IN' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు', speech: 'te-IN' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்', speech: 'ta-IN' },
  { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ', speech: 'kn-IN' },
  { code: 'mr', label: 'Marathi', native: 'मराठी', speech: 'mr-IN' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা', speech: 'bn-IN' },
  { code: 'gu', label: 'Gujarati', native: 'ગુજરાતી', speech: 'gu-IN' },
  { code: 'ml', label: 'Malayalam', native: 'മലയാളം', speech: 'ml-IN' }
];

export const speechCode = (code) => LANGUAGES.find((l) => l.code === code)?.speech ?? 'en-IN';

// How a person can talk to an assistant. t2t is always on: typing and reading must stay possible.
export const MODES = ['t2t', 't2s', 's2t', 's2s'];
export const DEFAULT_PREFERENCES = { language: 'en', modes: { t2t: true, t2s: false, s2t: false, s2s: false } };
