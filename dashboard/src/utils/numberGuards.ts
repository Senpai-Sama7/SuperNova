/**
 * Number Guards and Utilities
 * Type-safe number manipulation utilities
 */

/**
 * Safely convert any value to a finite number
 * Returns defaultValue if conversion fails
 */
export function toFiniteNumber(value: unknown, defaultValue: number = 0): number {
  if (value === null || value === undefined) {
    return defaultValue;
  }
  
  const num = typeof value === 'number' ? value : Number(value);
  
  if (Number.isFinite(num)) {
    return num;
  }
  
  return defaultValue;
}

/**
 * Clamp a number between min and max (inclusive)
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Clamp a value to percentage range (0-100)
 */
export function clampPercentage(value: number): number {
  return clamp(value, 0, 100);
}

/**
 * Clamp a value to normalized range (0-1)
 */
export function clampNormalized(value: number): number {
  return clamp(value, 0, 1);
}

/**
 * Round to specified decimal places
 */
export function roundTo(value: number, decimals: number = 2): number {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
}

/**
 * Format number as percentage string
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${roundTo(value, decimals)}%`;
}

/**
 * Check if value is a valid number (not NaN, not Infinity)
 */
export function isValidNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

/**
 * Safe division that returns 0 instead of NaN/Infinity
 */
export function safeDivide(numerator: number, denominator: number, defaultValue: number = 0): number {
  if (denominator === 0 || !Number.isFinite(numerator) || !Number.isFinite(denominator)) {
    return defaultValue;
  }
  return numerator / denominator;
}

/**
 * Calculate average of an array of numbers
 */
export function average(values: number[]): number {
  if (values.length === 0) return 0;
  const sum = values.reduce((a, b) => a + b, 0);
  return sum / values.length;
}

/**
 * Calculate standard deviation
 */
export function standardDeviation(values: number[]): number {
  if (values.length === 0) return 0;
  const avg = average(values);
  const squareDiffs = values.map(v => Math.pow(v - avg, 2));
  return Math.sqrt(average(squareDiffs));
}
