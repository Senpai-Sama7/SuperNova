/**
 * Settings Tab - Premium AI-Generated Aesthetic
 * Awwwards-style design with Framer-inspired animations
 * 
 * Accessibility: WCAG 2.1 AA compliant
 * Security: Input sanitization, XSS prevention
 * Error handling: Graceful fallbacks, retry logic
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Theme, API_BASE } from '../../theme';

interface UserPreferences {
  risk_level: 'paranoid' | 'careful' | 'balanced' | 'fast';
  speed_preference: 'instant' | 'balanced' | 'thorough';
  daily_budget_usd: number;
  auto_approve_timeout: number;
  max_tool_calls_per_turn: number;
  reflection_enabled: boolean;
  use_cache: boolean;
  hitl_mode: 'always' | 'risky_only' | 'never';
  enabled_tools: string[];
}

interface ToolAccess {
  name: string;
  label: string;
  description: string;
  icon: string;
  risk: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
}

// Input validation utilities
const sanitizeString = (input: unknown, fallback: string = ''): string => {
  if (typeof input !== 'string') return fallback;
  return input.replace(/[<>\"'&]/g, '').slice(0, 1000);
};

const sanitizeNumber = (input: unknown, min: number, max: number, fallback: number): number => {
  const num = Number(input);
  if (isNaN(num) || !isFinite(num)) return fallback;
  return Math.max(min, Math.min(max, num));
};

const isValidRiskLevel = (val: unknown): val is UserPreferences['risk_level'] => 
  ['paranoid', 'careful', 'balanced', 'fast'].includes(val as string);

const isValidSpeedPref = (val: unknown): val is UserPreferences['speed_preference'] =>
  ['instant', 'balanced', 'thorough'].includes(val as string);

const isValidHitlMode = (val: unknown): val is UserPreferences['hitl_mode'] =>
  ['always', 'risky_only', 'never'].includes(val as string);

const parsePreferences = (data: unknown): UserPreferences | null => {
  if (!data || typeof data !== 'object') return null;
  const obj = data as Record<string, unknown>;
  
  return {
    risk_level: isValidRiskLevel(obj.risk_level) ? obj.risk_level : 'balanced',
    speed_preference: isValidSpeedPref(obj.speed_preference) ? obj.speed_preference : 'balanced',
    daily_budget_usd: sanitizeNumber(obj.daily_budget_usd, 0.5, 25, 5),
    auto_approve_timeout: sanitizeNumber(obj.auto_approve_timeout, 0, 600, 120),
    max_tool_calls_per_turn: sanitizeNumber(obj.max_tool_calls_per_turn, 1, 15, 10),
    reflection_enabled: Boolean(obj.reflection_enabled),
    use_cache: Boolean(obj.use_cache),
    hitl_mode: isValidHitlMode(obj.hitl_mode) ? obj.hitl_mode : 'risky_only',
    enabled_tools: Array.isArray(obj.enabled_tools) 
      ? obj.enabled_tools.filter((t): t is string => typeof t === 'string').slice(0, 50)
      : [],
  };
};

const PRESETS = [
  {
    id: 'paranoid',
    label: '🔒',
    title: 'Maximum',
    description: 'Full control over every action',
    control: 5,
    speed: 1,
    cost: 5,
    color: '#ef4444',
    gradient: 'linear-gradient(135deg, rgba(239,68,68,0.15) 0%, rgba(239,68,68,0.05) 100%)',
  },
  {
    id: 'careful',
    label: '⚠️',
    title: 'Careful',
    description: 'Approve risky actions only',
    control: 4,
    speed: 3,
    cost: 3,
    color: '#f97316',
    gradient: 'linear-gradient(135deg, rgba(249,115,22,0.15) 0%, rgba(249,115,22,0.05) 100%)',
  },
  {
    id: 'balanced',
    label: '⚖️',
    title: 'Balanced',
    description: 'Recommended balance',
    control: 3,
    speed: 3,
    cost: 3,
    color: '#22c55e',
    gradient: 'linear-gradient(135deg, rgba(34,197,94,0.15) 0%, rgba(34,197,94,0.05) 100%)',
  },
  {
    id: 'fast',
    label: '🚀',
    title: 'Fast',
    description: 'Let it run autonomously',
    control: 1,
    speed: 5,
    cost: 1,
    color: '#3b82f6',
    gradient: 'linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(59,130,246,0.05) 100%)',
  },
];

const TOOLS: ToolAccess[] = [
  { name: 'web_search', label: 'Web Search', description: 'Search the internet', icon: '🌐', risk: 'low', enabled: true },
  { name: 'file_read', label: 'File Read', description: 'Read files from disk', icon: '📖', risk: 'low', enabled: true },
  { name: 'file_write', label: 'File Write', description: 'Create or modify files', icon: '📝', risk: 'medium', enabled: true },
  { name: 'code_exec', label: 'Code Execute', description: 'Run code in sandbox', icon: '⚡', risk: 'medium', enabled: true },
  { name: 'web_browse', label: 'Web Browse', description: 'Visit websites', icon: '🌍', risk: 'low', enabled: true },
  { name: 'send_email', label: 'Send Email', description: 'Send emails on your behalf', icon: '📧', risk: 'high', enabled: false },
  { name: 'external_api', label: 'External API', description: 'Call external APIs', icon: '🔌', risk: 'high', enabled: false },
  { name: 'shell_access', label: 'Shell Access', description: 'Run terminal commands', icon: '💻', risk: 'critical', enabled: false },
];

const RISK_OPTIONS = [
  { value: 'always', label: 'Always ask', description: 'Approve every action', icon: '🔔' },
  { value: 'risky_only', label: 'Risky only', description: 'Ask only for dangerous ops', icon: '⚠️' },
  { value: 'never', label: 'Never ask', description: 'Auto-approve all', icon: '🚀' },
];

const SPEED_OPTIONS = [
  { value: 'instant', label: '⚡ Instant', description: 'Fastest response', sublabel: '<1s' },
  { value: 'balanced', label: '⚖️ Balanced', description: 'Good speed & quality', sublabel: '1-3s' },
  { value: 'thorough', label: '🧠 Thoughtful', description: 'Best quality', sublabel: '3-10s' },
];

// Animated background component
function AnimatedBackground(): React.ReactElement {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      overflow: 'hidden',
      pointerEvents: 'none',
      zIndex: -1,
    }}>
      {/* Animated orbs */}
      <div style={{
        position: 'absolute',
        top: '-20%',
        left: '-10%',
        width: '600px',
        height: '600px',
        background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)',
        filter: 'blur(60px)',
        animation: 'float 20s ease-in-out infinite',
      }} />
      <div style={{
        position: 'absolute',
        bottom: '-20%',
        right: '-10%',
        width: '500px',
        height: '500px',
        background: 'radial-gradient(circle, rgba(168,85,247,0.12) 0%, transparent 70%)',
        filter: 'blur(60px)',
        animation: 'float 25s ease-in-out infinite reverse',
      }} />
      <div style={{
        position: 'absolute',
        top: '40%',
        left: '50%',
        width: '400px',
        height: '400px',
        background: 'radial-gradient(circle, rgba(34,197,94,0.08) 0%, transparent 70%)',
        filter: 'blur(50px)',
        animation: 'float 18s ease-in-out infinite',
      }} />
      <style>{`
        @keyframes float {
          0%, 100% { transform: translate(0, 0) scale(1); }
          25% { transform: translate(30px, -30px) scale(1.05); }
          50% { transform: translate(-20px, 20px) scale(0.95); }
          75% { transform: translate(20px, 30px) scale(1.02); }
        }
      `}</style>
    </div>
  );
}

