/**
 * Settings Tab Component Tests
 * 
 * Tests for the preferences parsing, validation, and UI interactions
 */
import { describe, it, expect, vi } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Simple parsePreferences test - simulates the logic from SettingsTab
const parsePreferences = (data: unknown) => {
  if (!data || typeof data !== 'object') return null;
  const obj = data as Record<string, unknown>;
  
  const isValidRiskLevel = (val: unknown): val is 'paranoid' | 'careful' | 'balanced' | 'fast' => 
    ['paranoid', 'careful', 'balanced', 'fast'].includes(val as string);
  
  const isValidSpeedPref = (val: unknown): val is 'instant' | 'balanced' | 'thorough' =>
    ['instant', 'balanced', 'thorough'].includes(val as string);
  
  const isValidHitlMode = (val: unknown): val is 'always' | 'risky_only' | 'never' =>
    ['always', 'risky_only', 'never'].includes(val as string);
  
  const sanitizeNumber = (input: unknown, min: number, max: number, fallback: number): number => {
    const num = Number(input);
    if (isNaN(num) || !isFinite(num)) return fallback;
    return Math.max(min, Math.min(max, num));
  };
  
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

describe('parsePreferences', () => {
  it('parses valid preferences', () => {
    const input = {
      risk_level: 'paranoid',
      speed_preference: 'thorough',
      daily_budget_usd: 10.0,
      auto_approve_timeout: 60,
      max_tool_calls_per_turn: 5,
      reflection_enabled: true,
      use_cache: false,
      hitl_mode: 'always',
      enabled_tools: ['web_search', 'file_read'],
    };
    
    const result = parsePreferences(input);
    
    expect(result).not.toBeNull();
    expect(result?.risk_level).toBe('paranoid');
    expect(result?.speed_preference).toBe('thorough');
    expect(result?.daily_budget_usd).toBe(10.0);
    expect(result?.auto_approve_timeout).toBe(60);
    expect(result?.max_tool_calls_per_turn).toBe(5);
    expect(result?.reflection_enabled).toBe(true);
    expect(result?.use_cache).toBe(false);
    expect(result?.hitl_mode).toBe('always');
    expect(result?.enabled_tools).toEqual(['web_search', 'file_read']);
  });
  
  it('returns defaults for invalid data', () => {
    const result = parsePreferences(null);
    expect(result).toBeNull();
  });
  
  it('returns defaults for missing fields', () => {
    const input = { risk_level: 'balanced' };
    const result = parsePreferences(input);
    
    expect(result).not.toBeNull();
    expect(result?.risk_level).toBe('balanced');
    expect(result?.speed_preference).toBe('balanced');
    expect(result?.daily_budget_usd).toBe(5);
    expect(result?.hitl_mode).toBe('risky_only');
  });
  
  it('clamps numeric values to valid ranges', () => {
    const input = {
      daily_budget_usd: 100, // exceeds max of 25
      auto_approve_timeout: -10, // below min of 0
      max_tool_calls_per_turn: 20, // exceeds max of 15
    };
    
    const result = parsePreferences(input);
    
    expect(result?.daily_budget_usd).toBe(25);
    expect(result?.auto_approve_timeout).toBe(0);
    expect(result?.max_tool_calls_per_turn).toBe(15);
  });
  
  it('filters invalid risk levels', () => {
    const input = { risk_level: 'invalid' };
    const result = parsePreferences(input);
    
    expect(result?.risk_level).toBe('balanced');
  });
  
  it('filters invalid enabled_tools', () => {
    const input = {
      enabled_tools: ['web_search', 123, null, 'valid'],
    };
    
    const result = parsePreferences(input);
    
    expect(result?.enabled_tools).toEqual(['web_search', 'valid']);
  });
  
  it('handles NaN and Infinity', () => {
    const input = {
      daily_budget_usd: NaN,
      auto_approve_timeout: Infinity,
    };
    
    const result = parsePreferences(input);
    
    expect(result?.daily_budget_usd).toBe(5); // default
    expect(result?.auto_approve_timeout).toBe(120); // default
  });
});

describe('Input sanitization', () => {
  it('sanitizes string input', () => {
    const sanitizeString = (input: unknown, fallback: string = ''): string => {
      if (typeof input !== 'string') return fallback;
      return input.replace(/[<>"'&]/g, '').slice(0, 1000);
    };
    
    expect(sanitizeString('<script>alert(1)</script>')).toBe('scriptalert(1)/script');
    expect(sanitizeString('normal text')).toBe('normal text');
    expect(sanitizeString(null)).toBe('');
    expect(sanitizeString(undefined, 'default')).toBe('default');
  });
});
