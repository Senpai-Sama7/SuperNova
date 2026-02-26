import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { clamp, toFiniteNumber } from "./utils/numberGuards";

// ─── Design System (Premium Aesthetic) ───────────────────────────────────────

const Theme = {
  colors: {
    bg: "#050608",
    cardBg: "rgba(15, 18, 25, 0.7)",
    accent: "#00ffd5", // SuperNova Cyan
    secondary: "#a78bfa", // Mystic Purple
    warning: "#fbbf24", // Amber
    error: "#f87171", // Rose
    text: "#f8fafc",
    textMuted: "#94a3b8",
    glassBorder: "rgba(255, 255, 255, 0.08)",
    neonGlow: "0 0 15px rgba(0, 255, 213, 0.3)",
  },
  fonts: {
    display: "'Space Grotesk', sans-serif",
    mono: "'JetBrains Mono', monospace",
  },
  glass: {
    backdropFilter: "blur(12px) saturate(180%)",
    backgroundColor: "rgba(15, 18, 25, 0.7)",
    border: "1px solid rgba(255, 255, 255, 0.08)",
    boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
  },
};

// Injecting Google Fonts dynamically
if (typeof document !== "undefined") {
  const link = document.createElement("link");
  link.href =
    "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap";
  link.rel = "stylesheet";
  document.head.appendChild(link);
}

// ─── Engines (from UPS decision-intelligence-ui skill) ───────────────────────

class BayesianEngine {
  constructor() {
    this.alpha = 1;
    this.beta = 1;
  }
  update(success) {
    if (success) this.alpha++;
    else this.beta++;
  }
  get mean() {
    return this.alpha / (this.alpha + this.beta);
  }
  get variance() {
    const n = this.alpha + this.beta;
    return (this.alpha * this.beta) / (n * n * (n + 1));
  }
  get credibleInterval() {
    const m = this.mean,
      v = this.variance;
    const w = 1.96 * Math.sqrt(v);
    return [Math.max(0, m - w), Math.min(1, m + w)];
  }
}

class ConformalEngine {
  constructor() {
    this.residuals = [];
    this.windowSize = 30;
  }
  update(actual, predicted) {
    this.residuals.push(Math.abs(actual - predicted));
    if (this.residuals.length > this.windowSize) this.residuals.shift();
  }
  getInterval(prediction, alpha = 0.1) {
    if (this.residuals.length < 3) return [prediction - 0.2, prediction + 0.2];
    const sorted = [...this.residuals].sort((a, b) => a - b);
    const q = sorted[Math.floor((1 - alpha) * sorted.length)] || 0.15;
    return [prediction - q, prediction + q];
  }
  get coverage() {
    if (this.residuals.length < 3) return 0.9;
    return Math.min(0.99, 0.7 + this.residuals.length / 300);
  }
}

function computeSemanticEntropy(hypotheses) {
  if (!hypotheses.length) return { entropy: 0, confidence: 1, clusters: [] };
  const clusters = hypotheses.reduce((acc, h) => {
    const key = h.cluster || "default";
    (acc[key] = acc[key] || []).push(h);
    return acc;
  }, {});
  const probs = Object.values(clusters).map(
    (c) => c.length / hypotheses.length,
  );
  const entropy = -probs.reduce(
    (s, p) => s + (p > 0 ? p * Math.log2(p) : 0),
    0,
  );
  const maxEntropy = Math.log2(Object.keys(clusters).length || 1);
  const normalized = maxEntropy > 0 ? entropy / maxEntropy : 0;
  const confidence = Math.max(0.05, 1 - normalized);
  return {
    entropy: normalized,
    confidence,
    clusters: Object.entries(clusters).map(([k, v]) => ({
      name: k,
      count: v.length,
      prob: v.length / hypotheses.length,
    })),
  };
}

// ─── Simulation layer ─────────────────────────────────────────────────────────

function useNovaSimulation(isHalted = false) {
  const bayesian = useRef(new BayesianEngine());
  const conformal = useRef(new ConformalEngine());
  const [tick, setTick] = useState(0);
  const [stream, setStream] = useState([]);
  const [agents, setAgents] = useState([
    {
      id: "planner",
      name: "Nova Prime",
      role: "Planner",
      status: "reasoning",
      task: "Strategic goal decomposition",
      load: 3,
      max: 5,
      success: 0.96,
      latency: 1.2,
      model: "claude-sonnet-4-5",
      memory_hits: 14,
      tools_called: 0,
    },
    {
      id: "researcher",
      name: "Iris",
      role: "Researcher",
      status: "active",
      task: "Temporal KG enrichment",
      load: 2,
      max: 5,
      success: 0.94,
      latency: 0.8,
      model: "gemini-2-flash",
      memory_hits: 31,
      tools_called: 3,
    },
    {
      id: "executor",
      name: "Atlas",
      role: "Executor",
      status: "waiting",
      task: "Awaiting plan delta",
      load: 0,
      max: 5,
      success: 0.91,
      latency: 1.9,
      model: "groq-llama-3-70b",
      memory_hits: 7,
      tools_called: 0,
    },
    {
      id: "auditor",
      name: "Aegis",
      role: "Auditor",
      status: "active",
      task: "Security threat scan",
      load: 1,
      max: 3,
      success: 0.99,
      latency: 0.3,
      model: "qwen2.5-32b-local",
      memory_hits: 2,
      tools_called: 1,
    },
    {
      id: "creative",
      name: "Muse",
      role: "Creative",
      status: "idle",
      task: "Dream-phase consolidation",
      load: 0,
      max: 4,
      success: 0.88,
      latency: 2.1,
      model: "claude-sonnet-4-5",
      memory_hits: 22,
      tools_called: 0,
    },
  ]);
  const [memoryNodes, setMemoryNodes] = useState([
    {
      id: "m1",
      label: "Project Helios",
      type: "episodic",
      connections: 5,
      strength: 0.92,
      age: "2h",
      x: 30,
      y: 25,
    },
    {
      id: "m2",
      label: "Weekly fitness",
      type: "procedural",
      connections: 3,
      strength: 0.78,
      age: "1d",
      x: 65,
      y: 20,
    },
    {
      id: "m3",
      label: "Client: Zara",
      type: "semantic",
      connections: 8,
      strength: 0.95,
      age: "5m",
      x: 50,
      y: 50,
    },
    {
      id: "m4",
      label: "API key mgmt",
      type: "procedural",
      connections: 2,
      strength: 0.65,
      age: "3d",
      x: 20,
      y: 65,
    },
    {
      id: "m5",
      label: "Q3 Strategy",
      type: "semantic",
      connections: 6,
      strength: 0.88,
      age: "30m",
      x: 75,
      y: 60,
    },
    {
      id: "m6",
      label: "Creative block fix",
      type: "procedural",
      connections: 4,
      strength: 0.71,
      age: "2d",
      x: 45,
      y: 80,
    },
    {
      id: "m7",
      label: "Morning routine",
      type: "episodic",
      connections: 7,
      strength: 0.83,
      age: "8h",
      x: 85,
      y: 35,
    },
  ]);
  const [pendingApprovals, setPendingApprovals] = useState([
    {
      id: "a1",
      tool: "send_email",
      risk: "high",
      agent: "Nova Prime",
      args: { to: "team@company.com", subject: "Sprint review" },
      expires: 285,
      auto_resolve: false,
    },
    {
      id: "a2",
      tool: "file_write",
      risk: "medium",
      agent: "Atlas",
      args: { path: "workspace/report.md" },
      expires: 102,
      auto_resolve: false,
    },
  ]);
  const [cognitiveLoop, setCognitiveLoop] = useState({
    phase: "REASON",
    step: 2,
    phaseProgress: 0.6,
  });
  const [metrics, setMetrics] = useState({
    totalCalls: 847,
    successRate: 0.94,
    avgLatency: 1.3,
    cost: 2.47,
    skillsCompiled: 12,
    memoriesConsolidated: 341,
  });
  const [decisionData, setDecisionData] = useState({
    actual: 0.72,
    predicted: 0.75,
    regime: "stable",
    success: 1,
  });

  useEffect(() => {
    const interval = setInterval(() => {
      if (isHalted) return;
      const t = Date.now();
      const predicted =
        0.7 + 0.15 * Math.sin(t / 8000) + (Math.random() - 0.5) * 0.04;
      const actual = predicted + (Math.random() - 0.5) * 0.08;
      const success = actual > 0.6 ? 1 : 0;

      bayesian.current.update(success);
      conformal.current.update(actual, predicted);

      const newPoint = {
        t: tick,
        actual,
        predicted,
        regime: Math.abs(actual - predicted) > 0.1 ? "volatile" : "stable",
        success,
        timestamp: t,
      };
      setStream((prev) => [...prev.slice(-40), newPoint]);

      setDecisionData({ actual, predicted, regime: newPoint.regime, success });

      // Rotate cognitive loop phases
      const phases = [
        "PERCEIVE",
        "REMEMBER",
        "REASON",
        "ACT",
        "REFLECT",
        "CONSOLIDATE",
      ];
      setCognitiveLoop((prev) => {
        const prog = prev.phaseProgress + 0.08;
        if (prog >= 1) {
          const nextIdx = (phases.indexOf(prev.phase) + 1) % phases.length;
          return { phase: phases[nextIdx], step: nextIdx, phaseProgress: 0 };
        }
        return { ...prev, phaseProgress: prog };
      });

      // Drift agent states
      setAgents((prev) =>
        prev.map((a) => ({
          ...a,
          load: Math.min(
            a.max,
            Math.max(
              0,
              a.load +
                (Math.random() > 0.85 ? (Math.random() > 0.5 ? 1 : -1) : 0),
            ),
          ),
          latency: Math.max(0.1, a.latency + (Math.random() - 0.5) * 0.1),
          tools_called: a.tools_called + (Math.random() > 0.95 ? 1 : 0),
          status:
            Math.random() > 0.97
              ? ["active", "reasoning", "waiting", "idle"][
                  Math.floor(Math.random() * 4)
                ]
              : a.status,
        })),
      );

      // Drift memory strengths
      setMemoryNodes((prev) =>
        prev.map((m) => ({
          ...m,
          strength: Math.min(
            1,
            Math.max(0.3, m.strength + (Math.random() - 0.5) * 0.01),
          ),
        })),
      );

      // Tick approvals down
      setPendingApprovals((prev) =>
        prev
          .map((a) => ({ ...a, expires: a.expires - 1 }))
          .filter((a) => a.expires > 0),
      );

      setMetrics((prev) => ({
        ...prev,
        totalCalls: prev.totalCalls + (Math.random() > 0.7 ? 1 : 0),
        cost: prev.cost + Math.random() * 0.002,
        avgLatency: Math.max(
          0.5,
          prev.avgLatency + (Math.random() - 0.5) * 0.05,
        ),
      }));

      setTick((t) => t + 1);
    }, 800);
    return () => clearInterval(interval);
  }, [tick, isHalted]);

  return {
    stream,
    agents,
    memoryNodes,
    pendingApprovals,
    cognitiveLoop,
    metrics,
    decisionData,
    bayesian: bayesian.current,
    conformal: conformal.current,
    setPendingApprovals,
  };
}