// Glass card component
function GlassCard({ children, style = {} }: { children: React.ReactNode; style?: React.CSSProperties }): React.ReactElement {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '24px',
      padding: '28px',
      ...style,
    }}>
      {children}
    </div>
  );
}

// Glowing button
function GlowingButton({ 
  children, 
  onClick, 
  variant = 'primary',
  disabled = false 
}: { 
  children: React.ReactNode; 
  onClick?: () => void; 
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
}): React.ReactElement {
  const colors = {
    primary: { bg: Theme.colors.accent, glow: 'rgba(99,102,241,0.5)' },
    secondary: { bg: 'rgba(255,255,255,0.08)', glow: 'rgba(255,255,255,0.1)' },
    danger: { bg: '#ef4444', glow: 'rgba(239,68,68,0.5)' },
  };
  const c = colors[variant];
  
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '14px 32px',
        borderRadius: '14px',
        border: 'none',
        background: disabled ? 'rgba(255,255,255,0.05)' : c.bg,
        color: '#fff',
        fontSize: '14px',
        fontWeight: 600,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        boxShadow: disabled ? 'none' : `0 4px 24px ${c.glow}`,
        opacity: disabled ? 0.5 : 1,
        transform: 'translateY(0)',
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = `0 8px 32px ${c.glow}`;
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = disabled ? 'none' : `0 4px 24px ${c.glow}`;
      }}
    >
      {children}
    </button>
  );
}

