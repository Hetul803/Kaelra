"""Unified notifier — one place that records an in-app notification AND delivers
a real browser push (when the user has a subscription + notifications enabled).

Everywhere Kaelra proactively reaches the user (scheduler routines + the
continuous re-index engine) goes through here, so behavior stays consistent.
"""

from __future__ import annotations

import logging

from config import get_db
from utils import new_id, now_iso
from services import push as push_service

logger = logging.getLogger("kaelra.notify")


async def notify(user_id: str, title: str, body: str = "", ntype: str = "reminder",
                 scheduled_for: str | None = None, url: str = "/", push: bool = True) -> dict:
    db = get_db()
    note = {
        "id": new_id(), "user_id": user_id, "title": title, "body": body,
        "type": ntype, "scheduled_for": scheduled_for, "status": "delivered",
        "read": False, "created_at": now_iso(),
    }
    await db.notifications.insert_one(note)
    if push:
        try:
            profile = await db.profiles.find_one(
                {"user_id": user_id}, {"notifications_enabled": 1}) or {}
            if profile.get("notifications_enabled", True):
                await push_service.send_push(user_id, title, body or title, url=url, tag=ntype)
        except Exception as e:  # noqa: BLE001
            logger.warning("push delivery skipped: %s", e)
    return {k: v for k, v in note.items() if k != "_id"}
