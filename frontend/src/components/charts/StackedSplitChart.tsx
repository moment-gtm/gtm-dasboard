/**
 * StackedSplitChart — horizontal bars per category, split into ordered parts (ordinal ramp,
 * 2px surface gap between segments). Clicking a segment selects (category, part). Data in only.
 */
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { tokens } from "@/theme/tokens";
import { formatMoney } from "@/utils/format";

export interface SplitPart {
  key: string;
  label: string;
}

const FILLS = [tokens.ordinal.strong, tokens.ordinal.light, tokens.ordinal.mid];

interface Row {
  category: string;
  [k: string]: number | string;
}

function SplitTooltip({
  active,
  payload,
  label,
  parts,
}: {
  active?: boolean;
  payload?: { dataKey: string; value: number }[];
  label?: string;
  parts: SplitPart[];
}) {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s, p) => s + (p.value ?? 0), 0);
  return (
    <div className="popover" style={{ padding: 8 }}>
      <p className="m-0 font-semibold">{label}</p>
      {parts.map((p) => {
        const v = payload.find((x) => x.dataKey === p.key)?.value ?? 0;
        return (
          <p key={p.key} className="m-0">
            {p.label}: {formatMoney(v)}
          </p>
        );
      })}
      <p className="m-0">Total: {formatMoney(total)}</p>
    </div>
  );
}

export function StackedSplitChart({
  data,
  parts,
  onSelect,
  ariaLabel,
}: {
  data: Row[];
  parts: SplitPart[];
  onSelect?: (category: string, part: string) => void;
  ariaLabel: string;
}) {
  const height = Math.max(160, data.length * 44 + 40);
  return (
    <div className="flex flex-col gap-2">
      <ul className="m-0 flex list-none flex-wrap gap-x-5 gap-y-1 p-0 text-sm">
        {parts.map((p, i) => (
          <li key={p.key} className="flex items-center gap-1.5">
            <span
              aria-hidden="true"
              style={{ width: 10, height: 10, borderRadius: 2, background: FILLS[i] }}
            />
            {p.label}
          </li>
        ))}
      </ul>
      <div role="img" aria-label={ariaLabel} style={{ width: "100%", height }}>
        <ResponsiveContainer>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 16, bottom: 4, left: 0 }}
          >
            <CartesianGrid horizontal={false} stroke={tokens.grid} />
            <XAxis
              type="number"
              tickFormatter={(v: number) => `$${Math.round(v / 1_000_000)}M`}
              tickLine={false}
              axisLine={{ stroke: tokens.axis }}
              tick={{ fontSize: 12, fill: tokens.ink.muted }}
            />
            <YAxis
              type="category"
              dataKey="category"
              width={150}
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 12, fill: tokens.ink.secondary }}
            />
            <Tooltip
              content={<SplitTooltip parts={parts} />}
              cursor={{ fill: "rgba(42,120,214,0.06)" }}
            />
            {parts.map((p, i) => (
              <Bar
                key={p.key}
                dataKey={p.key}
                name={p.label}
                stackId="split"
                fill={FILLS[i]}
                stroke={tokens.surface}
                strokeWidth={2}
                maxBarSize={24}
                radius={i === parts.length - 1 ? [0, 4, 4, 0] : 0}
                style={{ cursor: onSelect ? "pointer" : "default" }}
                onClick={(d: { payload?: Row }) => {
                  if (d.payload) onSelect?.(String(d.payload.category), p.key);
                }}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