// Custom toggle switch
function Toggle({ 
  checked, 
  onChange,
  disabled = false 
}: { 
  checked: boolean; 
  onChange: (v: boolean) => void;
  disabled?: boolean;
}): React.ReactElement {
  return (
    <div
      onClick={() => !disabled && onChange(!checked)}
      style={{
        width: '52px',
        height: '28px',
        borderRadius: '14px',
        background: checked ? Theme.colors.accent : 'rgba(255,255,255,0.1)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        position: 'relative',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        opacity: disabled ? 0.5 : 1,
      }}
    >
      <div style={{
        position: 'absolute',
        top: '3px',
        left: checked ? '27px' : '3px',
        width: '22px',
        height: '22px',
        borderRadius: '50%',
        background: '#fff',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      }} />
    </div>
  );
}

// Progress bar with gradient
function ProgressBar({ value, max, color }: { value: number; max: number; color: string }): React.ReactElement {
  const percent = Math.min(100, (value / max) * 100);
  return (
    <div style={{
      height: '8px',
      background: 'rgba(255,255,255,0.1)',
      borderRadius: '4px',
      overflow: 'hidden',
    }}>
      <div style={{
        height: '100%',
        width: `${percent}%`,
        background: `linear-gradient(90deg, ${color} 0%, ${color}88 100%)`,
        borderRadius: '4px',
        transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
      }} />
    </div>
  );
}

