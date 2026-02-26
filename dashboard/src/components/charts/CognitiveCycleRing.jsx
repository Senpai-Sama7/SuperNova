import { Theme } from "../../theme";

/**
 * Cognitive cycle phase ring visualization
 * @param {string} phase - Current phase name
 * @param {number} step - Current step index
 * @param {number} progress - Phase progress (0-1)
 */
export const CognitiveCycleRing = ({ phase, step, progress }) => {
  const phases = [
    "PERCEIVE",
    "REMEMBER",
    "REASON",
    "ACT",
    "REFLECT",
    "CONSOLIDATE",
  ];
  const colors = [
    Theme.colors.info,
    Theme.colors.secondary,
    Theme.colors.accent,
    Theme.colors.warning,
    Theme.colors.secondary,
    Theme.colors.success,
  ];
  const r = 55,
    cx = 70,
    cy = 70;
  const circumference = 2 * Math.PI * r;
  const segmentLen = circumference / phases.length;

  return (
    <div style={{ position: "relative", width: 140, height: 140 }}>
      <svg
        width={140}
        height={140}
        role="img"
        aria-label={`Cognitive cycle phase: ${phase}`}
      >
        <defs>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        {phases.map((p, i) => {
          const active = i === step;
          const done = i < step;
          const dashLen = segmentLen - 4;

          return (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={
                active
                  ? colors[i]
                  : done
                    ? colors[i] + "44"
                    : Theme.colors.border
              }
              strokeWidth={active ? 4 : 2}
              strokeDasharray={`${dashLen} ${circumference - dashLen}`}
              strokeDashoffset={-i * segmentLen + circumference / 4}
              strokeLinecap="round"
              style={{
                transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
                filter: active ? "url(#glow)" : "none",
                opacity: active ? 1 : done ? 0.6 : 0.3,
              }}
            />
          );
        })}
        {/* Progress arc for current phase */}
        <circle
          cx={cx}
          cy={cy}
          r={r - 10}
          fill="none"
          stroke={colors[step] + "22"}
          strokeWidth={1}
          strokeDasharray={`${(segmentLen - 4) * progress} ${circumference}`}
          strokeDashoffset={-step * segmentLen + circumference / 4}
          strokeLinecap="round"
        />
      </svg>
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%,-50%)",
          textAlign: "center",
          width: "100%",
        }}
      >
        <div
          style={{
            fontSize: 8,
            color: Theme.colors.textMuted,
            fontFamily: Theme.fonts.mono,
            letterSpacing: "0.2em",
            textTransform: "uppercase",
            marginBottom: 2,
          }}
        >
          PHASE
        </div>
        <div
          style={{
            fontSize: 10,
            color: colors[step],
            fontWeight: 800,
            fontFamily: Theme.fonts.mono,
            letterSpacing: "0.05em",
            filter: `drop-shadow(0 0 8px ${colors[step]}44)`,
          }}
        >
          {phase}
        </div>
      </div>
      {/* Phase labels around ring */}
      {phases.map((p, i) => {
        const angle = (i / phases.length) * 2 * Math.PI - Math.PI / 2;
        const lx = cx + (r + 14) * Math.cos(angle);
        const ly = cy + (r + 14) * Math.sin(angle);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: lx,
              top: ly,
              transform: "translate(-50%, -50%)",
              fontSize: 7,
              fontFamily: Theme.fonts.mono,
              color: i === step ? colors[i] : Theme.colors.textMuted,
              fontWeight: i === step ? 900 : 400,
              opacity: i === step ? 1 : 0.4,
              transition: "all 0.4s ease",
              pointerEvents: "none",
            }}
          >
            {p.slice(0, 3)}
          </div>
        );
      })}
    </div>
  );
};
