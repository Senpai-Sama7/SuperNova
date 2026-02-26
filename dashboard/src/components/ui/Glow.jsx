import { Theme } from "../../theme";

/**
 * Decorative glow effect for cards
 * @param {string} color - Glow color
 * @param {number} size - Glow size in pixels
 */
export const Glow = ({ color = Theme.colors.accent, size = 60 }) => (
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
