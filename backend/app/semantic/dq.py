"""Data-quality engine (RSD §6.6, FR-ADM-04): rules DQ-01..09 -> `dq_finding`, plus the weekly
mandatory-field completeness series behind the ≥95% go-live gate (AC-05).

A rule is data: an ID, what it catches, how the dashboard handles the record, and one or more
checks (SQL returning record_id, owner_upn, detail). Adding a rule means adding an entry here — the
ELT, console, export and tests all read this registry.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb

GATE_WEEKS = 2  # AC-05: complete for two consecutive weeks
HISTORY_WEEKS = 8
QUALIFIED_STAGES = ("Qualify", "Propose", "Orals", "Negotiate", "Closed Won", "Closed Lost")

# (key, label, SQL predicate on fact_opportunity alias f) — a qualified deal must have all of them.
MANDATORY_FIELDS: list[tuple[str, str, str]] = [
    ("offering", "Offering tag", "f.offering_class <> 'Untagged'"),
    ("lead_practice", "Lead practice", "coalesce(f.lead_practice, '') <> ''"),
    ("primary_platform", "Primary platform", "coalesce(f.primary_platform, '') <> ''"),
    ("lead_source", "Deal source", "coalesce(f.lead_source, '') <> ''"),
    ("owner", "Opportunity owner", "coalesce(f.owner_upn, '') <> ''"),
]


@dataclass(frozen=True)
class Check:
    record_type: str  # opportunity | account | bid_pursuit
    sql: str  # SELECT record_id, owner_upn, detail


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    description: str
    handling: str
    severity: str  # high | medium | low
    checks: tuple[Check, ...] = ()
    inactive_reason: str | None = None  # set when the source feeding the rule is not connected yet

    @property
    def active(self) -> bool:
        return self.inactive_reason is None


def _opp(predicate: str, detail: str) -> tuple[Check, ...]:
    return (
        Check(
            "opportunity",
            f"SELECT f.opportunity_id AS record_id, f.owner_upn, {detail} AS detail "
            f"FROM fact_opportunity f WHERE {predicate}",
        ),
    )


RULES: list[Rule] = [
    Rule(
        "DQ-01",
        "Untagged opportunity",
        "Open opportunity not tagged to an offering or Capability-led",
        "Counted in the Untagged bucket against EXE-05",
        "medium",
        _opp("f.stage_group = 'open' AND f.offering_class = 'Untagged'", "'No offering tag'"),
    ),
    Rule(
        "DQ-02",
        "Past-dated close date",
        "Open opportunity with a close date in the past",
        "Forced into EXE-10 Deals needing attention",
        "high",
        _opp("f.past_dated", "printf('Close date %s has passed', f.close_date)"),
    ),
    Rule(
        "DQ-03",
        "Missing loss reason",
        "Closed Lost opportunity with no loss reason",
        "Shown as Not recorded in PUR-02; the owner adds the reason in CRM",
        "low",
        _opp(
            "f.stage_group = 'lost' AND coalesce(trim(f.loss_reason), '') = ''",
            "'Closed Lost without a loss reason'",
        ),
    ),
    Rule(
        "DQ-04",
        "No valid CRM Opportunity ID",
        "Bid-tool pursuit with no matching CRM opportunity",
        "Excluded from Pursuits metrics; routed to the matching queue",
        "high",
        (
            Check(
                "bid_pursuit",
                """SELECT b.pursuit_id AS record_id, NULL AS owner_upn,
                          'Opportunity ID ' || b.opportunity_id || ' not found in CRM' AS detail
                   FROM raw_bid_pursuit b ANTI JOIN raw_crm_opportunity o USING (opportunity_id)""",
            ),
        ),
    ),
    Rule(
        "DQ-05",
        "Duplicate or orphan account",
        "Duplicate account name, or an opportunity whose account does not exist",
        "Flagged to the account owner; merge or re-parent the account in CRM",
        "medium",
        (
            Check(
                "account",
                """SELECT a.account_id AS record_id, a.client_partner_upn AS owner_upn,
                          'Duplicate account name: ' || a.name AS detail
                   FROM dim_account a
                   WHERE lower(trim(a.name)) IN
                         (SELECT lower(trim(name)) FROM dim_account GROUP BY 1 HAVING count(*) > 1)""",
            ),
            Check(
                "opportunity",
                """SELECT o.opportunity_id AS record_id, o.owner_upn,
                          'Account ' || o.account_id || ' not found' AS detail
                   FROM raw_crm_opportunity o ANTI JOIN raw_crm_account a USING (account_id)""",
            ),
        ),
    ),
    Rule(
        "DQ-06",
        "Non-USD amount",
        "Non-USD amount",
        "Converted at FY plan exchange rate; original kept",
        "low",
        _opp("f.original_currency <> 'USD'", "f.original_currency || ' amount converted at plan FX'"),
    ),
    Rule(
        "DQ-07",
        "Rep vs stage probability",
        "Rep-entered probability differs from stage probability",
        "Standard stage probability used for weighted metrics; rep value shown in drill-down",
        "low",
        _opp(
            "f.stage_group = 'open' AND abs(f.rep_probability - f.std_probability) > 0.001",
            "printf('Rep %d%% vs stage %d%%', CAST(round(f.rep_probability * 100) AS INTEGER), "
            "CAST(round(f.std_probability * 100) AS INTEGER))",
        ),
    ),
    Rule(
        "DQ-08",
        "AI-led without validation ID",
        "AI-led opportunity without a validation ID",
        "Flagged in the weekly alert when the deal is in Propose (FR-ALR-02); owner adds the ID in CRM",
        "high",
        _opp("f.ai_led AND coalesce(f.validation_id, '') = ''", "'AI-led, no validation ID'"),
    ),
    Rule(
        "DQ-09",
        "Released build item without Asset ID or type",
        "Released asset build item missing its Asset ID or asset type",
        "Excluded from asset-reuse metrics until the build tracker is corrected",
        "medium",
        (
            Check(
                "asset_build",
                """SELECT b.build_id AS record_id, NULL AS owner_upn,
                          'Released build item missing ' ||
                          CASE WHEN b.asset_id IS NULL AND b.asset_type IS NULL THEN 'Asset ID and type'
                               WHEN b.asset_id IS NULL THEN 'Asset ID' ELSE 'asset type' END AS detail
                   FROM raw_asset_build b
                   WHERE b.status = 'Released' AND (b.asset_id IS NULL OR b.asset_type IS NULL)""",
            ),
        ),
    ),
]
BY_ID = {r.rule_id: r for r in RULES}

FINDING_COLUMNS = """rule_id VARCHAR, description VARCHAR, handling VARCHAR, record_id VARCHAR,
                     owner_upn VARCHAR, detected_at TIMESTAMP, severity VARCHAR, record_type VARCHAR,
                     detail VARCHAR"""


def run_rules(conn: duckdb.DuckDBPyConnection) -> None:
    """Evaluate every active rule into `dq_finding` and build the weekly completeness series."""
    conn.execute(f"CREATE TABLE dq_finding ({FINDING_COLUMNS})")
    for rule in RULES:
        for check in rule.checks if rule.active else ():
            conn.execute(
                f"""INSERT INTO dq_finding
                    SELECT ?, ?, ?, c.record_id, c.owner_upn, (SELECT built_at FROM ref_run_context),
                           ?, ?, c.detail
                    FROM ({check.sql}) c""",
                [rule.rule_id, rule.description, rule.handling, rule.severity, check.record_type],
            )
    build_completeness(conn)


def complete_sql(alias: str = "f") -> str:
    return " AND ".join(p.replace("f.", f"{alias}.") for _, _, p in MANDATORY_FIELDS)


def build_completeness(conn: duckdb.DuckDBPyConnection) -> None:
    """Weekly completeness of qualified opportunities (Qualify or later) — the AC-05 gate input."""
    stages = ", ".join(f"'{s}'" for s in QUALIFIED_STAGES)
    conn.execute(f"""CREATE TABLE completeness_metric AS
            WITH qualified AS (
                SELECT opportunity_id, min(entered_date) AS qualified_date
                FROM fact_stage_history WHERE stage IN ({stages}) GROUP BY 1),
            weeks AS (
                SELECT CAST(date_trunc('week', c.as_of_date) - to_days(7 * i) AS DATE) AS week_start,
                       least(CAST(date_trunc('week', c.as_of_date) - to_days(7 * i) AS DATE) + 6,
                             c.as_of_date) AS week_end
                FROM range(0, {HISTORY_WEEKS}) t(i) CROSS JOIN ref_run_context c)
            SELECT w.week_start, w.week_end,
                   count(*) AS qualified,
                   count(*) FILTER (WHERE {complete_sql()}) AS complete
            FROM weeks w
            JOIN qualified q ON q.qualified_date <= w.week_end
            JOIN fact_opportunity f ON f.opportunity_id = q.opportunity_id
            GROUP BY w.week_start, w.week_end""")