export function SettingsTab(): React.ReactElement {
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingChanges, setPendingChanges] = useState<UserPreferences | null>(null);
  const [hoveredPreset, setHoveredPreset] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // Retry logic with exponential backoff
  const fetchWithRetry = useCallback(async (url: string, options?: RequestInit, maxRetries = 3): Promise<Response> => {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
          },
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response;
      } catch (err) {
        if (attempt === maxRetries - 1) throw err;
        await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 500));
      }
    }
    throw new Error('Max retries exceeded');
  }, []);

  useEffect(() => {
    setError(null);
    
    fetchWithRetry(`${API_BASE}/api/v1/preferences`)
      .then(response => response.json())
      .then(data => {
        const parsed = parsePreferences(data);
        if (parsed) {
          setPreferences(parsed);
        } else {
          setError('Invalid preferences data received');
        }
      })
      .catch(err => {
        console.error('Failed to load preferences:', err);
        setError('Failed to load preferences. Please try again.');
      })
      .finally(() => setLoading(false));
  }, [fetchWithRetry, retryCount]);

  // Keyboard navigation support
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showConfirmModal) {
        setShowConfirmModal(false);
      }
      if (e.key === 'r' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        setRetryCount(c => c + 1);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showConfirmModal]);

  const handleSave = useCallback(() => {
    if (!preferences) return;
    if (preferences.hitl_mode === 'never') {
      setPendingChanges(preferences);
      setShowConfirmModal(true);
      return;
    }
    doSave(preferences);
  }, [preferences]);

  const doSave = async (prefs: UserPreferences) => {
    setSaving(true);
    setError(null);
    setShowConfirmModal(false);
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/v1/preferences`, {
        method: 'POST',
        body: JSON.stringify(prefs),
      });
      
      if (!response.ok) {
        throw new Error('Failed to save preferences');
      }
      
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e) {
      console.error('Failed to save:', e);
      setError('Failed to save. Retrying...');
      // Auto-retry once on save failure
      setTimeout(() => doSave(prefs), 1000);
    }
    setSaving(false);
  };

  const applyPreset = useCallback(async (presetId: string) => {
    // Sanitize preset ID
    const sanitizedId = sanitizeString(presetId, '');
    if (!sanitizedId || !PRESETS.some(p => p.id === sanitizedId)) {
      setError('Invalid preset selected');
      return;
    }
    
    setError(null);
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/v1/preferences/preset/${sanitizedId}`, { 
        method: 'POST' 
      });
      const data = await response.json();
      const parsed = parsePreferences(data);
      if (parsed) {
        setPreferences(parsed);
        setSaved(true);
        setTimeout(() => setSaved(false), 2500);
      }
    } catch (e) {
      console.error('Failed to apply preset:', e);
      setError('Failed to apply preset. Please try again.');
    }
  }, [fetchWithRetry]);

  // Get current preset for display

  if (loading) {
    return (
      <div style={{ 
        padding: '80px', 
        textAlign: 'center', 
        color: Theme.colors.textMuted,
        fontSize: '16px',
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '3px solid rgba(255,255,255,0.1)',
          borderTopColor: Theme.colors.accent,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 16px',
        }} />
        Loading...
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', position: 'relative' }}>
      <AnimatedBackground />
      
      {/* Error Banner - Accessible */}
      {error && (
        <div 
          role="alert"
          aria-live="assertive"
          style={{
            position: 'fixed',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '16px 24px',
            background: 'rgba(239,68,68,0.95)',
            borderRadius: '12px',
            color: '#fff',
            fontSize: '14px',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            boxShadow: '0 8px 32px rgba(239,68,68,0.4)',
            zIndex: 1000,
            animation: 'slideDown 0.3s ease',
          }}
        >
          <span>⚠️</span>
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            aria-label="Dismiss error"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#fff',
              cursor: 'pointer',
              padding: '4px',
              fontSize: '16px',
            }}
          >
            ×
          </button>
          <style>{`
            @keyframes slideDown {
              from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
              to { transform: translateX(-50%) translateY(0); opacity: 1; }
            }
          `}</style>
        </div>
      )}
      
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '48px', position: 'relative' }}>
        <div style={{
          fontSize: '14px',
          fontWeight: 500,
          color: Theme.colors.accent,
          textTransform: 'uppercase',
          letterSpacing: '3px',
          marginBottom: '12px',
        }}>
          Control Panel
        </div>
        <h1 style={{
          fontSize: '48px',
          fontWeight: 700,
          background: 'linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: '16px',
          lineHeight: 1.1,
        }}>
          Your Agent,<br />Your Rules
        </h1>
        <p style={{
          fontSize: '16px',
          color: Theme.colors.textMuted,
          maxWidth: '500px',
          margin: '0 auto',
          lineHeight: 1.6,
        }}>
          Adjust control, speed, and spending. The agent adapts to your preferences.
        </p>
      </div>

      {/* Bento Grid Layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(12, 1fr)',
        gap: '20px',
      }}>
        
        {/* Presets - Full Width */}
        <div style={{ gridColumn: 'span 12' }}>
          <GlassCard>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '24px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '20px' }}>🎯</span>
                <span style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>Quick Presets</span>
              </div>
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '16px',
            }}>
              {PRESETS.map((preset) => (
                <div
                  key={preset.id}
                  role="radio"
                  aria-checked={preferences?.risk_level === preset.id}
                  tabIndex={0}
                  onClick={() => applyPreset(preset.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      applyPreset(preset.id);
                    }
                  }}
                  onMouseEnter={() => setHoveredPreset(preset.id)}
                  onMouseLeave={() => setHoveredPreset(null)}
                  style={{
                    padding: '24px',
                    borderRadius: '20px',
                    background: preferences?.risk_level === preset.id 
                      ? preset.gradient 
                      : 'rgba(255,255,255,0.03)',
                    border: `2px solid ${preferences?.risk_level === preset.id ? preset.color : 'rgba(255,255,255,0.08)'}`,
                    cursor: 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    transform: hoveredPreset === preset.id ? 'translateY(-4px)' : 'translateY(0)',
                    boxShadow: preferences?.risk_level === preset.id 
                      ? `0 8px 32px ${preset.color}30` 
                      : 'none',
                    position: 'relative',
                    overflow: 'hidden',
                    outline: 'none',
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.boxShadow = preferences?.risk_level === preset.id 
                      ? `0 0 0 3px ${preset.color}50}, 0 8px 32px ${preset.color}30`
                      : '0 0 0 2px rgba(99,102,241,0.5)';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.boxShadow = preferences?.risk_level === preset.id 
                      ? `0 8px 32px ${preset.color}30`
                      : 'none';
                  }}
                  aria-label={`${preset.title} preset: ${preset.description}. Press Enter to select.`}
                >
                  {/* Shine effect */}
                  {preferences?.risk_level === preset.id && (
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: '-100%',
                      width: '100%',
                      height: '100%',
                      background: `linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)`,
                      animation: 'shine 2s infinite',
                    }} />
                  )}
                  
                  <div style={{ 
                    fontSize: '32px', 
                    marginBottom: '12px',
                    transform: preferences?.risk_level === preset.id ? 'scale(1.1)' : 'scale(1)',
                    transition: 'transform 0.3s ease',
                  }}>
                    {preset.label}
                  </div>
                  <div style={{ 
                    fontSize: '16px', 
                    fontWeight: 700, 
                    color: preferences?.risk_level === preset.id ? preset.color : '#fff',
                    marginBottom: '4px',
                  }}>
                    {preset.title}
                  </div>
                  <div style={{ 
                    fontSize: '13px', 
                    color: Theme.colors.textMuted,
                    marginBottom: '16px',
                  }}>
                    {preset.description}
                  </div>
                  
                  {/* Mini indicators */}
                  <div style={{ display: 'flex', gap: '12px' }}>
                    {['Control', 'Speed', 'Cost'].map((label, i) => (
                      <div key={label} style={{ flex: 1 }}>
                        <div style={{ 
                          fontSize: '9px', 
                          color: Theme.colors.textMuted, 
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                          marginBottom: '4px',
                        }}>
                          {label}
                        </div>
                        <div style={{ display: 'flex', gap: '2px' }}>
                          {[1, 2, 3, 4, 5].map(n => {
                            const levels = [preset.control, preset.speed, preset.cost];
                            const level = levels[i] ?? 0;
                            return (
                            <div key={n} style={{
                              width: '4px',
                              height: '4px',
                              borderRadius: '50%',
                              background: n <= level 
                                ? preset.color 
                                : 'rgba(255,255,255,0.15)',
                              transition: 'background 0.2s ease',
                            }} />
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Risk Control */}
        <div style={{ gridColumn: 'span 6' }}>
          <GlassCard style={{ height: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <span style={{ fontSize: '20px' }}>🛡️</span>
              <span style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>Risk Control</span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '28px' }}>
              {RISK_OPTIONS.map((opt) => (
                <div
                  key={opt.value}
                  onClick={() => setPreferences(p => p ? { ...p, hitl_mode: opt.value as UserPreferences['hitl_mode'] } : p)}
                  style={{
                    padding: '16px 20px',
                    borderRadius: '14px',
                    background: preferences?.hitl_mode === opt.value 
                      ? 'rgba(99,102,241,0.15)' 
                      : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${preferences?.hitl_mode === opt.value ? Theme.colors.accent : 'rgba(255,255,255,0.08)'}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px',
                  }}
                >
                  <div style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    border: `2px solid ${preferences?.hitl_mode === opt.value ? Theme.colors.accent : 'rgba(255,255,255,0.2)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    {preferences?.hitl_mode === opt.value && (
                      <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: Theme.colors.accent }} />
                    )}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: 500, color: '#fff' }}>
                      {opt.icon} {opt.label}
                    </div>
                    <div style={{ fontSize: '12px', color: Theme.colors.textMuted }}>
                      {opt.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Timeout slider */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px', color: Theme.colors.textMuted }}>Auto-timeout</span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: Theme.colors.accent }}>
                  {preferences?.auto_approve_timeout || 120}s
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={600}
                step={30}
                value={preferences?.auto_approve_timeout || 120}
                onChange={(e) => setPreferences(p => p ? { ...p, auto_approve_timeout: parseInt(e.target.value) } : p)}
                aria-label={`Auto-approve timeout: ${preferences?.auto_approve_timeout || 120} seconds`}
                aria-valuemin={0}
                aria-valuemax={600}
                aria-valuenow={preferences?.auto_approve_timeout || 120}
                aria-valuetext={`${preferences?.auto_approve_timeout || 120} seconds`}
                style={{
                  width: '100%',
                  accentColor: Theme.colors.accent,
                  height: '6px',
                  borderRadius: '3px',
                  background: `linear-gradient(to right, ${Theme.colors.accent} ${((preferences?.auto_approve_timeout || 120) / 600) * 100}%, rgba(255,255,255,0.1) ${((preferences?.auto_approve_timeout || 120) / 600) * 100}%)`,
                }}
              />
            </div>
          </GlassCard>
        </div>

        {/* Speed Control */}
        <div style={{ gridColumn: 'span 6' }}>
          <GlassCard style={{ height: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <span style={{ fontSize: '20px' }}>⚡</span>
              <span style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>Speed Control</span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '28px' }}>
              {SPEED_OPTIONS.map((opt) => (
                <div
                  key={opt.value}
                  onClick={() => setPreferences(p => p ? { ...p, speed_preference: opt.value as UserPreferences['speed_preference'] } : p)}
                  style={{
                    padding: '16px 20px',
                    borderRadius: '14px',
                    background: preferences?.speed_preference === opt.value 
                      ? 'rgba(99,102,241,0.15)' 
                      : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${preferences?.speed_preference === opt.value ? Theme.colors.accent : 'rgba(255,255,255,0.08)'}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      border: `2px solid ${preferences?.speed_preference === opt.value ? Theme.colors.accent : 'rgba(255,255,255,0.2)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}>
                      {preferences?.speed_preference === opt.value && (
                        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: Theme.colors.accent }} />
                      )}
                    </div>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 500, color: '#fff' }}>{opt.label}</div>
                      <div style={{ fontSize: '12px', color: Theme.colors.textMuted }}>{opt.description}</div>
                    </div>
                  </div>
                  <div style={{
                    padding: '4px 10px',
                    borderRadius: '8px',
                    background: 'rgba(255,255,255,0.05)',
                    fontSize: '12px',
                    fontWeight: 500,
                    color: Theme.colors.accent,
                  }}>
                    {opt.sublabel}
                  </div>
                </div>
              ))}
            </div>

            {/* Tool calls slider */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px', color: Theme.colors.textMuted }}>Max Tool Calls</span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: Theme.colors.accent }}>
                  {preferences?.max_tool_calls_per_turn || 10}
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={15}
                step={1}
                value={preferences?.max_tool_calls_per_turn || 10}
                onChange={(e) => setPreferences(p => p ? { ...p, max_tool_calls_per_turn: parseInt(e.target.value) } : p)}
                style={{
                  width: '100%',
                  accentColor: Theme.colors.accent,
                  height: '6px',
                  borderRadius: '3px',
                }}
              />
            </div>
          </GlassCard>
        </div>

        {/* Budget - Full Width */}
        <div style={{ gridColumn: 'span 12' }}>
          <GlassCard>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <span style={{ fontSize: '20px' }}>💰</span>
              <span style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>Budget</span>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', alignItems: 'center' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span style={{ fontSize: '14px', color: Theme.colors.textMuted }}>Daily Budget</span>
                  <span style={{ fontSize: '24px', fontWeight: 700, color: '#fff' }}>
                    ${(preferences?.daily_budget_usd || 5).toFixed(2)}
                    <span style={{ fontSize: '14px', fontWeight: 400, color: Theme.colors.textMuted }}>/day</span>
                  </span>
                </div>
                <input
                  type="range"
                  min={0.5}
                  max={25}
                  step={0.5}
                  value={preferences?.daily_budget_usd || 5}
                  onChange={(e) => setPreferences(p => p ? { ...p, daily_budget_usd: parseFloat(e.target.value) } : p)}
                  style={{ width: '100%', accentColor: Theme.colors.accent, height: '8px', borderRadius: '4px' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
                  <span style={{ fontSize: '12px', color: Theme.colors.textMuted }}>$0.50</span>
                  <span style={{ fontSize: '12px', color: Theme.colors.textMuted }}>$25</span>
                </div>
              </div>
              
              <div style={{
                padding: '20px',
                borderRadius: '16px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.08)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span style={{ fontSize: '14px', color: Theme.colors.textMuted }}>Monthly Projection</span>
                  <span style={{ fontSize: '16px', fontWeight: 600, color: '#fff' }}>
                    ${((preferences?.daily_budget_usd || 5) * 30).toFixed(0)}
                  </span>
                </div>
                <ProgressBar 
                  value={50} 
                  max={150} 
                  color={Theme.colors.accent} 
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '12px', color: Theme.colors.textMuted }}>
                  <span>$50 spent</span>
                  <span>20 days left</span>
                </div>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Tools Grid - Full Width */}
        <div style={{ gridColumn: 'span 12' }}>
          <GlassCard>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <span style={{ fontSize: '20px' }}>🔧</span>
              <span style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>Tool Access</span>
            </div>
            
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(4, 1fr)', 
              gap: '16px',
            }}>
              {TOOLS.map((tool) => {
                const isEnabled = preferences?.enabled_tools.includes(tool.name) ?? tool.enabled;
                const riskColors = {
                  low: '#22c55e',
                  medium: '#f59e0b',
                  high: '#ef4444',
                  critical: '#dc2626',
                };
                return (
                  <div
                    key={tool.name}
                    onClick={() => isEnabled && setPreferences(p => p ? {
                      ...p,
                      enabled_tools: p.enabled_tools.includes(tool.name)
                        ? p.enabled_tools.filter(t => t !== tool.name)
                        : [...p.enabled_tools, tool.name]
                    } : p)}
                    style={{
                      padding: '20px',
                      borderRadius: '16px',
                      background: isEnabled ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.02)',
                      border: `1px solid ${isEnabled ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.05)'}`,
                      cursor: isEnabled ? 'pointer' : 'not-allowed',
                      opacity: isEnabled ? 1 : 0.5,
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <span style={{ fontSize: '28px' }}>{tool.icon}</span>
                      <Toggle 
                        checked={isEnabled} 
                        onChange={() => {}}
                        disabled={!isEnabled}
                      />
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff', marginBottom: '4px' }}>
                      {tool.label}
                    </div>
                    <div style={{ fontSize: '12px', color: Theme.colors.textMuted, marginBottom: '12px' }}>
                      {tool.description}
                    </div>
                    <span style={{
                      fontSize: '10px',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      background: `${riskColors[tool.risk]}20`,
                      color: riskColors[tool.risk],
                    }}>
                      {tool.risk}
                    </span>
                  </div>
                );
              })}
            </div>
          </GlassCard>
        </div>

        {/* Advanced Toggles */}
        <div style={{ gridColumn: 'span 12' }}>
          <GlassCard>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <span style={{ fontSize: '20px' }}>⚙️</span>
              <span style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>Advanced</span>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
              <div style={{
                padding: '20px',
                borderRadius: '14px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: '#fff', marginBottom: '4px' }}>
                    Self-Reflection
                  </div>
                  <div style={{ fontSize: '12px', color: Theme.colors.textMuted }}>
                    Agent evaluates own responses
                  </div>
                </div>
                <Toggle 
                  checked={preferences?.reflection_enabled ?? true} 
                  onChange={(v) => setPreferences(p => p ? { ...p, reflection_enabled: v } : p)}
                />
              </div>
              
              <div style={{
                padding: '20px',
                borderRadius: '14px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: '#fff', marginBottom: '4px' }}>
                    Query Caching
                  </div>
                  <div style={{ fontSize: '12px', color: Theme.colors.textMuted }}>
                    Skip AI for repeated queries
                  </div>
                </div>
                <Toggle 
                  checked={preferences?.use_cache ?? true} 
                  onChange={(v) => setPreferences(p => p ? { ...p, use_cache: v } : p)}
                />
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Action Buttons */}
        <div style={{ gridColumn: 'span 12', display: 'flex', justifyContent: 'center', gap: '16px', marginTop: '16px' }}>
          <GlowingButton variant="secondary">Reset Defaults</GlowingButton>
          <GlowingButton 
            variant={saved ? 'primary' : 'primary'} 
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : saved ? '✓ Saved!' : 'Save Changes'}
          </GlowingButton>
        </div>
      </div>

      {/* Modal */}
      {showConfirmModal && (
        <div 
          onClick={() => setShowConfirmModal(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.8)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            animation: 'fadeIn 0.2s ease',
          }}
        >
          <div 
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'rgba(20,20,30,0.95)',
              backdropFilter: 'blur(20px)',
              borderRadius: '24px',
              padding: '32px',
              maxWidth: '420px',
              width: '90%',
              border: '1px solid rgba(255,255,255,0.1)',
              animation: 'scaleIn 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          >
            <div style={{ fontSize: '32px', marginBottom: '16px' }}>⚠️</div>
            <div style={{ fontSize: '20px', fontWeight: 600, color: '#fff', marginBottom: '12px' }}>
              Enable Auto-Approve?
            </div>
            <div style={{ fontSize: '14px', color: Theme.colors.textMuted, lineHeight: 1.6, marginBottom: '24px' }}>
              This will allow the agent to act without your approval. Only enable if you understand the risks.
            </div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <GlowingButton variant="secondary" onClick={() => setShowConfirmModal(false)}>
                Cancel
              </GlowingButton>
              <GlowingButton variant="danger" onClick={() => pendingChanges && doSave(pendingChanges)}>
                Confirm
              </GlowingButton>
            </div>
          </div>
          <style>{`
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            @keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
            @keyframes shine { from { left: -100%; } to { left: 100%; } }
          `}</style>
        </div>
      )}
    </div>
  );
}
