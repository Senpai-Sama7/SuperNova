/**
 * SuperNova Neural Constellation Design Tokens
 * 
 * Token Hierarchy (DTCG Standard):
 * 1. Primitives: Raw values (colors, spacing, etc.)
 * 2. Semantics: Purpose-driven abstractions
 * 3. Components: UI-specific applications
 * 
 * @author Design Systems Architect
 * @phase Phase 1 - Foundation
 */

import { tokens as existingTokens } from './existing';

// ============================================================================
// PRIMITIVE TOKENS
// Raw values without semantic meaning
// ============================================================================

export const primitive = {
  color: {
    // SuperNova Core (retained from existing)
    supernovaCyan: '#00ffd5',
    supernovaCyan50: 'rgba(0, 255, 213, 0.5)',
    supernovaCyan30: 'rgba(0, 255, 213, 0.3)',
    supernovaCyan10: 'rgba(0, 255, 213, 0.1)',
    
    // Neural Constellation Extensions
    neuralPurple: '#7c3aed',
    neuralPurple50: 'rgba(124, 58, 237, 0.5)',
    neuralPurple30: 'rgba(124, 58, 237, 0.3)',
    neuralPurple15: 'rgba(124, 58, 237, 0.15)',
    
    knowledgeGold: '#fbbf24',
    knowledgeGold50: 'rgba(251, 191, 36, 0.5)',
    knowledgeGold30: 'rgba(251, 191, 36, 0.3)',
    
    skillAmber: '#f59e0b',
    skillAmber50: 'rgba(245, 158, 11, 0.5)',
    skillAmber30: 'rgba(245, 158, 11, 0.3)',
    
    workingCoral: '#f472b6',
    workingCoral50: 'rgba(244, 114, 182, 0.5)',
    workingCoral30: 'rgba(244, 114, 182, 0.3)',
    workingCoral15: 'rgba(244, 114, 182, 0.15)',
    
    // Risk Spectrum
    riskLow: '#22c55e',
    riskLow50: 'rgba(34, 197, 94, 0.5)',
    riskMedium: '#f59e0b',
    riskMedium50: 'rgba(245, 158, 11, 0.5)',
    riskHigh: '#ef4444',
    riskHigh50: 'rgba(239, 68, 68, 0.5)',
    riskCritical: '#dc2626',
    riskCritical80: 'rgba(220, 38, 38, 0.8)',
    
    // Space Environment
    deepSpace: '#0a0a0f',
    deepSpace90: 'rgba(10, 10, 15, 0.9)',
    deepSpace70: 'rgba(10, 10, 15, 0.7)',
    deepSpace50: 'rgba(10, 10, 15, 0.5)',
    
    nebulaFog: '#1a1a2e',
    nebulaFog90: 'rgba(26, 26, 46, 0.9)',
    nebulaFog70: 'rgba(26, 26, 46, 0.7)',
    nebulaFog60: 'rgba(26, 26, 46, 0.6)',
    nebulaFog50: 'rgba(26, 26, 46, 0.5)',
    
    // Utility
    white: '#ffffff',
    white80: 'rgba(255, 255, 255, 0.8)',
    white60: 'rgba(255, 255, 255, 0.6)',
    white40: 'rgba(255, 255, 255, 0.4)',
    white20: 'rgba(255, 255, 255, 0.2)',
    white10: 'rgba(255, 255, 255, 0.1)',
    white5: 'rgba(255, 255, 255, 0.05)',
    
    black: '#000000',
    black50: 'rgba(0, 0, 0, 0.5)',
    black30: 'rgba(0, 0, 0, 0.3)',
  },
  
  spacing: {
    0: '0',
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    5: '20px',
    6: '24px',
    8: '32px',
    10: '40px',
    12: '48px',
    16: '64px',
    20: '80px',
    24: '96px',
  },
  
  size: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
    '3xl': '64px',
    '4xl': '96px',
    '5xl': '128px',
  },
  
  radius: {
    none: '0',
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    '2xl': '24px',
    full: '9999px',
  },
  
  typography: {
    fontFamily: {
      display: '"Clash Display", "Space Grotesk", sans-serif',
      ui: '"Space Grotesk", system-ui, sans-serif',
      mono: '"JetBrains Mono", "Fira Code", monospace',
    },
    fontSize: {
      xs: '12px',
      sm: '14px',
      base: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px',
      '3xl': '30px',
      '4xl': '36px',
      '5xl': '48px',
      '6xl': '60px',
      '7xl': '72px',
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
    letterSpacing: {
      tight: '-0.02em',
      normal: '0',
      wide: '0.02em',
      wider: '0.05em',
    },
  },
  
  animation: {
    duration: {
      instant: '0ms',
      micro: '150ms',
      fast: '200ms',
      standard: '300ms',
      emphasis: '500ms',
      slow: '800ms',
      ambient: '3000ms',
    },
    easing: {
      linear: 'linear',
      standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
      enter: 'cubic-bezier(0, 0, 0.2, 1)',
      exit: 'cubic-bezier(0.4, 0, 1, 1)',
      bounce: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    },
    stagger: {
      fast: '30ms',
      standard: '50ms',
      slow: '100ms',
    },
  },
  
  zIndex: {
    base: 0,
    dropdown: 100,
    sticky: 200,
    fixed: 300,
    modalBackdrop: 400,
    modal: 500,
    popover: 600,
    tooltip: 700,
    toast: 800,
    devtools: 9999,
  },
  
  shadow: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px rgba(0, 0, 0, 0.3)',
    lg: '0 8px 16px rgba(0, 0, 0, 0.4)',
    xl: '0 12px 24px rgba(0, 0, 0, 0.5)',
    glow: {
      low: '0 0 10px rgba(0, 255, 213, 0.3)',
      medium: '0 0 20px rgba(0, 255, 213, 0.5)',
      high: '0 0 40px rgba(0, 255, 213, 0.7)',
      critical: '0 0 60px rgba(220, 38, 38, 0.8)',
    },
  },
  
  blur: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '20px',
    '2xl': '40px',
  },
} as const;

