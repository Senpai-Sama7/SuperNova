/**
 * Token Utility Functions
 * Helper functions for working with design tokens
 * 
 * @phase Phase 1 - Foundation
 */

import { tokens, primitive, semantic, component, dynamic } from './tokens';

// ============================================================================
// COLOR UTILITIES
// ============================================================================

/**
 * Convert hex color to RGB values
 * @param hex - Hex color string (e.g., '#00ffd5')
 * @returns RGB object or null if invalid
 */
export const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return null;
  
  const r = parseInt(result[1] ?? '00', 16);
  const g = parseInt(result[2] ?? '00', 16);
  const b = parseInt(result[3] ?? '00', 16);
  
  return { r, g, b };
};

/**
 * Convert RGB to hex color
 * @param r - Red value (0-255)
 * @param g - Green value (0-255)
 * @param b - Blue value (0-255)
 * @returns Hex color string
 */
export const rgbToHex = (r: number, g: number, b: number): string => {
  const toHex = (n: number) => n.toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
};

/**
 * Interpolate between two colors
 * @param color1 - Starting hex color
 * @param color2 - Ending hex color
 * @param factor - Interpolation factor (0-1)
 * @returns Interpolated hex color
 */
export const interpolateColor = (color1: string, color2: string, factor: number): string => {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);
  
  if (!rgb1 || !rgb2) return color1;
  
  const r = Math.round(rgb1.r + (rgb2.r - rgb1.r) * factor);
  const g = Math.round(rgb1.g + (rgb2.g - rgb1.g) * factor);
  const b = Math.round(rgb1.b + (rgb2.b - rgb1.b) * factor);
  
  return rgbToHex(r, g, b);
};

/**
 * Get agent color by role
 * @param role - Agent role
 * @returns Color hex string
 */
export const getAgentColor = (role: 'planner' | 'researcher' | 'executor' | 'auditor' | 'creative'): string => {
  return semantic.color.agent[role];
};

/**
 * Get memory color by type
 * @param type - Memory type
 * @returns Color hex string
 */
export const getMemoryColor = (type: 'episodic' | 'semantic' | 'procedural' | 'working'): string => {
  return semantic.color.memory[type];
};

/**
 * Get risk color by level
 * @param level - Risk level
 * @returns Color hex string
 */
export const getRiskColor = (level: 'low' | 'medium' | 'high' | 'critical'): string => {
  return semantic.color.risk[level];
};

/**
 * Get cognitive phase color
 * @param phase - Cognitive loop phase
 * @returns Color hex string
 */
export const getCognitiveColor = (
  phase: 'perceive' | 'remember' | 'prime' | 'assemble' | 'reason' | 'act' | 'reflect' | 'consolidate'
): string => {
  return semantic.color.cognitive[phase];
};

// ============================================================================
// CSS CUSTOM PROPERTY UTILITIES
// ============================================================================

/**
 * Set a CSS custom property on the root element
 * @param property - Property name (e.g., '--atmosphere-brightness')
 * @param value - Property value
 */
export const setCssProperty = (property: string, value: string): void => {
  if (typeof document !== 'undefined') {
    document.documentElement.style.setProperty(property, value);
  }
};

/**
 * Get a CSS custom property value
 * @param property - Property name
 * @returns Property value or null
 */
export const getCssProperty = (property: string): string | null => {
  if (typeof document === 'undefined') return null;
  return getComputedStyle(document.documentElement).getPropertyValue(property).trim();
};

/**
 * Batch update CSS custom properties
 * @param properties - Object of property names and values
 */
export const setCssProperties = (properties: Record<string, string>): void => {
  Object.entries(properties).forEach(([property, value]) => {
    setCssProperty(property, value);
  });
};

// ============================================================================
// ATMOSPHERIC LIGHTING CONTROLS
// ============================================================================

/**
 * Update atmospheric lighting based on confidence level
 * @param confidence - Confidence value (0-1)
 */
export const updateAtmosphereFromConfidence = (confidence: number): void => {
  // Map confidence to brightness (0.3 to 1.0)
  const brightness = 0.3 + confidence * 0.7;
  
  // Map confidence to color temperature
  let colorTemp: string;
  if (confidence >= 0.9) colorTemp = primitive.color.supernovaCyan;
  else if (confidence >= 0.7) colorTemp = primitive.color.neuralPurple;
  else if (confidence >= 0.5) colorTemp = primitive.color.knowledgeGold;
  else if (confidence >= 0.3) colorTemp = primitive.color.skillAmber;
  else colorTemp = primitive.color.workingCoral;
  
  setCssProperties({
    [dynamic.atmosphere.brightness]: brightness.toFixed(2),
    [dynamic.atmosphere.colorTemp]: colorTemp,
  });
};

