// Voice in and out, using what the browser provides (no extra service, nothing is sent anywhere by this file).
// Reading aloud and listening are separate features, and a browser may have one without the other.
const Recognition = typeof window !== 'undefined' ? window.SpeechRecognition || window.webkitSpeechRecognition : undefined;

export const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window;
export const canListen = Boolean(Recognition);

// Reads text aloud in a language ("hi-IN"). Uses a voice made for that language when the device has one.
export function speak(text, lang) {
  if (!canSpeak || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang;
  const voices = window.speechSynthesis.getVoices();
  const voice = voices.find((v) => v.lang === lang) || voices.find((v) => v.lang.startsWith(lang.slice(0, 2)));
  if (voice) utterance.voice = voice;
  window.speechSynthesis.speak(utterance);
}

export const stopSpeaking = () => { if (canSpeak) window.speechSynthesis.cancel(); };

// Listens for one spoken sentence in a language. Returns a function that stops listening.
//   onResult(text)   the words heard      onEnd()   listening finished      onError(message)   it could not listen
export function listen(lang, { onResult, onEnd, onError }) {
  if (!canListen) { onError?.('listen-unsupported'); return () => {}; }
  const recognition = new Recognition();
  recognition.lang = lang;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.onresult = (event) => onResult?.(event.results[0][0].transcript);
  recognition.onerror = (event) => onError?.(event.error);
  recognition.onend = () => onEnd?.();
  recognition.start();
  return () => recognition.stop();
}