// ============================================================================
// SEMANTIC TOKENS
// Purpose-driven abstractions
// ============================================================================

export const semantic = {
  color: {
    // Background hierarchy
    bg: {
      primary: primitive.color.deepSpace,
      secondary: primitive.color.nebulaFog,
      tertiary: primitive.color.nebulaFog70,
      overlay: primitive.color.deepSpace70,
      elevated: primitive.color.nebulaFog60,
    },
    
    // Text hierarchy
    text: {
      primary: primitive.color.white,
      secondary: primitive.color.white80,
      tertiary: primitive.color.white60,
      muted: primitive.color.white40,
      disabled: primitive.color.white20,
    },
    
    // Border hierarchy
    border: {
      default: primitive.color.white10,
      hover: primitive.color.white20,
      active: primitive.color.supernovaCyan50,
      focus: primitive.color.supernovaCyan,
      error: primitive.color.riskHigh,
      warning: primitive.color.riskMedium,
      success: primitive.color.riskLow,
    },
    
    // Interactive states
    interactive: {
      default: primitive.color.white10,
      hover: primitive.color.white20,
      active: primitive.color.supernovaCyan30,
      selected: primitive.color.supernovaCyan50,
      disabled: primitive.color.white5,
    },
    
    // Feedback states
    feedback: {
      info: primitive.color.supernovaCyan,
      success: primitive.color.riskLow,
      warning: primitive.color.riskMedium,
      error: primitive.color.riskHigh,
      critical: primitive.color.riskCritical,
    },
    
    // Agent roles (mapped to cognitive functions)
    agent: {
      planner: primitive.color.neuralPurple,
      researcher: primitive.color.knowledgeGold,
      executor: primitive.color.supernovaCyan,
      auditor: primitive.color.workingCoral,
      creative: primitive.color.skillAmber,
    },
    
    // Memory types
    memory: {
      episodic: primitive.color.workingCoral,
      semantic: primitive.color.knowledgeGold,
      procedural: primitive.color.skillAmber,
      working: primitive.color.supernovaCyan,
    },
    
    // Cognitive loop phases
    cognitive: {
      perceive: primitive.color.neuralPurple,
      remember: primitive.color.workingCoral,
      prime: primitive.color.knowledgeGold,
      assemble: primitive.color.skillAmber,
      reason: primitive.color.supernovaCyan,
      act: primitive.color.riskLow,
      reflect: primitive.color.workingCoral50,
      consolidate: primitive.color.neuralPurple50,
    },
    
    // Risk levels
    risk: {
      low: primitive.color.riskLow,
      medium: primitive.color.riskMedium,
      high: primitive.color.riskHigh,
      critical: primitive.color.riskCritical,
    },
    
    // Atmospheric states (confidence-based)
    atmosphere: {
      pristine: primitive.color.supernovaCyan,
      clear: primitive.color.neuralPurple,
      normal: primitive.color.knowledgeGold,
      hazy: primitive.color.skillAmber,
      turbulent: primitive.color.workingCoral,
      storm: primitive.color.riskHigh,
    },
  },
  
  spacing: {
    // Component spacing
    component: {
      xs: primitive.spacing[1],
      sm: primitive.spacing[2],
      md: primitive.spacing[3],
      lg: primitive.spacing[4],
      xl: primitive.spacing[6],
    },
    // Layout spacing
    layout: {
      xs: primitive.spacing[4],
      sm: primitive.spacing[6],
      md: primitive.spacing[8],
      lg: primitive.spacing[12],
      xl: primitive.spacing[16],
    },
  },
  
  typography: {
    heading: {
      h1: {
        fontSize: primitive.typography.fontSize['5xl'],
        fontWeight: primitive.typography.fontWeight.bold,
        lineHeight: primitive.typography.lineHeight.tight,
        letterSpacing: primitive.typography.letterSpacing.tight,
      },
      h2: {
        fontSize: primitive.typography.fontSize['4xl'],
        fontWeight: primitive.typography.fontWeight.bold,
        lineHeight: primitive.typography.lineHeight.tight,
        letterSpacing: primitive.typography.letterSpacing.tight,
      },
      h3: {
        fontSize: primitive.typography.fontSize['3xl'],
        fontWeight: primitive.typography.fontWeight.semibold,
        lineHeight: primitive.typography.lineHeight.tight,
      },
      h4: {
        fontSize: primitive.typography.fontSize['2xl'],
        fontWeight: primitive.typography.fontWeight.semibold,
        lineHeight: primitive.typography.lineHeight.normal,
      },
      h5: {
        fontSize: primitive.typography.fontSize.xl,
        fontWeight: primitive.typography.fontWeight.medium,
        lineHeight: primitive.typography.lineHeight.normal,
      },
    },
    body: {
      large: {
        fontSize: primitive.typography.fontSize.lg,
        fontWeight: primitive.typography.fontWeight.normal,
        lineHeight: primitive.typography.lineHeight.relaxed,
      },
      base: {
        fontSize: primitive.typography.fontSize.base,
        fontWeight: primitive.typography.fontWeight.normal,
        lineHeight: primitive.typography.lineHeight.normal,
      },
      small: {
        fontSize: primitive.typography.fontSize.sm,
        fontWeight: primitive.typography.fontWeight.normal,
        lineHeight: primitive.typography.lineHeight.normal,
      },
      caption: {
        fontSize: primitive.typography.fontSize.xs,
        fontWeight: primitive.typography.fontWeight.normal,
        lineHeight: primitive.typography.lineHeight.normal,
        letterSpacing: primitive.typography.letterSpacing.wide,
      },
    },
    code: {
      fontSize: primitive.typography.fontSize.sm,
      fontWeight: primitive.typography.fontWeight.normal,
      lineHeight: primitive.typography.lineHeight.normal,
      fontFamily: primitive.typography.fontFamily.mono,
    },
  },
} as const;

