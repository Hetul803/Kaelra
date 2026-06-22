"""Deterministic 'today context' builder.

This is the heart of Kaelra-as-a-system: it assembles everything she knows
right now from connectors (calendar/gmail/drive/maps/news) + the database
(memories, goals, routines, pending actions, reminders). The LLM layer only
ever sees this structured context — it never invents the user's day.
"""

from config import get_db
from connectors import CONNECTORS
from utils import clean_docs


async def _connected_providers(user_id: str) -> set[str]:
    db = get_db()
    accounts = await db.connected_accounts.find({"user_id": user_id}).to_list(100)
    return {a["provider"] for a in accounts if a.get("status") == "connected"}


async def build_today_context(user: dict) -> dict:
    db = get_db()
    user_id = user["id"]
    profile = await db.profiles.find_one({"user_id": user_id}) or {}

    connected = await _connected_providers(user_id)

    async def run(provider):
        if provider not in connected:
            return None
        result = await CONNECTORS[provider].fetch(user_id, profile)
        return result.data if result.connected else None

    calendar = await run("google_calendar")
    gmail = await run("gmail")
    drive = await run("google_drive")
    maps = await run("maps")
    news = await run("news")

    goals = clean_docs(await db.goals.find({"user_id": user_id}).to_list(100))
    routines = clean_docs(await db.routines.find({"user_id": user_id}).to_list(100))
    memories = clean_docs(
        await db.memories.find({"user_id": user_id}).sort("created_at", -1).to_list(200)
    )
    pending_actions = clean_docs(
        await db.actions.find({"user_id": user_id, "status": "pending"})
        .sort("created_at", -1)
        .to_list(50)
    )
    reminders = clean_docs(
        await db.notifications.find({"user_id": user_id})
        .sort("created_at", -1)
        .to_list(50)
    )

    return {
        "profile": {
            "name": profile.get("name") or user.get("name") or "there",
            "call_me": profile.get("call_me") or profile.get("name") or "there",
            "tone": profile.get("tone", "friendly"),
            "interests": profile.get("interests", []),
            "life_areas": profile.get("life_areas", []),
            "routine": profile.get("routine"),
        },
        "calendar": calendar,
        "emails": gmail,
        "files": drive,
        "commute": maps,
        "news": news,
        "goals": goals,
        "routines": routines,
        "memories": memories,
        "pending_actions": pending_actions,
        "reminders": reminders,
    }


def build_card_payload(context: dict) -> dict:
    """Shape the structured cards for the Today dashboard from context."""
    emails = context.get("emails") or {}
    files = context.get("files") or {}
    return {
        "calendar": context.get("calendar"),
        "emails": {
            "important": (emails.get("important") or []),
            "unread_count": emails.get("unread_count", 0),
        },
        "commute": context.get("commute"),
        "news": context.get("news"),
        "goals": context.get("goals", []),
        "reminders": context.get("reminders", []),
        "files_needing_attention": files.get("needs_attention", []),
        "pending_actions": context.get("pending_actions", []),
    }
