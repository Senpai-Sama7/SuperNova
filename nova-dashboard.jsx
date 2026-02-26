import { useState, useEffect, useRef, useCallback } from "react";

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

function useNovaSimulation() {
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
  }, [tick]);

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

const Glow = ({ color = "#00ffd5", size = 60 }) => (
  <div
    style={{
      position: "absolute",
      width: size,
      height: size,
      borderRadius: "50%",
      background: color,
      filter: "blur(40px)",
      opacity: 0.15,
      pointerEvents: "none",
    }}
  />
);

const Badge = ({ label, color }) => (
  <span
    style={{
      padding: "2px 8px",
      borderRadius: 4,
      fontSize: 10,
      fontWeight: 700,
      background: color + "22",
      color,
      border: `1px solid ${color}44`,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
    }}
  >
    {label}
  </span>
);

const StatusDot = ({ status }) => {
  const colors = {
    active: "#00ffd5",
    reasoning: "#a78bfa",
    waiting: "#fbbf24",
    idle: "#6b7280",
    error: "#f87171",
  };
  return (
    <span
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: colors[status] || "#6b7280",
        boxShadow: `0 0 6px ${colors[status] || "#6b7280"}`,
        marginRight: 6,
      }}
    />
  );
};

const MiniBar = ({ value, max, color = "#00ffd5", width = 80 }) => (
  <div
    style={{
      width,
      height: 4,
      background: "#ffffff10",
      borderRadius: 2,
      overflow: "hidden",
    }}
  >
    <div
      style={{
        width: `${(value / max) * 100}%`,
        height: "100%",
        background: color,
        transition: "width 0.4s ease",
        borderRadius: 2,
      }}
    />
  </div>
);

const RiskPill = ({ risk }) => {
  const map = {
    low: ["#34d399", "LOW"],
    medium: ["#fbbf24", "MED"],
    high: ["#f87171", "HIGH"],
    critical: ["#e879f9", "CRIT"],
  };
  const [color, label] = map[risk] || ["#6b7280", "?"];
  return <Badge label={label} color={color} />;
};

// ─── Sparkline ────────────────────────────────────────────────────────────────
const Sparkline = ({
  data,
  width = 200,
  height = 50,
  color = "#00ffd5",
  showBand = false,
  bandData = null,
}) => {
  if (!data.length) return null;
  const minV = Math.min(...data) - 0.05;
  const maxV = Math.max(...data) + 0.05;
  const scaleX = (i) => (i / (data.length - 1)) * width;
  const scaleY = (v) => height - ((v - minV) / (maxV - minV)) * height;
  const path = data
    .map((v, i) => `${i === 0 ? "M" : "L"} ${scaleX(i)} ${scaleY(v)}`)
    .join(" ");
  const areaPath = `${path} L ${scaleX(data.length - 1)} ${height} L ${scaleX(0)} ${height} Z`;

  return (
    <svg
      width={width}
      height={height}
      style={{ overflow: "visible" }}
      role="img"
      aria-label="Performance metrics sparkline"
    >
      <defs>
        <linearGradient
          id={`grad-${color.replace("#", "")}`}
          x1="0"
          x2="0"
          y1="0"
          y2="1"
        >
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {showBand && bandData && (
        <path d={bandData} fill={color} fillOpacity={0.08} stroke="none" />
      )}
      <path
        d={areaPath}
        fill={`url(#grad-${color.replace("#", "")})`}
        stroke="none"
      />
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
      />
      {data.length > 0 && (
        <circle
          cx={scaleX(data.length - 1)}
          cy={scaleY(data[data.length - 1])}
          r={3}
          fill={color}
        />
      )}
    </svg>
  );
};

