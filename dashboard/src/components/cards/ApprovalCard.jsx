import { Theme } from "../../theme";
import { Badge } from "../ui/Badge";
import { RiskPill } from "../ui/RiskPill";

/**
 * Human-in-the-loop approval request card
 * @param {Object} approval - Approval request data
 * @param {Function} onDecide - Callback for approve/deny decision
 */
export const ApprovalCard = ({ approval, onDecide }) => {
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
