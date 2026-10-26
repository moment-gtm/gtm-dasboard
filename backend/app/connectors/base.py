"""Source connector contract.

Each source system (RSD 6.1) is read through a connector that returns records in the
*source's own shape* (Salesforce field names, Anaplan export columns, Graph JSON). The ELT
maps them into the raw zone. Swapping a mock connector for a real API client is the only
change needed to go from synthetic to real data — nothing downstream changes.
"""

from __future__ import annotations

from typing import Protocol


class SourceUnavailable(RuntimeError):
    """Raised when a source cannot be reached (drives FR-GEN-09 / FR-GEN-13 states)."""


class SourceConnector(Protocol):
    source_id: str  # RSD source id, e.g. "SRC-01"
    key: str  # short key used in config and health, e.g. "crm"

    def extract(self) -> dict[str, list[dict]]:
        """Return {source_object: [records]} for one full extract."""
        ...
