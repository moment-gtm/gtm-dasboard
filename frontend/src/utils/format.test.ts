import { formatByUnit, formatDays, formatMoney, formatPct, formatX } from "./format";
import { filtersToParams, DEFAULT_FILTERS } from "@/state/filters";

describe("format", () => {
  it("formats money as $M to one decimal", () => {
    expect(formatMoney(1_234_567)).toBe("$1.2M");
    expect(formatMoney(0)).toBe("$0.0M");
    expect(formatMoney(-2_060_000)).toBe("-$2.1M");
    expect(formatMoney(null)).toBe("—");
  });
  it("formats pct, x and days", () => {
    expect(formatPct(0.384)).toBe("38.4%");
    expect(formatX(2.71)).toBe("2.7x");
    expect(formatDays(119.6)).toBe("120 days");
    expect(formatByUnit(3.04, "x")).toBe("3.0x");
  });
});

describe("filtersToParams", () => {
  it("repeats multi-value keys and drops unused period params", () => {
    const p = filtersToParams({
      ...DEFAULT_FILTERS,
      vertical: ["BFSI", "Retail & CPG"],
      quarter: "2026-Q1",
    });
    expect(p.getAll("vertical")).toEqual(["BFSI", "Retail & CPG"]);
    expect(p.get("period")).toBe("fytd");
    expect(p.has("quarter")).toBe(false);
  });
});
