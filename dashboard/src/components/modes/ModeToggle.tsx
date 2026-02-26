/**
 * ModeToggle — Switch between Simple and Advanced dashboard modes
 * Persists preference to localStorage
 * 15.2.3
 */
import React from 'react';

export type DashboardMode = 'simple' | 'advanced';

interface ModeToggleProps {
  mode: DashboardMode;
  onChange: (mode: DashboardMode) => void;
}

const ModeToggle: React.FC<ModeToggleProps> = ({ mode, onChange }) => (
  <div className="nv-mode-toggle" role="radiogroup" aria-label="Dashboard mode">
    <button role="radio" aria-checked={mode === 'simple'}
      className={`nv-mode-btn ${mode === 'simple' ? 'active' : ''}`}
      onClick={() => { onChange('simple'); localStorage.setItem('supernova_mode', 'simple'); }}>
      💬 Simple
    </button>
    <button role="radio" aria-checked={mode === 'advanced'}
      className={`nv-mode-btn ${mode === 'advanced' ? 'active' : ''}`}
      onClick={() => { onChange('advanced'); localStorage.setItem('supernova_mode', 'advanced'); }}>
      ⚙ Advanced
    </button>
  </div>
);

export default ModeToggle;
