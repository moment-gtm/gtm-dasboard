/**
 * GoalBarChart — one series of columns vs a per-category goal marker. Met / missed / QTD /
 * upcoming are spelled out under each tick (never colour alone). Data in only.
 */
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { tokens } from "@/theme/tokens";
import { formatMoney } from "@/utils/format";

export interface GoalBarDatum {
  key: string;
  label: string;
  value: number | null;
  goal: number | null;
  /** Tag shown under the tick, e.g. "Met", "Missed", "QTD", "Upcoming". */
  tag: string;
  tagTone?: "good" | "bad" | "neutral";
}

const TONE = {
  good: tokens.status.on_track.text,
  bad: tokens.status.off_track.text,
  neutral: tokens.ink.secondary,
};
const TAG_ICON: Record<string, string> = { good: "✓ ", bad: "✕ ", neutral: "" };

function GoalTick(props: {
  x?: number;
  y?: number;
  payload?: { value: string };
  data: GoalBarDatum[];
}) {
  const { x = 0, y = 0, payload, data } = props;
  const d = data.find((r) => r.key === payload?.value);
  if (!d) return null;
  const tone = d.tagTone ?? "neutral";
  return (
    <g transform={`translate(${x},${y})`}>
      <text dy={14} textAnchor="middle" fontSize={12} fill={tokens.ink.secondary}>
        {d.label}
      </text>
      <text dy={30} textAnchor="middle" fontSize={12} fontWeight={600} fill={TONE[tone]}>
        {TAG_ICON[tone]}
        {d.tag}
      </text>
    </g>
  );
}

function GoalMarker(props: { cx?: number; cy?: number }) {
  const { cx, cy } = props;
  if (cx == null || cy == null) return null;
  return <rect x={cx - 18} y={cy - 1} width={36} height={2.5} fill={tokens.ink.primary} rx={1} />;
}

interface TooltipPayload {
  payload: GoalBarDatum;
}

function GoalTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayload[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="popover" style={{ padding: 8 }}>
      <p className="m-0 font-semibold">{d.label}</p>
      <p className="m-0">Bookings: {formatMoney(d.value)}</p>
      <p className="m-0">Target: {formatMoney(d.goal)}</p>
      <p className="m-0">{d.tag}</p>
    </div>
  );
}

export function GoalBarChart({
  data,
  valueLabel,
  goalLabel,
  onSelect,
  height = 260,
}: {
  data: GoalBarDatum[];
  valueLabel: string;
  goalLabel: string;
  onSelect?: (key: string) => void;
  height?: number;
}) {
  const summary = data
    .map((d) => `${d.label}: ${formatMoney(d.value)} vs ${formatMoney(d.goal)} (${d.tag})`)
    .join("; ");
  return (
    <div className="flex flex-col gap-2">
      <div
        role="img"
        aria-label={`${valueLabel} vs ${goalLabel}. ${summary}`}
        style={{ width: "100%", height }}
      >
        {/* The wrapper's aria-label carries every value; Recharts' own role="img" symbols are
            unnamed, so the SVG is hidden from assistive tech (keyboard drill: ChartTable). */}
        <div aria-hidden="true" style={{ width: "100%", height: "100%" }}>
          <ResponsiveContainer>
            <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 24, left: 0 }}>
              <CartesianGrid vertical={false} stroke={tokens.grid} />
              <XAxis
                dataKey="key"
                interval={0}
                tickLine={false}
                axisLine={{ stroke: tokens.axis }}
                tick={<GoalTick data={data} />}
                height={44}
              />
              <YAxis
                tickFormatter={(v: number) => `$${Math.round(v / 1_000_000)}M`}
                tickLine={false}
                axisLine={false}
                width={52}
                tick={{ fontSize: 12, fill: tokens.ink.muted }}
              />
              <Tooltip content={<GoalTooltip />} cursor={{ fill: "rgba(42,120,214,0.06)" }} />
              <Bar
                dataKey="value"
                name={valueLabel}
                maxBarSize={24}
                radius={[4, 4, 0, 0]}
                onClick={(d: { key?: string; payload?: GoalBarDatum }) => {
                  const key = d.payload?.key ?? d.key;
                  if (key) onSelect?.(key);
                }}
                style={{ cursor: onSelect ? "pointer" : "default" }}
              >
                {data.map((d) => (
                  <Cell key={d.key} fill={tokens.series[0]} />
                ))}
              </Bar>
              <Scatter
                dataKey="goal"
                name={goalLabel}
                shape={<GoalMarker />}
                isAnimationActive={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
      <ul className="m-0 flex list-none flex-wrap gap-x-5 gap-y-1 p-0 text-sm" aria-hidden="true">
        <li className="flex items-center gap-1.5">
          <span style={{ width: 10, height: 10, borderRadius: 2, background: tokens.series[0] }} />
          {valueLabel}
        </li>
        <li className="flex items-center gap-1.5">
          <span style={{ width: 16, height: 2.5, background: tokens.ink.primary }} />
          {goalLabel}
        </li>
      </ul>
    </div>
  );
}
