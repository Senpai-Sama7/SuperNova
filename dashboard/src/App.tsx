/**
 * App Component
 * Root component with error boundary
 * 
 * Updated for Neural Constellation Design System v2.0
 * Phase 1: Foundation
 */
import React from 'react';
import NovaDashboard from './NovaDashboard';
import './App.css';

/**
 * Error Boundary for graceful error handling
 * Styled with Neural Constellation design tokens
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

/**
 * Error Fallback UI
 * Uses glassmorphism and neural design system
 */
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
      
      <button
        className="nv-error-reload"
        onClick={() => window.location.reload()}
      >
        Reinitialize System
      </button>
    </div>
  </div>
);

/**
 * Main App Component
 * Wraps dashboard in neural background with error boundary
 */
const App: React.FC = () => (
  <ErrorBoundary>
    <div className="nv-app-container">
      {/* Noise texture overlay */}
      <div className="nv-noise-overlay" aria-hidden="true" />
      
      {/* Main dashboard */}
      <NovaDashboard />
    </div>
  </ErrorBoundary>
);

export default App;