// ─── Memory Graph ─────────────────────────────────────────────────────────────
const MemoryGraph = ({ nodes }) => {
  const typeColors = {
    episodic: "#a78bfa",
    procedural: "#00ffd5",
    semantic: "#fbbf24",
  };
  const edges = [
    ["m1", "m3"],
    ["m3", "m5"],
    ["m2", "m6"],
    ["m3", "m7"],
    ["m4", "m6"],
    ["m1", "m5"],
    ["m3", "m2"],
    ["m5", "m7"],
  ];

  return (
    <div style={{ position: "relative", width: "100%", height: 180 }}>
      <svg
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
        }}
        role="img"
        aria-label="Neural memory graph visualization"
      >
        {edges.map(([a, b], i) => {
          const na = nodes.find((n) => n.id === a);
          const nb = nodes.find((n) => n.id === b);
          if (!na || !nb) return null;
          return (
            <line
              key={i}
              x1={`${na.x}%`}
              y1={`${na.y}%`}
              x2={`${nb.x}%`}
              y2={`${nb.y}%`}
              stroke="#ffffff15"
              strokeWidth={1}
              strokeDasharray="3,3"
            />
          );
        })}
      </svg>
      {nodes.map((node) => (
        <div
          key={node.id}
          style={{
            position: "absolute",
            left: `${node.x}%`,
            top: `${node.y}%`,
            transform: "translate(-50%, -50%)",
            cursor: "pointer",
          }}
        >
          <div
            style={{
              width: 10 + node.connections * 3,
              height: 10 + node.connections * 3,
              borderRadius: "50%",
              background: typeColors[node.type] + "33",
              border: `2px solid ${typeColors[node.type]}`,
              boxShadow: `0 0 ${node.strength * 12}px ${typeColors[node.type]}66`,
              transition: "all 0.6s ease",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                width: 4,
                height: 4,
                borderRadius: "50%",
                background: typeColors[node.type],
              }}
            />
          </div>
          <div
            style={{
              position: "absolute",
              top: "100%",
              left: "50%",
              transform: "translateX(-50%)",
              fontSize: 9,
              color: "#ffffff88",
              whiteSpace: "nowrap",
              marginTop: 3,
              fontFamily: "monospace",
            }}
          >
            {node.label}
          </div>
        </div>
      ))}
    </div>
  );
};

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
    "#38bdf8",
    "#a78bfa",
    "#00ffd5",
    "#f97316",
    "#e879f9",
    "#34d399",
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
        {phases.map((p, i) => {
          const angle = (i / phases.length) * 2 * Math.PI - Math.PI / 2;
          const offset = circumference - i * segmentLen;
          const active = i === step;
          const done = i < step;
          const dashLen = segmentLen - 3;

          return (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={
                active ? colors[i] : done ? colors[i] + "88" : "#ffffff15"
              }
              strokeWidth={active ? 5 : 3}
              strokeDasharray={`${dashLen} ${circumference - dashLen}`}
              strokeDashoffset={-i * segmentLen + circumference / 4}
              strokeLinecap="round"
              style={{
                transition: "stroke 0.4s ease",
                filter: active ? `drop-shadow(0 0 6px ${colors[i]})` : "none",
              }}
            />
          );
        })}
        {/* Progress arc for current phase */}
        <circle
          cx={cx}
          cy={cy}
          r={r - 8}
          fill="none"
          stroke={colors[step] + "44"}
          strokeWidth={2}
          strokeDasharray={`${(segmentLen - 3) * progress} ${circumference}`}
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
        }}
      >
        <div
          style={{
            fontSize: 9,
            color: "#ffffff66",
            fontFamily: "monospace",
            letterSpacing: "0.1em",
          }}
        >
          PHASE
        </div>
        <div
          style={{
            fontSize: 11,
            color: colors[step],
            fontWeight: 700,
            fontFamily: "monospace",
            letterSpacing: "0.06em",
          }}
        >
          {phase}
        </div>
      </div>
      {/* Phase labels around ring */}
      {phases.map((p, i) => {
        const angle = (i / phases.length) * 2 * Math.PI - Math.PI / 2;
        const lx = cx + (r + 16) * Math.cos(angle);
        const ly = cy + (r + 16) * Math.sin(angle);
        return (
          <text
            key={i}
            x={lx}
            y={ly}
            textAnchor="middle"
            dominantBaseline="middle"
            fill={i === step ? colors[i] : "#ffffff33"}
            fontSize={7}
            fontFamily="monospace"
            fontWeight={i === step ? 700 : 400}
            style={{ transition: "fill 0.4s ease" }}
          >
            {p.slice(0, 3)}
          </text>
        );
      })}
    </div>
  );
};

