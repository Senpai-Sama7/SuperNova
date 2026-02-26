import { Theme } from "../../theme";

/**
 * Styled badge component for labels
 * @param {string} label - Badge text
 * @param {string} color - Badge color
 */
export const Badge = ({ label, color = Theme.colors.accent }) => (
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
