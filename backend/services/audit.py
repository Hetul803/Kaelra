"""Audit log — every meaningful event Kaelra performs is recorded here."""

from config import get_db
from utils import new_id, now_iso


async def log_event(
    user_id: str,
    event: str,
    detail: str = "",
    entity_type: str | None = None,
    entity_id: str | None = None,
    meta: dict | None = None,
):
    db = get_db()
    doc = {
        "id": new_id(),
        "user_id": user_id,
        "event": event,
        "detail": detail,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "meta": meta or {},
        "created_at": now_iso(),
    }
    await db.audit_log.insert_one(doc)
    return doc
