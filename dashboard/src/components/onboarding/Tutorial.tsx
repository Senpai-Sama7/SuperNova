/**
 * Tutorial — Interactive onboarding overlay
 * Highlights features step-by-step with spotlight effect
 * 15.3.1
 */
import React, { useState } from 'react';

interface TutorialStep { target: string; title: string; description: string; position: 'top' | 'bottom' | 'left' | 'right' }

const TUTORIAL_STEPS: TutorialStep[] = [
  { target: '.nv-header', title: 'Dashboard Header', description: 'Monitor system status and switch between tabs.', position: 'bottom' },
  { target: '.nv-tab-overview', title: 'Overview Tab', description: 'See agent activity, memory usage, and cognitive loop state.', position: 'bottom' },
  { target: '.nv-tab-agents', title: 'Agents Tab', description: 'View and manage individual AI agents.', position: 'bottom' },
  { target: '.nv-tab-memory', title: 'Memory Tab', description: 'Explore episodic, semantic, and procedural memory graphs.', position: 'bottom' },
  { target: '.nv-chat-input', title: 'Chat Interface', description: 'Send messages to SuperNova and receive AI responses.', position: 'top' },
];

interface TutorialProps { onComplete: () => void }

const Tutorial: React.FC<TutorialProps> = ({ onComplete }) => {
  const [current, setCurrent] = useState(0);
  const step = TUTORIAL_STEPS[current];
  const isLast = current === TUTORIAL_STEPS.length - 1;

  const next = () => {
    if (isLast) { localStorage.setItem('supernova_tutorial_done', 'true'); onComplete(); }
    else setCurrent(c => c + 1);
  };

  return (
    <div className="nv-tutorial-overlay" role="dialog" aria-label="Tutorial">
      <div className={`nv-tutorial-tooltip nv-pos-${step.position}`}>
        <div style={{ fontSize: 11, opacity: 0.6 }}>Step {current + 1} of {TUTORIAL_STEPS.length}</div>
        <h3 style={{ margin: '4px 0' }}>{step.title}</h3>
        <p style={{ margin: '4px 0 12px', fontSize: 13, opacity: 0.8 }}>{step.description}</p>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button onClick={() => { localStorage.setItem('supernova_tutorial_done', 'true'); onComplete(); }}
            className="nv-wizard-btn">Skip</button>
          <button onClick={next} className="nv-wizard-btn primary">{isLast ? 'Finish' : 'Next'}</button>
        </div>
      </div>
    </div>
  );
};

export default Tutorial;
