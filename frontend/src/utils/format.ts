/** Formatting helpers — currency is always $M to one decimal (RSD 10.1). */

export function formatMoney(usd: number | null | undefined): string {
  if (usd === null || usd === undefined || Number.isNaN(usd)) return "—";
  const m = usd / 1_000_000;
  const sign = m < 0 ? "-" : "";
  return `${sign}$${Math.abs(m).toFixed(1)}M`;
}

export function formatPct(ratio: number | null | undefined, dp = 1): string {
  if (ratio === null || ratio === undefined || Number.isNaN(ratio)) return "—";
  return `${(ratio * 100).toFixed(dp)}%`;
}

export function formatX(ratio: number | null | undefined): string {
  if (ratio === null || ratio === undefined || Number.isNaN(ratio)) return "—";
  return `${ratio.toFixed(1)}x`;
}

export function formatDays(days: number | null | undefined): string {
  if (days === null || days === undefined || Number.isNaN(days)) return "—";
  return `${Math.round(days)} days`;
}

export function formatCount(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toLocaleString("en-US");
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export type Unit = "usd" | "x" | "pct" | "days" | "count";

export function formatByUnit(value: number | null | undefined, unit: Unit): string {
  switch (unit) {
    case "usd":
      return formatMoney(value);
    case "x":
      return formatX(value);
    case "pct":
      return formatPct(value);
    case "days":
      return formatDays(value);
    default:
      return formatCount(value);
  }
}