// ─── Micro-components ─────────────────────────────────────────────────────────

const Glow = ({ color = Theme.colors.accent, size = 60 }) => (
  <div
    style={{
      position: "absolute",
      width: size,
      height: size,
      borderRadius: "50%",
      background: color,
      filter: "blur(40px)",
      opacity: 0.12,
      pointerEvents: "none",
      zIndex: 0,
    }}
  />
);

const Badge = ({ label, color = Theme.colors.accent }) => (
  <span
    style={{
      padding: "3px 10px",
      borderRadius: "4px",
      fontSize: "9px",
      fontWeight: 700,
      background: `${color}15`,
      color,
      border: `1px solid ${color}30`,
      letterSpacing: "0.12em",
      textTransform: "uppercase",
      fontFamily: Theme.fonts.mono,
      display: "inline-flex",
      alignItems: "center",
      backdropFilter: "blur(4px)",
    }}
  >
    {label}
  </span>
);

const StatusDot = ({ status }) => {
  const colors = {
    active: Theme.colors.accent,
    reasoning: Theme.colors.secondary,
    waiting: Theme.colors.warning,
    idle: Theme.colors.textMuted,
    error: Theme.colors.error,
  };
  const sc = colors[status] || Theme.colors.textMuted;
  return (
    <span
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: sc,
        boxShadow: `0 0 10px ${sc}`,
        marginRight: 8,
        flexShrink: 0,
      }}
    />
  );
};

const MiniBar = ({ value, max, color = Theme.colors.accent, width = 80 }) => (
  <div
    style={{
      width,
      height: 4,
      background: "rgba(255, 255, 255, 0.05)",
      borderRadius: 10,
      overflow: "hidden",
    }}
  >
    <div
      style={{
        width: `${Math.min(100, (value / max) * 100)}%`,
        height: "100%",
        background: color,
        boxShadow: `0 0 8px ${color}66`,
        transition: "width 1s cubic-bezier(0.4, 0, 0.2, 1)",
      }}
    />
  </div>
);

const RiskPill = ({ risk }) => {
  const map = {
    low: [Theme.colors.accent, "LOW"],
    medium: [Theme.colors.warning, "MED"],
    high: [Theme.colors.error, "HIGH"],
    critical: [Theme.colors.secondary, "CRIT"],
  };
  const [color, label] = map[risk] || [Theme.colors.textMuted, "?"];
  return <Badge label={label} color={color} />;
};

// ─── Visualizations ───────────────────────────────────────────────────────── (Moved to end of file)

