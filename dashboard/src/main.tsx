/**
 * Application Entry Point
 * 
 * Neural Constellation Design System v2.0
 * Phase 1: Foundation - Design Tokens & CSS Architecture
 */
import React from 'react';
import ReactDOM from 'react-dom/client';

// Design System CSS (import order matters for cascade)
import './theme/tokens.css';           // CSS Custom Properties
import './styles/neural-constellation.css';  // Visual Foundation
import './index.css';                   // Base styles

import App from './App';

// Type-safe root element check
const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element not found. Ensure there is a <div id="root"></div> in index.html');
}

// Create root with strict mode for development checks
const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
