"""Action Queue service — create, list, and transition actions safely.

Sensitive actions are gated behind explicit approval. Approving certain action
types produces deterministic side effects (e.g. creating a reminder/notification),
so the Action Queue feels like a real operator, not a list of suggestions.
"""

from config import get_db
from utils import new_id, now_iso, clean_doc, clean_docs
from services.audit import log_event
from services.kaelra import SENSITIVE_TYPES

VALID_STATUSES = {"pending", "approved", "rejected", "completed", "snoozed"}


async def create_action(user_id: str, action: dict, origin: str = "kaelra") -> dict | None:
    db = get_db()
    title = action.get("title", "").strip()
    if not title:
        return None
    # Dedup: skip if an identical pending action already exists.
    existing = await db.actions.find_one(
        {"user_id": user_id, "title": title, "status": {"$in": ["pending", "approved"]}}
    )
    if existing:
        return None
    a_type = action.get("type", "general_task")
    sensitive = bool(action.get("sensitive")) or a_type in SENSITIVE_TYPES
    doc = {
        "id": new_id(),
        "user_id": user_id,
        "type": a_type,
        "title": title,
        "what": action.get("what", ""),
        "why": action.get("why", ""),
        "source": action.get("source", origin),
        "sensitive": sensitive,
        "requires_approval": bool(action.get("requires_approval")) or sensitive,
        "status": "pending",
        "origin": origin,
        "snooze_until": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.actions.insert_one(doc)
    await log_event(user_id, "action.prepared", f"Prepared: {title}", "action", doc["id"],
                    {"type": a_type, "sensitive": sensitive})
    return clean_doc(doc)


async def create_actions(user_id: str, actions: list[dict], origin: str = "kaelra") -> list[dict]:
    created = []
    for a in actions:
        c = await create_action(user_id, a, origin)
        if c:
            created.append(c)
    return created


async def list_actions(user_id: str, status: str | None = None) -> list[dict]:
    db = get_db()
    query = {"user_id": user_id}
    if status and status != "all":
        query["status"] = status
    docs = await db.actions.find(query).sort("created_at", -1).to_list(200)
    return clean_docs(docs)


async def _side_effect_on_approve(user_id: str, action: dict):
    """Deterministic side effects when an action is approved."""
    db = get_db()
    reminder_types = {"create_reminder", "assignment_reminder", "commute_alert", "schedule_alarm_placeholder"}
    if action.get("type") in reminder_types:
        note = {
            "id": new_id(),
            "user_id": user_id,
            "title": action.get("title"),
            "body": action.get("what"),
            "type": "reminder",
            "scheduled_for": action.get("snooze_until"),
            "status": "scheduled",
            "read": False,
            "source_action": action.get("id"),
            "created_at": now_iso(),
        }
        await db.notifications.insert_one(note)


async def update_action(user_id: str, action_id: str, update: dict) -> dict | None:
    db = get_db()
    action = await db.actions.find_one({"user_id": user_id, "id": action_id})
    if not action:
        return None
    changes = {"updated_at": now_iso()}
    for field in ("title", "what", "snooze_until"):
        if update.get(field) is not None:
            changes[field] = update[field]
    new_status = update.get("status")
    if new_status and new_status in VALID_STATUSES:
        changes["status"] = new_status

    await db.actions.update_one({"id": action_id}, {"$set": changes})
    updated = await db.actions.find_one({"id": action_id})

    if new_status:
        await log_event(user_id, f"action.{new_status}", f"{new_status.title()}: {updated.get('title')}",
                        "action", action_id, {"type": updated.get("type")})
        if new_status == "approved":
            await _side_effect_on_approve(user_id, updated)
    elif any(k in changes for k in ("title", "what")):
        await log_event(user_id, "action.edited", f"Edited: {updated.get('title')}", "action", action_id)
    return clean_doc(updated)


async def counts(user_id: str) -> dict:
    db = get_db()
    pending = await db.actions.count_documents({"user_id": user_id, "status": "pending"})
    return {"pending": pending}