// ─── Cognitive Loop Ring ──────────────────────────────────────────────────────
const CognitiveCycleRing = ({ phase, step, progress }) => {
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

// ─── Confidence Meter ──────────────────────────────────────────────────────────
const ConfidenceMeter = ({ confidence, entropy }) => {
  const safeConfidence = clamp(toFiniteNumber(confidence, 0), 0, 1);
  const safeEntropy = clamp(toFiniteNumber(entropy, 0), 0, 1);
  const decision =
    safeConfidence > 0.8
      ? { label: "PROCEED", color: "#34d399", icon: "◈" }
      : safeConfidence > 0.55
        ? { label: "MONITOR", color: "#fbbf24", icon: "◉" }
        : { label: "DEFER", color: "#f87171", icon: "◎" };

  const angle = safeConfidence * 180 - 90;
  const r = 45,
    cx = 70,
    cy = 65;
  const startAngle = -Math.PI;
  const endAngle = (endAngle) => endAngle;

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

// ─── Agent Card ───────────────────────────────────────────────────────────────
const AgentCard = ({ agent }) => {
  const statusColor = {
    active: Theme.colors.accent,
    reasoning: Theme.colors.secondary,
    waiting: Theme.colors.warning,
    idle: Theme.colors.textMuted,
  };
  const roleIcons = {
    Planner: "◈",
    Researcher: "◉",
    Executor: "◎",
    Auditor: "⬡",
    Creative: "✦",
  };
  const sc = statusColor[agent.status] || Theme.colors.textMuted;

  return (
    <div
      style={{
        ...Theme.glass,
        padding: "16px",
        position: "relative",
        overflow: "hidden",
        transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 2,
          background: `linear-gradient(90deg, transparent, ${sc}, transparent)`,
          opacity: 0.8,
        }}
      />
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 12,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                fontSize: 16,
                color: sc,
                textShadow: `0 0 10px ${sc}44`,
              }}
            >
              {roleIcons[agent.role]}
            </span>
            <span
              style={{
                fontSize: 14,
                fontWeight: 600,
                color: Theme.colors.text,
                fontFamily: Theme.fonts.display,
                letterSpacing: "-0.01em",
              }}
            >
              {agent.name}
            </span>
            <StatusDot status={agent.status} />
          </div>
          <div
            style={{
              fontSize: 10,
              color: Theme.colors.textMuted,
              fontFamily: Theme.fonts.mono,
              marginTop: 2,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            {agent.role} · {agent.model}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              fontSize: 9,
              color: Theme.colors.textMuted,
              fontFamily: Theme.fonts.mono,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
            }}
          >
            SUCCESS
          </div>
          <div
            style={{
              fontSize: 14,
              color:
                agent.success > 0.95
                  ? Theme.colors.accent
                  : agent.success > 0.9
                    ? Theme.colors.warning
                    : Theme.colors.error,
              fontWeight: 700,
              fontFamily: Theme.fonts.mono,
            }}
          >
            {(agent.success * 100).toFixed(0)}%
          </div>
        </div>
      </div>
      <div
        style={{
          fontSize: 11,
          color: "rgba(255, 255, 255, 0.7)",
          fontFamily: Theme.fonts.display,
          marginBottom: 12,
          fontStyle: "italic",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          borderLeft: `2px solid ${sc}44`,
          paddingLeft: 8,
        }}
      >
        {agent.task}
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: 10,
          fontFamily: Theme.fonts.mono,
          color: Theme.colors.textMuted,
          marginTop: 12,
        }}
      >
        <div style={{ display: "flex", gap: 10 }}>
          <span>
            <span style={{ color: "rgba(255, 255, 255, 0.2)" }}>LOAD:</span>{" "}
            {agent.load}/{agent.max}
          </span>
          <span>
            <span style={{ color: "rgba(255, 255, 255, 0.2)" }}>TOOLS:</span>{" "}
            {agent.tools_called}
          </span>
          <span>
            <span style={{ color: "rgba(255, 255, 255, 0.2)" }}>MEM:</span>{" "}
            {agent.memory_hits}
          </span>
        </div>
        <MiniBar value={agent.load} max={agent.max} color={sc} width={50} />
      </div>
    </div>
  );
};

// ─── Approval Card ────────────────────────────────────────────────────────────
const ApprovalCard = ({ approval, onDecide }) => {
  const riskColors = {
    low: Theme.colors.accent,
    medium: Theme.colors.warning,
    high: Theme.colors.error,
    critical: Theme.colors.secondary,
  };
  const rc = riskColors[approval.risk] || Theme.colors.accent;
  const progress = (approval.expires / 300) * 100;

  return (
    <div
      style={{
        ...Theme.glass,
        padding: "16px",
        position: "relative",
        overflow: "hidden",
        border: `1px solid ${rc}33`,
      }}
    >
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: `${progress}%`,
          height: 2,
          background: rc,
          transition: "width 0.8s linear",
          boxShadow: `0 0 10px ${rc}`,
          opacity: 0.8,
        }}
      />
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 12,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                fontSize: 14,
                fontWeight: 600,
                color: Theme.colors.text,
                fontFamily: Theme.fonts.display,
              }}
            >
              {approval.type || approval.tool}
            </span>
            <RiskPill risk={approval.risk} />
          </div>
          <div
            style={{
              fontSize: 10,
              color: Theme.colors.textMuted,
              fontFamily: Theme.fonts.mono,
              marginTop: 2,
              textTransform: "uppercase",
            }}
          >
            {approval.agent} · ID: {approval.id.split("-")[0]}
          </div>
        </div>
        <div
          style={{
            fontSize: 12,
            color: rc,
            fontWeight: 700,
            fontFamily: Theme.fonts.mono,
          }}
        >
          {approval.expires}s
        </div>
      </div>

      <div
        style={{
          fontSize: 12,
          color: "rgba(255, 255, 255, 0.8)",
          fontFamily: Theme.fonts.display,
          marginBottom: 16,
          lineHeight: "1.5",
          padding: "8px",
          background: "rgba(255, 255, 255, 0.03)",
          borderRadius: 4,
          borderLeft: `2px solid ${rc}`,
        }}
      >
        {approval.description ||
          Object.entries(approval.args || {})
            .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
            .join(", ")}
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={() => onDecide(approval.id, true)}
          style={{
            flex: 1,
            padding: "8px",
            borderRadius: 4,
            border: "none",
            background: Theme.colors.accent,
            color: "#000000",
            fontSize: 11,
            fontWeight: 700,
            fontFamily: Theme.fonts.mono,
            cursor: "pointer",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            transition: "all 0.2s",
          }}
        >
          Approve
        </button>
        <button
          onClick={() => onDecide(approval.id, false)}
          style={{
            flex: 1,
            padding: "8px",
            borderRadius: 4,
            border: `1px solid ${Theme.colors.error}44`,
            background: "transparent",
            color: Theme.colors.error,
            fontSize: 11,
            fontWeight: 700,
            fontFamily: Theme.fonts.mono,
            cursor: "pointer",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            transition: "all 0.2s",
          }}
        >
          Deny
        </button>
      </div>
    </div>
  );
};

