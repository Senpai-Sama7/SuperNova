/**
 * ExamplePrompts — Categorized prompt suggestions
 * 15.3.2
 */
import React, { useState } from 'react';

interface PromptExample { text: string; category: string }

const EXAMPLES: PromptExample[] = [
  { text: 'Summarize the key points from my last meeting notes', category: 'Productivity' },
  { text: 'Write a Python function to parse CSV files', category: 'Coding' },
  { text: 'Explain the difference between REST and GraphQL', category: 'Learning' },
  { text: 'Review this code for security vulnerabilities', category: 'Coding' },
  { text: 'Create a project timeline for a 3-month sprint', category: 'Productivity' },
  { text: 'What are the best practices for Docker security?', category: 'Learning' },
  { text: 'Debug this error: TypeError: Cannot read property of undefined', category: 'Coding' },
  { text: 'Draft an email to the team about the new release', category: 'Productivity' },
];

const CATEGORIES = [...new Set(EXAMPLES.map(e => e.category))];

interface ExamplePromptsProps { onSelect: (prompt: string) => void }

const ExamplePrompts: React.FC<ExamplePromptsProps> = ({ onSelect }) => {
  const [filter, setFilter] = useState<string | null>(null);
  const filtered = filter ? EXAMPLES.filter(e => e.category === filter) : EXAMPLES;

  return (
    <div className="nv-example-prompts">
      <h3 style={{ margin: '0 0 8px' }}>💡 Try asking…</h3>
      <div style={{ display: 'flex', gap: 6, marginBottom: 12, flexWrap: 'wrap' }}>
        <button className={`nv-prompt-tag ${!filter ? 'active' : ''}`} onClick={() => setFilter(null)}>All</button>
        {CATEGORIES.map(c => (
          <button key={c} className={`nv-prompt-tag ${filter === c ? 'active' : ''}`}
            onClick={() => setFilter(c)}>{c}</button>
        ))}
      </div>
      <div className="nv-prompt-list">
        {filtered.map((e, i) => (
          <button key={i} className="nv-prompt-item" onClick={() => onSelect(e.text)}>
            <span style={{ opacity: 0.5, fontSize: 11 }}>{e.category}</span>
            <span>{e.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ExamplePrompts;
