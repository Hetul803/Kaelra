"""Kaelra's proactive feed.

Turns the user's real, connected context (calendar/email/files) + what Kaelra has
recently handled into feed items. Each item carries a short *narration* (what
Kaelra would say out loud) and a structured *card* for the 'Kaelra speaks' view.
Narration is built deterministically from the card data — no LLM, fast + safe.
"""

from config import get_db
from utils import clean_docs
from services.context import build_today_context, build_card_payload
from services.briefing import get_cached
from services.actions import counts as action_counts


def _first_name(profile: dict, user: dict) -> str:
    return (profile or {}).get("call_me") or (user or {}).get("name") or "there"


async def build_feed(user: dict) -> dict:
    db = get_db()
    uid = user["id"]
    ctx = await build_today_context(user)
    cards = build_card_payload(ctx)
    name = _first_name(ctx.get("profile"), user)

    items = []

    # 1) Important emails Kaelra is watching
    for e in (cards.get("emails", {}).get("important") or [])[:5]:
        tags = []
        if e.get("monitored"):
            tags.append("this is on your monitored list")
        if e.get("needs_reply"):
            tags.append("it looks like it needs a reply")
        extra = (" — " + ", and ".join(tags) + ".") if tags else "."
        narration = (f"You have an email from {e.get('from')}. "
                     f"The subject is: {e.get('subject')}{extra} "
                     f"{e.get('snippet', '')}").strip()
        items.append({
            "id": f"email-{e.get('id')}",
            "kind": "email",
            "title": e.get("subject"),
            "subtitle": e.get("from"),
            "tone": "amber" if e.get("monitored") else ("teal" if e.get("needs_reply") else "default"),
            "narration": narration,
            "card": e,
        })

    # 2) Next calendar event
    events = cards.get("calendar", {}).get("events") if cards.get("calendar") else []
    if events:
        ev = events[0]
        loc = f" at {ev.get('location')}" if ev.get("location") else ""
        items.append({
            "id": f"event-{ev.get('id')}",
            "kind": "event",
            "title": ev.get("title"),
            "subtitle": f"{ev.get('start')} – {ev.get('end')}",
            "tone": "teal",
            "narration": f"Your next event is {ev.get('title')} at {ev.get('start')}{loc}.",
            "card": ev,
        })

    # 3) Files needing attention
    for f in (cards.get("files_needing_attention") or [])[:3]:
        items.append({
            "id": f"file-{f.get('id')}",
            "kind": "file",
            "title": f.get("name"),
            "subtitle": "Needs attention",
            "tone": "amber",
            "narration": f"One file may need your attention: {f.get('name')}. {f.get('reason', '')}".strip(),
            "card": f,
        })

    # 4) What Kaelra recently handled (notifications)
    notifs = await db.notifications.find({"user_id": uid}).sort("created_at", -1).to_list(8)
    for n in clean_docs(notifs)[:4]:
        items.append({
            "id": f"note-{n.get('id')}",
            "kind": "note",
            "title": n.get("title"),
            "subtitle": "Kaelra",
            "tone": "default",
            "narration": n.get("body") or n.get("title"),
            "card": {"title": n.get("title"), "body": n.get("body"), "type": n.get("type")},
            "read": bool(n.get("read")),
        })

    cnts = await action_counts(uid)
    briefing = await get_cached(uid)
    return {
        "name": name,
        "greeting": (briefing or {}).get("greeting"),
        "generated_at": (briefing or {}).get("generated_at"),
        "pending_actions": cnts.get("pending", 0),
        "items": items,
    }
