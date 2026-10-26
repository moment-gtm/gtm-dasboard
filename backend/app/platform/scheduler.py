"""APScheduler cadence per source (RSD 6.2; NFR-02 CRM fresh by 07:00 IST).

The prototype store is rebuilt in full from the mock extracts, so each job triggers a rebuild;
in production each job would run its own source's incremental ELT.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.platform.db import rebuild

log = logging.getLogger(__name__)
TZ = "Asia/Kolkata"

JOBS = [
    (
        "crm_daily",
        "SRC-01 CRM nightly delta (done by 07:00 IST)",
        CronTrigger(hour=5, minute=30, timezone=TZ),
    ),
    ("identity_nightly", "SRC-16 Entra ID groups", CronTrigger(hour=2, minute=0, timezone=TZ)),
    (
        "snapshot_weekly",
        "Weekly open-pipeline snapshot (Mon 00:00 IST)",
        CronTrigger(day_of_week="mon", hour=0, minute=0, timezone=TZ),
    ),
    (
        "finance_monthly",
        "SRC-04 Finance after period close",
        CronTrigger(day=3, hour=3, minute=0, timezone=TZ),
    ),
    (
        "planning_quarterly",
        "SRC-02 Planning targets",
        CronTrigger(month="1,4,7,10", day=1, hour=4, minute=0, timezone=TZ),
    ),
]


def _run(job_id: str) -> None:
    log.info("Scheduled ELT job %s starting", job_id)
    try:
        rebuild()
    except Exception:  # NFR-12: failure is logged and surfaced through /api/health
        log.exception("Scheduled ELT job %s failed", job_id)


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=TZ)
    for job_id, name, trigger in JOBS:
        scheduler.add_job(_run, trigger, args=[job_id], id=job_id, name=name, coalesce=True, max_instances=1)
    scheduler.start()
    return scheduler
