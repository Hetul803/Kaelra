"""In-app routine scheduler (APScheduler).

Kaelra is proactive: routines fire on schedule and PREPARE work (notifications +
Apction Queue items) before the user asks. We tick every minute, evaluate each
user's enabled routines, and fire those whose time has arrived (idempotent per
day via last_fired). Routines can also be fired on demand ("run now").

Deterministic by design — only the morning-briefing routine invokes the LLM
(once/day) so the scheduler stays cheap and reliable. Real push can be layered
on later; today we create in-app notifications.
"""

from __future__ import annotations

import logging
import re
import datetime as dt

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import get_db
from utils import new_id, now_iso, today_str
from services.audit import log_event
from services.actions import create_actions

logger = logging.getLogger("kaelra.scheduler")
_scheduler: AsyncIOScheduler | None = None


def _parse_hhmm(text: str) -> tuple[int, int] | None:
    if not text:
        return None
    m = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?", text.lower())
    if not m:
        return None
    h, mn = int(m.group(1)), int(m.group(2))
    ap = m.group(3)
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    return h, mn


async def _record_run(user_id: str, routine: dict, result: dict):
    db = get_db()
    await db.skill_runs.insert_one({
        "id": new_id(), "user_id": user_id, "skill": "routine",
        "routine_id": routine.get("id"), "routine_name": routine.get("name"),
        "result": result, "created_at": now_iso(),
    })


async def _notify(user_id: str, title: str, body: str, ntype: str = "reminder", scheduled_for: str | None = None):
    from services.notify import notify
    await notify(user_id, title, body, ntype, scheduled_for=scheduled_for, url="/")


async def fire_routine(user_id: str, routine: dict, user: dict | None = None) -> dict:
    """Execute one routine now. Returns a small result summary."""
    db = get_db()
    rtype = routine.get("type", "general")
    name = routine.get("name", "Routine")
    summary = {"type": rtype, "notifications": 0, "actions": 0}

    if rtype == "briefing":
        try:
            from services.briefing import generate
            u = user or await db.users.find_one({"id": user_id})
            if u:
                b = await generate(u, force=True)
                await _notify(user_id, "Your morning briefing is ready",
                              (b.get("greeting") or "")[:160], "briefing")
                summary["notifications"] = 1
                summary["actions"] = b.get("actions_prepared", 0)
        except Exception as e:  # noqa: BLE001
            logger.warning("briefing routine failed: %s", e)

    elif rtype == "commute":
        await _notify(user_id, "Leave-time reminder",
                      "Based on your next event and commute, Kaelra will remind you when to leave.", "reminder")
        acts = await create_actions(user_id, [{
            "type": "commute_alert", "title": "Leave on time for your next event",
            "what": "Prepared a leave-time reminder from your calendar + commute.",
            "why": "So you arrive without rushing.", "source": "Routine: " + name, "sensitive": False,
        }], origin="routine")
        summary["notifications"] = 1
        summary["actions"] = len(acts)

    elif rtype == "email_monitor":
        # Scan gmail connector for monitored (e.g. immigration) mail
        from connectors import CONNECTORS
        try:
            profile = await db.profiles.find_one({"user_id": user_id}) or {}
            res = await CONNECTORS["gmail"].fetch(user_id, profile)
            monitored = [e for e in (res.data.get("emails") or []) if e.get("monitored")]
            if monitored:
                await _notify(user_id, "Monitored email detected",
                              f"{len(monitored)} email(s) match what you asked me to watch.", "alert")
                summary["notifications"] = 1
            else:
                await _notify(user_id, "Email watch: all clear",
                              "Nothing new from your monitored sources.", "info")
                summary["notifications"] = 1
        except Exception as e:  # noqa: BLE001
            logger.warning("email_monitor failed: %s", e)

    elif rtype == "deadline":
        # Surface upcoming deadlines from file summaries
        summaries = await db.file_summaries.find({"user_id": user_id}).to_list(50)
        deadlines = [d for s in summaries for d in (s.get("deadlines") or [])][:5]
        if deadlines:
            acts = await create_actions(user_id, [{
                "type": "deadline_alert", "title": f"Upcoming: {d.get('title')}",
                "what": f"Deadline {d.get('date')} from your documents.",
                "why": "Stay ahead of it.", "source": "Routine: " + name, "sensitive": False,
            } for d in deadlines], origin="routine")
            summary["actions"] = len(acts)
        await _notify(user_id, "Deadline check complete", f"{len(deadlines)} deadline(s) tracked.", "info")
        summary["notifications"] = 1

    elif rtype == "news":
        acts = await create_actions(user_id, [{
            "type": "news_brief", "title": "Your daily tech & startup brief",
            "what": "Prepared a short briefing tuned to your interests.",
            "why": "Keeps you current without the doomscroll.", "source": "Routine: " + name, "sensitive": False,
        }], origin="routine")
        summary["actions"] = len(acts)

    elif rtype == "prep":
        acts = await create_actions(user_id, [{
            "type": "general_task", "title": "Tomorrow is prepped",
            "what": "Reviewed tomorrow's calendar and laid out what matters.",
            "why": "So you can rest knowing it's handled.", "source": "Routine: " + name, "sensitive": False,
        }], origin="routine")
        summary["actions"] = len(acts)
    else:
        await _notify(user_id, name, routine.get("description") or "Routine ran.", "info")
        summary["notifications"] = 1

    await db.routines.update_one({"user_id": user_id, "id": routine["id"]},
                                 {"$set": {"last_fired": now_iso(), "last_fired_date": today_str()}})
    await _record_run(user_id, routine, summary)
    await log_event(user_id, "routine.fired", f"Ran routine: {name}", "routine", routine["id"], summary)
    return summary


async def run_due(now: dt.datetime | None = None) -> int:
    """Evaluate all enabled, time-based routines and fire those that are due."""
    db = get_db()
    now = now or dt.datetime.utcnow()
    fired = 0
    cursor = db.routines.find({"enabled": True})
    async for r in cursor:
        hhmm = _parse_hhmm(r.get("schedule", ""))
        if not hhmm:
            continue  # trigger-based routines fire via watchers/run-now
        if r.get("last_fired_date") == today_str():
            continue
        h, mn = hhmm
        # fire if current time >= scheduled time today (within the day)
        if (now.hour, now.minute) >= (h, mn):
            try:
                await fire_routine(r["user_id"], r)
                fired += 1
            except Exception as e:  # noqa: BLE001
                logger.warning("routine fire error: %s", e)
    return fired


async def _reindex_tick():
    """Continuous re-index pass: keep every connected user's context fresh."""
    from services.reindex import reindex_all
    try:
        await reindex_all()
    except Exception as e:  # noqa: BLE001
        logger.warning("reindex tick failed: %s", e)


async def _consolidate_tick():
    """Periodically fold high-churn learned memories into durable memory."""
    from services.memory_consolidation import consolidate_all
    try:
        await consolidate_all()
    except Exception as e:  # noqa: BLE001
        logger.warning("consolidation tick failed: %s", e)


def start_scheduler():
    global _scheduler
    if _scheduler:
        return
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(run_due, "interval", minutes=1, id="kaelra_routine_tick",
                       max_instances=1, coalesce=True)
    _scheduler.add_job(_reindex_tick, "interval", minutes=3, id="kaelra_reindex_tick",
                       max_instances=1, coalesce=True)
    _scheduler.add_job(_consolidate_tick, "interval", hours=6, id="kaelra_consolidate_tick",
                       max_instances=1, coalesce=True)
    _scheduler.start()
    logger.info("Kaelra routine + reindex + consolidation scheduler started")


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
