/**
 * Entropy Calculation Tests
 */
import { describe, it, expect } from 'vitest';
import {
  calculateEntropy,
  normalizeToDistribution,
  computeSemanticEntropy,
  calculateDisagreement,
} from './entropy';
import type { SemanticCluster } from '../types';

describe('calculateEntropy', () => {
  it('calculates entropy for uniform distribution', () => {
    // Uniform distribution: maximum entropy
    const uniform = [0.25, 0.25, 0.25, 0.25];
    const result = calculateEntropy(uniform);
    expect(result).toBe(2); // log2(4) = 2
  });

  it('calculates entropy for deterministic distribution', () => {
    // Deterministic: zero entropy
    const deterministic = [1, 0, 0, 0];
    const result = calculateEntropy(deterministic);
    expect(result).toBe(0);
  });

  it('handles empty probabilities', () => {
    expect(calculateEntropy([])).toBe(0);
  });
});

describe('normalizeToDistribution', () => {
  it('normalizes values to sum to 1', () => {
    const result = normalizeToDistribution([1, 2, 3, 4]);
    const sum = result.reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1);
    expect(result).toEqual([0.1, 0.2, 0.3, 0.4]);
  });

  it('returns uniform distribution for all zeros', () => {
    const result = normalizeToDistribution([0, 0, 0]);
    expect(result).toEqual([1 / 3, 1 / 3, 1 / 3]);
  });

  it('handles single value', () => {
    expect(normalizeToDistribution([5])).toEqual([1]);
  });
});

describe('computeSemanticEntropy', () => {
  const createClusters = (sizes: number[], confidences: number[]): SemanticCluster[] => {
    return sizes.map((size, i) => ({
      id: `cluster-${i}`,
      label: `Cluster ${i}`,
      confidence: confidences[i] ?? 0.5,
      size,
      items: [],
    }));
  };

  it('returns neutral values for empty clusters', () => {
    const result = computeSemanticEntropy([]);
    expect(result.entropy).toBe(0);
    expect(result.confidence).toBe(0.5);
    expect(result.clusters).toBe(0);
    expect(result.distribution).toEqual([]);
  });

  it('calculates for single cluster', () => {
    const clusters = createClusters([10], [0.8]);
    const result = computeSemanticEntropy(clusters);
    expect(result.entropy).toBe(0);
    expect(result.clusters).toBe(1);
    expect(result.distribution).toEqual([1]);
  });

  it('calculates for multiple clusters', () => {
    const clusters = createClusters([10, 10, 10], [0.8, 0.7, 0.9]);
    const result = computeSemanticEntropy(clusters);
    expect(result.entropy).toBeGreaterThan(0);
    expect(result.entropy).toBeLessThanOrEqual(1);
    expect(result.clusters).toBe(3);
    expect(result.distribution).toEqual([1 / 3, 1 / 3, 1 / 3]);
  });

  it('handles zero-size clusters', () => {
    const clusters = createClusters([0, 10], [0.5, 0.8]);
    const result = computeSemanticEntropy(clusters);
    expect(result.clusters).toBe(2);
    expect(result.distribution).toEqual([0, 1]);
  });

  it('returns confidence in 0-1 range', () => {
    const clusters = createClusters([5, 5, 5, 5], [0.5, 0.5, 0.5, 0.5]);
    const result = computeSemanticEntropy(clusters);
    expect(result.confidence).toBeGreaterThanOrEqual(0);
    expect(result.confidence).toBeLessThanOrEqual(1);
  });
});

describe('calculateDisagreement', () => {
  const createClusters = (confidences: number[]): SemanticCluster[] => {
    return confidences.map((confidence, i) => ({
      id: `cluster-${i}`,
      label: `Cluster ${i}`,
      confidence,
      size: 1,
      items: [],
    }));
  };

  it('returns 0 for less than 2 clusters', () => {
    expect(calculateDisagreement([])).toBe(0);
    expect(calculateDisagreement(createClusters([0.8]))).toBe(0);
  });

  it('calculates disagreement as max - min confidence', () => {
    const clusters = createClusters([0.9, 0.5, 0.7]);
    expect(calculateDisagreement(clusters)).toBe(0.4); // 0.9 - 0.5
  });

  it('returns 0 when all confidences are equal', () => {
    const clusters = createClusters([0.7, 0.7, 0.7]);
    expect(calculateDisagreement(clusters)).toBe(0);
  });
});
