/**
 * App Component
 * Root component with error boundary, first-run wizard, and mode switching
 *
 * Updated for Phase 15: User Experience & Onboarding
 */
import React, { useState, useEffect, useCallback } from 'react';
import NovaDashboard from './NovaDashboard';
import { SetupWizard, Tutorial, FeatureDiscovery } from './components/onboarding';
import { SimpleMode } from './components/modes';
import { HelpPanel, KeyboardShortcuts } from './components/help';
import type { DashboardMode } from './components/modes';
import type { ChatMessage } from './types';
import './App.css';
import './responsive.css';

/**
 * Error Boundary for graceful error handling
 */
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): { hasError: boolean; error: Error } {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('Dashboard Error:', error, errorInfo);
  }

  override render(): React.ReactNode {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}

const ErrorFallback: React.FC<{ error: Error | null }> = ({ error }) => (
  <div className="nv-error-container">
    <div className="nv-error-card">
      <div className="nv-error-icon">⚠️</div>
      <h1 className="nv-error-title">System Error</h1>
      <p className="nv-error-message">
        The Neural Constellation dashboard encountered an error.
      </p>
      <details className="nv-error-details">
        <summary>Diagnostic Information</summary>
        <pre className="nv-error-stack">
          {error?.message}
          {'\n'}
          {error?.stack}
        </pre>
      </details>
      <button className="nv-error-reload" onClick={() => window.location.reload()}>
        Reinitialize System
      </button>
    </div>
  </div>
);

const App: React.FC = () => {
  const [setupDone, setSetupDone] = useState(() => localStorage.getItem('supernova_setup_complete') === 'true');
  const [showTutorial, setShowTutorial] = useState(() => !localStorage.getItem('supernova_tutorial_done'));
  const [showFeatures, setShowFeatures] = useState(true);
  const [mode, setMode] = useState<DashboardMode>(() => (localStorage.getItem('supernova_mode') as DashboardMode) || 'advanced');
  const [showHelp, setShowHelp] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [chatHistory] = useState<ChatMessage[]>([]);

  // Keyboard shortcuts listener
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === '?' && !e.ctrlKey && !e.metaKey && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault();
        setShowShortcuts(s => !s);
      }
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setShowHelp(s => !s);
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
        e.preventDefault();
        setMode(m => { const next = m === 'simple' ? 'advanced' : 'simple'; localStorage.setItem('supernova_mode', next); return next; });
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const handleSendMessage = useCallback((_msg: string) => {
    // Chat message handling delegated to NovaDashboard / SimpleMode
  }, []);

  // First-run: show setup wizard
  if (!setupDone) {
    return (
      <ErrorBoundary>
        <SetupWizard onComplete={() => setSetupDone(true)} />
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <div className="nv-app-container">
        <div className="nv-noise-overlay" aria-hidden="true" />

        {/* Tutorial overlay after setup */}
        {showTutorial && setupDone && <Tutorial onComplete={() => setShowTutorial(false)} />}

        {/* Feature discovery banner */}
        {!showTutorial && showFeatures && <FeatureDiscovery onDismiss={() => setShowFeatures(false)} />}

        {/* Mode-based rendering */}
        {mode === 'simple' ? (
          <SimpleMode chatHistory={chatHistory} onSendMessage={handleSendMessage}
            onSwitchMode={() => { setMode('advanced'); localStorage.setItem('supernova_mode', 'advanced'); }} />
        ) : (
          <NovaDashboard />
        )}

        {/* Help panel */}
        {showHelp && <HelpPanel onClose={() => setShowHelp(false)} />}

        {/* Keyboard shortcuts modal */}
        {showShortcuts && <KeyboardShortcuts onClose={() => setShowShortcuts(false)} />}
      </div>
    </ErrorBoundary>
  );
};

export default App;
