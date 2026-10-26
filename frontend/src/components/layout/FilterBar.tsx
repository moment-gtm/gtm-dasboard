/** Global filter bar (FR-GEN-02/03): period + core dims, plus "More filters"; session-persisted. */
import * as Popover from "@radix-ui/react-popover";
import { useState } from "react";
import type { Option } from "@/api/types";
import { useFilterOptions } from "@/hooks/useReference";
import {
  activeFilterCount,
  useFilterStore,
  useFilters,
  type MultiKey,
  type PeriodKind,
} from "@/state/filters";

function MultiSelect({
  label,
  filterKey,
  options,
}: {
  label: string;
  filterKey: MultiKey;
  options: Option[];
}) {
  const selected = useFilterStore((s) => s[filterKey]);
  const setMulti = useFilterStore((s) => s.setMulti);
  const toggle = (v: string) =>
    setMulti(filterKey, selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v]);
  const summary =
    selected.length === 0
      ? "All"
      : selected.length === 1
        ? (options.find((o) => o.value === selected[0])?.label ?? selected[0])
        : `${selected.length} selected`;
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          className="btn"
          data-testid={`filter-${filterKey}`}
          aria-label={`${label}: ${summary}`}
        >
          <span style={{ color: "var(--ink-2)" }}>{label}:</span>
          <span className="max-w-36 truncate font-medium">{summary}</span>
          <span aria-hidden="true">▾</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className="popover"
          sideOffset={4}
          align="start"
          style={{ maxHeight: 320, overflowY: "auto", minWidth: 220 }}
        >
          <fieldset className="m-0 flex flex-col gap-1 border-0 p-0">
            <legend className="mb-1 text-xs font-semibold" style={{ color: "var(--ink-2)" }}>
              {label}
            </legend>
            {options.map((o) => (
              <label
                key={o.value}
                className="flex cursor-pointer items-center gap-2 rounded px-1 py-0.5"
              >
                <input
                  type="checkbox"
                  checked={selected.includes(o.value)}
                  onChange={() => toggle(o.value)}
                  data-testid={`filter-option-${filterKey}-${o.value}`}
                />
                {o.label}
              </label>
            ))}
            {selected.length ? (
              <button type="button" className="btn mt-1" onClick={() => setMulti(filterKey, [])}>
                Clear {label.toLowerCase()}
              </button>
            ) : null}
          </fieldset>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

export function FilterBar() {
  const opts = useFilterOptions();
  const filters = useFilters();
  const setPeriod = useFilterStore((s) => s.setPeriod);
  const clearAll = useFilterStore((s) => s.clearAll);
  const [more, setMore] = useState(
    () =>
      filters.account.length +
        filters.client_partner.length +
        filters.deal_source.length +
        filters.geography.length >
      0,
  );
  const o = opts.data;
  const count = activeFilterCount(filters);

  return (
    <div
      role="search"
      aria-label="Global filters"
      data-testid="filter-bar"
      className="card mx-3 mt-3 flex flex-wrap items-center gap-2 px-3 py-2 md:mx-6"
      style={{ borderRadius: 16 }}
    >
      <span className="eyebrow hidden pr-1 sm:inline" aria-hidden="true">
        Filters
      </span>
      <label className="flex items-center gap-1 text-sm">
        <span style={{ color: "var(--ink-2)" }}>Period</span>
        <select
          data-testid="filter-period"
          className="btn"
          value={filters.period}
          onChange={(e) => {
            const p = e.target.value as PeriodKind;
            setPeriod(p, p === "quarter" ? { quarter: o?.current_quarter ?? null } : {});
          }}
        >
          {(
            o?.periods ?? [
              { value: "fytd", label: "Fiscal year to date" },
              { value: "quarter", label: "Quarter" },
              { value: "qtd", label: "Current quarter to date" },
              { value: "custom", label: "Custom range" },
            ]
          ).map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </label>
      {filters.period === "quarter" ? (
        <label className="flex items-center gap-1 text-sm">
          <span className="sr-only">Quarter</span>
          <select
            data-testid="filter-quarter"
            className="btn"
            value={filters.quarter ?? o?.current_quarter ?? ""}
            onChange={(e) => setPeriod("quarter", { quarter: e.target.value })}
          >
            {(o?.quarters ?? []).map((q) => (
              <option key={q.value} value={q.value}>
                {q.label}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {filters.period === "custom" ? (
        <span className="flex items-center gap-1 text-sm">
          <label className="flex items-center gap-1">
            <span style={{ color: "var(--ink-2)" }}>From</span>
            <input
              type="date"
              className="btn"
              data-testid="filter-start"
              value={filters.start ?? ""}
              onChange={(e) => setPeriod("custom", { start: e.target.value, end: filters.end })}
            />
          </label>
          <label className="flex items-center gap-1">
            <span style={{ color: "var(--ink-2)" }}>to</span>
            <input
              type="date"
              className="btn"
              data-testid="filter-end"
              value={filters.end ?? ""}
              onChange={(e) => setPeriod("custom", { start: filters.start, end: e.target.value })}
            />
          </label>
        </span>
      ) : null}
      <MultiSelect label="Vertical" filterKey="vertical" options={o?.verticals ?? []} />
      <MultiSelect label="Practice" filterKey="practice" options={o?.practices ?? []} />
      <MultiSelect label="Platform" filterKey="platform" options={o?.platforms ?? []} />
      <button
        type="button"
        className="btn btn-ghost"
        aria-expanded={more}
        onClick={() => setMore((m) => !m)}
        data-testid="filter-more"
      >
        {more ? "Fewer filters" : "More filters"}
      </button>
      {more ? (
        <>
          <MultiSelect label="Account" filterKey="account" options={o?.accounts ?? []} />
          <MultiSelect
            label="Client partner"
            filterKey="client_partner"
            options={o?.client_partners ?? []}
          />
          <MultiSelect
            label="Deal source"
            filterKey="deal_source"
            options={o?.deal_sources ?? []}
          />
          <MultiSelect label="Geography" filterKey="geography" options={o?.geographies ?? []} />
        </>
      ) : null}
      <span className="ml-auto flex items-center gap-2 text-sm">
        <span data-testid="filter-count" style={{ color: "var(--ink-2)" }} aria-live="polite">
          {count === 0 ? "No filters applied" : `${count} filter${count > 1 ? "s" : ""} applied`}
        </span>
        {count > 0 ? (
          <button type="button" className="btn" onClick={clearAll} data-testid="filter-clear">
            Clear all
          </button>
        ) : null}
      </span>
    </div>
  );
}
