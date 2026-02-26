import { Theme } from "../../theme";

/**
 * Status indicator dot with glow
 * @param {string} status - active | reasoning | waiting | idle | error
 */
export const StatusDot = ({ status }) => {
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