const Sparkline = ({ data, color = Theme.colors.accent, height = 30 }) => {
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

const MemoryGraph = ({ nodes }) => {
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

const OrchestrationGraph = () => {
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

const ConformalBandChart = ({ stream, ci, width = 450, height = 100 }) => {
  if (!stream || stream.length < 3) return null;
  const data = stream.slice(-40);
  const allVals = data.flatMap((d) => [d.actual, d.predicted]);
  const min = Math.min(...allVals, ci[0]) * 0.95;
  const max = Math.max(...allVals, ci[1]) * 1.05;
  const range = max - min || 1;
  const xScale = (i) => (i / (data.length - 1)) * 100;
  const yScale = (v) => 100 - ((v - min) / range) * 100;

  const upperY = yScale(ci[1]);
  const lowerY = yScale(ci[0]);

  const actualPoints = data
    .map((d, i) => `${xScale(i)},${yScale(d.actual)}`)
    .join(" ");
  const predictedPoints = data
    .map((d, i) => `${xScale(i)},${yScale(d.predicted)}`)
    .join(" ");

  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      style={{ borderRadius: 6, overflow: "visible" }}
    >
      <defs>
        <linearGradient id="ci-band" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#00ffd5" stopOpacity="0.15" />
          <stop offset="50%" stopColor="#00ffd5" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#00ffd5" stopOpacity="0.15" />
        </linearGradient>
      </defs>
      {/* CI band */}
      <rect
        x="0"
        y={upperY}
        width="100"
        height={lowerY - upperY}
        fill="url(#ci-band)"
      />
      <line
        x1="0"
        y1={upperY}
        x2="100"
        y2={upperY}
        stroke="#34d39944"
        strokeWidth="0.5"
        strokeDasharray="2 2"
      />
      <line
        x1="0"
        y1={lowerY}
        x2="100"
        y2={lowerY}
        stroke="#f8717144"
        strokeWidth="0.5"
        strokeDasharray="2 2"
      />
      {/* Predicted line */}
      <polyline
        points={predictedPoints}
        fill="none"
        stroke="#a78bfa"
        strokeWidth="1.5"
        opacity="0.6"
      />
      {/* Actual line */}
      <polyline
        points={actualPoints}
        fill="none"
        stroke="#00ffd5"
        strokeWidth="2"
        style={{ filter: "drop-shadow(0 0 3px #00ffd566)" }}
      />
    </svg>
  );
};

export default function NovaDashboard() {
  const [isHalted, setIsHalted] = useState(false);
  const {
    stream,
    agents,
    memoryNodes,
    pendingApprovals,
    cognitiveLoop,
    metrics,
    decisionData,
    bayesian,
    conformal,
    setPendingApprovals,
  } = useNovaSimulation(isHalted);
  const [activeTab, setActiveTab] = useState("overview");
  const [isNovaTyping, setIsNovaTyping] = useState(false);
  const [decisionLog, setDecisionLog] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([
    {
      role: "nova",
      content:
        "Good morning. I've completed your 06:00 review. 3 tasks crystallized into skills overnight. Zara's proposal is ready for your review. Your 10am is confirmed. What shall we focus on?",
    },
  ]);

  const hypotheses = [
    { cluster: "proceed" },
    { cluster: "proceed" },
    { cluster: "proceed" },
    { cluster: "monitor" },
    { cluster: "monitor" },
    { cluster: "defer" },
  ];
  const { entropy, confidence, clusters } = computeSemanticEntropy(hypotheses);
  const bayesianConf = bayesian.mean;
  const ci = conformal.getInterval(decisionData.predicted);
  const blended = bayesianConf * 0.6 + confidence * 0.4;

  const handleDecide = (id, approved) => {
    const approval = pendingApprovals.find((a) => a.id === id);
    setPendingApprovals((prev) => prev.filter((a) => a.id !== id));
    setDecisionLog((prev) =>
      [
        {
          id,
          tool: approval?.tool || "unknown",
          agent: approval?.agent || "unknown",
          approved,
          timestamp: new Date().toLocaleTimeString([], { hour12: false }),
          confidence: (blended * 100).toFixed(1) + "%",
        },
        ...prev,
      ].slice(0, 10),
    );
    setChatHistory((prev) => [
      ...prev,
      {
        role: "nova",
        content: `Tool ${approved ? "approved ✓" : "denied ✕"}. ${approved ? "Proceeding with execution." : "Action cancelled. I'll find an alternative approach."}`,
      },
    ]);
  };

  const sendMessage = () => {
    if (!chatInput.trim()) return;
    const msg = chatInput.trim();
    setChatInput("");
    setChatHistory((prev) => [...prev, { role: "user", content: msg }]);
    setIsNovaTyping(true);
    setTimeout(() => {
      const responses = [
        "On it. Routing to the appropriate specialist and assembling context from temporal memory.",
        "I've added that to your active goals. Atlas will begin execution in the next cycle.",
        "Interesting. Cross-referencing with your recent episodic context... I see a pattern worth discussing.",
        "Noted. I'll crystallize a skill from this once we have 3 successful completions.",
        "Already thinking about this. The Bayesian confidence for that path is currently 84%. Shall I proceed?",
      ];
      setIsNovaTyping(false);
      setChatHistory((prev) => [
        ...prev,
        {
          role: "nova",
          content: responses[Math.floor(Math.random() * responses.length)],
        },
      ]);
    }, 900);
  };

  const tabs = [
    { id: "overview", label: "OVERVIEW" },
    { id: "agents", label: "AGENTS" },
    { id: "memory", label: "MEMORY" },
    { id: "decisions", label: "DECISIONS" },
  ];

  const modelDist = agents.reduce((acc, a) => {
    const m = a.model.split("-")[0];
    acc[m] = (acc[m] || 0) + 1;
    return acc;
  }, {});

  return (
    <div
      style={{
        minHeight: "100vh",
        background: Theme.colors.background,
        color: Theme.colors.text,
        fontFamily: Theme.fonts.main,
        position: "relative",
        overflow: "hidden",
        selection: { background: Theme.colors.accent + "44" },
      }}
    >
      {/* Ambient background */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: "none",
          zIndex: 0,
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "-10%",
            left: "-10%",
            width: "60%",
            height: "60%",
            borderRadius: "50%",
            background: `radial-gradient(circle, ${Theme.colors.accent}15 0%, transparent 70%)`,
            filter: "blur(120px)",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "-10%",
            right: "-10%",
            width: "50%",
            height: "50%",
            borderRadius: "50%",
            background: `radial-gradient(circle, ${Theme.colors.secondary}10 0%, transparent 70%)`,
            filter: "blur(100px)",
          }}
        />
      </div>

      {/* Scanline overlay */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: "none",
          zIndex: 1,
          background:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
        }}
      />

      <div
        style={{
          position: "relative",
          zIndex: 2,
          maxWidth: 1200,
          margin: "0 auto",
          padding: "0 16px 24px",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "24px 0 20px",
            borderBottom: `1px solid ${Theme.colors.border}`,
            marginBottom: 20,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ position: "relative" }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: "12px",
                  background: `linear-gradient(135deg, ${Theme.colors.accent}, ${Theme.colors.secondary})`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 22,
                  fontWeight: 900,
                  color: Theme.colors.background,
                  boxShadow: `0 8px 16px ${Theme.colors.accent}44`,
                  transform: "rotate(-5deg)",
                }}
              >
                Σ
              </div>
              <div
                style={{
                  position: "absolute",
                  bottom: -2,
                  right: -2,
                  width: 14,
                  height: 14,
                  borderRadius: "50%",
                  background: Theme.colors.success,
                  border: `3px solid ${Theme.colors.background}`,
                  boxShadow: `0 0 10px ${Theme.colors.success}aa`,
                }}
              />
            </div>
            <div>
              <div
                style={{
                  fontSize: 20,
                  fontWeight: 900,
                  letterSpacing: "-0.02em",
                  color: Theme.colors.text,
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                }}
              >
                SUPERNOVA
                <span
                  style={{
                    color: Theme.colors.accent,
                    animation: "pulse 2s infinite",
                  }}
                >
                  •
                </span>
                OS
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: Theme.colors.textMuted,
                  letterSpacing: "0.2em",
                  fontWeight: 600,
                  textTransform: "uppercase",
                }}
              >
                Decision Intelligence Platform
              </div>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              gap: 32,
              fontSize: 11,
              color: Theme.colors.textMuted,
            }}
          >
            {[
              {
                label: "CALLS",
                value: metrics.totalCalls.toLocaleString(),
                color: Theme.colors.accent,
              },
              {
                label: "SUCCESS",
                value: `${(metrics.successRate * 100).toFixed(1)}%`,
                color: Theme.colors.success,
              },
              {
                label: "LATENCY",
                value: `${metrics.avgLatency.toFixed(2)}s`,
                color: Theme.colors.warning,
              },
              {
                label: "COST",
                value: `$${metrics.cost.toFixed(2)}`,
                color: Theme.colors.error,
              },
              {
                label: "SKILLS",
                value: metrics.skillsCompiled,
                color: Theme.colors.secondary,
              },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ textAlign: "center" }}>
                <div
                  style={{
                    fontSize: 8,
                    color: Theme.colors.textMuted,
                    letterSpacing: "0.15em",
                    fontWeight: 600,
                    marginBottom: 2,
                  }}
                >
                  {label}
                </div>
                <div
                  style={{
                    fontSize: 14,
                    color,
                    fontWeight: 800,
                    fontFamily: Theme.fonts.mono,
                    letterSpacing: "-0.02em",
                  }}
                >
                  {value}
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {pendingApprovals.length > 0 && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  background: "#f8717122",
                  border: "1px solid #f8717155",
                  borderRadius: 6,
                  padding: "4px 10px",
                  fontSize: 11,
                  color: "#f87171",
                  cursor: "pointer",
                }}
                onClick={() => setActiveTab("overview")}
                aria-label={`${pendingApprovals.length} pending approvals`}
              >
                <span style={{ animation: "pulse 1s infinite" }}>⚠</span>
                {pendingApprovals.length} approval
                {pendingApprovals.length > 1 ? "s" : ""}
              </div>
            )}
            {/* System Controls */}
            <button
              onClick={() => setIsHalted(!isHalted)}
              aria-label={
                isHalted ? "Resume cognitive cycle" : "Halt cognitive cycle"
              }
              style={{
                background: isHalted
                  ? Theme.colors.error + "22"
                  : Theme.colors.success + "22",
                border: `1px solid ${isHalted ? Theme.colors.error + "55" : Theme.colors.success + "55"}`,
                borderRadius: 8,
                padding: "6px 14px",
                fontSize: 10,
                fontFamily: Theme.fonts.mono,
                fontWeight: 700,
                color: isHalted ? Theme.colors.error : Theme.colors.success,
                cursor: "pointer",
                letterSpacing: "0.08em",
                transition: "all 0.3s ease",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <div
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: isHalted
                    ? Theme.colors.error
                    : Theme.colors.success,
                  boxShadow: `0 0 8px ${isHalted ? Theme.colors.error : Theme.colors.success}`,
                  animation: isHalted ? "none" : "pulse 2s infinite",
                }}
              />
              {isHalted ? "HALTED" : "LIVE"}
            </button>
            <div
              style={{
                fontSize: 10,
                color:
                  decisionData.regime === "volatile"
                    ? Theme.colors.warning
                    : Theme.colors.textMuted,
                fontFamily: Theme.fonts.mono,
                padding: "4px 10px",
                background:
                  decisionData.regime === "volatile"
                    ? Theme.colors.warning + "11"
                    : "transparent",
                borderRadius: 6,
                fontWeight: 600,
                letterSpacing: "0.08em",
              }}
            >
              {decisionData.regime === "volatile" ? "⚡ VOLATILE" : "◈ STABLE"}
            </div>
            <div
              style={{
                fontSize: 10,
                color: "#ffffff33",
                fontFamily: Theme.fonts.mono,
              }}
            >
              {new Date().toLocaleTimeString([], { hour12: false })}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div
          role="tablist"
          aria-label="Dashboard navigation"
          style={{
            display: "flex",
            gap: 8,
            marginTop: 4,
            marginBottom: 24,
            padding: "4px",
            background: Theme.colors.surfaceMid,
            borderRadius: 12,
            width: "fit-content",
            border: `1px solid ${Theme.colors.border}`,
          }}
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`tabpanel-${tab.id}`}
              tabIndex={activeTab === tab.id ? 0 : -1}
              onClick={() => setActiveTab(tab.id)}
              onKeyDown={(e) => {
                const tabIds = tabs.map((t) => t.id);
                const idx = tabIds.indexOf(tab.id);
                if (e.key === "ArrowRight") {
                  e.preventDefault();
                  setActiveTab(tabIds[(idx + 1) % tabIds.length]);
                } else if (e.key === "ArrowLeft") {
                  e.preventDefault();
                  setActiveTab(
                    tabIds[(idx - 1 + tabIds.length) % tabIds.length],
                  );
                }
              }}
              style={{
                padding: "8px 24px",
                background:
                  activeTab === tab.id
                    ? Theme.colors.accent + "11"
                    : "transparent",
                borderRadius: 8,
                color:
                  activeTab === tab.id
                    ? Theme.colors.accent
                    : Theme.colors.textMuted,
                fontSize: 11,
                fontFamily: Theme.fonts.mono,
                fontWeight: activeTab === tab.id ? 800 : 500,
                letterSpacing: "0.1em",
                cursor: "pointer",
                transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                boxShadow:
                  activeTab === tab.id
                    ? `0 4px 12px ${Theme.colors.accent}11`
                    : "none",
                border:
                  activeTab === tab.id
                    ? `1px solid ${Theme.colors.accent}33`
                    : "1px solid transparent",
                outline: "none",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW TAB ── */}
        {activeTab === "overview" && (
          <div
            role="tabpanel"
            id="tabpanel-overview"
            aria-labelledby="overview"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 20,
            }}
          >
            {/* Cognitive Loop */}
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <Glow color={Theme.colors.info} size={80} />
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 12,
                }}
              >
                COGNITIVE LOOP
              </div>
              <div style={{ display: "flex", justifyContent: "center" }}>
                <CognitiveCycleRing
                  phase={cognitiveLoop.phase}
                  step={cognitiveLoop.step}
                  progress={cognitiveLoop.phaseProgress}
                />
              </div>
              <div
                style={{
                  marginTop: 8,
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 6,
                }}
              >
                {[
                  {
                    label: "memories consolidated",
                    value: metrics.memoriesConsolidated,
                  },
                  {
                    label: "skills crystallized",
                    value: metrics.skillsCompiled,
                  },
                  { label: "context tokens", value: "87.2k" },
                  { label: "model tier", value: "planning" },
                ].map(({ label, value }) => (
                  <div
                    key={label}
                    style={{
                      background: Theme.colors.surfaceMid,
                      borderRadius: 8,
                      padding: "8px 10px",
                      border: `1px solid ${Theme.colors.border}`,
                    }}
                  >
                    <div style={{ fontSize: 9, color: "#ffffff33" }}>
                      {label}
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: "#ffffff",
                        fontWeight: 700,
                      }}
                    >
                      {value}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Decision Intelligence */}
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <Glow color={Theme.colors.accent} size={80} />
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 8,
                }}
              >
                DECISION INTELLIGENCE
              </div>
              <ConfidenceMeter confidence={blended} entropy={entropy} />
              <div style={{ marginTop: 8 }}>
                <div
                  style={{ fontSize: 9, color: "#ffffff33", marginBottom: 4 }}
                >
                  SEMANTIC CLUSTERS
                </div>
                {clusters.map((c) => (
                  <div
                    key={c.name}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      marginBottom: 4,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 10,
                        color: "#ffffff55",
                        width: 55,
                        textAlign: "right",
                      }}
                    >
                      {c.name}
                    </div>
                    <div
                      style={{
                        flex: 1,
                        height: 5,
                        background: Theme.colors.surfaceMid,
                        borderRadius: 3,
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          width: `${c.prob * 100}%`,
                          height: "100%",
                          background:
                            c.name === "proceed"
                              ? "#34d399"
                              : c.name === "monitor"
                                ? "#fbbf24"
                                : "#f87171",
                          borderRadius: 3,
                          transition: "width 0.6s ease",
                        }}
                      />
                    </div>
                    <div
                      style={{ fontSize: 10, color: "#ffffff44", width: 30 }}
                    >
                      {(c.prob * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
                <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
                  <div
                    style={{
                      flex: 1,
                      background: Theme.colors.surfaceMid,
                      border: `1px solid ${Theme.colors.border}`,
                      borderRadius: 6,
                      padding: "5px 8px",
                    }}
                  >
                    <div style={{ fontSize: 9, color: "#ffffff33" }}>
                      Bayesian
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: "#a78bfa",
                        fontWeight: 700,
                      }}
                    >
                      {(bayesianConf * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div
                    style={{
                      flex: 1,
                      background: Theme.colors.surfaceMid,
                      border: `1px solid ${Theme.colors.border}`,
                      borderRadius: 6,
                      padding: "5px 8px",
                    }}
                  >
                    <div style={{ fontSize: 9, color: "#ffffff33" }}>
                      Coverage
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: "#00ffd5",
                        fontWeight: 700,
                      }}
                    >
                      {(conformal.coverage * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Live Stream Chart */}
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <Glow color={Theme.colors.secondary} size={80} />
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 8,
                }}
              >
                PERFORMANCE STREAM
              </div>
              {stream.length > 3 && (
                <>
                  <Sparkline
                    data={stream.map((d) => d.actual)}
                    height={60}
                    color={Theme.colors.accent}
                  />
                  <div style={{ marginTop: 4 }}>
                    <Sparkline
                      data={stream.map((d) => d.predicted)}
                      width={220}
                      height={30}
                      color="#a78bfa44"
                    />
                  </div>
                </>
              )}
              <div
                style={{
                  display: "flex",
                  gap: 10,
                  marginTop: 10,
                  fontSize: 10,
                  color: "#ffffff44",
                }}
              >
                <span style={{ color: "#00ffd5" }}>─ actual</span>
                <span style={{ color: "#a78bfa" }}>─ predicted</span>
                <span
                  style={{
                    marginLeft: "auto",
                    color:
                      decisionData.regime === "volatile"
                        ? "#f87171"
                        : "#34d399",
                  }}
                >
                  {decisionData.regime === "volatile"
                    ? "⚡ volatile"
                    : "● stable"}
                </span>
              </div>
              <div
                style={{
                  marginTop: 10,
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr",
                  gap: 6,
                }}
              >
                {[
                  {
                    label: "actual",
                    value: (decisionData.actual * 100).toFixed(1) + "%",
                    color: "#00ffd5",
                  },
                  {
                    label: "predicted",
                    value: (decisionData.predicted * 100).toFixed(1) + "%",
                    color: "#a78bfa",
                  },
                  {
                    label: "CI width",
                    value: ((ci[1] - ci[0]) * 100).toFixed(1) + "%",
                    color: "#fbbf24",
                  },
                ].map(({ label, value, color }) => (
                  <div
                    key={label}
                    style={{
                      background: "#ffffff06",
                      borderRadius: 6,
                      padding: "5px 8px",
                    }}
                  >
                    <div style={{ fontSize: 9, color: "#ffffff33" }}>
                      {label}
                    </div>
                    <div style={{ fontSize: 12, color, fontWeight: 700 }}>
                      {value}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* HITL Approvals */}
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 12,
                }}
              >
                HITL APPROVALS
              </div>
              {pendingApprovals.length === 0 ? (
                <div
                  style={{
                    color: "#34d399",
                    fontSize: 12,
                    textAlign: "center",
                    padding: "24px 0",
                    opacity: 0.6,
                  }}
                >
                  <div style={{ fontSize: 24, marginBottom: 8 }}>✓</div>
                  All clear — no pending approvals
                </div>
              ) : (
                <div
                  style={{ display: "flex", flexDirection: "column", gap: 10 }}
                >
                  {pendingApprovals.map((a) => (
                    <ApprovalCard
                      key={a.id}
                      approval={a}
                      onDecide={handleDecide}
                    />
                  ))}
                </div>
              )}
              <div
                style={{
                  marginTop: 12,
                  padding: "8px 10px",
                  background: "#ffffff06",
                  borderRadius: 6,
                  fontSize: 10,
                  color: "#ffffff44",
                }}
              >
                Risk policy: LOW=auto-approve(30s) · MED/HIGH=await ·
                CRIT=await(10m)
              </div>
            </div>

            {/* Agent Status Summary */}
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 12,
                }}
              >
                AGENT SWARM
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {agents.map((a) => (
                  <div
                    key={a.id}
                    style={{ display: "flex", alignItems: "center", gap: 8 }}
                  >
                    <StatusDot status={a.status} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                        }}
                      >
                        <span
                          style={{
                            fontSize: 11,
                            color: "#ffffff",
                            fontWeight: 600,
                          }}
                        >
                          {a.name}
                        </span>
                        <span style={{ fontSize: 10, color: "#ffffff44" }}>
                          {a.tools_called}⟳
                        </span>
                      </div>
                      <MiniBar
                        value={a.load}
                        max={a.max}
                        color={
                          a.status === "active"
                            ? "#00ffd5"
                            : a.status === "reasoning"
                              ? "#a78bfa"
                              : a.status === "waiting"
                                ? "#fbbf24"
                                : "#6b7280"
                        }
                        width={180}
                      />
                    </div>
                    <div
                      style={{
                        fontSize: 10,
                        color: "#ffffff33",
                        width: 28,
                        textAlign: "right",
                      }}
                    >
                      {(a.success * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
              <div
                style={{
                  marginTop: 12,
                  borderTop: "1px solid #ffffff0a",
                  paddingTop: 10,
                }}
              >
                <div
                  style={{ fontSize: 9, color: "#ffffff33", marginBottom: 6 }}
                >
                  MODEL DISTRIBUTION
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {Object.entries(modelDist).map(([m, count]) => (
                    <div
                      key={m}
                      style={{
                        padding: "2px 8px",
                        background: "#ffffff0a",
                        borderRadius: 4,
                        fontSize: 10,
                        color: "#ffffff55",
                      }}
                    >
                      {m} ×{count}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Nova Chat */}
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 10,
                }}
              >
                NOVA DIRECT
              </div>
              <div
                style={{
                  flex: 1,
                  overflowY: "auto",
                  maxHeight: 200,
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                  marginBottom: 10,
                }}
              >
                {chatHistory.map((msg, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      gap: 8,
                      alignItems: "flex-start",
                      animation: "fadeIn 0.3s ease",
                    }}
                  >
                    <div
                      style={{
                        width: 20,
                        height: 20,
                        borderRadius: "50%",
                        flexShrink: 0,
                        marginTop: 1,
                        background:
                          msg.role === "nova"
                            ? "linear-gradient(135deg,#00ffd5,#a78bfa)"
                            : "#ffffff22",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 9,
                        fontWeight: 900,
                        color: "#070b10",
                      }}
                    >
                      {msg.role === "nova" ? "N" : "U"}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: msg.role === "nova" ? "#e2e8f0" : "#ffffff88",
                        background:
                          msg.role === "nova" ? "#ffffff0a" : "transparent",
                        padding: msg.role === "nova" ? "6px 10px" : "0",
                        borderRadius: 8,
                        lineHeight: 1.5,
                      }}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
                {isNovaTyping && (
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      alignItems: "center",
                      animation: "fadeIn 0.2s ease",
                    }}
                  >
                    <div
                      style={{
                        width: 20,
                        height: 20,
                        borderRadius: "50%",
                        flexShrink: 0,
                        background: "linear-gradient(135deg,#00ffd5,#a78bfa)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 9,
                        fontWeight: 900,
                        color: "#070b10",
                      }}
                    >
                      N
                    </div>
                    <div
                      style={{
                        display: "flex",
                        gap: 4,
                        padding: "8px 12px",
                        background: "#ffffff0a",
                        borderRadius: 8,
                      }}
                    >
                      {[0, 1, 2].map((i) => (
                        <div
                          key={i}
                          style={{
                            width: 6,
                            height: 6,
                            borderRadius: "50%",
                            background: Theme.colors.accent,
                            animation: `typingDot 1.4s ease-in-out ${i * 0.16}s infinite`,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Tell Nova anything..."
                  style={{
                    flex: 1,
                    background: "#ffffff08",
                    border: "1px solid #ffffff15",
                    borderRadius: 8,
                    padding: "8px 12px",
                    color: "#ffffff",
                    fontSize: 11,
                    fontFamily: "monospace",
                    outline: "none",
                  }}
                />
                <button
                  onClick={sendMessage}
                  style={{
                    padding: "8px 14px",
                    background: "#00ffd522",
                    border: "1px solid #00ffd555",
                    borderRadius: 8,
                    color: "#00ffd5",
                    fontSize: 11,
                    fontFamily: "monospace",
                    cursor: "pointer",
                    fontWeight: 700,
                  }}
                >
                  →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── AGENTS TAB ── */}
        {activeTab === "agents" && (
          <div role="tabpanel" id="tabpanel-agents" aria-labelledby="agents">
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: 14,
                marginBottom: 14,
              }}
            >
              {agents.map((a) => (
                <AgentCard key={a.id} agent={a} />
              ))}
            </div>
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 12,
                }}
              >
                ORCHESTRATION TOPOLOGY
              </div>
              <OrchestrationGraph />

              <div
                style={{
                  marginTop: 12,
                  padding: "10px 14px",
                  background: "#ffffff06",
                  borderRadius: 8,
                  fontSize: 10,
                  color: "#ffffff55",
                  fontFamily: "monospace",
                }}
              >
                Pattern: Manager-Worker with Peer Review gates · Conflict
                resolution: Nova Prime arbitrates · Communication: shared state
                (Redis) + direct signals · Auto-spawn on load spike
              </div>
            </div>
          </div>
        )}

        {/* ── MEMORY TAB ── */}
        {activeTab === "memory" && (
          <div
            role="tabpanel"
            id="tabpanel-memory"
            aria-labelledby="memory"
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}
          >
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <Glow color={Theme.colors.accent} size={80} />
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 12,
                }}
              >
                TEMPORAL KNOWLEDGE GRAPH
              </div>
              <MemoryGraph nodes={memoryNodes} />
              <div
                style={{
                  display: "flex",
                  gap: 16,
                  marginTop: 8,
                  fontSize: 10,
                  color: "#ffffff44",
                }}
              >
                <span style={{ color: "#a78bfa" }}>◉ episodic</span>
                <span style={{ color: "#00ffd5" }}>◉ procedural</span>
                <span style={{ color: "#fbbf24" }}>◉ semantic</span>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div
                style={{
                  background: Theme.colors.surfaceLow,
                  backdropFilter: Theme.glass.blur,
                  border: `1px solid ${Theme.colors.border}`,
                  borderRadius: 16,
                  padding: 20,
                  boxShadow: Theme.glass.shadow,
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                <Glow color={Theme.colors.secondary} size={80} />
                <div
                  style={{
                    fontSize: 10,
                    color: "#ffffff44",
                    letterSpacing: "0.1em",
                    marginBottom: 10,
                  }}
                >
                  MEMORY NODES
                </div>
                <div
                  style={{ display: "flex", flexDirection: "column", gap: 6 }}
                >
                  {memoryNodes.map((m) => {
                    const typeColors = {
                      episodic: "#a78bfa",
                      procedural: "#00ffd5",
                      semantic: "#fbbf24",
                    };
                    const tc = typeColors[m.type];
                    return (
                      <div
                        key={m.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                          padding: "6px 8px",
                          background: "#ffffff05",
                          borderRadius: 6,
                        }}
                      >
                        <div
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: "50%",
                            background: tc,
                            boxShadow: `0 0 4px ${tc}`,
                          }}
                        />
                        <span
                          style={{ flex: 1, fontSize: 11, color: "#ffffff" }}
                        >
                          {m.label}
                        </span>
                        <span style={{ fontSize: 9, color: "#ffffff33" }}>
                          {m.age}
                        </span>
                        <MiniBar
                          value={m.strength}
                          max={1}
                          color={tc}
                          width={50}
                        />
                        <span
                          style={{
                            fontSize: 10,
                            color: "#ffffff44",
                            width: 30,
                          }}
                        >
                          {(m.strength * 100).toFixed(0)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
              <div
                style={{
                  background: Theme.colors.surfaceLow,
                  backdropFilter: Theme.glass.blur,
                  border: `1px solid ${Theme.colors.border}`,
                  borderRadius: 16,
                  padding: 20,
                  boxShadow: Theme.glass.shadow,
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                <Glow color={Theme.colors.warning} size={80} />
                <div
                  style={{
                    fontSize: 10,
                    color: "#ffffff44",
                    letterSpacing: "0.1em",
                    marginBottom: 10,
                  }}
                >
                  MEMORY STATISTICS
                </div>
                {[
                  { label: "Episodic nodes", value: "1,241", color: "#a78bfa" },
                  { label: "Semantic facts", value: "341", color: "#fbbf24" },
                  {
                    label: "Compiled skills",
                    value: metrics.skillsCompiled,
                    color: "#00ffd5",
                  },
                  { label: "Forgotten (decay)", value: "47", color: "#6b7280" },
                  {
                    label: "Context primacy %",
                    value: "3.4%",
                    color: "#38bdf8",
                  },
                  {
                    label: "Context recency %",
                    value: "22.1%",
                    color: "#34d399",
                  },
                ].map(({ label, value, color }) => (
                  <div
                    key={label}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      padding: "5px 0",
                      borderBottom: "1px solid #ffffff06",
                    }}
                  >
                    <span style={{ fontSize: 11, color: "#ffffff66" }}>
                      {label}
                    </span>
                    <span style={{ fontSize: 11, color, fontWeight: 700 }}>
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── DECISIONS TAB ── */}
        {activeTab === "decisions" && (
          <div
            role="tabpanel"
            id="tabpanel-decisions"
            aria-labelledby="decisions"
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}
          >
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <Glow color={Theme.colors.accent} size={80} />
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 12,
                }}
              >
                CONFORMAL PREDICTION INTERVALS
              </div>
              {stream.length > 10 && (
                <ConformalBandChart
                  stream={stream}
                  ci={ci}
                  width={450}
                  height={100}
                />
              )}
              <div
                style={{
                  marginTop: 10,
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr 1fr",
                  gap: 6,
                }}
              >
                {[
                  {
                    label: "CI lower",
                    value: (ci[0] * 100).toFixed(1) + "%",
                    color: "#f87171",
                  },
                  {
                    label: "prediction",
                    value: (decisionData.predicted * 100).toFixed(1) + "%",
                    color: "#a78bfa",
                  },
                  {
                    label: "CI upper",
                    value: (ci[1] * 100).toFixed(1) + "%",
                    color: "#34d399",
                  },
                  {
                    label: "CI width",
                    value: ((ci[1] - ci[0]) * 100).toFixed(1) + "%",
                    color: "#fbbf24",
                  },
                ].map(({ label, value, color }) => (
                  <div
                    key={label}
                    style={{
                      background: "#ffffff06",
                      borderRadius: 8,
                      padding: "8px 10px",
                    }}
                  >
                    <div style={{ fontSize: 9, color: "#ffffff33" }}>
                      {label}
                    </div>
                    <div style={{ fontSize: 14, color, fontWeight: 700 }}>
                      {value}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <Glow color={Theme.colors.primary} size={80} />
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 12,
                }}
              >
                BAYESIAN POSTERIOR
              </div>
              <div style={{ padding: "16px 0" }}>
                <ConfidenceMeter confidence={bayesianConf} entropy={entropy} />
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 8,
                }}
              >
                {[
                  {
                    label: "α (successes)",
                    value: bayesian.alpha,
                    color: "#34d399",
                  },
                  {
                    label: "β (failures)",
                    value: bayesian.beta,
                    color: "#f87171",
                  },
                  {
                    label: "posterior mean",
                    value: (bayesian.mean * 100).toFixed(1) + "%",
                    color: "#00ffd5",
                  },
                  {
                    label: "variance",
                    value: (bayesian.variance * 1000).toFixed(2) + "×10⁻³",
                    color: "#a78bfa",
                  },
                ].map(({ label, value, color }) => (
                  <div
                    key={label}
                    style={{
                      background: "#ffffff06",
                      borderRadius: 8,
                      padding: "8px 10px",
                    }}
                  >
                    <div style={{ fontSize: 9, color: "#ffffff33" }}>
                      {label}
                    </div>
                    <div style={{ fontSize: 13, color, fontWeight: 700 }}>
                      {value}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <Glow color={Theme.colors.warning} size={80} />
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 12,
                }}
              >
                MODEL CAPABILITY FLEET
              </div>
              {[
                {
                  model: "claude-sonnet-4-5",
                  reasoning: 0.91,
                  tool_use: 0.94,
                  context: 0.92,
                  cost: "$3/$15",
                  latency: "800ms",
                },
                {
                  model: "gemini-2-flash",
                  reasoning: 0.82,
                  tool_use: 0.88,
                  context: 0.9,
                  cost: "$0.1/$0.4",
                  latency: "400ms",
                },
                {
                  model: "groq-llama-3-70b",
                  reasoning: 0.78,
                  tool_use: 0.81,
                  context: 0.75,
                  cost: "$0.6/$0.8",
                  latency: "150ms",
                },
                {
                  model: "qwen2.5-32b-local",
                  reasoning: 0.72,
                  tool_use: 0.73,
                  context: 0.7,
                  cost: "free",
                  latency: "1200ms",
                },
              ].map((m) => (
                <div
                  key={m.model}
                  style={{
                    marginBottom: 10,
                    padding: "8px 10px",
                    background: "#ffffff05",
                    borderRadius: 8,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: 6,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 11,
                        color: "#ffffff",
                        fontWeight: 600,
                      }}
                    >
                      {m.model}
                    </span>
                    <div
                      style={{
                        display: "flex",
                        gap: 8,
                        fontSize: 10,
                        color: "#ffffff44",
                      }}
                    >
                      <span>{m.cost}</span>
                      <span>{m.latency}</span>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    {[
                      ["reasoning", m.reasoning, "#00ffd5"],
                      ["tool_use", m.tool_use, "#a78bfa"],
                      ["context", m.context, "#fbbf24"],
                    ].map(([label, val, color]) => (
                      <div key={label} style={{ flex: 1 }}>
                        <div
                          style={{
                            fontSize: 9,
                            color: "#ffffff33",
                            marginBottom: 2,
                          }}
                        >
                          {label}
                        </div>
                        <MiniBar value={val} max={1} color={color} width={70} />
                        <div style={{ fontSize: 9, color, marginTop: 1 }}>
                          {(val * 100).toFixed(0)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                position: "relative",
                overflow: "hidden",
              }}
            >
              <Glow color={Theme.colors.secondary} size={80} />
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                  marginBottom: 12,
                }}
              >
                DEFERRAL MODULE
              </div>
              {[
                {
                  threshold: 0.8,
                  label: "PROCEED",
                  desc: "High confidence — execute autonomously",
                  color: "#34d399",
                },
                {
                  threshold: 0.55,
                  label: "MONITOR",
                  desc: "Moderate confidence — execute with logging",
                  color: "#fbbf24",
                },
                {
                  threshold: 0,
                  label: "DEFER",
                  desc: "Low confidence — request human input",
                  color: "#f87171",
                },
              ].map((tier) => {
                const active =
                  blended >= tier.threshold &&
                  (tier.threshold === 0.8
                    ? true
                    : blended < (tier.threshold === 0.55 ? 0.8 : 0.55));
                const isActive =
                  (tier.threshold === 0.8 && blended >= 0.8) ||
                  (tier.threshold === 0.55 &&
                    blended >= 0.55 &&
                    blended < 0.8) ||
                  (tier.threshold === 0 && blended < 0.55);
                return (
                  <div
                    key={tier.label}
                    style={{
                      display: "flex",
                      gap: 12,
                      alignItems: "flex-start",
                      padding: "10px 12px",
                      background: isActive ? tier.color + "15" : "#ffffff05",
                      border: `1px solid ${isActive ? tier.color + "44" : "transparent"}`,
                      borderRadius: 8,
                      marginBottom: 8,
                      transition: "all 0.4s ease",
                    }}
                  >
                    <div
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: "50%",
                        background: tier.color,
                        marginTop: 2,
                        flexShrink: 0,
                        boxShadow: isActive ? `0 0 8px ${tier.color}` : "none",
                      }}
                    />
                    <div>
                      <div
                        style={{
                          fontSize: 12,
                          fontWeight: 700,
                          color: tier.color,
                          letterSpacing: "0.08em",
                        }}
                      >
                        {tier.label}
                      </div>
                      <div
                        style={{
                          fontSize: 10,
                          color: "#ffffff55",
                          marginTop: 2,
                        }}
                      >
                        {tier.desc}
                      </div>
                      <div
                        style={{
                          fontSize: 9,
                          color: "#ffffff33",
                          marginTop: 1,
                        }}
                      >
                        threshold: {tier.threshold * 100}%
                      </div>
                    </div>
                    {isActive && (
                      <div
                        style={{
                          marginLeft: "auto",
                          fontSize: 10,
                          color: tier.color,
                          fontWeight: 700,
                        }}
                      >
                        ACTIVE
                      </div>
                    )}
                  </div>
                );
              })}
              <div
                style={{
                  marginTop: 6,
                  padding: "8px 10px",
                  background: "#ffffff06",
                  borderRadius: 6,
                  fontSize: 10,
                  color: "#ffffff44",
                }}
              >
                Current:{" "}
                <span
                  style={{
                    color:
                      blended >= 0.8
                        ? "#34d399"
                        : blended >= 0.55
                          ? "#fbbf24"
                          : "#f87171",
                    fontWeight: 700,
                  }}
                >
                  {blended >= 0.8
                    ? "PROCEED"
                    : blended >= 0.55
                      ? "MONITOR"
                      : "DEFER"}
                </span>{" "}
                · blended confidence:{" "}
                <span style={{ color: "#00ffd5" }}>
                  {(blended * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Decision Audit Trail — full-width across both columns */}
            {decisionLog.length > 0 && (
              <div
                style={{
                  gridColumn: "1 / -1",
                  background: Theme.colors.surfaceLow,
                  backdropFilter: Theme.glass.blur,
                  border: `1px solid ${Theme.colors.border}`,
                  borderRadius: 16,
                  padding: 20,
                  boxShadow: Theme.glass.shadow,
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                <Glow color={Theme.colors.info} size={60} />
                <div
                  style={{
                    fontSize: 10,
                    color: "#ffffff44",
                    letterSpacing: "0.1em",
                    marginBottom: 12,
                  }}
                >
                  DECISION AUDIT TRAIL
                </div>
                <div
                  style={{ display: "flex", flexDirection: "column", gap: 4 }}
                >
                  {decisionLog.map((entry, idx) => (
                    <div
                      key={`${entry.id}-${idx}`}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 12,
                        padding: "6px 10px",
                        background: idx === 0 ? "#ffffff08" : "#ffffff03",
                        borderRadius: 6,
                        borderLeft: `3px solid ${entry.approved ? Theme.colors.success : Theme.colors.error}`,
                        animation: idx === 0 ? "fadeIn 0.3s ease" : "none",
                      }}
                    >
                      <span
                        style={{
                          fontSize: 9,
                          color: "#ffffff33",
                          fontFamily: "monospace",
                          width: 55,
                          flexShrink: 0,
                        }}
                      >
                        {entry.timestamp}
                      </span>
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 700,
                          color: entry.approved
                            ? Theme.colors.success
                            : Theme.colors.error,
                          width: 55,
                          flexShrink: 0,
                        }}
                      >
                        {entry.approved ? "✓ APPROVED" : "✕ DENIED"}
                      </span>
                      <span
                        style={{
                          fontSize: 10,
                          color: "#ffffffbb",
                          flex: 1,
                          fontFamily: "monospace",
                        }}
                      >
                        {entry.tool}
                      </span>
                      <span style={{ fontSize: 9, color: "#ffffff55" }}>
                        by {entry.agent}
                      </span>
                      <span
                        style={{
                          fontSize: 9,
                          color: Theme.colors.accent,
                          fontFamily: "monospace",
                        }}
                      >
                        {entry.confidence}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes typingDot { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1); opacity: 1; } }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #ffffff22; border-radius: 2px; }
        * { box-sizing: border-box; }
        input::placeholder { color: #ffffff33; }
        button:focus-visible { outline: 2px solid #00ffd5; outline-offset: 2px; }
      `}</style>
    </div>
  );
}
