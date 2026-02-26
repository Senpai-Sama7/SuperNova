import { clamp, toFiniteNumber } from "../../utils/numberGuards";
import { Theme } from "../../theme";

/**
 * Memory nodes graph visualization
 * @param {Array} nodes - Array of memory node objects
 */
export const MemoryGraph = ({ nodes }) => {
  const mappedNodes = nodes.map((n) => ({
    ...n,
    strength: clamp(toFiniteNumber(n.strength ?? n.v, 0.5), 0, 1),
    vx: clamp(toFiniteNumber(n.x, 50), 0, 100) * 4,
    vy: clamp(toFiniteNumber(n.y, 50), 0, 100) * 1.8,
  }));

  const edges = [];
  for (let i = 0; i < mappedNodes.length; i++) {
    for (let j = i + 1; j < mappedNodes.length; j++) {
      const dx = mappedNodes[i].vx - mappedNodes[j].vx;
      const dy = mappedNodes[i].vy - mappedNodes[j].vy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 100) {
        edges.push({ source: mappedNodes[i], target: mappedNodes[j], dist });
      }
    }
  }

  return (
    <div
      style={{
        width: "100%",
        height: 180,
        position: "relative",
        background: "rgba(0,0,0,0.2)",
        borderRadius: 8,
        border: "1px solid rgba(255,255,255,0.05)",
        overflow: "hidden",
      }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 400 180"
        style={{ position: "absolute", zIndex: 1 }}
      >
        <defs>
          <radialGradient id="node-glow-concept">
            <stop
              offset="0%"
              stopColor={Theme.colors.accent}
              stopOpacity="0.8"
            />
            <stop
              offset="100%"
              stopColor={Theme.colors.accent}
              stopOpacity="0"
            />
          </radialGradient>
          <radialGradient id="node-glow-other">
            <stop
              offset="0%"
              stopColor={Theme.colors.secondary}
              stopOpacity="0.8"
            />
            <stop
              offset="100%"
              stopColor={Theme.colors.secondary}
              stopOpacity="0"
            />
          </radialGradient>
        </defs>

        {edges.map((e, i) => (
          <line
            key={`edge-${i}`}
            x1={e.source.vx}
            y1={e.source.vy}
            x2={e.target.vx}
            y2={e.target.vy}
            stroke="#ffffff22"
            strokeWidth={Math.max(0.5, 2 - e.dist / 50)}
            opacity={Math.max(0.1, 1 - e.dist / 100)}
          />
        ))}

        {mappedNodes.map((n) => {
          const isConcept = n.type === "concept";
          const r = 3 + n.strength * 5;
          return (
            <g key={n.id}>
              {n.strength > 0.5 && (
                <circle
                  cx={n.vx}
                  cy={n.vy}
                  r={r * 3}
                  fill={`url(#node-glow-${isConcept ? "concept" : "other"})`}
                />
              )}
              <circle
                cx={n.vx}
                cy={n.vy}
                r={r}
                fill={isConcept ? Theme.colors.accent : Theme.colors.secondary}
                opacity={0.6 + n.strength * 0.4}
              />

              {n.strength > 0.6 && (
                <text
                  x={n.vx}
                  y={n.vy + r + 6 + 4}
                  fill={Theme.colors.textMuted}
                  fontSize="8"
                  fontFamily="monospace"
                  textAnchor="middle"
                  opacity="0.8"
                >
                  {n.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      {/* Background grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `radial-gradient(${Theme.colors.textMuted}11 1px, transparent 1px)`,
          backgroundSize: "20px 20px",
          opacity: 0.3,
          zIndex: 0,
        }}
      />
    </div>
  );
};
