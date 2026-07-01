"""Microsoft Graph readers (Outlook Mail + Calendar) — multi-account aware.

Same output shape as the Gmail/Calendar mock connectors so the connector layer
can swap real <-> mock. Returns None when Microsoft is not configured/connected.
"""

from __future__ import annotations

import datetime as dt

import httpx

from services.microsoft_oauth import get_all_access_tokens

GRAPH = "https://graph.microsoft.com/v1.0"


def _fmt(iso: str) -> str:
    try:
        return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%-I:%M %p")
    except Exception:
        return iso


async def outlook_important(user_id: str) -> dict | None:
    tokens = await get_all_access_tokens(user_id)
    if not tokens:
        return None
    emails = []
    async with httpx.AsyncClient(timeout=20) as client:
        for email, at in tokens:
            try:
                r = await client.get(
                    f"{GRAPH}/me/messages",
                    params={"$top": "10", "$select": "subject,from,bodyPreview,isRead,receivedDateTime"},
                    headers={"Authorization": f"Bearer {at}"})
                r.raise_for_status()
                for m in r.json().get("value", []):
                    sender = (m.get("from", {}) or {}).get("emailAddress", {}) or {}
                    subject = m.get("subject", "(no subject)")
                    snippet = m.get("bodyPreview", "")
                    low = f"{sender.get('name','')} {subject} {snippet}".lower()
                    monitored = "immigration" if any(k in low for k in ["uscis", "immigration", "visa"]) else None
                    important = bool(monitored) or any(
                        k in low for k in ["deadline", "assignment", "recruiter", "interview", "invoice", "due"])
                    emails.append({"id": m.get("id"), "from": sender.get("name") or sender.get("address", ""),
                                   "from_email": sender.get("address", ""), "subject": subject,
                                   "snippet": snippet, "important": important, "unread": not m.get("isRead", True),
                                   "received": _fmt(m.get("receivedDateTime", "")), "needs_reply": False,
                                   "monitored": monitored, "account": email})
            except Exception:
                continue
    important_list = [e for e in emails if e["important"]] or emails[:3]
    return {"emails": emails, "important": important_list,
            "unread_count": sum(1 for e in emails if e["unread"])}


async def outlook_events(user_id: str) -> dict | None:
    tokens = await get_all_access_tokens(user_id)
    if not tokens:
        return None
    events = []
    now = dt.datetime.now(dt.timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()
    async with httpx.AsyncClient(timeout=20) as client:
        for email, at in tokens:
            try:
                r = await client.get(
                    f"{GRAPH}/me/calendarView",
                    params={"startDateTime": start, "endDateTime": end, "$orderby": "start/dateTime", "$top": "20"},
                    headers={"Authorization": f"Bearer {at}", "Prefer": 'outlook.timezone="UTC"'})
                r.raise_for_status()
                for e in r.json().get("value", []):
                    s = (e.get("start", {}) or {}).get("dateTime")
                    en = (e.get("end", {}) or {}).get("dateTime")
                    title = e.get("subject", "(no title)")
                    events.append({"id": e.get("id"), "title": title, "start": _fmt(s) if s else "",
                                   "end": _fmt(en) if en else "", "start_iso": s,
                                   "location": (e.get("location", {}) or {}).get("displayName", ""),
                                   "kind": "work", "account": email})
            except Exception:
                continue
    events.sort(key=lambda x: x.get("start_iso") or "")
    return {"events": events, "primary_event": events[-1] if events else None}