// ─── Confidence Meter ──────────────────────────────────────────────────────────
const ConfidenceMeter = ({ confidence, entropy }) => {
  const decision =
    confidence > 0.8
      ? { label: "PROCEED", color: "#34d399", icon: "◈" }
      : confidence > 0.55
        ? { label: "MONITOR", color: "#fbbf24", icon: "◉" }
        : { label: "DEFER", color: "#f87171", icon: "◎" };

  const angle = confidence * 180 - 90;
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
        {confidence > 0 && (
          <path
            d={`M ${cx - r} ${cy} A ${r} ${r} 0 ${confidence > 0.5 ? 1 : 0} 1 ${cx + r * Math.cos(Math.PI - confidence * Math.PI)} ${cy - r * Math.sin(confidence * Math.PI)}`}
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
          x2={cx + (r - 8) * Math.cos(Math.PI - confidence * Math.PI)}
          y2={cy - (r - 8) * Math.sin(confidence * Math.PI)}
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
          {(confidence * 100).toFixed(1)}%
        </span>{" "}
        · entropy:{" "}
        <span style={{ color: "#a78bfa" }}>{(entropy * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
};

// ─── Agent Card ───────────────────────────────────────────────────────────────
const AgentCard = ({ agent }) => {
  const statusColor = {
    active: "#00ffd5",
    reasoning: "#a78bfa",
    waiting: "#fbbf24",
    idle: "#6b7280",
  };
  const roleIcons = {
    Planner: "◈",
    Researcher: "◉",
    Executor: "◎",
    Auditor: "⬡",
    Creative: "✦",
  };
  const sc = statusColor[agent.status] || "#6b7280";

  return (
    <div
      style={{
        background: "#0f1117",
        border: `1px solid ${sc}33`,
        borderRadius: 10,
        padding: "12px 14px",
        position: "relative",
        overflow: "hidden",
        transition: "border-color 0.4s ease",
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
          opacity: 0.6,
        }}
      />
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 8,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 14, color: sc }}>
              {roleIcons[agent.role]}
            </span>
            <span
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: "#ffffff",
                fontFamily: "monospace",
              }}
            >
              {agent.name}
            </span>
            <StatusDot status={agent.status} />
          </div>
          <div
            style={{
              fontSize: 10,
              color: "#ffffff55",
              fontFamily: "monospace",
              marginTop: 1,
            }}
          >
            {agent.role} · {agent.model}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              fontSize: 10,
              color: "#ffffff44",
              fontFamily: "monospace",
            }}
          >
            success
          </div>
          <div
            style={{
              fontSize: 13,
              color:
                agent.success > 0.95
                  ? "#34d399"
                  : agent.success > 0.9
                    ? "#fbbf24"
                    : "#f87171",
              fontWeight: 700,
              fontFamily: "monospace",
            }}
          >
            {(agent.success * 100).toFixed(0)}%
          </div>
        </div>
      </div>
      <div
        style={{
          fontSize: 10,
          color: "#ffffff66",
          fontFamily: "monospace",
          marginBottom: 8,
          fontStyle: "italic",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        ↳ {agent.task}
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <div
            style={{
              fontSize: 9,
              color: "#ffffff44",
              marginBottom: 3,
              fontFamily: "monospace",
            }}
          >
            load {agent.load}/{agent.max}
          </div>
          <MiniBar value={agent.load} max={agent.max} color={sc} width={90} />
        </div>
        <div
          style={{
            display: "flex",
            gap: 12,
            fontSize: 10,
            color: "#ffffff55",
            fontFamily: "monospace",
          }}
        >
          <span>⟳ {agent.tools_called}</span>
          <span>⬡ {agent.memory_hits}</span>
          <span>~{agent.latency.toFixed(1)}s</span>
        </div>
      </div>
    </div>
  );
};

