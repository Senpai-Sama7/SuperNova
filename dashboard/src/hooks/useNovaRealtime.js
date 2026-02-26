import { useState, useEffect, useCallback } from "react";
import { clamp, toFiniteNumber } from "../utils/numberGuards";
import { API_BASE, POLL_INTERVAL_MS } from "../theme";

function toApiNumber(value, fallback = 0) {
  return toFiniteNumber(value, fallback);
}

/**
 * Custom hook for Nova Dashboard real-time data
 * @param {boolean} isHalted - Whether to pause polling
 * @returns {Object} Real-time dashboard data and methods
 */
export function useNovaRealtime(isHalted = false) {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/dashboard/snapshot`, {
        method: "GET",
        cache: "no-store",
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body?.detail || response.statusText);
      }
      setSnapshot(body);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (isHalted) return undefined;
    const interval = setInterval(() => {
      void refresh();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [isHalted, refresh]);

  const resolveApproval = useCallback(
    async (approvalId, approved) => {
      const response = await fetch(
        `${API_BASE}/api/v1/dashboard/approvals/${approvalId}/resolve`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ approved, actor: "dashboard-user" }),
        },
      );
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body?.detail || response.statusText);
      }
      await refresh();
      return body;
    },
    [refresh],
  );

  const sendAgentMessage = useCallback(async (message, sessionId = "dashboard-session") => {
    const response = await fetch(`${API_BASE}/api/v1/agent/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        actor: "dashboard-user",
      }),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body?.detail || response.statusText);
    }
    await refresh();
    return body;
  }, [refresh]);

  const stream = Array.isArray(snapshot?.stream)
    ? snapshot.stream.map((point, idx) => ({
        t: idx,
        actual: clamp(toApiNumber(point.actual, 0), 0, 1),
        predicted: clamp(toApiNumber(point.predicted, 0), 0, 1),
        regime: point.regime || "unknown",
        timestamp: point.timestamp || new Date().toISOString(),
      }))
    : [];

  const metrics = {
    totalCalls: toApiNumber(snapshot?.metrics?.total_calls, 0),
    successRate: clamp(toApiNumber(snapshot?.metrics?.success_rate, 0), 0, 1),
    avgLatency: Math.max(0, toApiNumber(snapshot?.metrics?.avg_latency_sec, 0)),
    cost: Math.max(0, toApiNumber(snapshot?.metrics?.cost_usd, 0)),
    skillsCompiled: toApiNumber(snapshot?.metrics?.skills_compiled, 0),
    memoriesConsolidated: toApiNumber(
      snapshot?.metrics?.memories_consolidated,
      0,
    ),
    activeSessions: toApiNumber(snapshot?.metrics?.active_sessions, 0),
    episodicNodes: toApiNumber(snapshot?.metrics?.episodic_nodes, 0),
  };

  const cognitiveLoop = {
    phase: snapshot?.cognitive_loop?.phase || "unknown",
    step: toApiNumber(snapshot?.cognitive_loop?.step, 0),
    phaseProgress: clamp(
      toApiNumber(snapshot?.cognitive_loop?.phase_progress, 0),
      0,
      1,
    ),
  };

  const decisionData = {
    actual: clamp(toApiNumber(snapshot?.decision?.actual, 0), 0, 1),
    predicted: clamp(toApiNumber(snapshot?.decision?.predicted, 0), 0, 1),
    regime: snapshot?.decision?.regime || "unknown",
  };

  const bayesian = {
    alpha: toApiNumber(snapshot?.bayesian?.alpha, 1),
    beta: toApiNumber(snapshot?.bayesian?.beta, 1),
    mean: clamp(toApiNumber(snapshot?.bayesian?.mean, 0), 0, 1),
    variance: Math.max(0, toApiNumber(snapshot?.bayesian?.variance, 0)),
  };

  const intervalLower = snapshot?.conformal?.interval_lower;
  const intervalUpper = snapshot?.conformal?.interval_upper;
  const conformal = {
    coverage: clamp(toApiNumber(snapshot?.conformal?.coverage, 0), 0, 1),
    getInterval(prediction) {
      const safePrediction = clamp(toApiNumber(prediction, 0), 0, 1);
      const lower = intervalLower === null || intervalLower === undefined
        ? safePrediction
        : clamp(toApiNumber(intervalLower, safePrediction), 0, 1);
      const upper = intervalUpper === null || intervalUpper === undefined
        ? safePrediction
        : clamp(toApiNumber(intervalUpper, safePrediction), 0, 1);
      return [lower, upper];
    },
  };

  const agents = Array.isArray(snapshot?.agents)
    ? snapshot.agents.map((agent) => ({
        id: agent.id,
        name: agent.name || agent.id,
        role: agent.role || "session",
        status: agent.status || "unknown",
        task: agent.task || "",
        load: toApiNumber(agent.load, 0),
        max: Math.max(1, toApiNumber(agent.max, 1)),
        success: clamp(toApiNumber(agent.success_rate, 0), 0, 1),
        latency: Math.max(0, toApiNumber(agent.latency_sec, 0)),
        model: agent.model || "unknown",
        memory_hits: toApiNumber(agent.memory_hits, 0),
        tools_called: toApiNumber(agent.tools_called, 0),
      }))
    : [];

  const memoryNodes = Array.isArray(snapshot?.memory_nodes)
    ? snapshot.memory_nodes.map((node) => ({
        id: node.id,
        label: node.label || node.id,
        type: node.type || "unknown",
        strength: clamp(toApiNumber(node.strength, 0), 0, 1),
        age: node.age || "unknown",
        x: toApiNumber(node.x, 50),
        y: toApiNumber(node.y, 50),
      }))
    : [];

  const pendingApprovals = Array.isArray(snapshot?.pending_approvals)
    ? snapshot.pending_approvals.map((approval) => ({
        id: approval.id,
        type: approval.tool,
        tool: approval.tool,
        risk: approval.risk || "unknown",
        agent: approval.agent || "unknown",
        args: approval.args || {},
        expires: Math.max(0, toApiNumber(approval.expires_seconds, 0)),
      }))
    : [];

  const memoryStats = {
    episodicNodes: toApiNumber(snapshot?.memory_stats?.episodic_nodes, 0),
    semanticFacts: toApiNumber(snapshot?.memory_stats?.semantic_facts, 0),
    compiledSkills: toApiNumber(snapshot?.memory_stats?.compiled_skills, 0),
    activeSessions: toApiNumber(snapshot?.memory_stats?.active_sessions, 0),
  };

  const modelFleet = Array.isArray(snapshot?.model_fleet) ? snapshot.model_fleet : [];
  const semanticClusters = Array.isArray(snapshot?.semantic_clusters)
    ? snapshot.semantic_clusters
    : [];

  const policy = {
    proceedThreshold: clamp(
      toApiNumber(snapshot?.policy?.proceed_threshold, 0.8),
      0,
      1,
    ),
    monitorThreshold: clamp(
      toApiNumber(snapshot?.policy?.monitor_threshold, 0.55),
      0,
      1,
    ),
  };

  return {
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
    sourceErrors: Array.isArray(snapshot?.source_errors) ? snapshot.source_errors : [],
    error,
    resolveApproval,
    sendAgentMessage,
  };
}
