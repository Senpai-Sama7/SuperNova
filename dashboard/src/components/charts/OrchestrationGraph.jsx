import { Theme } from "../../theme";

/**
 * Agent orchestration topology visualization
 * Shows Nova Prime and worker agents with animated data flows
 */
export const OrchestrationGraph = () => {
  return (
    <div style={{ padding: "16px 0", overflow: "visible" }}>
      <svg
        width="100%"
        height="220"
        viewBox="0 0 500 220"
        style={{ overflow: "visible" }}
      >
        <defs>
          <filter id="glow-prime" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glow-worker" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <style>
            {`
              @keyframes dashFlow {
                to {
                  stroke-dashoffset: -20;
                }
              }
            `}
          </style>
        </defs>

        {/* Minimal connecting edges */}
        <path
          d="M 250 40 L 100 160"
          stroke="#ffffff15"
          strokeWidth="2"
          fill="none"
        />
        <path
          d="M 250 40 L 200 160"
          stroke="#ffffff15"
          strokeWidth="2"
          fill="none"
        />
        <path
          d="M 250 40 L 300 160"
          stroke="#ffffff15"
          strokeWidth="2"
          fill="none"
        />
        <path
          d="M 250 40 L 400 160"
          stroke="#ffffff15"
          strokeWidth="2"
          fill="none"
        />

        {/* Animated data flow along edges */}
        <path
          d="M 250 40 L 100 160"
          stroke={Theme.colors.primary}
          strokeWidth="2"
          fill="none"
          strokeDasharray="4 8"
          style={{ animation: "dashFlow 1s linear infinite" }}
          opacity="0.6"
        />
        <path
          d="M 250 40 L 200 160"
          stroke={Theme.colors.secondary}
          strokeWidth="2"
          fill="none"
          strokeDasharray="4 8"
          style={{ animation: "dashFlow 1.2s linear infinite" }}
          opacity="0.6"
        />
        <path
          d="M 250 40 L 300 160"
          stroke={Theme.colors.accent}
          strokeWidth="2"
          fill="none"
          strokeDasharray="4 8"
          style={{ animation: "dashFlow 0.8s linear infinite" }}
          opacity="0.6"
        />
        <path
          d="M 250 40 L 400 160"
          stroke={Theme.colors.warning}
          strokeWidth="2"
          fill="none"
          strokeDasharray="4 8"
          style={{ animation: "dashFlow 1.5s linear infinite" }}
          opacity="0.6"
        />

        {/* Nova Prime - Central Hub */}
        <circle
          cx="250"
          cy="40"
          r="26"
          fill={Theme.colors.surfaceLow}
          stroke={Theme.colors.primary}
          strokeWidth="2"
          filter="url(#glow-prime)"
        />
        <text
          x="250"
          y="43"
          fill="#fff"
          fontSize="20"
          textAnchor="middle"
          dominantBaseline="middle"
        >
          ◈
        </text>
        <text
          x="250"
          y="85"
          fill="#fff"
          fontSize="12"
          fontFamily="monospace"
          textAnchor="middle"
          fontWeight="bold"
        >
          Nova Prime
        </text>
        <text
          x="250"
          y="100"
          fill="#ffffff55"
          fontSize="10"
          fontFamily="monospace"
          textAnchor="middle"
        >
          Planner
        </text>

        {/* Iris - Researcher */}
        <circle
          cx="100"
          cy="160"
          r="20"
          fill={Theme.colors.surfaceLow}
          stroke={Theme.colors.border}
          strokeWidth="1"
          filter="url(#glow-worker)"
        />
        <text
          x="100"
          y="163"
          fill="#fff"
          fontSize="14"
          textAnchor="middle"
          dominantBaseline="middle"
        >
          ◉
        </text>
        <text
          x="100"
          y="195"
          fill="#fff"
          fontSize="11"
          fontFamily="monospace"
          textAnchor="middle"
        >
          Iris
        </text>
        <text
          x="100"
          y="210"
          fill="#ffffff55"
          fontSize="9"
          fontFamily="monospace"
          textAnchor="middle"
        >
          Researcher
        </text>

        {/* Atlas - Executor */}
        <circle
          cx="200"
          cy="160"
          r="20"
          fill={Theme.colors.surfaceLow}
          stroke={Theme.colors.border}
          strokeWidth="1"
          filter="url(#glow-worker)"
        />
        <text
          x="200"
          y="163"
          fill="#fff"
          fontSize="14"
          textAnchor="middle"
          dominantBaseline="middle"
        >
          ◎
        </text>
        <text
          x="200"
          y="195"
          fill="#fff"
          fontSize="11"
          fontFamily="monospace"
          textAnchor="middle"
        >
          Atlas
        </text>
        <text
          x="200"
          y="210"
          fill="#ffffff55"
          fontSize="9"
          fontFamily="monospace"
          textAnchor="middle"
        >
          Executor
        </text>

        {/* Aegis - Auditor */}
        <circle
          cx="300"
          cy="160"
          r="20"
          fill={Theme.colors.surfaceLow}
          stroke={Theme.colors.border}
          strokeWidth="1"
          filter="url(#glow-worker)"
        />
        <text
          x="300"
          y="163"
          fill="#fff"
          fontSize="14"
          textAnchor="middle"
          dominantBaseline="middle"
        >
          ⬡
        </text>
        <text
          x="300"
          y="195"
          fill="#fff"
          fontSize="11"
          fontFamily="monospace"
          textAnchor="middle"
        >
          Aegis
        </text>
        <text
          x="300"
          y="210"
          fill="#ffffff55"
          fontSize="9"
          fontFamily="monospace"
          textAnchor="middle"
        >
          Auditor
        </text>

        {/* Muse - Creative */}
        <circle
          cx="400"
          cy="160"
          r="20"
          fill={Theme.colors.surfaceLow}
          stroke={Theme.colors.border}
          strokeWidth="1"
          filter="url(#glow-worker)"
        />
        <text
          x="400"
          y="163"
          fill="#fff"
          fontSize="14"
          textAnchor="middle"
          dominantBaseline="middle"
        >
          ✦
        </text>
        <text
          x="400"
          y="195"
          fill="#fff"
          fontSize="11"
          fontFamily="monospace"
          textAnchor="middle"
        >
          Muse
        </text>
        <text
          x="400"
          y="210"
          fill="#ffffff55"
          fontSize="9"
          fontFamily="monospace"
          textAnchor="middle"
        >
          Creative
        </text>
      </svg>
    </div>
  );
};