/**
 * Update atmospheric turbulence based on entropy
 * @param entropy - Entropy value (0-1)
 */
export const updateAtmosphereFromEntropy = (entropy: number): void => {
  setCssProperty(dynamic.atmosphere.turbulence, entropy.toFixed(2));
};

/**
 * Update cognitive loop visualization
 * @param phase - Current phase index (0-7)
 * @param speed - Flow speed multiplier
 */
export const updateCognitiveState = (phase: number, speed: number = 1): void => {
  setCssProperties({
    [dynamic.cognitive.currentPhase]: phase.toString(),
    [dynamic.cognitive.flowSpeed]: speed.toFixed(2),
  });
};

// ============================================================================
// SPACING UTILITIES
// ============================================================================

/**
 * Convert spacing token to pixels
 * @param token - Spacing token (e.g., '4', '6', '8')
 * @returns Number of pixels
 */
export const getSpacing = (token: keyof typeof primitive.spacing): string => {
  return primitive.spacing[token];
};

/**
 * Create spacing CSS string
 * @param vertical - Vertical spacing token
 * @param horizontal - Horizontal spacing token (defaults to vertical)
 * @returns CSS spacing string (e.g., '16px 24px')
 */
export const createSpacing = (
  vertical: keyof typeof primitive.spacing,
  horizontal?: keyof typeof primitive.spacing
): string => {
  const v = getSpacing(vertical);
  const h = horizontal ? getSpacing(horizontal) : v;
  return `${v} ${h}`;
};

// ============================================================================
// ANIMATION UTILITIES
// ============================================================================

/**
 * Create CSS transition string
 * @param properties - Properties to transition
 * @param duration - Duration token
 * @param easing - Easing token
 * @returns CSS transition string
 */
export const createTransition = (
  properties: string[],
  duration: keyof typeof primitive.animation.duration = 'standard',
  easing: keyof typeof primitive.animation.easing = 'standard'
): string => {
  const dur = primitive.animation.duration[duration];
  const ease = primitive.animation.easing[easing];
  return properties.map(prop => `${prop} ${dur} ${ease}`).join(', ');
};

/**
 * Create stagger delay for animations
 * @param index - Item index
 * @param stagger - Stagger timing token
 * @returns Delay in milliseconds
 */
export const createStaggerDelay = (
  index: number,
  stagger: keyof typeof primitive.animation.stagger = 'standard'
): string => {
  const staggerMs = parseInt(primitive.animation.stagger[stagger]);
  return `${index * staggerMs}ms`;
};

// ============================================================================
// TYPOGRAPHY UTILITIES
// ============================================================================

/**
 * Get font stack by type
 * @param type - Font type
 * @returns Font family string
 */
export const getFontFamily = (type: 'display' | 'ui' | 'mono'): string => {
  return primitive.typography.fontFamily[type];
};

/**
 * Clamp text to specific number of lines
 * @param lines - Number of lines
 * @returns CSS string for line clamping
 */
export const lineClamp = (lines: number): string => `
  display: -webkit-box;
  -webkit-line-clamp: ${lines};
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

// ============================================================================
// TOKEN VALIDATION
// ============================================================================

/**
 * Validate if a string is a valid token color
 * @param color - Color string to validate
 * @returns True if valid hex or rgba
 */
export const isValidColor = (color: string): boolean => {
  const hexRegex = /^#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$/;
  const rgbaRegex = /^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*[\d.]+\s*)?\)$/;
  return hexRegex.test(color) || rgbaRegex.test(color);
};

/**
 * Check if all required tokens are defined
 * @returns Validation result
 */
export const validateTokens = (): { valid: boolean; missing: string[] } => {
  const requiredTokens = [
    '--nv-cyan',
    '--nv-bg-primary',
    '--nv-text-primary',
    '--nv-font-ui',
  ];
  
  if (typeof document === 'undefined') {
    return { valid: true, missing: [] };
  }
  
  const missing = requiredTokens.filter(token => {
    const value = getCssProperty(token);
    return !value || value === '';
  });
  
  return {
    valid: missing.length === 0,
    missing,
  };
};

// ============================================================================
// EXPORT HELPERS
// ============================================================================

export type TokenPath = string;

/**
 * Get nested token value by path
 * @param obj - Token object
 * @param path - Dot-separated path (e.g., 'color.agent.planner')
 * @returns Token value or undefined
 */
export const getTokenByPath = (obj: Record<string, unknown>, path: string): unknown => {
  return path.split('.').reduce<unknown>((acc, part) => {
    if (acc && typeof acc === 'object') {
      return (acc as Record<string, unknown>)[part];
    }
    return undefined;
  }, obj);
};

// Re-exports for convenience
export { tokens, primitive, semantic, component, dynamic };
export default tokens;
