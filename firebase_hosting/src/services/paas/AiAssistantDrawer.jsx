import React, { useState, useRef } from 'react';
import { chat } from './index';
import { triageReturn } from '../saas';
import { shrinkPhoto } from '../saas/photo';
import { X, Sparkles, Send, Camera, CheckCircle, Mic, Square } from 'lucide-react';
import { useSettings } from '../../settings/SettingsProvider';
import { speak, stopSpeaking, listen } from '../../settings/speech';

export default function AiAssistantDrawer({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    { sender: 'ai', text: 'Hello! I am your AI shopping assistant. How can I help you with shopping, returns, or circular trade-ins today?' }
  ]);
  const [inputText, setInputText] = useState('');
  const [triageResult, setTriageResult] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const { t, language, speech, modes, canListen } = useSettings();
  const [listening, setListening] = useState(false);
  const stopListening = useRef(null);
  const photoInput = useRef(null); // a hook, so it sits here with the others, above the early return below
  const choosePhoto = () => photoInput.current?.click();
  const voiceIn = (modes.s2t || modes.s2s) && canListen;

  if (!isOpen) return null;

  const handleSend = async (spoken = null) => {
    const userMsg = spoken ?? inputText;
    if (!userMsg.trim()) return;
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setInputText('');
    setIsTyping(true);

    try {
      const res = await chat(userMsg, { language });

      setMessages(prev => [...prev, { sender: 'ai', text: res.reply, actions: res.suggested_actions }]);
      if (spoken !== null ? modes.s2s : modes.t2s) speak(res.reply, speech);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'ai', text: 'I can assist with product search, returns, or live multi-seller bids!' }]);
    } finally {
      setIsTyping(false);
    }
  };

  // Grades the chosen photo with Gemini and shows the grade, estimated value and the route it recommends
  const gradePhoto = async (file) => {
    if (!file) return;
    setIsTyping(true);
    try {
      const res = await triageReturn('', await shrinkPhoto(file));
      setTriageResult(res);
      setMessages(prev => [
        ...prev,
        { sender: 'user', text: `Uploaded a photo for AI condition grading (${file.name})` },
        { sender: 'ai', text: res.ai_evaluated_grade
          ? `${res.ai_evaluated_grade}. ${res.reasoning} Recommended route: ${res.recommended_channel}.`
          : res.reasoning }
      ]);
    } catch (err) {
      setTriageResult(null);
      setMessages(prev => [...prev, { sender: 'ai', text: err.status === 422 || !err.status ? (err.message || 'That photo could not be graded.') : 'The photo could not be graded just now. Please try again.' }]);
    } finally {
      setIsTyping(false);
      if (photoInput.current) photoInput.current.value = '';
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end animate-fade-in">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col justify-between border-l border-google-gray-200">
        {/* Drawer Header */}
        <div className="p-4 google-hero text-white flex justify-between items-center ">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5" />
            <div>
              <h3 className="font-bold text-sm">{t('assistant.title')}</h3>
              <p className="text-[10px] text-white/80">Shopping, delivery and support</p>
            </div>
          </div>
          <button onClick={onClose} aria-label="Close assistant" title="Close" className="p-1 text-white/80 hover:text-white rounded-full hover:bg-white/10">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-google-gray-50">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-google-blue-dark text-white rounded-tr-none'
                  : 'bg-white text-google-gray-800 border border-google-gray-200  rounded-tl-none'
              }`}>
                {msg.text}

                {msg.actions && (
                  <div className="mt-2 pt-2 border-t border-google-gray-100 flex flex-wrap gap-1">
                    {msg.actions.map((act, i) => (
                      <button
                        key={i}
                        onClick={() => act.includes('Photo') ? choosePhoto() : setInputText(act)}
                        className="px-2 py-1 bg-google-blue-light text-google-teal rounded-md text-[10px] font-semibold hover:bg-google-blue-dark hover:text-white transition-all"
                      >
                        {act}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white border border-google-gray-200 rounded-2xl p-3 text-xs text-google-gray-500 animate-pulse">
                {t('assistant.thinking')}
              </div>
            </div>
          )}

          <input ref={photoInput} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" aria-label="Choose a photo to grade" tabIndex={-1} onChange={(e) => gradePhoto(e.target.files?.[0])} />
          {triageResult && triageResult.ai_evaluated_grade && (
            <div className="p-3 bg-google-green-light border border-google-green rounded-xl text-xs space-y-1">
              <div className="font-bold text-google-green flex items-center gap-1">
                <CheckCircle className="h-3.5 w-3.5" />
                <span>AI Photo Condition Triage Complete</span>
              </div>
              <div>Grade: <strong>{triageResult.ai_evaluated_grade}</strong></div>
              <div>Estimated recovery value: <strong>{triageResult.predicted_recovery_percentage}%</strong></div>
              <div>Recommended route: <strong>{triageResult.recommended_channel}</strong></div>
              {triageResult.defects?.length > 0 && <div>Seen: {triageResult.defects.join(', ')}</div>}
            </div>
          )}
        </div>

        {/* Input Controls */}
        <div className="p-3 bg-white border-t border-google-gray-200 space-y-2">
          <div className="flex items-center space-x-2">
            <button
              onClick={choosePhoto}
              title="Upload Photo for AI Condition Triage"
              className="p-2.5 bg-google-gray-100 text-google-teal rounded-xl hover:bg-google-blue-light transition-all"
            >
              <Camera className="h-4 w-4" />
            </button>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={t('assistant.placeholder')}
              className="flex-1 px-3 py-2 border border-google-gray-300 rounded-xl text-xs outline-none focus:ring-2 focus:ring-google-blue-dark"
            />
            {voiceIn && (
              <button
                onClick={() => {
                  if (listening) { stopListening.current?.(); return; }
                  stopSpeaking();
                  setListening(true);
                  stopListening.current = listen(speech, { onResult: (said) => handleSend(said), onEnd: () => setListening(false), onError: () => setListening(false) });
                }}
                aria-pressed={listening}
                aria-label={listening ? t('assistant.stop') : t('assistant.speak')}
                title={listening ? t('assistant.listening') : t('assistant.speak')}
                className={`p-2.5 rounded-xl transition-all ${listening ? 'bg-google-red-light text-google-red' : 'bg-google-gray-100 text-google-teal hover:bg-google-blue-light'}`}
              >
                {listening ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </button>
            )}
            <button
              onClick={() => handleSend()}
              className="p-2.5 bg-google-blue-dark text-white rounded-xl hover:bg-google-blue-deep transition-all"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

