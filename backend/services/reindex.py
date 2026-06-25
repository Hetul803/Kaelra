"""Continuous re-index — Kaelra keeps watching connected accounts and learns.

Runs on a schedule. For each connected user she:
  • detects NEW important emails / soon meetings / new documents,
  • proactively notifies (in-app + web push),
  • continuously LEARNS lightweight memories (people, documents, things to
    monitor) so her context evolves without a manual rebuild.

Baseline-first: the very first pass after connecting only records cursors and
does NOT spam historical items. Deterministic + cheap (no LLM).
"""

from __future__ import annotations

import datetime as dt
import logging

from config import get_db
from utils import new_id, now_iso
from connectors import CONNECTORS
from services.audit import log_event
from services.notify import notify

logger = logging.getLogger("kaelra.reindex")

SOON_MINUTES = 75
MAX_ALERTS_PER_PASS = 4
MAX_LEARN_PER_PASS = 3


async def _state(user_id: str) -> dict:
    db = get_db()
    return await db.reindex_state.find_one({"user_id": user_id}) or {
        "user_id": user_id, "seen_emails": [], "seen_events": [],
        "seen_files": [], "alerted_events": [], "baseline_done": False,
    }


async def _save_state(state: dict):
    db = get_db()
    state = {k: v for k, v in state.items() if k != "_id"}
    state["updated_at"] = now_iso()
    await db.reindex_state.update_one({"user_id": state["user_id"]}, {"$set": state}, upsert=True)


async def _indexing_paused(user_id: str) -> bool:
    db = get_db()
    st = await db.context_state.find_one({"user_id": user_id}) or {}
    return bool(st.get("indexing_paused"))


async def _learn_memory(user_id: str, category: str, content: str, source: str) -> bool:
    """Add a deduped, lightweight LEARNED memory (continuous consumption)."""
    db = get_db()
    content = (content or "").strip()
    if not content:
        return False
    if await db.memories.find_one({"user_id": user_id, "content": content}):
        return False
    await db.memories.insert_one({
        "id": new_id(), "user_id": user_id, "category": category, "content": content,
        "important": False, "temporary": False, "learned": True, "source": source,
        "created_at": now_iso(),
    })
    await log_event(user_id, "memory.learned", f"Learned: {content[:60]}", "memory", None, {"source": source})
    return True


async def _refresh_index(user_id: str, items: list[dict]):
    db = get_db()
    await db.indexed_items.delete_many({"user_id": user_id})
    if items:
        await db.indexed_items.insert_many(
            [{"id": new_id(), "user_id": user_id, "created_at": now_iso(), **it} for it in items]
        )


async def poll_user(user_id: str) -> dict:
    db = get_db()
    if await _indexing_paused(user_id):
        return {"skipped": "paused"}
    profile = await db.profiles.find_one({"user_id": user_id}) or {}
    connected = {a["provider"] async for a in db.connected_accounts.find({"user_id": user_id})
                 if a.get("status") == "connected"}
    if not connected:
        return {"skipped": "no_sources"}

    state = await _state(user_id)
    first = not state.get("baseline_done")
    alerts = 0
    learned = 0
    index_items: list[dict] = []

    # ---- Gmail ----
    if "gmail" in connected:
        try:
            gm = (await CONNECTORS["gmail"].fetch(user_id, profile)).data
            for e in gm.get("emails", []):
                index_items.append({"kind": "email", "title": e.get("subject", ""), "meta": e.get("from", "")})
            seen = set(state.get("seen_emails", []))
            for e in gm.get("important", []):
                eid = str(e.get("id"))
                if eid in seen:
                    continue
                seen.add(eid)
                if not first and alerts < MAX_ALERTS_PER_PASS:
                    sender = e.get("from", "someone")
                    await notify(user_id, f"New email from {sender}",
                                 e.get("subject", "") or "It looks important.", "alert", url="/")
                    alerts += 1
                    if learned < MAX_LEARN_PER_PASS and e.get("monitored"):
                        if await _learn_memory(user_id, "Things to monitor",
                                               f"Watching {e.get('monitored')} updates from {sender}.", "email"):
                            learned += 1
            state["seen_emails"] = list(seen)[-200:]
        except Exception as e:  # noqa: BLE001
            logger.warning("gmail reindex failed: %s", e)

    # ---- Calendar ----
    if "google_calendar" in connected:
        try:
            cal = (await CONNECTORS["google_calendar"].fetch(user_id, profile)).data
            events = cal.get("events", [])
            for ev in events:
                index_items.append({"kind": "event", "title": ev.get("title", ""), "meta": ev.get("location", "")})
            seen_ev = set(state.get("seen_events", []))
            alerted = set(state.get("alerted_events", []))
            now = dt.datetime.now(dt.timezone.utc)
            for ev in events:
                evid = str(ev.get("id"))
                seen_ev.add(evid)
                start_iso = ev.get("start_iso")
                if start_iso and evid not in alerted:
                    try:
                        start = dt.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
                        mins = (start - now).total_seconds() / 60
                        if 0 <= mins <= SOON_MINUTES and alerts < MAX_ALERTS_PER_PASS:
                            loc = f" {ev.get('location')}" if ev.get("location") else ""
                            await notify(user_id, f"Coming up: {ev.get('title')}",
                                         f"Starts at {ev.get('start')}.{loc}", "reminder", url="/")
                            alerted.add(evid)
                            alerts += 1
                    except Exception:  # noqa: BLE001
                        pass
            state["seen_events"] = list(seen_ev)[-200:]
            state["alerted_events"] = list(alerted)[-200:]
        except Exception as e:  # noqa: BLE001
            logger.warning("calendar reindex failed: %s", e)

    # ---- Drive ----
    if "google_drive" in connected:
        try:
            dr = (await CONNECTORS["google_drive"].fetch(user_id, profile)).data
            files = dr.get("files", [])
            for f in files:
                index_items.append({"kind": "file", "title": f.get("name", ""), "meta": f.get("kind", "")})
            seen_f = set(state.get("seen_files", []))
            for f in files:
                fid = str(f.get("id"))
                if fid in seen_f:
                    continue
                seen_f.add(fid)
                if first:
                    continue
                if f.get("needs_attention") and alerts < MAX_ALERTS_PER_PASS:
                    await notify(user_id, f"New document: {f.get('name')}",
                                 f.get("reason", "") or "May need your attention.", "info", url="/files")
                    alerts += 1
                if learned < MAX_LEARN_PER_PASS:
                    if await _learn_memory(user_id, "Important documents/files",
                                           f"{f.get('name')} is in your Drive.", "drive"):
                        learned += 1
            state["seen_files"] = list(seen_f)[-300:]
        except Exception as e:  # noqa: BLE001
            logger.warning("drive reindex failed: %s", e)

    if index_items:
        await _refresh_index(user_id, index_items)

    state["baseline_done"] = True
    await _save_state(state)
    return {"baseline": first, "alerts": alerts, "learned": learned, "sources": sorted(connected)}


async def reindex_all() -> int:
    """Scheduled pass: poll the demo operator + every real google-connected user."""
    db = get_db()
    user_ids: set[str] = set()
    async for t in db.google_tokens.find({}, {"user_id": 1}):
        if t.get("user_id"):
            user_ids.add(t["user_id"])
    demo = await db.users.find_one({"is_demo": True}, {"id": 1})
    if demo:
        user_ids.add(demo["id"])
    count = 0
    for uid in user_ids:
        try:
            await poll_user(uid)
            count += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("reindex poll failed for %s: %s", uid, e)
    return count
