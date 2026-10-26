/** Money — $M to one decimal; every currency value in the UI goes through here (RSD 10.1). */
import { formatByUnit, formatMoney, type Unit } from "@/utils/format";

export function Money({
  value,
  className,
}: {
  value: number | null | undefined;
  className?: string;
}) {
  return (
    <span
      className={className}
      title={value != null ? `$${Math.round(value).toLocaleString("en-US")}` : undefined}
    >
      {formatMoney(value)}
    </span>
  );
}

export function UnitValue({
  value,
  unit,
  className,
}: {
  value: number | null | undefined;
  unit: Unit;
  className?: string;
}) {
  if (unit === "usd") return <Money value={value} className={className} />;
  return <span className={className}>{formatByUnit(value, unit)}</span>;
}
