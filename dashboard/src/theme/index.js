// ─── Design System (Premium Aesthetic) ───────────────────────────────────────

export const Theme = {
  colors: {
    bg: "#050608",
    cardBg: "rgba(15, 18, 25, 0.7)",
    accent: "#00ffd5", // SuperNova Cyan
    secondary: "#a78bfa", // Mystic Purple
    warning: "#fbbf24", // Amber
    error: "#f87171", // Rose
    text: "#f8fafc",
    textMuted: "#94a3b8",
    glassBorder: "rgba(255, 255, 255, 0.08)",
    neonGlow: "0 0 15px rgba(0, 255, 213, 0.3)",
    info: "#38bdf8",
    success: "#34d399",
    border: "rgba(255, 255, 255, 0.08)",
    surfaceLow: "rgba(15, 18, 25, 0.7)",
    surfaceMid: "rgba(30, 35, 48, 0.5)",
  },
  fonts: {
    display: "'Space Grotesk', sans-serif",
    mono: "'JetBrains Mono', monospace",
    main: "'Space Grotesk', sans-serif",
  },
  glass: {
    backdropFilter: "blur(12px) saturate(180%)",
    backgroundColor: "rgba(15, 18, 25, 0.7)",
    border: "1px solid rgba(255, 255, 255, 0.08)",
    boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
    blur: "blur(12px) saturate(180%)",
  },
};

export const API_BASE = import.meta.env.VITE_SUPERNOVA_API_BASE || "http://127.0.0.1:8000";
export const POLL_INTERVAL_MS = 3000;

// Injecting Google Fonts dynamically
if (typeof document !== "undefined") {
  const link = document.createElement("link");
  link.href =
    "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap";
  link.rel = "stylesheet";
  document.head.appendChild(link);
}
