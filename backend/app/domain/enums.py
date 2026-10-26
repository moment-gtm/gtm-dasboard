"""Controlled vocabularies shared by every module (RSD 1.5, 6.4)."""

from __future__ import annotations

from enum import StrEnum


class Stage(StrEnum):
    IDENTIFY = "Identify"
    QUALIFY = "Qualify"
    PROPOSE = "Propose"
    ORALS = "Orals"
    NEGOTIATE = "Negotiate"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"
    NO_BID = "No Bid"
    CLIENT_CANCELLED = "Client Cancelled"


OPEN_STAGES: tuple[Stage, ...] = (
    Stage.IDENTIFY,
    Stage.QUALIFY,
    Stage.PROPOSE,
    Stage.ORALS,
    Stage.NEGOTIATE,
)
# Qualified pipeline = open at Qualify or later (RSD 1.5).
QUALIFIED_STAGES: tuple[Stage, ...] = (Stage.QUALIFY, Stage.PROPOSE, Stage.ORALS, Stage.NEGOTIATE)
COMMIT_STAGES: tuple[Stage, ...] = (Stage.ORALS, Stage.NEGOTIATE)
BEST_CASE_STAGES: tuple[Stage, ...] = (Stage.QUALIFY, Stage.PROPOSE)


class Status(StrEnum):
    ON_TRACK = "on_track"
    WATCH = "watch"
    OFF_TRACK = "off_track"


class OfferingClass(StrEnum):
    OFFERING_LED = "Offering-led"
    CAPABILITY_LED = "Capability-led"
    UNTAGGED = "Untagged"


class Role(StrEnum):
    GTM_LEAD = "gtm_lead"
    LEADERSHIP = "leadership"
    FINANCE = "finance"
    PRACTICE_LEAD = "practice_lead"
    CLIENT_PARTNER = "client_partner"
    ALLIANCE_MANAGER = "alliance_manager"
    MARKETING = "marketing"
    SALES_OPS = "sales_ops"
    SOLUTIONS_LEAD = "solutions_lead"


class Scope(StrEnum):
    """Row-level scope kinds (RSD 9 / Shared doc 5)."""

    ALL = "all"
    PRACTICE = "practice"  # own practice in full, others aggregated
    ACCOUNTS = "accounts"  # assigned accounts only
    PARTNER = "partner"  # partner-tagged opportunities
    CAMPAIGN = "campaign"  # campaign- or workshop-linked opportunities
