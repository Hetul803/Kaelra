"""LLM memory consolidation — Kaelra's durable, self-improving memory.

Continuous re-index produces many small `learned` observations. This service
periodically (and on demand) asks the LLM to merge them into a compact set of
durable, non-redundant canonical memories (facts, preferences, important people,
watch-rules). This is the 'excellent, self-evolving memory' layer — fully synced
because it lives server-side and every device reads the same store.
"""

from __future__ import annotations

import json
import logging

from config import get_db
from utils import new_id, now_iso
from llm import complete_json, TaskType
from services.audit import log_event

logger = logging.getLogger("kaelra.memory")

MIN_TO_CONSOLIDATE = 3

_SYSTEM = (
    "You are Kaelra's memory consolidator. Merge raw observations into a SMALL set of durable, "
    "non-redundant canonical memories about the user. Combine duplicates, keep only lasting facts, "
    "preferences, important people, and 'watch' rules. Do NOT repeat anything already present in "
    "existing_memories. Return JSON: {\"memories\":[{\"category\":str,\"content\":str,\"important\":bool}]}. "
    "Allowed categories: 'Important people','Preferences','Things to monitor','Work/class schedule',"
    "'Important documents/files','About me'. Each content must be ONE concise sentence."
)


async def consolidate(user_id: str, force: bool = False) -> dict:
    db = get_db()
    learned = await db.memories.find(
        {"user_id": user_id, "learned": True, "consolidated": {"$ne": True}}
    ).sort("created_at", 1).to_list(200)
    if not learned:
        return {"consolidated": 0, "processed": 0, "skipped": "nothing"}
    if len(learned) < MIN_TO_CONSOLIDATE and not force:
        return {"consolidated": 0, "processed": 0, "skipped": "not_enough", "pending": len(learned)}

    existing = await db.memories.find({"user_id": user_id, "learned": {"$ne": True}}).to_list(200)
    payload = {
        "existing_memories": [m.get("content") for m in existing][:60],
        "new_observations": [
            {"category": m.get("category"), "content": m.get("content"), "source": m.get("source")}
            for m in learned
        ],
    }
    try:
        result = await complete_json(
            system=_SYSTEM, prompt=json.dumps(payload),
            session_id=f"memcon-{user_id}", task=TaskType.PRIORITIZATION, max_tokens=1500,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("consolidation llm failed: %s", e)
        return {"consolidated": 0, "processed": 0, "error": "llm"}

    mems = (result or {}).get("memories") or []
    created = 0
    for m in mems:
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if await db.memories.find_one({"user_id": user_id, "content": content}):
            continue
        await db.memories.insert_one({
            "id": new_id(), "user_id": user_id, "category": m.get("category") or "About me",
            "content": content, "important": bool(m.get("important")), "temporary": False,
            "learned": False, "consolidated": True, "source": "consolidation",
            "created_at": now_iso(),
        })
        created += 1

    ids = [m["id"] for m in learned]
    await db.memories.update_many(
        {"user_id": user_id, "id": {"$in": ids}},
        {"$set": {"consolidated": True, "consolidated_at": now_iso()}},
    )
    await log_event(user_id, "memory.consolidated",
                    f"Consolidated {len(learned)} observations into {created} durable memories",
                    "memory", None, {"created": created})
    return {"consolidated": created, "processed": len(learned)}


async def consolidate_all() -> int:
    db = get_db()
    count = 0
    pipeline = [
        {"$match": {"learned": True, "consolidated": {"$ne": True}}},
        {"$group": {"_id": "$user_id", "n": {"$sum": 1}}},
        {"$match": {"n": {"$gte": MIN_TO_CONSOLIDATE}}},
    ]
    async for row in db.memories.aggregate(pipeline):
        try:
            await consolidate(row["_id"])
            count += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("consolidate_all failed for %s: %s", row["_id"], e)
    return count
