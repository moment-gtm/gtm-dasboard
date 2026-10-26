"""Domain entities used across layers (RSD 7.2 core logical entities)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import Role, Scope


@dataclass(frozen=True)
class User:
    """The caller, resolved from Entra ID group membership (SRC-16; mocked in the prototype)."""

    upn: str
    name: str
    role: Role
    role_label: str
    scope: Scope
    modules: tuple[str, ...]
    restricted: bool
    # Scope parameters — only the one matching `scope` is populated.
    practice: str | None = None
    accounts: tuple[str, ...] = field(default_factory=tuple)
    partner: str | None = None

    def can_access(self, module: str) -> bool:
        return module in self.modules
