import { Theme } from "../../theme";

/**
 * Mini progress bar component
 * @param {number} value - Current value
 * @param {number} max - Maximum value
 * @param {string} color - Bar color
 * @param {number} width - Bar width in pixels
 */
export const MiniBar = ({ value, max, color = Theme.colors.accent, width = 80 }) => (
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
