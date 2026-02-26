/**
 * Semantic Entropy Calculation
 * Measures uncertainty in semantic clustering
 */
import type { SemanticCluster, SemanticEntropyResult } from '../types';

/**
 * Calculate Shannon entropy from cluster distribution
 * Higher entropy = more uncertainty/disagreement
 */
export function calculateEntropy(probabilities: number[]): number {
  return probabilities.reduce((entropy, p) => {
    if (p > 0) {
      return entropy - p * Math.log2(p);
    }
    return entropy;
  }, 0);
}

/**
 * Normalize values to sum to 1 (probability distribution)
 */
export function normalizeToDistribution(values: number[]): number[] {
  const sum = values.reduce((a, b) => a + b, 0);
  if (sum === 0) {
    // Uniform distribution if all zeros
    return values.map(() => 1 / values.length);
  }
  return values.map(v => v / sum);
}

/**
 * Compute semantic entropy from clusters
 * Returns entropy (0-1), confidence (0-1), and cluster count
 */
export function computeSemanticEntropy(
  clusters: SemanticCluster[]
): SemanticEntropyResult {
  // Handle empty case
  if (!clusters || clusters.length === 0) {
    return {
      entropy: 0,
      confidence: 0.5, // Neutral confidence when no data
      clusters: 0,
      distribution: [],
    };
  }

  // Calculate sizes for distribution
  const sizes = clusters.map(c => c.size);
  const totalSize = sizes.reduce((a, b) => a + b, 0);
  
  if (totalSize === 0) {
    return {
      entropy: 0,
      confidence: 0.5,
      clusters: clusters.length,
      distribution: clusters.map(() => 1 / clusters.length),
    };
  }

  // Create probability distribution
  const distribution = sizes.map(s => s / totalSize);
  
  // Calculate entropy (max entropy is log2(n) for n clusters)
  const rawEntropy = calculateEntropy(distribution);
  const maxEntropy = Math.log2(clusters.length || 1);
  
  // Normalize to 0-1
  const normalizedEntropy = maxEntropy > 0 ? rawEntropy / maxEntropy : 0;
  
  // Confidence is inverse of entropy (high entropy = low confidence)
  // Apply sigmoid-like transformation for better UX
  const confidence = Math.pow(1 - normalizedEntropy, 2);

  return {
    entropy: roundTo(normalizedEntropy, 4),
    confidence: roundTo(confidence, 4),
    clusters: clusters.length,
    distribution,
  };
}

/**
 * Calculate disagreement ratio between clusters
 * (higher = more disagreement between semantic interpretations)
 */
export function calculateDisagreement(clusters: SemanticCluster[]): number {
  if (!clusters || clusters.length < 2) return 0;
  
  const confidences = clusters.map(c => c.confidence);
  const maxConf = Math.max(...confidences);
  const minConf = Math.min(...confidences);
  
  return maxConf - minConf;
}

/**
 * Round number to specified decimal places
 */
function roundTo(value: number, decimals: number): number {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
}
