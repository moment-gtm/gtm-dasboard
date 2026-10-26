/**
 * Module page frame: eyebrow, title, one-line description, actions, optional highlights strip
 * (e.g. a StatusSummary scorecard) and responsive content (RSD 10.1). The frame renders at the
 * module content density (`.module-content` → `--content-scale`), so every module scales alike.
 */
import type { ReactNode } from "react";

export function ModuleLayout({
  title,
  description,
  eyebrow,
  actions,
  highlights,
  children,
}: {
  title: string;
  description: string;
  eyebrow?: string;
  actions?: ReactNode;
  highlights?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="module-content mx-auto flex w-full max-w-[1600px] flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3 pt-4">
        <div className="min-w-0">
          {eyebrow ? <p className="eyebrow m-0 mb-1">{eyebrow}</p> : null}
          <h1
            className="m-0 text-2xl font-bold tracking-tight md:text-[28px]"
            style={{ color: "var(--nav)", lineHeight: 1.15 }}
          >
            {title}
          </h1>
          <p className="m-0 mt-1.5 max-w-3xl text-sm" style={{ color: "var(--ink-2)" }}>
            {description}
          </p>
        </div>
        {actions ? <div className="no-print flex items-center gap-2">{actions}</div> : null}
      </div>
      {highlights}
      {children}
    </div>
  );
}
