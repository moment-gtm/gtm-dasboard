"""Row-level security (RSD §9, NFR-05). Every query, drill-down and export goes through here.

Users are resolved from Entra ID group membership (SRC-16, mocked): the group gives the role
and scope value, CRM account assignment gives a client partner's accounts.

Two predicates per user:
- `row`: rows that may feed any aggregate.
- `detail`: rows that may be shown individually (drill-down, lists, row exports). For a
  practice lead, other practices are visible only as aggregates (RSD §4 personas).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.data import reference_data as ref
from app.domain.enums import Role, Scope
from app.domain.models import User
from app.platform.db import Platform

ROLE_DEFS = {r["role"]: r for r in ref.ROLES}


class UnknownRole(LookupError):
    pass


def resolve_user(platform: Platform, identifier: str) -> User:
    """Mock SSO: identifier can be an Entra UPN or a role string."""
    persona = None
    role_enum = None
    cleaned = identifier.strip().lower()

    # 1. Try matching by UPN in PERSONA_USERS
    persona = next((p for p in ref.PERSONA_USERS if p["upn"].lower() == cleaned), None)
    if persona:
        role_enum = persona["role"]
    else:
        # Check CLIENT_PARTNERS
        cp = next((c for c in ref.CLIENT_PARTNERS if c["upn"].lower() == cleaned), None)
        if cp:
            persona = {"upn": cp["upn"], "name": cp["name"], "role": Role.CLIENT_PARTNER}
            role_enum = Role.CLIENT_PARTNER

    # 2. If not a UPN, resolve as a Role enum
    if not persona:
        try:
            role_enum = Role(cleaned)
        except ValueError as exc:
            raise UnknownRole(f"Unknown role or persona '{identifier}'") from exc
        persona = next((p for p in ref.PERSONA_USERS if p["role"] == role_enum), None)
        if not persona:
            raise UnknownRole(f"No persona found for role '{identifier}'")

    groups = platform.query(
        """SELECT g.role, g.scope_value FROM raw_identity_user u
           JOIN raw_identity_group_membership m ON m.user_id = u.user_id
           JOIN raw_identity_group g ON g.group_id = m.group_id
           WHERE u.upn = ? AND g.role = ?""",
        [persona["upn"], role_enum.value],
    )
    rd = ROLE_DEFS[role_enum]
    if not groups:
        # Identity source not loaded / user not in group: no access beyond nothing.
        return User(
            upn=persona["upn"],
            name=persona["name"],
            role=role_enum,
            role_label=rd["label"],
            scope=Scope.ACCOUNTS,
            modules=(),
            restricted=False,
        )
    scope_value = groups[0]["scope_value"]
    accounts: tuple[str, ...] = ()
    if rd["scope"] == Scope.ACCOUNTS:
        accounts = tuple(
            r["account_id"]
            for r in platform.query(
                "SELECT account_id FROM dim_account WHERE client_partner_upn = ? ORDER BY 1", [persona["upn"]]
            )
        )
    return User(
        upn=persona["upn"],
        name=persona["name"],
        role=role_enum,
        role_label=rd["label"],
        scope=rd["scope"],
        modules=tuple(rd["modules"]),
        restricted=rd["restricted"],
        practice=scope_value if rd["scope"] == Scope.PRACTICE else None,
        partner=scope_value if rd["scope"] == Scope.PARTNER else None,
        accounts=accounts,
    )


@dataclass(frozen=True)
class RowScope:
    row_sql: str
    row_args: tuple
    detail_sql: str
    detail_args: tuple
    description: str

    @property
    def narrows_rows(self) -> bool:
        return self.row_sql != "TRUE"

    @property
    def has_detail_limit(self) -> bool:
        return self.detail_sql != "TRUE"


def scope_for(user: User, alias: str = "o") -> RowScope:
    a = alias
    if user.scope == Scope.ALL:
        return RowScope("TRUE", (), "TRUE", (), "All data")
    if user.scope == Scope.PRACTICE:
        return RowScope(
            "TRUE",
            (),
            f"{a}.lead_practice = ?",
            (user.practice,),
            f"{user.practice} practice in full; other practices aggregated",
        )
    if user.scope == Scope.ACCOUNTS:
        if not user.accounts:
            return RowScope("FALSE", (), "FALSE", (), "No assigned accounts")
        marks = ", ".join("?" * len(user.accounts))
        sql = f"{a}.account_id IN ({marks})"
        return RowScope(sql, user.accounts, sql, user.accounts, f"{len(user.accounts)} assigned accounts")
    if user.scope == Scope.PARTNER:
        sql = f"{a}.partner = ?"
        return RowScope(
            sql, (user.partner,), sql, (user.partner,), f"{user.partner} partner-tagged opportunities"
        )
    if user.scope == Scope.CAMPAIGN:
        sql = f"({a}.campaign_id IS NOT NULL OR {a}.workshop_originated)"
        return RowScope(sql, (), sql, (), "Campaign- or workshop-linked opportunities")
    return RowScope("FALSE", (), "FALSE", (), "No access")


def describe(user: User) -> str:
    return scope_for(user).description
