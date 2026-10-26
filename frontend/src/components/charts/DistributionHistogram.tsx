/**
 * DistributionHistogram — count per configurable band (bars), with value in the tooltip and a
 * count label on every bar so colour is never the only signal. Click selects a band. Data in only.
 */
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { tokens } from "@/theme/tokens";

export interface HistogramBand {
  key: string;
  label: string;
  count: number;
  value: number;
}

export function DistributionHistogram({
  bands,
  onSelect,
  formatValue,
  ariaLabel,
}: {
  bands: HistogramBand[];
  onSelect?: (key: string) => void;
  formatValue: (v: number) => string;
  ariaLabel: string;
}) {
  return (
    <div role="img" aria-label={ariaLabel} style={{ width: "100%", height: 260 }}>
      <ResponsiveContainer>
        <BarChart data={bands} margin={{ top: 20, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid vertical={false} stroke={tokens.grid} />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={{ stroke: tokens.axis }}
            tick={{ fontSize: 12, fill: tokens.ink.secondary }}
          />
          <YAxis
            allowDecimals={false}
            tickLine={false}
            axisLine={false}
            width={32}
            tick={{ fontSize: 12, fill: tokens.ink.muted }}
          />
          <Tooltip
            cursor={{ fill: "rgba(42,120,214,0.06)" }}
            content={({ active, payload }) => {
              const b = payload?.[0]?.payload as HistogramBand | undefined;
              if (!active || !b) return null;
              return (
                <div className="popover" style={{ padding: 8 }}>
                  <p className="m-0 font-semibold">{b.label}</p>
                  <p className="m-0">{b.count} deals</p>
                  <p className="m-0">{formatValue(b.value)} TCV</p>
                </div>
              );
            }}
          />
          <Bar
            dataKey="count"
            fill={tokens.ordinal.strong}
            radius={[4, 4, 0, 0]}
            maxBarSize={56}
            style={{ cursor: onSelect ? "pointer" : "default" }}
            onClick={(d: { payload?: HistogramBand }) => {
              if (d.payload) onSelect?.(d.payload.key);
            }}
          >
            <LabelList dataKey="count" position="top" style={{ fontSize: 12 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
