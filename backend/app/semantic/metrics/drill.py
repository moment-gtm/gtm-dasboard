"""Drill-down conditions for Offerings (OFF-*), Accounts (ACC-*), and Partners (PAR-*) metrics."""

from __future__ import annotations

from datetime import date

from app.data.reference_data import OFFERINGS, PARTNERS, PRACTICES
from app.semantic import helpers as h
from app.semantic.context import QueryContext
from app.semantic.metrics.exe import InvalidSegment
from app.semantic.metrics.off import STATE_SQL
from app.semantic.metrics.par import HAS_PARTNER, ROLE

OPEN_STAGES = ("Identify", "Qualify", "Propose", "Orals", "Negotiate")


def drill_condition(
    ctx: QueryContext, metric_id: str | None, segment: str | None
) -> tuple[str, list, str]:
    start = ctx.period.start
    end = min(ctx.period.end, ctx.today)
    seg = (segment or "").strip()

    if metric_id == "OFF-01":
        if not seg:
            raise InvalidSegment("OFF-01 drill requires segment '<offering>[|<open|won>]'")
        parts = seg.split("|", 1)
        offering = parts[0].strip()
        mode = parts[1].strip().lower() if len(parts) > 1 else "all"
        valid_offerings = {o["name"] for o in OFFERINGS} | {"Capability-led", "Untagged"}
        if offering not in valid_offerings:
            raise InvalidSegment(f"Unknown offering segment {offering!r} for OFF-01")
        if offering == "Untagged":
            off_sql, off_params = "o.offering_class = 'Untagged'", []
        else:
            off_sql, off_params = "o.offering = ?", [offering]

        if mode == "open":
            return f"{off_sql} AND o.stage_group = 'open'", off_params, f"{offering} — open pipeline"
        if mode == "won":
            return (
                f"{off_sql} AND o.stage_group = 'won' AND o.close_date BETWEEN ? AND ?",
                [*off_params, start, end],
                f"{offering} — won in period",
            )
        if mode == "all":
            return (
                f"{off_sql} AND (o.stage_group = 'open' "
                "OR (o.stage_group = 'won' AND o.close_date BETWEEN ? AND ?))",
                [*off_params, start, end],
                f"{offering} — open & won",
            )
        raise InvalidSegment(f"Unknown OFF-01 stage mode {mode!r}")

    if metric_id == "OFF-02":
        if seg in ("3+", "3_plus"):
            return (
                "o.stage_group = 'won' AND o.close_date BETWEEN ? AND ? AND "
                "(SELECT count(b.practice) FROM bridge_opportunity_practice b "
                "WHERE b.opportunity_id = o.opportunity_id) >= 3",
                [start, end],
                "Won deals with 3+ practices",
            )
        if "+" in seg:
            p1, p2 = [p.strip() for p in seg.split("+", 1)]
            if p1 not in PRACTICES or p2 not in PRACTICES:
                raise InvalidSegment(f"Unknown practice pair {segment!r} for OFF-02")
            return (
                "o.stage_group = 'won' AND o.close_date BETWEEN ? AND ? AND "
                "o.opportunity_id IN "
                "(SELECT opportunity_id FROM bridge_opportunity_practice WHERE practice = ?) AND "
                "o.opportunity_id IN "
                "(SELECT opportunity_id FROM bridge_opportunity_practice WHERE practice = ?)",
                [start, end, p1, p2],
                f"Won deals with {p1} + {p2}",
            )
        try:
            n_practices = int(seg)
        except ValueError as exc:
            raise InvalidSegment(
                f"OFF-02 drill requires integer practice count, got {segment!r}"
            ) from exc
        if n_practices < 1:
            raise InvalidSegment(f"OFF-02 practice count must be >= 1, got {n_practices}")
        return (
            "o.stage_group = 'won' AND o.close_date BETWEEN ? AND ? AND "
            "(SELECT count(b.practice) FROM bridge_opportunity_practice b "
            "WHERE b.opportunity_id = o.opportunity_id) = ?",
            [start, end, n_practices],
            f"Won deals with {n_practices} practice{'s' if n_practices > 1 else ''}",
        )

    if metric_id == "OFF-03":
        state_map = {
            "validated": "validated",
            "unvalidated": "unvalidated",
            "pending": "unvalidated",
            "not_ai_led": "not_ai_led",
        }
        norm_seg = state_map.get(seg.lower())
        if norm_seg is None:
            raise InvalidSegment(f"Unknown OFF-03 validation state {segment!r}")
        state_o2 = STATE_SQL.replace("o.", "o2.")
        return (
            "o.stage_group = 'open' AND o.opportunity_id IN ("
            "SELECT o2.opportunity_id FROM mart_opportunity o2 "
            "LEFT JOIN fact_validation v "
            "ON v.validation_id = o2.validation_id AND v.opportunity_id = o2.opportunity_id "
            f"WHERE ({state_o2}) = ?)",
            [norm_seg],
            f"Open pipeline — {norm_seg}",
        )

    if metric_id == "ACC-01":
        if "|" not in seg:
            raise InvalidSegment("ACC-01 drill requires '<account_id>|<practice>'")
        account_id, practice = [p.strip() for p in seg.split("|", 1)]
        if not account_id or practice not in PRACTICES:
            raise InvalidSegment(f"Invalid ACC-01 segment {segment!r}")
        fy_start = date(ctx.today.year, 1, 1)
        return (
            "o.account_id = ? AND "
            "((o.stage_group = 'won' AND o.close_date BETWEEN ? AND ?) OR o.stage_group = 'open') AND "
            "o.opportunity_id IN (SELECT opportunity_id FROM bridge_opportunity_practice WHERE practice = ?)",
            [account_id, fy_start, ctx.today, practice],
            f"{account_id} × {practice}",
        )

    if metric_id == "ACC-02":
        if seg not in PRACTICES:
            raise InvalidSegment(f"ACC-02 drill requires a valid practice, got {segment!r}")
        fy_start = date(ctx.today.year, 1, 1)
        return (
            "o.stage_group = 'open' AND "
            "o.opportunity_id IN "
            "(SELECT opportunity_id FROM bridge_opportunity_practice WHERE practice = ?) AND "
            "o.account_id NOT IN ("
            "  SELECT o2.account_id FROM mart_opportunity o2 "
            "  JOIN bridge_opportunity_practice b2 ON b2.opportunity_id = o2.opportunity_id "
            "  WHERE o2.stage_group = 'won' AND o2.close_date BETWEEN ? AND ? AND b2.practice = ?"
            ")",
            [seg, fy_start, ctx.today, seg],
            f"Whitespace pursuits — {seg}",
        )

    if metric_id == "ACC-03":
        w_start, w_end = start, end
        mode = seg
        if "|" in seg:
            q_str, mode = [p.strip() for p in seg.split("|", 1)]
            try:
                q_s, q_e = h.quarter_bounds(q_str)
            except Exception as exc:
                raise InvalidSegment(f"Invalid quarter in ACC-03 segment {segment!r}") from exc
            w_start, w_end = q_s, min(q_e, ctx.today)
        if mode not in {"expansion", "new_logo"}:
            raise InvalidSegment(f"ACC-03 drill requires 'expansion' or 'new_logo', got {segment!r}")
        exists_kw = "EXISTS" if mode == "expansion" else "NOT EXISTS"
        return (
            f"o.stage_group = 'won' AND o.close_date BETWEEN ? AND ? AND {exists_kw} ("
            "  SELECT 1 FROM fact_account_booking_history bh "
            "  WHERE bh.account_id = o.account_id "
            "    AND bh.booked_on < o.close_date "
            "    AND bh.booked_on >= o.close_date - INTERVAL 24 MONTH"
            ")",
            [w_start, w_end],
            "Expansion wins" if mode == "expansion" else "New logo wins",
        )

    if metric_id == "PAR-01":
        if not seg:
            raise InvalidSegment("PAR-01 drill requires '<partner>[|<sourced|influenced>]'")
        parts = seg.split("|", 1)
        partner = parts[0].strip()
        raw_mode = parts[1].strip() if len(parts) > 1 else "all"
        role_mode = raw_mode.lower()
        if partner not in PARTNERS:
            raise InvalidSegment(f"Unknown partner {partner!r} for PAR-01")
        if role_mode == "sourced":
            return (
                f"o.stage_group = 'open' AND o.partner = ? AND {ROLE} = 'Sourced'",
                [partner],
                f"{partner} — partner-sourced open pipeline",
            )
        if role_mode == "influenced":
            return (
                f"o.stage_group = 'open' AND o.partner = ? AND {ROLE} <> 'Sourced'",
                [partner],
                f"{partner} — partner-influenced open pipeline",
            )
        if raw_mode in OPEN_STAGES:
            return (
                "o.stage_group = 'open' AND o.partner = ? AND o.stage = ?",
                [partner, raw_mode],
                f"{partner} — {raw_mode} open pipeline",
            )
        if role_mode == "all":
            return (
                "o.stage_group = 'open' AND o.partner = ?",
                [partner],
                f"{partner} — open partner pipeline",
            )
        raise InvalidSegment(f"Unknown PAR-01 role mode {raw_mode!r}")

    if metric_id == "PAR-02":
        if not seg:
            raise InvalidSegment("PAR-02 drill requires '<with_partner|without_partner>[|<won|lost>]'")
        parts = seg.split("|", 1)
        group = parts[0].strip()
        outcome = parts[1].strip().lower() if len(parts) > 1 else "decided"
        if group == "with_partner":
            p_sql, p_args = HAS_PARTNER, []
        elif group in ("without_partner", "Direct"):
            p_sql, p_args = f"NOT {HAS_PARTNER}", []
        elif group in PARTNERS:
            p_sql, p_args = "o.partner = ?", [group]
        else:
            raise InvalidSegment(f"Unknown PAR-02 group {group!r}")

        if outcome == "won":
            stage_sql = "o.stage_group = 'won'"
        elif outcome == "lost":
            stage_sql = "o.stage_group = 'lost'"
        elif outcome in ("decided", "co_sell", "solo"):
            stage_sql = "o.stage_group IN ('won', 'lost')"
        else:
            raise InvalidSegment(f"Unknown PAR-02 outcome {outcome!r}")
        return (
            f"{stage_sql} AND o.close_date BETWEEN ? AND ? AND {p_sql}",
            [start, end, *p_args],
            f"Co-sell {group} ({outcome})",
        )

    raise InvalidSegment(f"No drill-down defined for {metric_id}")