// ============================================================================
// COMPONENT TOKENS
// UI-specific applications
// ============================================================================

export const component = {
  // Agent Node Component
  agentNode: {
    size: {
      sm: primitive.size.md,
      md: primitive.size.lg,
      lg: primitive.size.xl,
    },
    glowIntensity: {
      idle: '0.3',
      active: '0.6',
      focused: '0.9',
    },
    pulseSpeed: {
      slow: '4s',
      normal: '2s',
      fast: '1s',
    },
  },
  
  // Card Component
  card: {
    padding: {
      sm: primitive.spacing[3],
      md: primitive.spacing[4],
      lg: primitive.spacing[6],
    },
    radius: primitive.radius.lg,
    background: primitive.color.nebulaFog60,
    border: primitive.color.white10,
    shadow: primitive.shadow.lg,
  },
  
  // Button Component
  button: {
    padding: {
      sm: `${primitive.spacing[1]} ${primitive.spacing[3]}`,
      md: `${primitive.spacing[2]} ${primitive.spacing[4]}`,
      lg: `${primitive.spacing[3]} ${primitive.spacing[6]}`,
    },
    radius: primitive.radius.md,
    fontSize: {
      sm: primitive.typography.fontSize.sm,
      md: primitive.typography.fontSize.base,
      lg: primitive.typography.fontSize.lg,
    },
  },
  
  // Badge Component
  badge: {
    padding: `${primitive.spacing[1]} ${primitive.spacing[2]}`,
    radius: primitive.radius.full,
    fontSize: primitive.typography.fontSize.xs,
    fontWeight: primitive.typography.fontWeight.semibold,
  },
  
  // Tab Component
  tab: {
    padding: `${primitive.spacing[2]} ${primitive.spacing[4]}`,
    gap: primitive.spacing[2],
    radius: primitive.radius.md,
    active: {
      background: primitive.color.supernovaCyan30,
      color: primitive.color.supernovaCyan,
      border: primitive.color.supernovaCyan,
    },
    inactive: {
      background: 'transparent',
      color: primitive.color.white60,
      border: 'transparent',
    },
  },
  
  // Progress Component
  progress: {
    height: {
      sm: '4px',
      md: '8px',
      lg: '12px',
    },
    radius: primitive.radius.full,
    background: primitive.color.white10,
    fill: {
      low: primitive.color.riskLow,
      medium: primitive.color.riskMedium,
      high: primitive.color.riskHigh,
      critical: primitive.color.riskCritical,
    },
  },
  
  // Tooltip Component
  tooltip: {
    padding: `${primitive.spacing[2]} ${primitive.spacing[3]}`,
    radius: primitive.radius.md,
    background: primitive.color.deepSpace90,
    border: primitive.color.white10,
    shadow: primitive.shadow.lg,
    fontSize: primitive.typography.fontSize.sm,
  },
  
  // Modal Component
  modal: {
    padding: primitive.spacing[6],
    radius: primitive.radius.xl,
    background: primitive.color.nebulaFog90,
    border: primitive.color.white10,
    shadow: primitive.shadow.xl,
    backdropBlur: primitive.blur.xl,
  },
  
  // Input Component
  input: {
    padding: `${primitive.spacing[2]} ${primitive.spacing[4]}`,
    radius: primitive.radius.md,
    background: primitive.color.white5,
    border: {
      default: primitive.color.white10,
      hover: primitive.color.white20,
      focus: primitive.color.supernovaCyan,
    },
    fontSize: primitive.typography.fontSize.base,
  },
} as const;

