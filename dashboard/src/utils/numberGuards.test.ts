/**
 * Number Guards Tests
 */
import { describe, it, expect } from 'vitest';
import {
  toFiniteNumber,
  clamp,
  clampPercentage,
  clampNormalized,
  roundTo,
  formatPercent,
  isValidNumber,
  safeDivide,
  average,
  standardDeviation,
} from './numberGuards';

describe('toFiniteNumber', () => {
  it('returns the value when given a valid number', () => {
    expect(toFiniteNumber(42)).toBe(42);
    expect(toFiniteNumber(3.14)).toBe(3.14);
    expect(toFiniteNumber(0)).toBe(0);
    expect(toFiniteNumber(-10)).toBe(-10);
  });

  it('converts string numbers to numbers', () => {
    expect(toFiniteNumber('42')).toBe(42);
    expect(toFiniteNumber('3.14')).toBe(3.14);
    expect(toFiniteNumber('0')).toBe(0);
  });

  it('returns default value for null/undefined', () => {
    expect(toFiniteNumber(null)).toBe(0);
    expect(toFiniteNumber(undefined)).toBe(0);
    expect(toFiniteNumber(null, 5)).toBe(5);
    expect(toFiniteNumber(undefined, 10)).toBe(10);
  });

  it('returns default value for non-finite numbers', () => {
    expect(toFiniteNumber(NaN)).toBe(0);
    expect(toFiniteNumber(Infinity)).toBe(0);
    expect(toFiniteNumber(-Infinity)).toBe(0);
    expect(toFiniteNumber(NaN, 99)).toBe(99);
  });

  it('returns default value for invalid strings', () => {
    expect(toFiniteNumber('not a number')).toBe(0);
    expect(toFiniteNumber('')).toBe(0);
  });
});

describe('clamp', () => {
  it('returns value when within range', () => {
    expect(clamp(5, 0, 10)).toBe(5);
    expect(clamp(0, 0, 10)).toBe(0);
    expect(clamp(10, 0, 10)).toBe(10);
  });

  it('clamps to min when below range', () => {
    expect(clamp(-5, 0, 10)).toBe(0);
    expect(clamp(-100, -50, 50)).toBe(-50);
  });

  it('clamps to max when above range', () => {
    expect(clamp(15, 0, 10)).toBe(10);
    expect(clamp(100, -50, 50)).toBe(50);
  });
});

describe('clampPercentage', () => {
  it('clamps values to 0-100 range', () => {
    expect(clampPercentage(50)).toBe(50);
    expect(clampPercentage(0)).toBe(0);
    expect(clampPercentage(100)).toBe(100);
    expect(clampPercentage(-10)).toBe(0);
    expect(clampPercentage(150)).toBe(100);
  });
});

describe('clampNormalized', () => {
  it('clamps values to 0-1 range', () => {
    expect(clampNormalized(0.5)).toBe(0.5);
    expect(clampNormalized(0)).toBe(0);
    expect(clampNormalized(1)).toBe(1);
    expect(clampNormalized(-0.5)).toBe(0);
    expect(clampNormalized(1.5)).toBe(1);
  });
});

describe('roundTo', () => {
  it('rounds to specified decimal places', () => {
    expect(roundTo(3.14159, 2)).toBe(3.14);
    expect(roundTo(3.14159, 0)).toBe(3);
    expect(roundTo(3.14159, 4)).toBe(3.1416);
  });

  it('handles negative numbers', () => {
    expect(roundTo(-3.14159, 2)).toBe(-3.14);
  });
});

describe('formatPercent', () => {
  it('formats number as percentage', () => {
    expect(formatPercent(42.5)).toBe('42.5%');
    expect(formatPercent(100)).toBe('100%');
    expect(formatPercent(0)).toBe('0%');
  });

  it('respects decimal places', () => {
    expect(formatPercent(42.555, 2)).toBe('42.56%');
    expect(formatPercent(42.555, 0)).toBe('43%');
  });
});

describe('isValidNumber', () => {
  it('returns true for valid numbers', () => {
    expect(isValidNumber(42)).toBe(true);
    expect(isValidNumber(0)).toBe(true);
    expect(isValidNumber(-10)).toBe(true);
    expect(isValidNumber(3.14)).toBe(true);
  });

  it('returns false for invalid values', () => {
    expect(isValidNumber(NaN)).toBe(false);
    expect(isValidNumber(Infinity)).toBe(false);
    expect(isValidNumber('42')).toBe(false);
    expect(isValidNumber(null)).toBe(false);
    expect(isValidNumber(undefined)).toBe(false);
  });
});

describe('safeDivide', () => {
  it('returns quotient for valid division', () => {
    expect(safeDivide(10, 2)).toBe(5);
    expect(safeDivide(7, 3)).toBeCloseTo(2.333, 3);
  });

  it('returns default value for division by zero', () => {
    expect(safeDivide(10, 0)).toBe(0);
    expect(safeDivide(10, 0, 99)).toBe(99);
  });

  it('returns default value for non-finite inputs', () => {
    expect(safeDivide(NaN, 2)).toBe(0);
    expect(safeDivide(10, Infinity)).toBe(0);
  });
});

describe('average', () => {
  it('calculates average of array', () => {
    expect(average([1, 2, 3, 4, 5])).toBe(3);
    expect(average([10, 20, 30])).toBe(20);
  });

  it('returns 0 for empty array', () => {
    expect(average([])).toBe(0);
  });

  it('handles single value', () => {
    expect(average([42])).toBe(42);
  });
});

describe('standardDeviation', () => {
  it('calculates standard deviation', () => {
    const result = standardDeviation([2, 4, 4, 4, 5, 5, 7, 9]);
    expect(result).toBeCloseTo(2, 0);
  });

  it('returns 0 for empty array', () => {
    expect(standardDeviation([])).toBe(0);
  });

  it('returns 0 for single value', () => {
    expect(standardDeviation([5])).toBe(0);
  });
});
