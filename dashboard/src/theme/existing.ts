/**
 * Legacy Theme Values
 * Preserved for backward compatibility during migration
 * 
 * @deprecated Use tokens.ts instead for new code
 */

// API Configuration
export const API_BASE = 'http://127.0.0.1:8000';

// Legacy Theme Object (used by NovaDashboard)
export const Theme = {
  colors: {
    bg: '#0a0a0f',
    surfaceLow: 'rgba(26, 26, 46, 0.6)',
    surfaceMid: 'rgba(26, 26, 46, 0.8)',
    surfaceHigh: 'rgba(26, 26, 46, 0.95)',
    border: 'rgba(255, 255, 255, 0.1)',
    text: '#ffffff',
    textMuted: 'rgba(255, 255, 255, 0.6)',
    accent: '#00ffd5',
    secondary: '#7c3aed',
    success: '#22c55e',
    warning: '#f59e0b',
    error: '#ef4444',
  },
  fonts: {
    main: '"Space Grotesk", system-ui, sans-serif',
    mono: '"JetBrains Mono", monospace',
  },
  glass: {
    backdropFilter: 'blur(20px) saturate(180%)',
    WebkitBackdropFilter: 'blur(20px) saturate(180%)',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  },
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
  },
  animation: {
    fast: '150ms',
    normal: '300ms',
    slow: '500ms',
  },
} as const;

// Legacy tokens export
export const tokens = {
  // Colors (Legacy naming)
  SuperNovaCyan: '#00ffd5',
  SuperNovaCyanRgb: '0, 255, 213',
  
  // Backgrounds
  bgPrimary: 'rgba(10, 10, 15, 0.95)',
  bgSecondary: 'rgba(26, 26, 46, 0.8)',
  bgTertiary: 'rgba(255, 255, 255, 0.05)',
  
  // Text
  textPrimary: '#ffffff',
  textSecondary: 'rgba(255, 255, 255, 0.7)',
  textMuted: 'rgba(255, 255, 255, 0.4)',
  
  // Fonts
  SpaceGrotesk: '"Space Grotesk", system-ui, sans-serif',
  JetBrainsMono: '"JetBrains Mono", "Fira Code", monospace',
  
  // Spacing (Legacy)
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
  
  // Animation (Legacy)
  animation: {
    micro: '150ms',
    fast: '200ms',
    normal: '300ms',
    slow: '500ms',
  },
  
  // Z-index (Legacy)
  zIndex: {
    base: 0,
    floating: 100,
    overlay: 200,
    modal: 300,
    tooltip: 400,
  },
} as const;

export default tokens;
