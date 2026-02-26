import { Theme } from "../../theme";
import { StatusDot } from "../ui/StatusDot";
import { MiniBar } from "../ui/MiniBar";

/**
 * Agent information card component
 * @param {Object} agent - Agent data object
 */
export const AgentCard = ({ agent }) => {
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
