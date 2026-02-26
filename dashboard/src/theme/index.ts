/**
 * SuperNova Theme Module
 * 
 * Design tokens, utilities, and theming for the Neural Constellation dashboard.
 * 
 * @example
 * ```tsx
 * import { tokens, getAgentColor, setCssProperty } from '@/theme';
 * 
 * // Use tokens in components
 * const color = tokens.semantic.color.agent.executor;
 * 
 * // Get color by role
 * const agentColor = getAgentColor('planner');
 * 
 * // Update CSS custom property at runtime
 * setCssProperty('--atmosphere-brightness', '0.8');
 * ```
 * 
 * @module theme
 * @phase Phase 1 - Foundation
 */

// ============================================================================
// CORE TOKENS
// ============================================================================

export {
  tokens,
  primitive,
  semantic,
  component,
  dynamic,
  legacy,
} from './tokens';

export type {
  PrimitiveTokens,
  SemanticTokens,
  ComponentTokens,
  DynamicTokens,
} from './tokens';

// ============================================================================
// UTILITIES
// ============================================================================

export {
  // Color utilities
  hexToRgb,
  rgbToHex,
  interpolateColor,
  getAgentColor,
  getMemoryColor,
  getRiskColor,
  getCognitiveColor,
  
  // CSS custom property utilities
  setCssProperty,
  getCssProperty,
  setCssProperties,
  
  // Atmospheric controls
  updateAtmosphereFromConfidence,
  updateAtmosphereFromEntropy,
  updateCognitiveState,
  
  // Spacing utilities
  getSpacing,
  createSpacing,
  
  // Animation utilities
  createTransition,
  createStaggerDelay,
  
  // Typography utilities
  getFontFamily,
  lineClamp,
  
  // Validation
  isValidColor,
  validateTokens,
  getTokenByPath,
} from './utils';

// Re-export all utils as namespace
export * as utils from './utils';

// ============================================================================
// LEGACY COMPATIBILITY
// ============================================================================

// Legacy exports for backward compatibility during migration
export { Theme, API_BASE } from './existing';

// Default export (new tokens)
export { tokens as default } from './tokens';

// ============================================================================
// MODULE METADATA
// ============================================================================

export const THEME_VERSION = '2.0.0-neural-constellation';
export const THEME_PHASE = 'Phase 1 - Foundation';

/**
 * Initialize theme system
 * Validates that CSS custom properties are loaded
 */
export const initializeTheme = (): boolean => {
  if (typeof document === 'undefined') return true;
  
  const testProp = getComputedStyle(document.documentElement)
    .getPropertyValue('--nv-cyan')
    .trim();
  
  const isLoaded = testProp === '#00ffd5' || testProp === '';
  
  if (!isLoaded) {
    console.warn('[Theme] CSS custom properties not loaded. Ensure tokens.css is imported.');
  }
  
  return isLoaded;
};
