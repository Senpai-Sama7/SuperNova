import { Theme } from "../../theme";
import { Badge } from "./Badge";

/**
 * Risk level indicator pill
 * @param {string} risk - low | medium | high | critical
 */
export const RiskPill = ({ risk }) => {
  const map = {
    low: [Theme.colors.accent, "LOW"],
    medium: [Theme.colors.warning, "MED"],
    high: [Theme.colors.error, "HIGH"],
    critical: [Theme.colors.secondary, "CRIT"],
  };
  const [color, label] = map[risk] || [Theme.colors.textMuted, "?"];
  return <Badge label={label} color={color} />;
};