// ============================================================================
// DYNAMIC TOKENS (Runtime values)
// These are CSS custom properties that can be updated at runtime
// ============================================================================

export const dynamic = {
  // Atmospheric lighting (controlled by confidence/entropy)
  atmosphere: {
    brightness: '--atmosphere-brightness',
    colorTemp: '--atmosphere-color-temp',
    turbulence: '--atmosphere-turbulence',
    fogDensity: '--atmosphere-fog-density',
  },
  
  // Agent constellation state
  constellation: {
    nodeCount: '--constellation-node-count',
    connectionOpacity: '--constellation-connection-opacity',
    pulsePhase: '--constellation-pulse-phase',
  },
  
  // Cognitive loop state
  cognitive: {
    currentPhase: '--cognitive-current-phase',
    flowSpeed: '--cognitive-flow-speed',
    bottleneckSeverity: '--cognitive-bottleneck-severity',
  },
  
  // Memory space camera
  memory: {
    cameraX: '--memory-camera-x',
    cameraY: '--memory-camera-y',
    cameraZ: '--memory-camera-z',
    zoom: '--memory-zoom',
  },
} as const;

// ============================================================================
// TOKEN EXPORTS
// ============================================================================

export type PrimitiveTokens = typeof primitive;
export type SemanticTokens = typeof semantic;
export type ComponentTokens = typeof component;
export type DynamicTokens = typeof dynamic;

// Flattened export for easy access
export const tokens = {
  primitive,
  semantic,
  component,
  dynamic,
} as const;

// Legacy compatibility (existing theme values)
export const legacy = {
  ...existingTokens,
  SuperNovaCyan: primitive.color.supernovaCyan,
  SpaceGrotesk: primitive.typography.fontFamily.ui,
};

export default tokens;
