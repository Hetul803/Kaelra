"""Context Builder — the heart of 'Kaelra is a system, not a wrapper'.

After the user connects sources, Kaelra INDEXES what she can see (calendar,
email, drive/files), detects important documents, proposes MEMORIES for the
user to approve, and prepares useful actions. It reports human progress steps.
Kaelra only ever touches sources the user connected.
"""

from __future__ import annotations

import json

from config import get_db
from utils import new_id, now_iso, clean_docs
from connectors import CONNECTORS
from services.audit import log_event
from services.actions import create_actions
from llm import complete_json, TaskType

PROGRESS_STEPS = [
    "Give me a moment — I'm learning what matters to you.",
    "I'm organizing your context.",
    "I'm finding important files, routines, deadlines, and people.",
    "I'm preparing your first personal briefing.",
    "Your Kaelra context is ready.",
]


async def _connected(user_id: str) -> set[str]:
    db = get_db()
    return {a["provider"] async for a in db.connected_accounts.find({"user_id": user_id})
            if a.get("status") == "connected"}


async def build(user: dict) -> dict:
    db = get_db()
    user_id = user["id"]
    state = await db.context_state.find_one({"user_id": user_id}) or {}
    if state.get("indexing_paused"):
        return {"paused": True, "message": "Indexing is paused. Resume it in Privacy settings."}

    profile = await db.profiles.find_one({"user_id": user_id}) or {}
    connected = await _connected(user_id)

    indexed = {"events": 0, "emails": 0, "files": 0}
    index_items = []
    important_docs = []
    signal = {"events": [], "important_emails": [], "files": []}

    if "google_calendar" in connected:
        cal = (await CONNECTORS["google_calendar"].fetch(user_id, profile)).data
        evs = cal.get("events", [])
        indexed["events"] = len(evs)
        signal["events"] = [{"title": e["title"], "start": e.get("start")} for e in evs]
        for e in evs:
            index_items.append({"kind": "event", "title": e["title"], "meta": e.get("location", "")})

    if "gmail" in connected:
        gm = (await CONNECTORS["gmail"].fetch(user_id, profile)).data
        imp = gm.get("important", [])
        indexed["emails"] = len(gm.get("emails", []))
        signal["important_emails"] = [{"from": e["from"], "subject": e["subject"], "monitored": e.get("monitored")} for e in imp]
        for e in imp:
            index_items.append({"kind": "email", "title": e["subject"], "meta": e["from"]})

    if "google_drive" in connected:
        dr = (await CONNECTORS["google_drive"].fetch(user_id, profile)).data
        files = dr.get("files", [])
        indexed["files"] = len(files)
        important_docs = [f["name"] for f in dr.get("needs_attention", [])]
        signal["files"] = [{"name": f["name"], "kind": f.get("kind")} for f in files]
        for f in files:
            index_items.append({"kind": "file", "title": f["name"], "meta": f.get("kind", "")})

    # Persist a light index (references only — never raw content dumps)
    await db.indexed_items.delete_many({"user_id": user_id})
    if index_items:
        await db.indexed_items.insert_many([{"id": new_id(), "user_id": user_id, "created_at": now_iso(), **it}
                                            for it in index_items])

    # Ask the LLM to PROPOSE memories (user approves later) + a couple actions
    suggested = await _suggest_memories(profile, signal, user_id)
    actions = await create_actions(user_id, [
        {"type": "organize_file_suggestion", "title": "Review the documents I indexed",
         "what": f"I indexed {indexed['files']} file(s); {len(important_docs)} may need attention.",
         "why": "So nothing important slips through.", "source": "Context Builder", "sensitive": False},
    ] if important_docs else [], origin="context_builder")

    summary = {
        "indexed": indexed,
        "important_docs": important_docs,
        "suggested_memories": len(suggested),
        "actions_prepared": len(actions),
        "sources": sorted(connected),
        "steps": PROGRESS_STEPS,
    }
    await db.context_state.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "last_built": now_iso(), "indexed": indexed,
                  "indexing_paused": False, "updated_at": now_iso()}},
        upsert=True,
    )
    await log_event(user_id, "context.built", "Built personal context", meta=indexed)
    return summary


async def _suggest_memories(profile: dict, signal: dict, user_id: str) -> list[dict]:
    db = get_db()
    if not any(signal.values()):
        return []
    system = (
        "You are Kaelra building a user's context from the sources they connected. "
        "Propose 3-6 concise MEMORIES worth remembering (facts, people, routines, things to monitor, "
        "important documents). Return JSON {\"memories\": [{\"category\": one of "
        "[Personal facts, Work/class schedule, Goals, Preferences, Important people, Places, Routines, "
        "Interests, Important documents/files, Things to monitor], \"content\": short fact}]}. "
        "Only use the provided signal; do not invent."
    )
    prompt = json.dumps(signal, indent=2)
    try:
        data = await complete_json(system=system, prompt=prompt, session_id=f"ctx-{user_id}",
                                   task=TaskType.PRIORITIZATION)
        mems = data.get("memories", []) if isinstance(data, dict) else []
    except Exception:
        mems = []
    docs = []
    for m in mems[:6]:
        if not isinstance(m, dict) or not m.get("content"):
            continue
        docs.append({"id": new_id(), "user_id": user_id, "category": m.get("category", "Personal facts"),
                     "content": m["content"], "status": "suggested", "created_at": now_iso()})
    if docs:
        await db.suggested_memories.insert_many(docs)
    return docs


async def status(user_id: str) -> dict:
    db = get_db()
    st = await db.context_state.find_one({"user_id": user_id}) or {}
    pending = await db.suggested_memories.count_documents({"user_id": user_id, "status": "suggested"})
    return {
        "last_built": st.get("last_built"),
        "indexed": st.get("indexed", {"events": 0, "emails": 0, "files": 0}),
        "indexing_paused": bool(st.get("indexing_paused")),
        "suggested_memories_pending": pending,
    }


async def list_suggested(user_id: str) -> list[dict]:
    db = get_db()
    docs = await db.suggested_memories.find({"user_id": user_id, "status": "suggested"}).to_list(50)
    return clean_docs(docs)


async def resolve_suggested(user_id: str, sm_id: str, approve: bool) -> bool:
    db = get_db()
    sm = await db.suggested_memories.find_one({"user_id": user_id, "id": sm_id})
    if not sm:
        return False
    if approve:
        await db.memories.insert_one({"id": new_id(), "user_id": user_id, "category": sm["category"],
                                      "content": sm["content"], "important": False, "temporary": False,
                                      "created_at": now_iso()})
        await log_event(user_id, "memory.added", f"Approved suggested memory: {sm['content'][:50]}")
    await db.suggested_memories.update_one({"id": sm_id}, {"$set": {"status": "approved" if approve else "rejected"}})
    return True


async def set_paused(user_id: str, paused: bool):
    db = get_db()
    await db.context_state.update_one({"user_id": user_id},
                                      {"$set": {"user_id": user_id, "indexing_paused": paused, "updated_at": now_iso()}},
                                      upsert=True)
    await log_event(user_id, "context.indexing", "Paused" if paused else "Resumed")


async def delete_indexed(user_id: str):
    db = get_db()
    await db.indexed_items.delete_many({"user_id": user_id})
    await db.suggested_memories.delete_many({"user_id": user_id})
    await db.context_state.update_one({"user_id": user_id},
                                      {"$set": {"indexed": {"events": 0, "emails": 0, "files": 0}, "last_built": None}},
                                      upsert=True)
    await log_event(user_id, "context.deleted", "Deleted indexed data")
