import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { ErrorNote, FIELD } from '../consumer/ui';

// A conversation with the assistant of the current service, in place of four separate text/voice forms.
// Text goes through the service's text endpoint; the reply and any suggested follow-ups appear in the thread.
const TEXT = {
  paas: { path: '/paas/assistant/chat/text-to-text/v1', field: 'message' },
  taas: { path: '/taas/assistant/delivery/text-to-text/v1', field: 'message' },
  saas: { path: '/saas/assistant/support/text-to-text/v1', field: 'message' },
  maas: { path: '/maas/assistant/account-help/ask/v1', field: 'question' }
};

export default function AssistantChat({ service, call, can }) {
  const spec = TEXT[service];
  const [thread, setThread] = useState([]); // { from: 'you' | 'assistant', text, actions? }
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const session = useRef(undefined);
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView?.({ block: 'nearest' }); }, [thread, busy]);

  if (!spec || !can(spec.path)) {
    return <div className="py-6 text-center text-base text-google-gray-600">Typed chat is not switched on for this assistant.</div>;
  }
  const send = async (message) => {
    const q = message.trim();
    if (!q || busy) return;
    setThread((t) => [...t, { from: 'you', text: q }]);
    setText('');
    setBusy(true);
    setError('');
    try {
      const data = await call(spec.path, { [spec.field]: q, ...(session.current ? { session_id: session.current } : {}) });
      if (data.session_id) session.current = data.session_id;
      setThread((t) => [...t, { from: 'assistant', text: data.reply || data.answer || data.message || 'Done.', actions: data.suggested_actions }]);
    } catch (err) {
      setError(err.message || 'The assistant could not answer.');
    } finally {
      setBusy(false);
    }
  };
  const lastActions = thread.length && thread[thread.length - 1].from === 'assistant' ? thread[thread.length - 1].actions : null;
  return (
    <section className="google-card flex flex-col p-4 sm:p-5" aria-label="Assistant chat">
      <div className="mb-3 flex min-h-[16rem] max-h-[28rem] flex-1 flex-col gap-3 overflow-y-auto" aria-live="polite">
        {thread.length === 0 && (
          <div className="m-auto max-w-sm text-center text-sm text-google-gray-500">
            <Sparkles className="mx-auto mb-2 h-6 w-6 text-google-blue" />Ask a question to get started.
          </div>
        )}
        {thread.map((m, i) => (
          <div key={i} className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-base ${m.from === 'you' ? 'self-end bg-google-blue text-white' : 'self-start bg-google-gray-100 text-google-gray-900'}`}>{m.text}</div>
        ))}
        {busy && <div className="self-start rounded-2xl bg-google-gray-100 px-4 py-2 text-sm text-google-gray-500">Thinking...</div>}
        <div ref={end} />
      </div>
      {lastActions?.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {lastActions.map((a) => <button key={a} type="button" onClick={() => send(a)} className="rounded-full border border-google-gray-300 px-3 py-1 text-sm text-google-gray-700 hover:bg-google-gray-50">{a}</button>)}
        </div>
      )}
      <ErrorNote error={error} />
      <form onSubmit={(e) => { e.preventDefault(); send(text); }} className="flex gap-2">
        <input className={FIELD} aria-label="Your message" placeholder="Type your question" value={text} onChange={(e) => setText(e.target.value)} />
        <button type="submit" disabled={busy || !text.trim()} className="inline-flex shrink-0 items-center gap-1.5 rounded-lg google-btn-gradient px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"><Send className="h-4 w-4" />Send</button>
      </form>
    </section>
  );
}
