import { clamp, toFiniteNumber } from "../../utils/numberGuards";

/**
 * Confidence gauge meter with threshold indicators
 * @param {number} confidence - Confidence value (0-1)
 * @param {number} entropy - Entropy value (0-1)
 * @param {number} proceedThreshold - Threshold for PROCEED state
 * @param {number} monitorThreshold - Threshold for MONITOR state
 */
export const ConfidenceMeter = ({
  confidence,
  entropy,
  proceedThreshold = 0.8,
  monitorThreshold = 0.55,
}) => {
  const safeConfidence = clamp(toFiniteNumber(confidence, 0), 0, 1);
  const safeEntropy = clamp(toFiniteNumber(entropy, 0), 0, 1);
  const decision =
    safeConfidence > proceedThreshold
      ? { label: "PROCEED", color: "#34d399", icon: "◈" }
      : safeConfidence > monitorThreshold
        ? { label: "MONITOR", color: "#fbbf24", icon: "◉" }
        : { label: "DEFER", color: "#f87171", icon: "◎" };

  const r = 45,
    cx = 70,
    cy = 65;

  return (
    <div style={{ textAlign: "center" }}>
      <svg width={140} height={85} style={{ overflow: "visible" }}>
        {/* Track */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="#ffffff10"
          strokeWidth={8}
          strokeLinecap="round"
        />
        {/* Fill */}
        {safeConfidence > 0 && (
          <path
            d={`M ${cx - r} ${cy} A ${r} ${r} 0 ${safeConfidence > 0.5 ? 1 : 0} 1 ${cx + r * Math.cos(Math.PI - safeConfidence * Math.PI)} ${cy - r * Math.sin(safeConfidence * Math.PI)}`}
            fill="none"
            stroke={decision.color}
            strokeWidth={8}
            strokeLinecap="round"
            style={{
              filter: `drop-shadow(0 0 4px ${decision.color})`,
              transition: "all 0.8s ease",
            }}
          />
        )}
        {/* Needle */}
        <line
          x1={cx}
          y1={cy}
          x2={cx + (r - 8) * Math.cos(Math.PI - safeConfidence * Math.PI)}
          y2={cy - (r - 8) * Math.sin(safeConfidence * Math.PI)}
          stroke="#ffffff"
          strokeWidth={2}
          strokeLinecap="round"
          style={{ transition: "all 0.8s ease" }}
        />
        <circle cx={cx} cy={cy} r={4} fill="#ffffff" />
        <text
          x={cx}
          y={cy + 20}
          textAnchor="middle"
          fill={decision.color}
          fontSize={20}
          fontFamily="monospace"
          fontWeight={700}
        >
          {decision.icon}
        </text>
        <text
          x={cx}
          y={cy + 35}
          textAnchor="middle"
          fill={decision.color}
          fontSize={10}
          fontFamily="monospace"
          fontWeight={700}
          letterSpacing="0.1em"
        >
          {decision.label}
        </text>
        <text
          x={cx - r + 5}
          y={cy + 15}
          fill="#ffffff44"
          fontSize={8}
          fontFamily="monospace"
        >
          0%
        </text>
        <text
          x={cx + r - 12}
          y={cy + 15}
          fill="#ffffff44"
          fontSize={8}
          fontFamily="monospace"
        >
          100%
        </text>
      </svg>
      <div
        style={{ fontSize: 11, color: "#ffffff66", fontFamily: "monospace" }}
      >
        conf:{" "}
        <span style={{ color: decision.color }}>
          {(safeConfidence * 100).toFixed(1)}%
        </span>{" "}
        · entropy:{" "}
        <span style={{ color: "#a78bfa" }}>{(safeEntropy * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
};
