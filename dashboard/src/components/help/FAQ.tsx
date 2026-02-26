/**
 * FAQ — Expandable frequently asked questions
 * 15.4.4
 */
import React from 'react';

interface FAQItem { question: string; answer: string }

const FAQ_ITEMS: FAQItem[] = [
  { question: 'What is SuperNova?', answer: 'SuperNova is a durable, observable AI agent with persistent memory systems inspired by human cognition.' },
  { question: 'How does memory work?', answer: 'SuperNova uses three memory types: episodic (events in Neo4j), semantic (facts in PostgreSQL/pgvector), and procedural (compiled skills).' },
  { question: 'Is my data secure?', answer: 'Yes. Secrets are encrypted with AES-256-GCM, tool execution is capability-gated, and high-risk actions require human approval.' },
  { question: 'Can I use local models?', answer: 'Yes. SuperNova supports Ollama for local LLM inference with zero API costs.' },
  { question: 'How do I control costs?', answer: 'Set monthly budgets in Settings. The cost controller routes to cheaper models as limits approach.' },
  { question: 'What is MCP?', answer: 'Model Context Protocol lets you extend SuperNova with external tool servers for file access, web browsing, and more.' },
  { question: 'How do I reset my setup?', answer: 'Clear browser localStorage and refresh. The setup wizard will reappear on next visit.' },
];

const FAQ: React.FC = () => (
  <div className="nv-faq">
    <h3 style={{ margin: '0 0 12px' }}>❓ Frequently Asked Questions</h3>
    {FAQ_ITEMS.map((item, i) => (
      <details key={i} className="nv-faq-item">
        <summary style={{ fontWeight: 600, cursor: 'pointer', padding: '8px 0' }}>{item.question}</summary>
        <p style={{ margin: '4px 0 8px', fontSize: 13, opacity: 0.8, paddingLeft: 12 }}>{item.answer}</p>
      </details>
    ))}
  </div>
);

export default FAQ;
