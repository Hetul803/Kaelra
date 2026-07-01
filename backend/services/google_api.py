"""Real Google API readers (Calendar, Gmail, Drive) — MULTI-ACCOUNT aware.

Each reader aggregates across EVERY connected Google account for the user and
merges results into the SAME shape the mock connectors produce. Items are tagged
with the source `account` email. Returns None only when no account is connected,
so the connector layer can fall back to mock/demo data.
"""

from __future__ import annotations

import base64
import datetime as dt

from googleapiclient.discovery import build

from services.google_oauth import get_all_credentials, get_credentials


def _svc(creds, name, version):
    return build(name, version, credentials=creds, cache_discovery=False)


def _fmt_time(iso: str) -> str:
    try:
        d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return d.strftime("%-I:%M %p")
    except Exception:
        return iso


async def calendar_today(user_id: str) -> dict | None:
    accounts = await get_all_credentials(user_id)
    if not accounts:
        return None
    events = []
    for email, creds in accounts:
        try:
            svc = _svc(creds, "calendar", "v3")
            now = dt.datetime.utcnow()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
            end = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"
            res = svc.events().list(calendarId="primary", timeMin=start, timeMax=end,
                                    singleEvents=True, orderBy="startTime", maxResults=20).execute()
            for e in res.get("items", []):
                s = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date")
                en = e.get("end", {}).get("dateTime") or e.get("end", {}).get("date")
                title = e.get("summary", "(no title)")
                kind = "class" if any(k in title.lower() for k in ["class", "lecture", "cs-", "course"]) else "work"
                events.append({"id": e.get("id"), "title": title, "start": _fmt_time(s) if s else "",
                               "end": _fmt_time(en) if en else "", "start_iso": s,
                               "location": e.get("location", ""), "kind": kind, "account": email})
        except Exception:
            continue
    events.sort(key=lambda x: x.get("start_iso") or "")
    return {"events": events, "primary_event": events[-1] if events else None}


async def gmail_important(user_id: str) -> dict | None:
    accounts = await get_all_credentials(user_id)
    if not accounts:
        return None
    emails = []
    for email, creds in accounts:
        try:
            svc = _svc(creds, "gmail", "v1")
            res = svc.users().messages().list(userId="me", maxResults=12,
                                              q="newer_than:7d category:primary").execute()
            ids = [m["id"] for m in res.get("messages", [])]
            for mid in ids[:10]:
                m = svc.users().messages().get(userId="me", id=mid, format="metadata",
                                               metadataHeaders=["From", "Subject"]).execute()
                headers = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
                labels = m.get("labelIds", [])
                sender = headers.get("From", "")
                subject = headers.get("Subject", "(no subject)")
                snippet = m.get("snippet", "")
                low = (sender + " " + subject + " " + snippet).lower()
                monitored = "immigration" if any(k in low for k in ["uscis", "immigration", "visa", "green card"]) else None
                important = bool(monitored) or "IMPORTANT" in labels or any(
                    k in low for k in ["deadline", "assignment", "recruiter", "interview", "invoice", "due"])
                needs_reply = any(k in low for k in ["?", "please reply", "let me know", "can you"])
                emails.append({"id": mid, "from": sender.split("<")[0].strip().strip('"') or sender,
                               "from_email": sender, "subject": subject, "snippet": snippet,
                               "important": important, "unread": "UNREAD" in labels,
                               "received": "", "needs_reply": needs_reply, "monitored": monitored,
                               "account": email})
        except Exception:
            continue
    important_list = [e for e in emails if e["important"]] or emails[:3]
    return {"emails": emails, "important": important_list,
            "unread_count": sum(1 for e in emails if e["unread"])}


async def drive_files(user_id: str) -> dict | None:
    accounts = await get_all_credentials(user_id)
    if not accounts:
        return None
    files = []
    for email, creds in accounts:
        try:
            svc = _svc(creds, "drive", "v3")
            res = svc.files().list(pageSize=20, orderBy="modifiedTime desc",
                                   fields="files(id,name,mimeType,modifiedTime)",
                                   q="trashed=false").execute()
            for f in res.get("files", []):
                name = f.get("name", "")
                low = name.lower()
                needs = any(k in low for k in ["syllabus", "form", "contract", "i-", "deadline"])
                files.append({"id": f.get("id"), "name": name, "kind": _kind(f.get("mimeType", "")),
                              "modified": (f.get("modifiedTime", "") or "")[:10],
                              "needs_attention": needs, "account": email,
                              "reason": "May contain deadlines worth turning into reminders" if needs else ""})
        except Exception:
            continue
    return {"files": files, "needs_attention": [f for f in files if f["needs_attention"]]}


def _kind(mime: str) -> str:
    if "pdf" in mime: return "pdf"
    if "document" in mime: return "doc"
    if "spreadsheet" in mime: return "sheet"
    if "presentation" in mime: return "slides"
    return "file"


async def drive_file_text(user_id: str, file_id: str) -> tuple[str, str]:
    """Return (filename, extracted text) for a Drive file (search all accounts)."""
    for _email, creds in await get_all_credentials(user_id):
        try:
            svc = _svc(creds, "drive", "v3")
            meta = svc.files().get(fileId=file_id, fields="name,mimeType").execute()
            name, mime = meta.get("name", "file"), meta.get("mimeType", "")
            if mime.startswith("application/vnd.google-apps"):
                data = svc.files().export(fileId=file_id, mimeType="text/plain").execute()
                return name, data.decode("utf-8", errors="ignore") if isinstance(data, bytes) else str(data)
            data = svc.files().get_media(fileId=file_id).execute()
            if mime == "application/pdf":
                import io
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(data))
                return name, "\n".join((p.extract_text() or "") for p in reader.pages)
            return name, data.decode("utf-8", errors="ignore")
        except Exception:
            continue
    return "", ""


async def create_gmail_draft(user_id: str, to: str, subject: str, body: str) -> str | None:
    """Create a Gmail DRAFT (never auto-send) on the primary account."""
    creds = await get_credentials(user_id)
    if not creds:
        return None
    try:
        from email.mime.text import MIMEText
        svc = _svc(creds, "gmail", "v1")
        msg = MIMEText(body)
        msg["to"] = to or ""
        msg["subject"] = subject or ""
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        draft = svc.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        return draft.get("id")
    except Exception:
        return None
