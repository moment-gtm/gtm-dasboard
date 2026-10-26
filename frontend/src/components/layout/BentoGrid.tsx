/**
 * Bento layout: a 12-column grid (1 column below lg) whose items span a fixed set of widths.
 * Modules arrange their widgets with BentoItem instead of ad-hoc grids so every module shares
 * one rhythm. Class names are literal so Tailwind can see them.
 */
import type { ReactNode } from "react";

export type BentoSpan = 3 | 4 | 5 | 6 | 7 | 8 | 12;

const SPAN: Record<BentoSpan, string> = {
  3: "lg:col-span-6 xl:col-span-3",
  4: "lg:col-span-6 xl:col-span-4",
  5: "lg:col-span-5",
  6: "lg:col-span-6",
  7: "lg:col-span-7",
  8: "lg:col-span-12 xl:col-span-8",
  12: "lg:col-span-12",
};

export function BentoGrid({ children, testId }: { children: ReactNode; testId?: string }) {
  return (
    <div data-testid={testId} className="grid grid-cols-1 gap-4 md:gap-5 lg:grid-cols-12">
      {children}
    </div>
  );
}

/**
 * A full-width row inside BentoGrid with its own 12-column track. Use it to pair a hero with a
 * sticky spotlight: a sticky element is confined to its parent, so inside a BentoRow the
 * spotlight pins only while the hero scrolls and stops at the hero's bottom edge, instead of
 * sliding over every widget below.
 */
export function BentoRow({ children }: { children: ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:gap-5 lg:col-span-12 lg:grid-cols-12">{children}</div>
  );
}

/**
 * `sticky`: keep the tile at its natural height and pin it below the app header while a taller
 * neighbour scrolls (use for spotlights beside a tall hero). Must sit inside a `BentoRow` with
 * that neighbour, or it will pin across the whole grid and overlap the rows below.
 * Otherwise the tile fills its row. The pin offset is divided by `--content-scale` so it still
 * clears the (unscaled) header when module content is zoomed.
 */
export function BentoItem({
  span = 12,
  id,
  sticky = false,
  children,
}: {
  span?: BentoSpan;
  id?: string;
  sticky?: boolean;
  children: ReactNode;
}) {
  const fit = sticky
    ? "lg:sticky lg:top-[calc(6rem/var(--content-scale,1))] lg:self-start"
    : "*:flex-1";
  return (
    <div id={id} className={`flex min-w-0 flex-col ${fit} ${SPAN[span]}`}>
      {children}
    </div>
  );
}
