/**
 * SimpleMode — Chat-only interface hiding technical internals
 * 15.2.1
 */
import React, { useState, useRef, useEffect } from 'react';
import type { ChatMessage } from '../../types';
import { Theme } from '../../theme/existing';

interface SimpleModeProps {
  chatHistory: ChatMessage[];
  onSendMessage: (msg: string) => void;
  onSwitchMode: () => void;
}

const SimpleMode: React.FC<SimpleModeProps> = ({ chatHistory, onSendMessage, onSwitchMode }) => {
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatHistory]);

  const send = () => {
    if (!input.trim()) return;
    onSendMessage(input.trim());
    setInput('');
  };

  return (
    <div className="nv-simple-mode">
      <header className="nv-simple-header">
        <h1 style={{ margin: 0, fontSize: 18, background: `linear-gradient(135deg, ${Theme.colors.accent}, ${Theme.colors.secondary})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          ⚡ SuperNova
        </h1>
        <button onClick={onSwitchMode} className="nv-wizard-btn-sm" title="Switch to Advanced Mode">
          ⚙ Advanced
        </button>
      </header>
      <div className="nv-simple-messages">
        {chatHistory.length === 0 && (
          <div style={{ textAlign: 'center', opacity: 0.5, padding: 40 }}>
            <p style={{ fontSize: 32 }}>⚡</p>
            <p>How can I help you today?</p>
          </div>
        )}
        {chatHistory.map(m => (
          <div key={m.id} className={`nv-simple-msg nv-msg-${m.role}`}>
            {m.content}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <div className="nv-simple-input-bar">
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask SuperNova anything…" className="nv-simple-input" autoFocus />
        <button onClick={send} className="nv-wizard-btn primary" disabled={!input.trim()}>Send</button>
      </div>
    </div>
  );
};

export default SimpleMode;
