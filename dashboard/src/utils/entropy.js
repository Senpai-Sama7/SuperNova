import { clamp, toFiniteNumber } from "./numberGuards";

/**
 * Compute semantic entropy from hypotheses
 * @param {Array} hypotheses - Array of hypothesis objects
 * @returns {Object} { entropy, confidence, clusters }
 */
export function computeSemanticEntropy(hypotheses) {
  if (!hypotheses.length) return { entropy: 0, confidence: 1, clusters: [] };
  let probs = [];
  let clusterRows = [];

  if (
    hypotheses.every(
      (h) =>
        h &&
        typeof h === "object" &&
        (Object.prototype.hasOwnProperty.call(h, "probability") ||
          Object.prototype.hasOwnProperty.call(h, "prob")),
    )
  ) {
    const normalized = hypotheses
      .map((h) => ({
        name: h.name || h.cluster || "default",
        prob: clamp(toFiniteNumber(h.probability ?? h.prob, 0), 0, 1),
      }))
      .filter((h) => h.prob > 0);

    const total = normalized.reduce((sum, row) => sum + row.prob, 0);
    if (total <= 0) return { entropy: 0, confidence: 1, clusters: [] };

    clusterRows = normalized.map((row) => ({
      name: row.name,
      count: row.prob,
      prob: row.prob / total,
    }));
    probs = clusterRows.map((row) => row.prob);
  } else {
    const clusters = hypotheses.reduce((acc, h) => {
      const key = h.cluster || "default";
      (acc[key] = acc[key] || []).push(h);
      return acc;
    }, {});
    probs = Object.values(clusters).map((c) => c.length / hypotheses.length);
    clusterRows = Object.entries(clusters).map(([k, v]) => ({
      name: k,
      count: v.length,
      prob: v.length / hypotheses.length,
    }));
  }

  const entropy = -probs.reduce(
    (s, p) => s + (p > 0 ? p * Math.log2(p) : 0),
    0,
  );
  const maxEntropy = Math.log2(clusterRows.length || 1);
  const normalized = maxEntropy > 0 ? entropy / maxEntropy : 0;
  const confidence = Math.max(0.05, 1 - normalized);
  return {
    entropy: normalized,
    confidence,
    clusters: clusterRows,
  };
}
