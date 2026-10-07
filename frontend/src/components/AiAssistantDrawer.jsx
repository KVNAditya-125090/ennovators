import React, { useState } from 'react';
import { X, Sparkles, Send, Camera, CheckCircle, RefreshCw, MessageSquare } from 'lucide-react';

export default function AiAssistantDrawer({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    { sender: 'ai', text: 'Hello! I am your Gemini Flash Conversational Assistant. How can I help you with shopping, returns, or circular trade-ins today?' }
  ]);
  const [inputText, setInputText] = useState('');
  const [triageResult, setTriageResult] = useState(null);
  const [isTyping, setIsTyping] = useState(false);

  if (!isOpen) return null;

  const handleSend = async () => {
    if (!inputText.trim()) return;
    const userMsg = inputText;
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setInputText('');
    setIsTyping(true);

    try {
      const res = await fetch('/api/v1/saas/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      }).then(r => r.json());

      setMessages(prev => [...prev, { sender: 'ai', text: res.reply, actions: res.suggested_actions }]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'ai', text: 'Vertex AI Gemini Flash Mock: I can assist with product search, returns, or live multi-seller bids!' }]);
    } finally {
      setIsTyping(false);
    }
  };

  const simulatePhotoTriage = async () => {
    setIsTyping(true);
    try {
      const res = await fetch('/api/v1/saas/returns/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: 'SKU-WATCH-G3', image_url: 'sample.jpg' })
      }).then(r => r.json());

      setTriageResult(res);
      setMessages(prev => [
        ...prev,
        { sender: 'user', text: '📸 Uploaded return photo for AI condition grading' },
        { sender: 'ai', text: `Gemini Flash & TabFM visual triage complete! Result: ${res.ai_evaluated_grade}. Recommended Route: ${res.recommended_channel}.` }
      ]);
    } catch (err) {
      console.warn('Triage error:', err);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end animate-fade-in">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col justify-between border-l border-google-gray-200">
        {/* Drawer Header */}
        <div className="p-4 bg-gradient-to-r from-google-teal to-google-blue text-white flex justify-between items-center shadow-xs">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5" />
            <div>
              <h3 className="font-bold text-sm">Gemini Flash AI Assistant</h3>
              <p className="text-[10px] text-white/80">Support as a Service (SaaS)</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-white/80 hover:text-white rounded-full hover:bg-white/10">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-google-gray-50">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-google-teal text-white rounded-tr-none'
                  : 'bg-white text-google-gray-800 border border-google-gray-200 shadow-xs rounded-tl-none'
              }`}>
                {msg.text}

                {msg.actions && (
                  <div className="mt-2 pt-2 border-t border-google-gray-100 flex flex-wrap gap-1">
                    {msg.actions.map((act, i) => (
                      <button
                        key={i}
                        onClick={() => act.includes('Photo') ? simulatePhotoTriage() : setInputText(act)}
                        className="px-2 py-1 bg-google-teal-surface text-google-teal rounded-md text-[10px] font-semibold hover:bg-google-teal hover:text-white transition-all"
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
                Gemini Flash is generating response...
              </div>
            </div>
          )}

          {triageResult && (
            <div className="p-3 bg-google-green-light border border-google-green rounded-xl text-xs space-y-1">
              <div className="font-bold text-google-green flex items-center gap-1">
                <CheckCircle className="h-3.5 w-3.5" />
                <span>AI Photo Condition Triage Complete</span>
              </div>
              <div>Grade: <strong>{triageResult.ai_evaluated_grade}</strong></div>
              <div>Recovery Value: <strong>{triageResult.predicted_recovery_percentage}%</strong></div>
              <div>Carbon Saved: <strong>{triageResult.carbon_saved_kg} kg CO2e</strong></div>
            </div>
          )}
        </div>

        {/* Input Controls */}
        <div className="p-3 bg-white border-t border-google-gray-200 space-y-2">
          <div className="flex items-center space-x-2">
            <button
              onClick={simulatePhotoTriage}
              title="Upload Photo for AI Condition Triage"
              className="p-2.5 bg-google-gray-100 text-google-teal rounded-xl hover:bg-google-teal-surface transition-all"
            >
              <Camera className="h-4 w-4" />
            </button>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about products, bids, or returns..."
              className="flex-1 px-3 py-2 border border-google-gray-300 rounded-xl text-xs outline-none focus:ring-2 focus:ring-google-teal"
            />
            <button
              onClick={handleSend}
              className="p-2.5 bg-google-teal text-white rounded-xl hover:bg-google-teal-dark transition-all"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

