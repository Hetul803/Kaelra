"""Daily Briefing engine — precompute + cache the user's day.

The greeting (LLM) is cached per-day so the dashboard feels instant; structured
cards are built deterministically from connectors on every request. Generating a
briefing also proposes Action Queue items (pending approval).
"""

from config import get_db
from utils import new_id, now_iso, today_str, clean_doc
from services.context import build_today_context
from services import kaelra
from services.actions import create_actions
from services.audit import log_event


async def get_cached(user_id: str) -> dict | None:
    db = get_db()
    doc = await db.daily_briefings.find_one({"user_id": user_id, "date": today_str()})
    return clean_doc(doc)


async def generate(user: dict, force: bool = False, create_actions_flag: bool = True) -> dict:
    db = get_db()
    user_id = user["id"]
    if not force:
        cached = await get_cached(user_id)
        if cached:
            return cached

    context = await build_today_context(user)
    profile = context["profile"]
    session = f"briefing-{user_id}-{today_str()}"

    greeting = await kaelra.generate_briefing_text(profile, context, session)

    created = []
    if create_actions_flag:
        proposed = await kaelra.propose_actions(profile, context, session)
        created = await create_actions(user_id, proposed, origin="daily_briefing")

    doc = {
        "id": new_id(),
        "user_id": user_id,
        "date": today_str(),
        "greeting": greeting,
        "generated_at": now_iso(),
        "actions_prepared": len(created),
    }
    await db.daily_briefings.update_one(
        {"user_id": user_id, "date": today_str()}, {"$set": doc}, upsert=True
    )
    await log_event(user_id, "briefing.generated", "Daily briefing generated",
                    "briefing", doc["id"], {"actions_prepared": len(created)})
    return clean_doc(doc)
