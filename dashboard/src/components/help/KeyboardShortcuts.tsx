/**
 * KeyboardShortcuts — Modal showing all keyboard shortcuts
 * Accessible via ? key
 * 15.4.3
 */
import React, { useEffect } from 'react';

interface Shortcut { keys: string; description: string; category: string }

const SHORTCUTS: Shortcut[] = [
  { keys: '?', description: 'Show keyboard shortcuts', category: 'General' },
  { keys: 'Ctrl + K', description: 'Open command palette', category: 'General' },
  { keys: 'Ctrl + /', description: 'Toggle help panel', category: 'General' },
  { keys: 'Ctrl + Enter', description: 'Send message', category: 'Chat' },
  { keys: 'Escape', description: 'Close modal / cancel', category: 'General' },
  { keys: 'Ctrl + 1-5', description: 'Switch dashboard tabs', category: 'Navigation' },
  { keys: 'Ctrl + M', description: 'Toggle Simple/Advanced mode', category: 'Navigation' },
  { keys: 'Ctrl + H', description: 'Toggle halt/resume agents', category: 'Agents' },
];

const CATEGORIES = [...new Set(SHORTCUTS.map(s => s.category))];

interface KeyboardShortcutsProps { onClose: () => void }

const KeyboardShortcuts: React.FC<KeyboardShortcutsProps> = ({ onClose }) => {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div className="nv-wizard-overlay" role="dialog" aria-label="Keyboard Shortcuts" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="nv-shortcuts-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ margin: 0, fontSize: 16 }}>⌨️ Keyboard Shortcuts</h2>
          <button onClick={onClose} className="nv-wizard-btn-sm">✕</button>
        </div>
        {CATEGORIES.map(cat => (
          <div key={cat} style={{ marginBottom: 12 }}>
            <h3 style={{ margin: '0 0 6px', fontSize: 13, opacity: 0.6, textTransform: 'uppercase' }}>{cat}</h3>
            {SHORTCUTS.filter(s => s.category === cat).map((s, i) => (
              <div key={i} className="nv-shortcut-row">
                <kbd className="nv-kbd">{s.keys}</kbd>
                <span style={{ fontSize: 13 }}>{s.description}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default KeyboardShortcuts;
