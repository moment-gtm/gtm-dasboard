/**
 * Design tokens — the ONLY place colours live (skill golden rule 10).
 * Placeholder accessible palette (dataviz reference instance) until Moment brand assets arrive
 * (Exec plan OQ-1). Ordinal blue steps validated with dataviz/scripts/validate_palette.js
 * (--ordinal, light surface #fcfcfb): ALL CHECKS PASS.
 *
 * Bento theme: chart colours are unchanged (they are validated against `surface`); the bento
 * layer only adds chrome — nav, hero/spotlight tiles, radii and elevation. Never draw chart
 * marks on `spotlight` (dark) tiles: they carry text, status badges and buttons only.
 */
export const tokens = {
  surface: "#fcfcfb",
  page: "#eef0ec",
  ink: {
    primary: "#0b0b0b",
    secondary: "#52514e",
    muted: "#6b6a65",
  },
  grid: "#e1e0d9",
  axis: "#c3c2b7",
  border: "rgba(11,11,11,0.10)",
  focus: "#2a78d6",
  /** Categorical slot order (fixed, never cycled). */
  series: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
  /** Ordinal ramp (one hue, light→dark); lightest step clears 2:1 on the surface. */
  ordinal: {
    strong: "#184f95", // booked / qualified
    mid: "#3987e5", // weighted commit
    light: "#86b6ef", // weighted best case / Identify
  },
  /** Status palette — reserved; always paired with icon + label (FR-GEN-05, NFR-08). */
  status: {
    on_track: { fill: "#0ca30c", text: "#006300", bg: "#e7f6e7" },
    watch: { fill: "#fab219", text: "#7a5200", bg: "#fff4dc" },
    off_track: { fill: "#d03b3b", text: "#a12626", bg: "#fbe9e9" },
  },
  /** Bento chrome (non-data). Text on `nav`/`spotlight` uses the paired ink (≥ 7:1). */
  bento: {
    nav: "#0d1b33",
    navInk: "#d5deee",
    navMuted: "#93a3c1",
    navActive: "rgba(134,182,239,0.16)",
    spotlight: "linear-gradient(135deg, #0d1b33 0%, #133a6e 60%, #184f95 100%)",
    spotlightInk: "#ffffff",
    spotlightMuted: "#c3d3ec",
    headerGlass: "rgba(238,240,236,0.85)",
    spotlightRow: "rgba(255,255,255,0.06)",
    spotlightStat: "rgba(255,255,255,0.08)",
    brandMark: "linear-gradient(135deg, #3987e5, #184f95)",
    heroWash: "linear-gradient(180deg, #e8f1fc 0%, rgba(232,241,252,0) 160px)",
    radius: 20,
    radiusInner: 14,
    /** Module content density from lg up (CSS `--content-scale`; 1 below lg); app chrome stays at 1. */
    contentScale: 0.8,
  },
  font: '"Segoe UI Variable", "Segoe UI", system-ui, -apple-system, sans-serif',
} as const;

export type StatusKey = keyof typeof tokens.status;
