import { toFiniteNumber } from "../../utils/numberGuards";
import { Theme } from "../../theme";

/**
 * SVG Sparkline chart component
 * @param {number[]} data - Array of data points
 * @param {string} color - Line color
 * @param {number} height - Chart height
 */
export const Sparkline = ({ data, color = Theme.colors.accent, height = 30 }) => {
  const safeData = (Array.isArray(data) ? data : []).map((value) =>
    toFiniteNumber(value, 0),
  );
  if (!safeData.length) return null;
  if (safeData.length === 1) safeData.push(safeData[0]);
  const denominator = Math.max(1, safeData.length - 1);
  const max = Math.max(...safeData, 0.01);
  const min = Math.min(...safeData);
  const range = max - min || 1;
  const points = safeData
    .map(
      (value, index) =>
        `${(index / denominator) * 100},${100 - ((value - min) / range) * 100}`,
    )
    .join(" ");

  return (
    <svg
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      style={{ width: "100%", height, overflow: "visible" }}
    >
      <defs>
        <linearGradient id={`grad-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d={`M ${safeData.map((value, index) => `${(index / denominator) * 100} ${100 - ((value - min) / range) * 100}`).join(" L ")} L 100 100 L 0 100 Z`}
        fill={`url(#grad-${color})`}
      />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{
          filter: `drop-shadow(0 0 4px ${color}66)`,
        }}
      />
    </svg>
  );
};