// ─── Approval Card ────────────────────────────────────────────────────────────
const ApprovalCard = ({ approval, onDecide }) => {
  const riskColors = {
    low: "#34d399",
    medium: "#fbbf24",
    high: "#f87171",
    critical: "#e879f9",
  };
  const rc = riskColors[approval.risk];
  const progress = (approval.expires / 300) * 100;

  return (
    <div
      style={{
        background: "#0f1117",
        border: `1px solid ${rc}55`,
        borderRadius: 10,
        padding: "12px 14px",
        position: "relative",
        overflow: "hidden",
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
          opacity: 0.8,
        }}
      />
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 6,
        }}
      >
        <div>
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              color: "#ffffff",
              fontFamily: "monospace",
            }}
          >
            {approval.tool}
          </div>
          <div
            style={{
              fontSize: 10,
              color: "#ffffff55",
              fontFamily: "monospace",
            }}
          >
            {approval.agent}
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <RiskPill risk={approval.risk} />
          <span
            style={{
              fontSize: 10,
              color: "#ffffff44",
              fontFamily: "monospace",
            }}
          >
            {approval.expires}s
          </span>
        </div>
      </div>
      <div
        style={{
          fontSize: 10,
          color: "#ffffff66",
          fontFamily: "monospace",
          marginBottom: 10,
          background: "#ffffff08",
          padding: "4px 8px",
          borderRadius: 4,
        }}
      >
        {Object.entries(approval.args)
          .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
          .join(", ")}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={() => onDecide(approval.id, true)}
          style={{
            flex: 1,
            padding: "6px 0",
            background: "#34d39922",
            border: "1px solid #34d39966",
            borderRadius: 6,
            color: "#34d399",
            fontSize: 11,
            fontFamily: "monospace",
            cursor: "pointer",
            fontWeight: 700,
            letterSpacing: "0.06em",
          }}
        >
          ✓ APPROVE
        </button>
        <button
          onClick={() => onDecide(approval.id, false)}
          style={{
            flex: 1,
            padding: "6px 0",
            background: "#f8717122",
            border: "1px solid #f8717166",
            borderRadius: 6,
            color: "#f87171",
            fontSize: 11,
            fontFamily: "monospace",
            cursor: "pointer",
            fontWeight: 700,
            letterSpacing: "0.06em",
          }}
        >
          ✕ DENY
        </button>
      </div>
    </div>
  );
};

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function NovaDashboard() {
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
  } = useNovaSimulation();
  const [activeTab, setActiveTab] = useState("overview");
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
    setPendingApprovals((prev) => prev.filter((a) => a.id !== id));
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
    setTimeout(() => {
      const responses = [
        "On it. Routing to the appropriate specialist and assembling context from temporal memory.",
        "I've added that to your active goals. Atlas will begin execution in the next cycle.",
        "Interesting. Cross-referencing with your recent episodic context... I see a pattern worth discussing.",
        "Noted. I'll crystallize a skill from this once we have 3 successful completions.",
        "Already thinking about this. The Bayesian confidence for that path is currently 84%. Shall I proceed?",
      ];
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
        background: "#070b10",
        color: "#e2e8f0",
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
        position: "relative",
        overflow: "hidden",
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
            top: "10%",
            left: "5%",
            width: 300,
            height: 300,
            borderRadius: "50%",
            background: "#00ffd5",
            filter: "blur(120px)",
            opacity: 0.04,
          }}
        />
        <div
          style={{
            position: "absolute",
            top: "50%",
            right: "5%",
            width: 250,
            height: 250,
            borderRadius: "50%",
            background: "#a78bfa",
            filter: "blur(100px)",
            opacity: 0.05,
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "10%",
            left: "40%",
            width: 200,
            height: 200,
            borderRadius: "50%",
            background: "#f97316",
            filter: "blur(80px)",
            opacity: 0.04,
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
            padding: "16px 0 12px",
            borderBottom: "1px solid #ffffff0f",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ position: "relative" }}>
              <div
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: "50%",
                  background: "linear-gradient(135deg, #00ffd5, #a78bfa)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 18,
                  fontWeight: 900,
                  color: "#070b10",
                  boxShadow: "0 0 20px #00ffd544",
                }}
              >
                N
              </div>
              <div
                style={{
                  position: "absolute",
                  bottom: 0,
                  right: 0,
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: "#34d399",
                  border: "2px solid #070b10",
                  boxShadow: "0 0 6px #34d399",
                }}
              />
            </div>
            <div>
              <div
                style={{
                  fontSize: 18,
                  fontWeight: 900,
                  letterSpacing: "0.15em",
                  color: "#ffffff",
                }}
              >
                NOVA<span style={{ color: "#00ffd5" }}>_</span>2.0
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: "#ffffff44",
                  letterSpacing: "0.1em",
                }}
              >
                INTELLIGENCE COMMAND CENTER
              </div>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              gap: 24,
              fontSize: 11,
              color: "#ffffff55",
            }}
          >
            {[
              {
                label: "CALLS",
                value: metrics.totalCalls.toLocaleString(),
                color: "#00ffd5",
              },
              {
                label: "SUCCESS",
                value: `${(metrics.successRate * 100).toFixed(1)}%`,
                color: "#34d399",
              },
              {
                label: "LATENCY",
                value: `${metrics.avgLatency.toFixed(2)}s`,
                color: "#fbbf24",
              },
              {
                label: "COST",
                value: `$${metrics.cost.toFixed(2)}`,
                color: "#f87171",
              },
              {
                label: "SKILLS",
                value: metrics.skillsCompiled,
                color: "#a78bfa",
              },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ textAlign: "center" }}>
                <div
                  style={{
                    fontSize: 9,
                    color: "#ffffff33",
                    letterSpacing: "0.08em",
                    marginBottom: 1,
                  }}
                >
                  {label}
                </div>
                <div style={{ fontSize: 13, color, fontWeight: 700 }}>
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
              >
                <span style={{ animation: "pulse 1s infinite" }}>⚠</span>
                {pendingApprovals.length} approval
                {pendingApprovals.length > 1 ? "s" : ""}
              </div>
            )}
            <div style={{ fontSize: 10, color: "#ffffff33" }}>
              {new Date().toLocaleTimeString([], { hour12: false })}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div
          style={{
            display: "flex",
            gap: 2,
            marginTop: 12,
            marginBottom: 16,
            borderBottom: "1px solid #ffffff0f",
          }}
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "8px 18px",
                background: "none",
                border: "none",
                borderBottom:
                  activeTab === tab.id
                    ? "2px solid #00ffd5"
                    : "2px solid transparent",
                color: activeTab === tab.id ? "#00ffd5" : "#ffffff44",
                fontSize: 11,
                fontFamily: "monospace",
                fontWeight: activeTab === tab.id ? 700 : 400,
                letterSpacing: "0.1em",
                cursor: "pointer",
                transition: "all 0.2s",
                marginBottom: -1,
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW TAB ── */}
        {activeTab === "overview" && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 14,
            }}
          >
            {/* Cognitive Loop */}
            <div
              style={{
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
                      background: "#ffffff06",
                      borderRadius: 6,
                      padding: "6px 8px",
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
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
              }}
            >
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
                        background: "#ffffff0f",
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
                      background: "#ffffff06",
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
                      background: "#ffffff06",
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
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
              }}
            >
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
                    width={220}
                    height={50}
                    color="#00ffd5"
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
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
          <div>
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
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-around",
                  alignItems: "center",
                  padding: "16px 0",
                }}
              >
                {[
                  { name: "Nova Prime", role: "Planner", x: "50%", y: 0 },
                  { name: "Iris", role: "Researcher", x: "20%", y: 60 },
                  { name: "Atlas", role: "Executor", x: "40%", y: 60 },
                  { name: "Aegis", role: "Auditor", x: "60%", y: 60 },
                  { name: "Muse", role: "Creative", x: "80%", y: 60 },
                ].map((node, i) => (
                  <div key={node.name} style={{ textAlign: "center" }}>
                    <div
                      style={{
                        width: node.role === "Planner" ? 52 : 42,
                        height: node.role === "Planner" ? 52 : 42,
                        borderRadius: "50%",
                        background:
                          node.role === "Planner"
                            ? "linear-gradient(135deg,#00ffd5,#a78bfa)"
                            : "#ffffff0f",
                        border: `2px solid ${node.role === "Planner" ? "#00ffd5" : "#ffffff22"}`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: node.role === "Planner" ? 20 : 16,
                        margin: "0 auto 8px",
                        boxShadow:
                          node.role === "Planner"
                            ? "0 0 20px #00ffd544"
                            : "none",
                      }}
                    >
                      {["◈", "◉", "◎", "⬡", "✦"][i]}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: "#ffffff",
                        fontWeight: 600,
                        fontFamily: "monospace",
                      }}
                    >
                      {node.name}
                    </div>
                    <div
                      style={{
                        fontSize: 9,
                        color: "#ffffff44",
                        fontFamily: "monospace",
                      }}
                    >
                      {node.role}
                    </div>
                  </div>
                ))}
              </div>
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
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}
          >
            <div
              style={{
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
                  background: "#0a0e14",
                  border: "1px solid #ffffff0f",
                  borderRadius: 12,
                  padding: 16,
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
                  background: "#0a0e14",
                  border: "1px solid #ffffff0f",
                  borderRadius: 12,
                  padding: 16,
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
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}
          >
            <div
              style={{
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
                CONFORMAL PREDICTION INTERVALS
              </div>
              {stream.length > 10 && (
                <Sparkline
                  data={stream.map((d) => d.actual)}
                  width={450}
                  height={80}
                  color="#00ffd5"
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
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
                background: "#0a0e14",
                border: "1px solid #ffffff0f",
                borderRadius: 12,
                padding: 16,
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
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #ffffff22; border-radius: 2px; }
        * { box-sizing: border-box; }
        input::placeholder { color: #ffffff33; }
      `}</style>
    </div>
  );
}
