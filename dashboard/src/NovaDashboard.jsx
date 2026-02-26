import { useState } from "react";
import { clamp, toFiniteNumber } from "./utils/numberGuards";
import { computeSemanticEntropy } from "./utils/entropy";
import { useNovaRealtime } from "./hooks/useNovaRealtime";
import { Theme } from "./theme";
import {
  Glow,
  StatusDot,
  MiniBar,
  AgentCard,
  ApprovalCard,
  CognitiveCycleRing,
  ConfidenceMeter,
  Sparkline,
  MemoryGraph,
  OrchestrationGraph,
} from "./components";

function toApiNumber(value, fallback = 0) {
  return toFiniteNumber(value, fallback);
}

/**
 * Nova Dashboard - SuperNova AI Agent Monitoring Interface
 * 
 * A production-grade dashboard for monitoring AI agent cognition,
 * memory systems, and decision intelligence in real-time.
 */
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
    modelFleet,
    semanticClusters,
    policy,
    memoryStats,
    sourceErrors,
    error: backendError,
    resolveApproval,
    sendAgentMessage,
  } = useNovaRealtime(isHalted);
  
  const [activeTab, setActiveTab] = useState("overview");
  const [isNovaTyping, setIsNovaTyping] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([
    {
      role: "nova",
      content: "Live mode active. Connected to SuperNova API.",
    },
  ]);

  const { entropy, confidence, clusters } = computeSemanticEntropy(semanticClusters);
  const bayesianConf = clamp(toApiNumber(bayesian.mean, 0), 0, 1);
  const ci = conformal.getInterval(decisionData.predicted);
  const blended = clamp(bayesianConf * 0.6 + confidence * 0.4, 0, 1);
  const proceedThreshold = policy.proceedThreshold;
  const monitorThreshold = policy.monitorThreshold;

  const handleDecide = async (id, approved) => {
    const approval = pendingApprovals.find((a) => a.id === id);
    try {
      await resolveApproval(id, approved);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        {
          role: "nova",
          content: `Approval request failed: ${err instanceof Error ? err.message : String(err)}`,
        },
      ]);
      return;
    }

    setChatHistory((prev) => [
      ...prev,
      {
        role: "nova",
        content: `Approval ${approved ? "approved ✓" : "denied ✕"} for ${approval?.tool || "tool"} and persisted to audit log.`,
      },
    ]);
  };

  const sendMessage = async () => {
    if (!chatInput.trim()) return;
    const msg = chatInput.trim();
    setChatInput("");
    setChatHistory((prev) => [...prev, { role: "user", content: msg }]);
    setIsNovaTyping(true);
    try {
      const result = await sendAgentMessage(msg);
      setChatHistory((prev) => [
        ...prev,
        {
          role: "nova",
          content: `Message accepted by live agent endpoint for session ${result.session_id} at ${result.received_at}.`,
        },
      ]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        {
          role: "nova",
          content: `Agent API error: ${err instanceof Error ? err.message : String(err)}`,
        },
      ]);
    } finally {
      setIsNovaTyping(false);
    }
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
        background: Theme.colors.bg,
        color: Theme.colors.text,
        fontFamily: Theme.fonts.main,
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
                  color: Theme.colors.bg,
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
                  border: `3px solid ${Theme.colors.bg}`,
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
            {(backendError || sourceErrors.length > 0) && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  background: "#fbbf2422",
                  border: "1px solid #fbbf2455",
                  borderRadius: 6,
                  padding: "4px 10px",
                  fontSize: 11,
                  color: "#fbbf24",
                }}
              >
                <span>⚠</span>
                {backendError
                  ? "backend degraded"
                  : `${sourceErrors.length} source warning${sourceErrors.length > 1 ? "s" : ""}`}
              </div>
            )}
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
            <button
              onClick={() => setIsHalted(!isHalted)}
              aria-label={isHalted ? "Resume cognitive cycle" : "Halt cognitive cycle"}
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
                  { label: "active sessions", value: metrics.activeSessions },
                  { label: "episodic nodes", value: metrics.episodicNodes },
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
              <ConfidenceMeter
                confidence={blended}
                entropy={entropy}
                proceedThreshold={proceedThreshold}
                monitorThreshold={monitorThreshold}
              />
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
                  {
                    label: "Episodic nodes",
                    value: memoryStats.episodicNodes,
                    color: "#a78bfa",
                  },
                  {
                    label: "Semantic facts",
                    value: memoryStats.semanticFacts,
                    color: "#fbbf24",
                  },
                  {
                    label: "Compiled skills",
                    value: memoryStats.compiledSkills,
                    color: "#00ffd5",
                  },
                  {
                    label: "Active sessions",
                    value: memoryStats.activeSessions,
                    color: "#6b7280",
                  },
                  {
                    label: "Snapshot errors",
                    value: sourceErrors.length,
                    color: "#38bdf8",
                  },
                  {
                    label: "Backend status",
                    value: backendError ? "degraded" : "healthy",
                    color: backendError ? "#f87171" : "#34d399",
                  },
                ].map(({ label, value, color }) => (
                  <div
                    key={label}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "6px 0",
                      borderBottom: "1px solid #ffffff08",
                    }}
                  >
                    <span style={{ fontSize: 11, color: "#ffffff55" }}>
                      {label}
                    </span>
                    <span
                      style={{
                        fontSize: 12,
                        color,
                        fontWeight: 700,
                        fontFamily: Theme.fonts.mono,
                      }}
                    >
                      {typeof value === "number" ? value.toLocaleString() : value}
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
          >
            <div
              style={{
                background: Theme.colors.surfaceLow,
                backdropFilter: Theme.glass.blur,
                border: `1px solid ${Theme.colors.border}`,
                borderRadius: 16,
                padding: 20,
                boxShadow: Theme.glass.shadow,
                textAlign: "center",
                color: Theme.colors.textMuted,
              }}
            >
              Decision history and detailed analytics coming in v2.0
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
