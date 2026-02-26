/**
 * HelpPanel — Searchable in-app documentation
 * 15.4.2
 */
import React, { useState, useMemo } from 'react';

interface HelpEntry { title: string; content: string; tags: string[] }

const HELP_ENTRIES: HelpEntry[] = [
  { title: 'Getting Started', content: 'SuperNova is an AI agent with persistent memory. Start by sending a message in the chat.', tags: ['start', 'begin', 'intro'] },
  { title: 'Memory System', content: 'SuperNova uses episodic (events), semantic (facts), and procedural (skills) memory for context-aware responses.', tags: ['memory', 'episodic', 'semantic'] },
  { title: 'Dashboard Modes', content: 'Simple Mode shows chat only. Advanced Mode reveals agent internals, memory graphs, and metrics.', tags: ['mode', 'simple', 'advanced'] },
  { title: 'API Keys', content: 'Configure API keys in Settings. Supports OpenAI, Anthropic, Google, and local Ollama models.', tags: ['api', 'key', 'config'] },
  { title: 'Security', content: 'All secrets are encrypted with AES-256-GCM. Tool execution is capability-gated with HITL approval for risky operations.', tags: ['security', 'encryption', 'hitl'] },
  { title: 'MCP Integration', content: 'Model Context Protocol servers extend SuperNova with external tools. Manage them in the MCP tab.', tags: ['mcp', 'tools', 'integration'] },
  { title: 'Cost Control', content: 'Set monthly budgets per model. The cost controller automatically routes to cheaper models when limits approach.', tags: ['cost', 'budget', 'billing'] },
  { title: 'Keyboard Shortcuts', content: 'Press ? to view all shortcuts. Ctrl+K opens command palette. Ctrl+/ toggles help panel.', tags: ['keyboard', 'shortcut', 'hotkey'] },
];

interface HelpPanelProps { onClose: () => void }

const HelpPanel: React.FC<HelpPanelProps> = ({ onClose }) => {
  const [query, setQuery] = useState('');
  const results = useMemo(() => {
    if (!query.trim()) return HELP_ENTRIES;
    const q = query.toLowerCase();
    return HELP_ENTRIES.filter(e =>
      e.title.toLowerCase().includes(q) || e.content.toLowerCase().includes(q) || e.tags.some(t => t.includes(q))
    );
  }, [query]);

  return (
    <div className="nv-help-panel" role="complementary" aria-label="Help">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h2 style={{ margin: 0, fontSize: 16 }}>📖 Help</h2>
        <button onClick={onClose} className="nv-wizard-btn-sm">✕</button>
      </div>
      <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search help…"
        className="nv-wizard-input" autoFocus />
      <div className="nv-help-results">
        {results.map((e, i) => (
          <details key={i} className="nv-help-entry">
            <summary style={{ fontWeight: 600, cursor: 'pointer', padding: '8px 0' }}>{e.title}</summary>
            <p style={{ margin: '4px 0 8px', fontSize: 13, opacity: 0.8, paddingLeft: 12 }}>{e.content}</p>
          </details>
        ))}
        {results.length === 0 && <p style={{ opacity: 0.5, textAlign: 'center' }}>No results found.</p>}
      </div>
    </div>
  );
};

export default HelpPanel;
