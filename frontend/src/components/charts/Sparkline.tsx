/** Sparkline — 2px line, end dot, partial (QTD) point drawn hollow. Data in only. */
import type { SparkPoint } from "@/api/types";
import { tokens } from "@/theme/tokens";

export function Sparkline({
  points,
  format,
  width = 120,
  height = 32,
}: {
  points: SparkPoint[];
  format: (v: number | null) => string;
  width?: number;
  height?: number;
}) {
  const vals = points.map((p) => p.value).filter((v): v is number => v != null);
  if (vals.length < 2) return null;
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const pad = 5;
  const span = max - min || 1;
  const x = (i: number) => pad + (i * (width - pad * 2)) / Math.max(1, points.length - 1);
  const y = (v: number) => height - pad - ((v - min) / span) * (height - pad * 2);
  const coords = points.map((p, i) => (p.value == null ? null : ([x(i), y(p.value)] as const)));
  const d = coords
    .filter((c): c is readonly [number, number] => c !== null)
    .map((c, i) => `${i ? "L" : "M"}${c[0].toFixed(1)},${c[1].toFixed(1)}`)
    .join(" ");
  const summary = points
    .map((p) => `${p.label}${p.partial ? " (QTD)" : ""}: ${format(p.value)}`)
    .join("; ");
  return (
    <svg
      width={width}
      height={height}
      role="img"
      aria-label={`Four-quarter trend. ${summary}`}
      data-testid="sparkline"
    >
      <title>{summary}</title>
      <path
        d={d}
        fill="none"
        stroke={tokens.series[0]}
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {coords.map((c, i) =>
        c && (i === coords.length - 1 || points[i].partial) ? (
          <circle
            key={i}
            cx={c[0]}
            cy={c[1]}
            r={4}
            fill={points[i].partial ? tokens.surface : tokens.series[0]}
            stroke={points[i].partial ? tokens.series[0] : tokens.surface}
            strokeWidth={2}
          />
        ) : null,
      )}
    </svg>
  );
}
